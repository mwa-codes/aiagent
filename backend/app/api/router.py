from fastapi import APIRouter
from . import auth, files, gpt

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(files.router)
api_router.include_router(gpt.router)
