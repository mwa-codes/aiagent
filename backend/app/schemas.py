from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator
import re


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError(
                'Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError(
                'Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError(
                'Password must contain at least one special character')
        return v


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None

    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        if v is not None:
            if len(v) < 8:
                raise ValueError('Password must be at least 8 characters long')
            if not re.search(r'[A-Z]', v):
                raise ValueError(
                    'Password must contain at least one uppercase letter')
            if not re.search(r'[a-z]', v):
                raise ValueError(
                    'Password must contain at least one lowercase letter')
            if not re.search(r'\d', v):
                raise ValueError('Password must contain at least one digit')
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
                raise ValueError(
                    'Password must contain at least one special character')
        return v


class UserOut(UserBase):
    id: int
    plan_id: Optional[int] = None

    class Config:
        from_attributes = True


class UserProfile(UserOut):
    """Extended user profile with plan information"""
    plan_name: Optional[str] = None
    max_files: Optional[int] = None
    current_files_count: Optional[int] = None

    class Config:
        from_attributes = True


class PasswordChange(BaseModel):
    current_password: str
    new_password: str

    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError(
                'Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError(
                'Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError(
                'Password must contain at least one special character')
        return v


class EmailUpdate(BaseModel):
    new_email: EmailStr
    password: str  # Require password confirmation for email changes


class AccountDeactivation(BaseModel):
    password: str
    confirmation: str = "DELETE"

    @field_validator('confirmation')
    @classmethod
    def validate_confirmation(cls, v):
        if v != "DELETE":
            raise ValueError(
                'Must type "DELETE" to confirm account deactivation')
        return v
