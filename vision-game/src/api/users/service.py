import base64
import copy
import os, shutil
import subprocess
import uuid
import random
import smtplib
from abc import ABC, abstractmethod
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from sqlalchemy import and_
from sqlalchemy.orm import Session

from ...models import Users, ResetPassword, UsersPhoto, GamesPlayed, AllowedGames
from .schemas import UserCreateScheme, UserUpdateScheme, ResetPasswordPathScheme
from typing import Union
from fastapi import HTTPException
from ...tools.request_service import BaseModelRequest
from ...tools.validation import verify_email_exist
from ...tools.audit import add_audit
from ...config import SMTP_EMAIL, SMTP_EMAIL_PASSWORD, SMTP_SERVER, SMTP_PORT
from ..auth.schemas import TokenData
from odtemplater import ConfigurationMyOdt, ODTemplater


class ErrorSecretKey(Exception):
    def __init__(self, data):
        self.data = data

    def __str__(self):
        return repr(self.data)


class ExpiredSecretKey(Exception):
    def __init__(self, data):
        self.data = data

    def __str__(self):
        return repr(self.data)


class BaseModelRequestUser(BaseModelRequest):
    def __init__(self, session: Session, **kwargs):
        super().__init__(session, Users, **kwargs)
        self.res = self.apply_filter_user()

    def apply_filter_user(self):
        if self.role != 'superadmin' and self.model == Users:
            self.request = self.request.filter(Users.is_superadmin == False)
        return self.apply_filter()


async def new_user_register(body: UserCreateScheme, session: Session, no_admin: bool, role: str, token_data) -> Users:
    now_utc = datetime.utcnow()
    user = Users(password=body.password)
    user.id = str(uuid.uuid4())
    user.created_utc = now_utc
    user.updated_utc = now_utc
    user.lastname = body.lastname
    user.firstname = body.firstname
    user.middlename = body.middlename
    user.email = body.email
    user.phone = body.phone
    user.gender = body.gender
    user.birthday = body.birthday
    user.login = body.login
    user.is_locked = False
    if not no_admin:
        if role == 'superadmin':
            user.is_superadmin = body.is_superadmin
            user.is_admin = body.is_admin
        elif role == 'admin':
            user.is_superadmin = False
            user.is_admin = body.is_admin
        else:
            user.is_superadmin = False
            user.is_admin = False
    else:
        user.is_superadmin = False
        user.is_admin = False
    if token_data is not None:
        current = session.query(Users).filter(Users.id == token_data.user_id).first()
        description = f'{current.fio_and_login} - создал пользователя {user.fio_and_login}'
        add_audit(session, user=current.login, action=description)
    else:
        description = f'Новый пользователь {user.fio_and_login} - зарегистрированный через форму регистрации.'
        add_audit(session, user='-', action=description)
    session.add(user)
    session.commit()
    return user


async def create_user_registration(request: UserCreateScheme, session: Session, **kwargs) -> Union[
    Users, HTTPException]:
    user = await verify_email_exist(request.email, session)
    if user:
        raise HTTPException(status_code=400, detail='The user with this email already exist in the system.')
    no_admin = kwargs['no_admin']
    role = kwargs['role']
    token_data = kwargs['token_data'] if 'token_data' in kwargs else None
    new_user = await new_user_register(request, session, no_admin, role, token_data)
    return new_user


async def update_user(user_id: str, request: UserUpdateScheme, session: Session, current_user: TokenData) -> Union[Users, HTTPException]:
    user_update = session.query(Users).filter(Users.id == user_id).first()
    temp_request = copy.deepcopy(request)
    for attr in temp_request:
        if attr[1] is None:
            delattr(request, attr[0])
    user_update.update(**request.dict())
    current = session.query(Users).filter(Users.id == current_user.user_id).first()
    description = f'{current.fio_and_login} - обновил данные пользователя {user_update.fio_and_login}'
    add_audit(session, user=current.login, action=description)
    session.commit()
    return user_update


async def del_user(session: Session, user_id: str, current_user: TokenData):
    session.query(ResetPassword).filter(ResetPassword.user_id == user_id).delete()
    session.query(GamesPlayed).filter(GamesPlayed.user_id == user_id).delete()
    session.query(UsersPhoto).filter(UsersPhoto.user_id == user_id).delete()
    files = session.query(UsersPhoto).filter(UsersPhoto.user_id == user_id).all()
    for i in files:
        my_file = Path(f'./avatars/{i.filename}')
        my_file.unlink(missing_ok=True)
        session.delete(i)
    session.query(AllowedGames).filter(AllowedGames.user_id == user_id).delete()
    del_user = session.query(Users).filter(Users.id == user_id).one()
    current = session.query(Users).filter(Users.id == current_user.user_id).first()
    description = f'{current.fio_and_login} - удалил пользователя {del_user.fio_and_login}'
    add_audit(session, user=current.login, action=description)
    session.delete(del_user)
    session.commit()


