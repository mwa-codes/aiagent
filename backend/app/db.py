from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:55432/postgres")

engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False)
