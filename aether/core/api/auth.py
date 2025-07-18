"""
Authentication system for Aether AI Companion API.
"""

import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from shared.config.settings import get_settings


class UserCredentials(BaseModel):
    """User credentials for authentication."""
    username: str
    password: str


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None


class JWTPayload(BaseModel):
    """JWT token payload."""
    sub: str  # subject (user ID)
    username: str
    exp: datetime
    iat: datetime
    type: str = "access"  # access or refresh


class JWTAuth:
    """JWT authentication handler."""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7
    
    def create_access_token(self, user_id: str, username: str) -> str:
        """
        Create JWT access token.
        
        Args:
            user_id: User identifier
            username: Username
        
        Returns:
            JWT token string
        """
        now = datetime.utcnow()
        expire = now + timedelta(minutes=self.access_token_expire_minutes)
        
        payload = {
            "sub": user_id,
            "username": username,
            "exp": expire,
            "iat": now,
            "type": "access"
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, user_id: str, username: str) -> str:
        """
        Create JWT refresh token.
        
        Args:
            user_id: User identifier
            username: Username
        
        Returns:
            JWT refresh token string
        """
        now = datetime.utcnow()
        expire = now + timedelta(days=self.refresh_token_expire_days)
        
        payload = {
            "sub": user_id,
            "username": username,
            "exp": expire,
            "iat": now,
            "type": "refresh"
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode JWT token.
        
        Args:
            token: JWT token string
        
        Returns:
            Decoded token payload
        
        Raises:
            HTTPException: If token is invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"}
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"}
            )
    
    def refresh_access_token(self, refresh_token: str) -> str:
        """
        Create new access token from refresh token.
        
        Args:
            refresh_token: Valid refresh token
        
        Returns:
            New access token
        
        Raises:
            HTTPException: If refresh token is invalid
        """
        payload = self.verify_token(refresh_token)
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        return self.create_access_token(
            payload["sub"], 
            payload["username"]
        )


class AuthManager:
    """Authentication manager for user management."""
    
    def __init__(self):
        self.settings = get_settings()
        self.jwt_auth = JWTAuth(self.settings.secret_key)
        # In production, this would be a database
        self._users = {
            "admin": {
                "id": "admin-001",
                "username": "admin",
                "password_hash": self._hash_password("admin123"),
                "is_active": True,
                "permissions": ["read", "write", "admin"]
            },
            "user": {
                "id": "user-001", 
                "username": "user",
                "password_hash": self._hash_password("user123"),
                "is_active": True,
                "permissions": ["read", "write"]
            }
        }
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash."""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate user credentials.
        
        Args:
            username: Username
            password: Password
        
        Returns:
            User data if authenticated, None otherwise
        """
        user = self._users.get(username)
        if not user or not user["is_active"]:
            return None
        
        if not self._verify_password(password, user["password_hash"]):
            return None
        
        return user
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user by ID.
        
        Args:
            user_id: User identifier
        
        Returns:
            User data if found, None otherwise
        """
        for user in self._users.values():
            if user["id"] == user_id:
                return user
        return None
    
    def login(self, credentials: UserCredentials) -> TokenResponse:
        """
        Login user and return tokens.
        
        Args:
            credentials: User credentials
        
        Returns:
            Token response with access and refresh tokens
        
        Raises:
            HTTPException: If authentication fails
        """
        user = self.authenticate_user(credentials.username, credentials.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        access_token = self.jwt_auth.create_access_token(user["id"], user["username"])
        refresh_token = self.jwt_auth.create_refresh_token(user["id"], user["username"])
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.jwt_auth.access_token_expire_minutes * 60
        )
    
    def refresh_token(self, refresh_token: str) -> TokenResponse:
        """
        Refresh access token.
        
        Args:
            refresh_token: Valid refresh token
        
        Returns:
            New token response
        """
        access_token = self.jwt_auth.refresh_access_token(refresh_token)
        
        return TokenResponse(
            access_token=access_token,
            expires_in=self.jwt_auth.access_token_expire_minutes * 60
        )


# FastAPI dependency for authentication
security = HTTPBearer()
auth_manager = AuthManager()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    FastAPI dependency to get current authenticated user.
    
    Args:
        credentials: HTTP Bearer credentials
    
    Returns:
        Current user data
    
    Raises:
        HTTPException: If authentication fails
    """
    payload = auth_manager.jwt_auth.verify_token(credentials.credentials)
    user = auth_manager.get_user_by_id(payload["sub"])
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user


async def require_permission(permission: str):
    """
    Create dependency that requires specific permission.
    
    Args:
        permission: Required permission
    
    Returns:
        FastAPI dependency function
    """
    async def check_permission(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        if permission not in user.get("permissions", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        return user
    
    return check_permission


# Common permission dependencies
require_read = require_permission("read")
require_write = require_permission("write") 
require_admin = require_permission("admin")