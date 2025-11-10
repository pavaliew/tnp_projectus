from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from config import settings



class Base(DeclarativeBase):
    pass



async_engine = create_async_engine(settings.DATABASE_URL_ASYNC)
async_session_maker = async_sessionmaker(
    async_engine,
    expire_on_commit=False,
)



async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session