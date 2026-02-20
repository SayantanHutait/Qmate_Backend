from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from app.models.user import UserRole


class SignupRequest(BaseModel):
    """Request schema for user signup."""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    name: str = Field(..., min_length=1, max_length=255)
    role: UserRole = UserRole.STUDENT
    department_id: Optional[str] = None  # UUID as string


class LoginRequest(BaseModel):
    """Request schema for user login."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Response schema for authentication tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Response schema for user information."""
    id: str
    email: str
    name: str
    role: UserRole
    department_id: Optional[str] = None
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class RefreshTokenRequest(BaseModel):
    """Request schema for token refresh."""
    refresh_token: str
