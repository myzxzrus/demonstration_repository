from sqlalchemy import Column, TEXT, TIMESTAMP, INTEGER, DATE, BOOLEAN, ForeignKey, String, LargeBinary, desc, func, \
    DATETIME
from sqlalchemy.orm import relationship

from ..session import Base
from ..tools import hashing


# Base = session.Base
class ResetPassword(Base):

    __tablename__ = 'reset_password'
    __table_args__ = {"schema": "vision"}

    id = Column(TEXT, primary_key=True, nullable=False)  # ID
    created_utc = Column(TIMESTAMP(timezone=False), nullable=False)  # Дата создания
    disabled_utc = Column(TIMESTAMP(timezone=False), nullable=False)  # Время конца действия
    user_id = Column(TEXT, ForeignKey('vision.users.id'), nullable=False)  # Ключ на персону
    secret_key = Column(String(6), nullable=False)  # Секретный ключ
    email = Column(TEXT, nullable=False)  # Электронная почта
    is_reset = Column(BOOLEAN, nullable=False)  # Сброшен пароль или нет

    def __repr__(self):
        return f"{self.id} {self.created_utc} {self.disabled_utc} {self.user_id} {self.secret_key} {self.email} {self.is_reset}"


class Users(Base):

    __tablename__ = 'users'
    __table_args__ = {"schema": "vision"}

    id = Column(TEXT, primary_key=True, nullable=False)  # ID
    created_utc = Column(TIMESTAMP(timezone=False), nullable=False)  # Дата создания
    updated_utc = Column(TIMESTAMP(timezone=False), nullable=False)  # Дата обновления
    lastname = Column(TEXT, nullable=True)  # Фамилия
    firstname = Column(TEXT, nullable=True)  # Имя
    middlename = Column(TEXT, nullable=True)  # Отчество
    email = Column(TEXT, nullable=True, unique=True)  # Электронная почта
    phone = Column(TEXT, nullable=True)  # Телефон
    gender = Column(TEXT, nullable=True)  # Пол
    birthday = Column(DATE, nullable=True)  # День рождения
    login = Column(TEXT, nullable=False)  # Логин
    password = Column(TEXT, nullable=False)  # Пароль
    is_locked = Column(BOOLEAN, nullable=False)  # Активен/Заблокирован
    is_admin = Column(BOOLEAN, nullable=False, default=False)  # Администратор
    is_superadmin = Column(BOOLEAN, nullable=False, default=False, server_default='f')  # Супер-администратор

    rel_res_pass = relationship(ResetPassword, order_by=desc(ResetPassword.created_utc), uselist=False, viewonly=False)
    rel_photo = relationship('UsersPhoto', uselist=False, viewonly=False)
    rel_allowed_games = relationship('Games', secondary="vision.allowed_games", uselist=True, viewonly=False, lazy='joined')

    def __repr__(self):
        return f"{self.id} {self.created_utc} {self.updated_utc} {self.lastname} {self.firstname} {self.middlename} " \
               f"{self.gender} {self.birthday} {self.login} {self.password} {self.is_locked}"

    def __init__(self, password, *args, **kwargs):
        self.password = hashing.get_password_hash(password)

    def check_password(self, password):
        return hashing.verify_password(self.password, password)

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if (key == 'password'):
                setattr(self, key, hashing.get_password_hash(value))
            else:
                setattr(self, key, value)

    def reset_password(self, value):
        setattr(self, 'password', hashing.get_password_hash(value))

    @property
    def fio_and_login(self):
        return f'{self.lastname} {self.firstname} {self.middlename} (логин: {self.login})'




