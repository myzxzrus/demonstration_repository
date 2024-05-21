import asyncio
import subprocess

from fastapi import APIRouter, Depends, status, Response, HTTPException, File, UploadFile, Request
from .schemas import *
from sqlalchemy.orm import Session
from ...session import get_db
from ...models import Users
from .service import BaseModelRequestUser, create_user_registration, update_user, ResetPasswordService, \
    get_photo_service, delete_photo_service, save_photo_file, del_user, ReportUserService, ReportUserUpdateService
from ..auth.service import get_current_user, verify_token
from ..auth.schemas import TokenData
from ...config import Config
from starlette.responses import FileResponse

base_url = Config.base_url

router = APIRouter(tags=['Users'], prefix=f'{base_url}/users')


@router.get("/users", response_model=UserResponseScheme)
async def get_users(page: int = None, size: int = None, filters: str = None, session: Session = Depends(get_db),
                    current_user: TokenData = Depends(get_current_user)) -> UserResponseScheme:
    if current_user.role == 'admin' or current_user.role == 'superadmin':
        response_get = BaseModelRequestUser(session, page=page, size=size, filters=filters, role=current_user.role,
                                            global_field=['firstname', 'lastname', 'middlename', 'email', 'phone',
                                                          'login'], key_is_date='birthday')
        res = response_get.make_response()
        res['users'] = res['response']
        return res
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Not available to current user')


@router.get("/user/{user_id}", response_model=UsersScheme)
async def get_user(user_id: str, session: Session = Depends(get_db),
                   current_user: TokenData = Depends(get_current_user)) -> UsersScheme:
    if current_user:
        response_get = session.query(Users).filter(Users.id == user_id).one()
        return response_get


@router.patch("/user/{user_id}", response_model=UsersScheme)
async def patch_user(user_id: str, body: UserUpdateScheme, session: Session = Depends(get_db),
                     current_user: TokenData = Depends(get_current_user)) -> UsersScheme | FileResponse:
    if current_user:
        user = await update_user(user_id, body, session, current_user)
        if getattr(body, 'password', False):
            response_get = ReportUserUpdateService(user, body)
            result = response_get.make_report()
            subprocess.run(["libreoffice", "--headless", "--convert-to", "pdf", result['filename'], "--outdir", result['base_path'] + '/temp/out/'])
            return FileResponse(path=result['res'], media_type='application/pdf')
        return user


@router.delete("/user/{user_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_user(user_id: str, session: Session = Depends(get_db),
                      current_user: TokenData = Depends(get_current_user)):
    if current_user.role == 'admin' or current_user.role == 'superadmin':
        await del_user(session, user_id, current_user)


@router.post("/user", response_model=UsersScheme)
async def create_user(body: UserCreateScheme, request: Request, session: Session = Depends(get_db)) -> FileResponse:
    if not not request.headers.get('authorization'):
        data = request.headers.get('authorization').replace('Bearer ', '')
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        res = verify_token(data, credentials_exception)
        no_admin = not bool((res.role == 'admin') or (res.role == 'superadmin'))
        role = res.role
        await create_user_registration(body, session, no_admin=no_admin, role=role, token_data=res)
        response_get = ReportUserService(body)
        result = response_get.make_report()
        subprocess.run(["libreoffice", "--headless", "--convert-to", "pdf", result['filename'], "--outdir",
                        result['base_path'] + '/temp/out/'])
        return FileResponse(path=result['res'], media_type='application/pdf')
    else:
        await create_user_registration(body, session, no_admin=True, role='user')
        response_get = ReportUserService(body)
        result = response_get.make_report()
        subprocess.run(["libreoffice", "--headless", "--convert-to", "pdf", result['filename'], "--outdir",
                        result['base_path'] + '/temp/out/'])
        return FileResponse(path=result['res'], media_type='application/pdf')



@router.get("/current_user", response_model=UsersScheme)
async def get_cur_user(session: Session = Depends(get_db),
                   current_user: TokenData = Depends(get_current_user)) -> UsersScheme:
    response_get = session.query(Users).filter(Users.id == current_user.user_id).one()
    return response_get


@router.get("/check_email", response_model=CheckScheme)
async def get_check_email(email: str, session: Session = Depends(get_db)) -> dict:
    response_get = session.query(Users).filter(Users.email == email).all()
    if len(response_get) > 0:
        return {'check': False}
    else:
        return {'check': True}


@router.get("/check_login", response_model=CheckScheme)
async def get_check_login(login: str, session: Session = Depends(get_db)) -> dict:
    response_get = session.query(Users).filter(Users.login == login).all()
    if len(response_get) > 0:
        return {'check': False}
    else:
        return {'check': True}


@router.post("/reset_password/{type_operation}", response_model=ResetPasswordResponseScheme)
async def post_reset_password(type_operation: ResetPasswordPathScheme, body: ResetPasswordScheme,
                   session: Session = Depends(get_db)) -> dict:
    res_pass = ResetPasswordService(session, type_operation, **body.dict())
    try:
        if type_operation == 'init':
            res_pass_id = res_pass.reset_password_init()
            return {'res_pass_id': res_pass_id}
        elif type_operation == 'secret_key':
            is_validate = res_pass.validate_secret_key()
            return {'check_secret_key': is_validate}
        elif type_operation == 'reset':
            is_reset_password = res_pass.reset_password()
            return {'is_reset_password': is_reset_password}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail=e.data)


@router.post("/photo", status_code=status.HTTP_201_CREATED, response_model=UploadPhotoResponseScheme)
async def upload_photo(file: UploadFile = File(...), session: Session = Depends(get_db),
                       current_user: TokenData = Depends(get_current_user)):
    if current_user:
        await save_photo_file(session, current_user.user_id, file)
        return {'msg': 'Photo saved'}


@router.get("/photo", response_model=UploadPhotoResponseScheme)
async def get_photo(session: Session = Depends(get_db), current_user: TokenData = Depends(get_current_user)):
    if current_user:
        q=1
        res = await get_photo_service(session, current_user.user_id)
        return {'msg': res}


@router.delete("/photo", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_photo(session: Session = Depends(get_db), current_user: TokenData = Depends(get_current_user)):
    if current_user:
        await delete_photo_service(session, current_user.user_id)


@router.post("/test")
async def test(request: Request):
    print(request.headers.get('authorization'))
