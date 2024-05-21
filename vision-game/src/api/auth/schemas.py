from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from ..users.schemas import UsersScheme


class Login(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    login: Optional[str] = None
    email: Optional[str] = None
    user_id: Optional[str] = None
    role: Optional[str] = None



class LoginResponseScheme(BaseModel):
    access_token: str
    expire_access_token: datetime
    refresh_token: str
    expire_refresh_token: datetime
    token_type: str
    user: UsersScheme
    role: str


class RefreshResponseScheme(BaseModel):
    access_token: str
    expire_access_token: datetime
    token_type: str
    user: UsersScheme
    role: str


# {'access_token': access_token, 'token_type': 'bearer', 'user': user, 'role': 'string'}