from typing import Optional, List, Union
from pydantic import BaseModel, validator
import datetime
from enum import Enum


class GamesScheme(BaseModel):
    id: str = None
    name: str = None
    code_name: str = None
    descriptions: str = None

    class Config:
        orm_mode = True


class UsersScheme(BaseModel):
    id: str = None
    created_utc: datetime.datetime = None
    updated_utc: datetime.datetime = None
    lastname: str = None
    firstname: str = None
    middlename: str = None
    email: str = None
    phone: str = None
    gender: str = None
    birthday: datetime.date = None
    login: str = None
    is_locked: bool = None
    is_admin: bool = None
    is_superadmin: bool = None

    rel_allowed_games: Union[List[GamesScheme]] = None

    class Config:
        orm_mode = True


class UserCreateScheme(BaseModel):
    lastname: str
    firstname: str
    middlename: str
    email: str = None
    phone: str = None
    gender: str
    birthday: datetime.date = None
    login: str
    password: str
    is_admin: bool
    is_superadmin: bool

    @validator('gender')
    def gender_validate(cls, v):
        if v not in ['male', 'female']:
            raise ValueError('The gender field can only be equal to "male", "female"')
        return v


class UserUpdateScheme(BaseModel):
    update_utc: datetime.datetime = datetime.datetime.utcnow()
    lastname: Optional[str] = None
    firstname: Optional[str] = None
    middlename: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    gender: Optional[str] = None
    birthday: Optional[datetime.date] = None
    login: Optional[str] = None
    password: Optional[str] = None
    is_locked: Optional[bool] = None
    is_admin: Optional[bool] = None
    is_superadmin: Optional[bool] = None


class UserResponseScheme(BaseModel):
    count: int
    users: List[UsersScheme]
    page: int = None
    size: int = None


class Test(BaseModel):
    lastname: str
    firstname: str
    middlename: str


class CheckScheme(BaseModel):
    check: bool


class ResetPasswordResponseScheme(BaseModel):
    res_pass_id: Optional[str] = None
    check_secret_key: Optional[bool] = None
    is_reset_password: Optional[bool] = None


class UploadPhotoResponseScheme(BaseModel):
    msg: Optional[str] = None


class UploadPhotoBodyScheme(BaseModel):
    data: str


class TestResponseScheme(BaseModel):
    msg: Optional[bytes] = None


class ResetPasswordPathScheme(str, Enum):
    init = "init"
    secret_key = "secret_key"
    reset = "reset"


class ResetPasswordScheme(BaseModel):
    email: Optional[str] = None
    user_id: Optional[str] = None
    secret_key: Optional[str] = None
    password: Optional[str] = None
    res_pass_id: Optional[str] = None
