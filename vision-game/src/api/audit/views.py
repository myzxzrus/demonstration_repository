from typing import Dict

from fastapi import APIRouter, Depends, status, HTTPException
from starlette.responses import FileResponse
from .schemas import *
from sqlalchemy.orm import Session
from ...session import get_db
from ...redis_session import get_redis
from .service import BaseModelRequestAudit, ReportAuditService
from ...config import Config
from ..auth.schemas import TokenData
from ..auth.service import get_current_user
from ...tools.audit import UsersMonitor, RedisSession

base_url = Config.base_url

router = APIRouter(tags=['Audit'], prefix=f'{base_url}/audit')


@router.get("/items", response_model=AuditResponseScheme)
async def get_users(page: int = None, size: int = None, filters: str = None, session: Session = Depends(get_db),
                    current_user: TokenData = Depends(get_current_user)) -> AuditResponseScheme:
    if current_user.role == 'admin' or current_user.role == 'superadmin':
        page = page if page else 1
        size = size if size else 10
        response_get = BaseModelRequestAudit(session, page=page, size=size, filters=filters, role=current_user.role,
                                             key_is_date='date', global_field=['user', 'action'])
        res = response_get.make_response()
        res['audit'] = res['response']
        return res
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Not available to current user')


@router.get("/download_report")
async def get_users(filters: str = None, session: Session = Depends(get_db),
                    current_user: TokenData = Depends(get_current_user)) -> FileResponse:
    if current_user.role == 'admin' or current_user.role == 'superadmin':
        response_get = ReportAuditService(session, filters=filters, role=current_user.role,
                                             key_is_date='date')
        res = response_get.make_report()
        return FileResponse(path=res, filename='audit_report', media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')


@router.post("/set_user_online", status_code=202)
async def set_online(current_user: TokenData = Depends(get_current_user),
                     redis_session: RedisSession = Depends(get_redis)) -> Dict:
    if current_user and redis_session:
        um = UsersMonitor(redis_session)
        um.set_active_user(current_user)
    return {"msg": f'Users - {current_user.login} set online'}


@router.get("/get_users_online")
async def get_online(current_user: TokenData = Depends(get_current_user),
                     redis_session: RedisSession = Depends(get_redis)) -> List:
    result = []
    if current_user.role == 'admin' or current_user.role == 'superadmin' and redis_session:
        um = UsersMonitor(redis_session)
        result = um.get_active_users()
    return result


# @router.get("/get_statistic")
# async def get_online(current_user: TokenData = Depends(get_current_user),
#                      redis_session: RedisSession = Depends(get_redis)) -> List:
#     result = []
#     if current_user.role == 'admin' or current_user.role == 'superadmin' and redis_session:
#         um = UsersMonitor(redis_session)
#         result = um.get_active_users()
#     return result