class Games(Base):
    __tablename__ = 'games'
    __table_args__ = {"schema": "vision"}

    id = Column(TEXT, primary_key=True, nullable=False)  # ID
    created_utc = Column(TIMESTAMP(timezone=False), server_default=func.now(), nullable=False)  # Дата создания
    updated_utc = Column(TIMESTAMP(timezone=False), server_default=func.now(), onupdate=func.now(),
                         nullable=False)  # Дата обновления
    name = Column(TEXT, nullable=False)  # Имя на Русском
    code_name = Column(TEXT, nullable=False)  # Имя на латинице
    descriptions = Column(TEXT, nullable=True)  # Описание


    def __repr__(self):
        return f"{self.id} {self.created_utc} {self.updated_utc} {self.name} {self.code_name} {self.descriptions}"


class GamesPlayed(Base):

    __tablename__ = 'games_played'
    __table_args__ = {"schema": "vision"}

    id = Column(TEXT, primary_key=True, nullable=False)  # ID
    created_utc = Column(TIMESTAMP(timezone=False), server_default=func.now(), nullable=False)  # Дата создания
    updated_utc = Column(TIMESTAMP(timezone=False), server_default=func.now(), onupdate=func.now(), nullable=False)  # Дата обновления
    user_id = Column(TEXT, ForeignKey(Users.id), nullable=False)  # Индетефикатор пользователя
    game_id = Column(TEXT, ForeignKey(Games.id), nullable=False)  # Индетефикатор игры
    points = Column(INTEGER, nullable=False)  # Очки

    rel_games = relationship('Games', uselist=False, viewonly=False, lazy='joined', foreign_keys=[game_id])
    def __repr__(self):
        return f"{self.id} {self.created_utc} {self.updated_utc} {self.user_id} {self.games_id} {self.points}"


class UsersPhoto(Base):

    __tablename__ = 'users_photo'
    __table_args__ = {"schema": "vision"}

    id = Column(TEXT, primary_key=True, nullable=False)  # ID
    created_utc = Column(TIMESTAMP(timezone=False), server_default=func.now(), nullable=False)  # Дата создания
    updated_utc = Column(TIMESTAMP(timezone=False), server_default=func.now(), onupdate=func.now(), nullable=False)  # Дата обновления
    user_id = Column(TEXT, ForeignKey(Users.id), nullable=False, unique=True)  # Индетефикатор пользователя
    filename = Column(TEXT, nullable=False)  # изображение
    content_type = Column(TEXT, nullable=False)  # изображение

    def __repr__(self):
        return f"{self.id} {self.created_utc} {self.updated_utc} {self.user_id} {self.data}"


class AllowedGames(Base):

    __tablename__ = 'allowed_games'
    __table_args__ = {"schema": "vision"}

    id = Column(TEXT, primary_key=True, nullable=False)  # ID
    created_utc = Column(TIMESTAMP(timezone=False), server_default=func.now(), nullable=False)  # Дата создания
    updated_utc = Column(TIMESTAMP(timezone=False), server_default=func.now(), onupdate=func.now(), nullable=False)  # Дата обновления
    user_id = Column(TEXT, ForeignKey(Users.id), nullable=False)  # Индетефикатор пользователя
    game_id = Column(TEXT, ForeignKey(Games.id), nullable=False)  # Индетефикатор игры

    def __repr__(self):
        return f"{self.id} {self.created_utc} {self.updated_utc} {self.user_id} {self.games_id}"

class Audit(Base):
    __tablename__ = 'audit'
    __table_args__ = {"schema": "vision"}

    id = Column(TEXT, primary_key=True, nullable=False)  # ID
    created_utc = Column(TIMESTAMP(timezone=False), server_default=func.now(), nullable=False)  # Дата создания
    updated_utc = Column(TIMESTAMP(timezone=False), server_default=func.now(), onupdate=func.now(),
                         nullable=False)  # Дата обновления
    user = Column(TEXT, nullable=False)
    action = Column(TEXT, nullable=False)
    date = Column(TIMESTAMP(timezone=True), nullable=False)

    def __repr__(self):
        return f"{self.id} {self.created_utc} {self.updated_utc} {self.user} {self.action} {self.date}"
