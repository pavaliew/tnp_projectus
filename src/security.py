from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

import orm
import models
from database import get_async_session
from config import settings



oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")



class TokenData(BaseModel):
    """Схема для данных, извлеченных из токена."""
    username: str | None = None



async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_async_session)):
    """
    Зависимость для FastAPI: декодирует токен, валидирует его 
    и возвращает пользователя из БД.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user = await orm.get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
        
    return user



async def get_current_active_user(current_user: models.User = Depends(get_current_user)):
    """
    Зависимость-обертка для проверки, активен ли пользователь.
    Именно ее мы будем использовать в защищенных эндпоинтах.
    """
    return current_user