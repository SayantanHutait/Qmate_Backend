from sqlalchemy.orm import Session
from typing import Optional
from datetime import timedelta
import uuid
from app.models.user import User, UserRole
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token, decode_token
from app.config import settings
from fastapi import HTTPException, status


class AuthService:
    """Service for authentication operations."""
    
    @staticmethod
    def signup(
        db: Session,
        email: str,
        password: str,
        name: str,
        role: UserRole = UserRole.STUDENT,
        department_id: Optional[uuid.UUID] = None,
    ) -> User:
        """Register a new user."""
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Validate department if provided
        if department_id:
            from app.models.user import Department
            department = db.query(Department).filter(Department.id == department_id).first()
            if not department:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Department not found"
                )
        
        # Create new user
        password_hash = get_password_hash(password)
        user = User(
            email=email,
            password_hash=password_hash,
            name=name,
            role=role,
            department_id=department_id,
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def login(db: Session, email: str, password: str) -> tuple[User, str, str]:
        """Authenticate user and return user with tokens."""
        user = db.query(User).filter(User.email == email).first()
        
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        # Create tokens
        token_data = {"sub": str(user.id), "email": user.email, "role": user.role.value}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        return user, access_token, refresh_token
    
    @staticmethod
    def refresh_access_token(refresh_token: str) -> tuple[str, str]:
        """Generate new access token from refresh token."""
        payload = decode_token(refresh_token)
        
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is not a refresh token"
            )
        
        # Create new access token
        token_data = {
            "sub": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role"),
        }
        access_token = create_access_token(token_data)
        
        # Optionally create new refresh token (refresh token rotation)
        new_refresh_token = create_refresh_token(token_data)
        
        return access_token, new_refresh_token
    
    @staticmethod
    def get_current_user(db: Session, user_id: uuid.UUID) -> User:
        """Get user by ID."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        return user