class ResetPasswordService:
    SECRET_KEY_EXPIRE_MINUTES = 15

    def __init__(self, session: Session, type_operation: ResetPasswordPathScheme, **kwargs):
        self.session = session
        self.type_operation = type_operation
        self.email = kwargs['email'] if 'email' in kwargs else None
        self.user_id = kwargs['user_id'] if 'user_id' in kwargs else None
        self.current_user = self.session.query(Users).filter(Users.email == self.email).one()
        self.secret_key = kwargs['secret_key'] if 'secret_key' in kwargs else None
        self.password = kwargs['password'] if 'password' in kwargs else None
        self.res_pass_id = kwargs['res_pass_id'] if 'res_pass_id' in kwargs else None
        self.user_id = self.__get_user_id()

    def __create_secret_key(self) -> str:
        return ''.join([str(random.randint(0, 999)).zfill(3) for _ in range(2)])

    def __get_user_id(self) -> str:
        if self.user_id is not None:
            res = self.session.query(Users).filter(and_(Users.email == self.email, Users.id == self.user_id)).first()
            return res.id
        else:
            res = self.session.query(Users).filter(Users.email == self.email).first()
            return res.id

    def __send_code(self, code):

        msg = MIMEMultipart()
        msg['From'] = SMTP_EMAIL
        msg['To'] = self.email
        msg['Subject'] = "Test Mail"
        body = f'Ваш код для сброса пароля: {code}'
        msg.attach(MIMEText(body, 'plain'))
        text = msg.as_string()

        # smtp_obj = smtplib.SMTP('smtp.gmail.com', 587)
        # smtp_obj.connect('smtp.gmail.com', 587)

        # smtp_obj = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        smtp_obj = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        smtp_obj.connect(SMTP_SERVER, SMTP_PORT)
        smtp_obj.ehlo()
        # smtp_obj.starttls()
        smtp_obj.login(SMTP_EMAIL, SMTP_EMAIL_PASSWORD)
        smtp_obj.sendmail(SMTP_EMAIL, self.email, text)
        smtp_obj.quit()

    def reset_password_init(self):
        try:
            now_utc = datetime.utcnow()
            end_uts = now_utc + timedelta(minutes=self.SECRET_KEY_EXPIRE_MINUTES)

            res_pass = ResetPassword()
            res_pass.id = str(uuid.uuid4())
            res_pass.created_utc = now_utc
            res_pass.disabled_utc = end_uts
            res_pass.user_id = self.user_id
            res_pass.secret_key = self.__create_secret_key()
            res_pass.email = self.email
            res_pass.is_reset = False

            self.__send_code(res_pass.secret_key)
            description = f'{self.current_user.fio_and_login} - инициировал восстановление пароля'
            add_audit(self.session, user=self.current_user.login, action=description)

            self.session.add(res_pass)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
        return res_pass.id

    def validate_secret_key(self) -> bool:
        now_utc = datetime.utcnow()
        if self.res_pass_id is not None:
            val: ResetPassword = self.session.query(ResetPassword).filter(ResetPassword.id == self.res_pass_id).one()
            if val:
                if now_utc > val.disabled_utc:
                    raise ExpiredSecretKey('Истек срок действия секретного ключа')
                if val.secret_key != self.secret_key:
                    raise ErrorSecretKey('Неверный секретный ключь')

                description = f'{self.current_user.fio_and_login} - верифицировал проверочный код отправленный на email'
                add_audit(self.session, user=self.current_user.login, action=description)
                return True
            else:
                raise ErrorSecretKey('Не получен секретный ключь')

    def reset_password(self):
        user: Users = self.session.query(Users).filter(Users.id == self.user_id).one()
        now_utc = datetime.utcnow()
        if user.rel_res_pass.secret_key != self.secret_key or user.rel_res_pass.is_reset:
            raise ErrorSecretKey('Неверный секретный ключь')
        if now_utc > user.rel_res_pass.disabled_utc:
            raise ExpiredSecretKey('Истек срок действия секретного ключа')

        user.reset_password(self.password)
        user.rel_res_pass.is_reset = True

        description = f'{self.current_user.fio_and_login} - успешно восстановил пароль'
        add_audit(self.session, user=self.current_user.login, action=description)
        self.session.commit()
        return True


async def save_photo_file(session: Session, user_id: str, data: any) -> str:
    Path('./avatars').mkdir(parents=True, exist_ok=True)
    filename = f'{user_id}_avatar.{data.filename.split(".")[-1]}'
    with open(f'./avatars/{filename}', 'wb') as file:
        file.write(data.file.read())
    is_exists_photo = session.query(UsersPhoto).filter(UsersPhoto.user_id == user_id).scalar()
    if is_exists_photo:
        user_ph = session.query(UsersPhoto).filter(UsersPhoto.user_id == user_id).first()
    else:
        user_ph = UsersPhoto()
        user_ph.id = str(uuid.uuid4())
        user_ph.user_id = user_id
    user_ph.filename = filename
    user_ph.content_type = data.content_type
    if not is_exists_photo:
        session.add(user_ph)

    current = session.query(Users).filter(Users.id == user_id).first()
    description = f'{current.fio_and_login} - обновил фотографию'
    add_audit(session, user=current.login, action=description)
    session.commit()
    session.close()
    return filename


async def get_photo_service(session: Session, user_id: str) -> Union[str, None]:
    user_ph = session.query(UsersPhoto).filter(UsersPhoto.user_id == user_id).first()
    if user_ph is not None:
        my_file = Path(f'./avatars/{user_ph.filename}')
        if my_file.exists():
            with open(f'./avatars/{user_ph.filename}', 'rb') as file:
                return f'data:{user_ph.content_type};base64, {base64.b64encode(file.read()).decode("utf-8")}'
    else:
        return None


async def delete_photo_service(session: Session, user_id: str):
    files = session.query(UsersPhoto).filter(UsersPhoto.user_id == user_id).all()
    for i in files:
        my_file = Path(f'./avatars/{i.filename}')
        my_file.unlink(missing_ok=True)
        session.delete(i)
    current = session.query(Users).filter(Users.id == user_id).first()
    description = f'{current.fio_and_login} - удалил фотографию'
    add_audit(session, user=current.login, action=description)
    session.commit()
    session.close()


class BaseReportUserService(ABC):

    def __init__(self):
        self.data = {'document_name': 'report_user_info',
                     'document_template_binary': b'PK\x03\x04\x14\x00\x00\x08\x00\x00...',
                     'content': {
                         'text_and_table_content': [],
                     }
                     }
        self.base_path = f'{os.path.dirname(os.path.abspath(__file__))}/../../templates'
        self.file_template = self.base_path + '/user_info_registration.odt'
        self._clear_data()

    def _clear_data(self):
        folder = self.base_path + '/temp/out'
        if not os.path.exists(folder):
            os.makedirs(folder)
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (file_path, e))

    @abstractmethod
    def _make_date(self):
        pass

    def _open_template(self):
        with open(self.file_template, 'rb') as text:
            self.data['document_template_binary'] = text.read()

    def make_report(self):
        my_id = uuid.uuid4()
        self._make_date()
        self._open_template()
        setattr(ConfigurationMyOdt, 'path_template_folder', self.base_path + '/temp/')
        doc = ODTemplater(self.data)
        doc_out = doc.create()
        with open(self.base_path + f'/temp/out/user_info_registration-{my_id}.odt', 'wb') as file_out:
            file_out.write(doc_out)
        return {'base_path': self.base_path,
                'filename': self.base_path + f'/temp/out/user_info_registration-{my_id}.odt',
                'res': self.base_path + f'/temp/out/user_info_registration-{my_id}.pdf'
                }


class ReportUserService(BaseReportUserService):

    def __init__(self, user_data: UserCreateScheme):
        super().__init__()
        self.user_data = user_data

    def _make_date(self):
        suf = {'key_': 'suf', 'render_text': 'ый' if self.user_data.gender == 'male' else 'ая'}
        lastname = {'key_': 'lastname', 'render_text': self.user_data.lastname}
        firstname = {'key_': 'firstname', 'render_text': self.user_data.firstname}
        middlename = {'key_': 'middlename', 'render_text': self.user_data.middlename}
        login = {'key_': 'login', 'render_text': self.user_data.login}
        password = {'key_': 'password', 'render_text': self.user_data.password}
        self.data['content']['text_and_table_content'].extend([suf, lastname, firstname, middlename, login, password])


class ReportUserUpdateService(BaseReportUserService):

    def __init__(self, user: Users, user_data: UserUpdateScheme):
        super().__init__()
        self.user_data = user_data
        self.user = user

    def _make_date(self):
        suf = {'key_': 'suf', 'render_text': 'ый' if self.user.gender == 'male' else 'ая'}
        lastname = {'key_': 'lastname', 'render_text': self.user.lastname}
        firstname = {'key_': 'firstname', 'render_text': self.user.firstname}
        middlename = {'key_': 'middlename', 'render_text': self.user.middlename}
        login = {'key_': 'login', 'render_text': self.user.login}
        password = {'key_': 'password', 'render_text': self.user_data.password}
        self.data['content']['text_and_table_content'] = [suf, lastname, firstname, middlename, login, password]

