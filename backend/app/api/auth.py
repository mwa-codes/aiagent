from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["auth"])


class UserLogin(BaseModel):
    email: str
    password: str


@router.post("/login")
def login(user: UserLogin):
    # Placeholder logic
    if user.email == "test@example.com" and user.password == "password":
        return {"access_token": "fake-jwt-token"}
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
