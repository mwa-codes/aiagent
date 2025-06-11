from .db import SessionLocal
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends


async def get_db() -> AsyncSession:
    async with SessionLocal() as session:
        yield session
