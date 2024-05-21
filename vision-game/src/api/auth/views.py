from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ...session import get_db
from ...tools.hashing import verify_password
from ...models import Users
from .service import create_token, get_current_user, get_current_user_refres
from ...config import Config
from .schemas import *

base_url = Config.base_url

router = APIRouter(tags=['Auth'], prefix=f'{base_url}/auth')


@router.post('/login', response_model=LoginResponseScheme)
def login(request: OAuth2PasswordRequestForm = Depends(), database: Session = Depends(get_db)):
    user: Users = database.query(Users).filter(Users.login == request.username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Invalid Credentials')

    if not verify_password(request.password, user.password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid Password')

    if user.is_locked:
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail='This user is blocked')

    # Generate a JWT Token
    refresh_token = create_token(data={'login': user.login, 'email': user.email, 'user_id': user.id, 'role': 'superadmin' if user.is_superadmin else 'admin' if user.is_admin else 'user'}, is_refresh=True)
    access_token = create_token(data={'login': user.login, 'email': user.email, 'user_id': user.id, 'role': 'superadmin' if user.is_superadmin else 'admin' if user.is_admin else 'user'})


    return {'access_token': access_token['encoded_jwt'],
            'expire_access_token': access_token['expire'],
            'refresh_token': refresh_token['encoded_jwt'],
            'expire_refresh_token': refresh_token['expire'],
            'token_type': 'bearer',
            'user': user,
            'role': 'superadmin' if user.is_superadmin else 'admin' if user.is_admin else 'user'}


@router.get("/refresh_token", response_model=RefreshResponseScheme)
async def refresh_token(database: Session = Depends(get_db), current_user: TokenData = Depends(get_current_user_refres)):
    user: Users = database.query(Users).filter(Users.login == current_user.login).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Invalid Credentials')

    if user.is_locked:
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail='This user is blocked')

    access_token = create_token(data={'login': user.login, 'email': user.email, 'user_id': user.id, 'role': 'superadmin' if user.is_superadmin else 'admin' if user.is_admin else 'user'})

    return {'access_token': access_token['encoded_jwt'],
            'expire_access_token': access_token['expire'],
            'token_type': 'bearer',
            'user': user,
            'role': 'superadmin' if user.is_superadmin else 'admin' if user.is_admin else 'user'}
