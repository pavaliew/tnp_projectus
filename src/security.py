from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from repository import Repository
from models import User

from config import settings
import schemas


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
    scheme_name="JWT"
)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Создает новый JWT токен."""
    
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # Если время жизни не передано, берем 15 минут по умолчанию
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> schemas.TokenData:
    """
    Декодирует токен доступа, проверяет его и возвращает полезную нагрузку.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub")
        user_id: int = payload.get("id")
        username: str = payload.get("username")
        
        if email is None or user_id is None:
            raise credentials_exception
            
        token_data = schemas.TokenData(email=email, id=user_id, username=username)
    except JWTError:
        raise credentials_exception
        
    return token_data



# async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
#     """
#     Декодирует JWT токен, извлекает email, находит пользователя в БД
#     и возвращает его объект. Если что-то не так - вызывает HTTPException.
#     """
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials",
#         headers={"WWW-Authenticate": "Bearer"},
#     )
#     
#     try:
#         payload = jwt.decode(
#             token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
#         )
#         email: str = payload.get("sub")
#         if email is None:
#             raise credentials_exception
#         token_data = schemas.TokenData(email=email, id=payload.get("id"), username=payload.get("username"))
#     except JWTError:
#         raise credentials_exception
#     
#     # ДЕЛАЕМ ЗАПРОС К РЕПОЗИТОРИЮ
#     user = await Repository.get_user_by_email(token_data.email)
#     
#     if user is None:
#         # Если пользователь был удален, пока токен был действителен
#         raise credentials_exception
#         
#     return user



async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Декодирует JWT токен, извлекает email, находит пользователя в БД
    и возвращает его объект. Если что-то не так - вызывает HTTPException.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Делаем асинхронный запрос к репозиторию
    user = await Repository.get_user_by_email(email)
    
    if user is None:
        raise credentials_exception
        
    return user



# async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
#     """
#     ВРЕМЕННАЯ ВЕРСИЯ ДЛЯ ОТЛАДКИ.
#     Просто возвращает фейкового пользователя, чтобы проверить роутинг.
#     """
#     print(f"Token received: {token}") # Добавим лог, чтобы видеть, что функция вызывается
#     
#     # Возвращаем "захардкоженного" пользователя.
#     # Убедитесь, что у вас в базе есть пользователь с ID=1
#     fake_user = User(
#         id=19,
#         email="alice@example.com",
#         username="Alice Potter",
#         password_hash="$2b$12$I7tCwSUr/h73NEOy5XrEm.uXi2RGV3hRWW5zT2b3tbkVuTMVeUmva" 
#     )
#     return fake_user