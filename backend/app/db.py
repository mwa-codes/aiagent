from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, Session
import os

# PostgreSQL database configuration
DATABASE_URL_ASYNC = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:55432/postgres")

# Sync database setup
DATABASE_URL_SYNC = os.getenv(
    "DATABASE_URL_SYNC", "postgresql://postgres:postgres@localhost:55432/postgres")

# Async engine and session
async_engine = create_async_engine(DATABASE_URL_ASYNC, echo=True)
AsyncSessionLocal = sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False)

# Sync engine and session
sync_engine = create_engine(DATABASE_URL_SYNC, echo=True)
SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=sync_engine)


# Dependency to get sync DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Dependency to get async DB session
async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session
