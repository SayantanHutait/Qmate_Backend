from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
import uuid
from app.core.database import get_db
from app.schemas.auth import (
    SignupRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
    RefreshTokenRequest,
)
from app.services.auth_service import AuthService
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(
    request: SignupRequest,
    db: Session = Depends(get_db),
):
    """Register a new user."""
    department_id = None
    if request.department_id:
        try:
            department_id = uuid.UUID(request.department_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid department ID format"
            )
    
    user = AuthService.signup(
        db=db,
        email=request.email,
        password=request.password,
        name=request.name,
        role=request.role,
        department_id=department_id,
    )
    
    return UserResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        role=user.role,
        department_id=str(user.department_id) if user.department_id else None,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.post("/login", response_model=TokenResponse)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    """Authenticate user and return access and refresh tokens."""
    user, access_token, refresh_token = AuthService.login(
        db=db,
        email=request.email,
        password=request.password,
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    request: RefreshTokenRequest,
):
    """Refresh access token using refresh token."""
    access_token, new_refresh_token = AuthService.refresh_access_token(
        refresh_token=request.refresh_token,
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """Get current authenticated user information."""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        name=current_user.name,
        role=current_user.role,
        department_id=str(current_user.department_id) if current_user.department_id else None,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )
