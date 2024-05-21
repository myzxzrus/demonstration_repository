from datetime import datetime, timedelta
from .schemas import TokenData
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from ...config import Config

base_url = Config.base_url

SECRET_KEY = "1111111"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 5


def create_token(data: dict, is_refresh: bool = False) -> dict:
    to_encode = data.copy()
    if is_refresh:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    else:
        expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return dict(encoded_jwt=encoded_jwt, expire=expire)


def verify_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        login: str = payload.get("login")
        email: str = payload.get("email")
        user_id: str = payload.get("user_id")
        role: str = payload.get("role")
        if login is None:
            raise credentials_exception
        token_data = TokenData(login=login, email=email, user_id=user_id, role=role)
        return token_data
    except JWTError:
        raise credentials_exception


oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{base_url}/auth/login")
oauth2_scheme_refresh = OAuth2PasswordBearer(tokenUrl=f"{base_url}/auth/refresh_token")

def get_current_user(data: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    return verify_token(data, credentials_exception)


def get_current_user_refres(data: str = Depends(oauth2_scheme_refresh)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    return verify_token(data, credentials_exception)
