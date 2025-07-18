"""
Authentication routes for Aether AI Companion API.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..auth import AuthManager, UserCredentials, TokenResponse, get_current_user
from ..middleware import rate_limit_strict

router = APIRouter()
auth_manager = AuthManager()


class RefreshTokenRequest(BaseModel):
    """Request model for token refresh."""
    refresh_token: str


class UserProfile(BaseModel):
    """User profile response."""
    id: str
    username: str
    permissions: list
    is_active: bool


@router.post("/login", response_model=TokenResponse)
@rate_limit_strict("5/minute")
async def login(credentials: UserCredentials):
    """
    Authenticate user and return access tokens.
    
    Args:
        credentials: User login credentials
    
    Returns:
        JWT tokens for authentication
    
    Raises:
        HTTPException: If authentication fails
    """
    return auth_manager.login(credentials)


@router.post("/refresh", response_model=TokenResponse)
@rate_limit_strict("10/minute")
async def refresh_token(request: RefreshTokenRequest):
    """
    Refresh access token using refresh token.
    
    Args:
        request: Refresh token request
    
    Returns:
        New access token
    
    Raises:
        HTTPException: If refresh token is invalid
    """
    return auth_manager.refresh_token(request.refresh_token)


@router.get("/profile", response_model=UserProfile)
async def get_profile(current_user: dict = Depends(get_current_user)):
    """
    Get current user profile.
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        User profile information
    """
    return UserProfile(
        id=current_user["id"],
        username=current_user["username"],
        permissions=current_user["permissions"],
        is_active=current_user["is_active"]
    )


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """
    Logout current user.
    
    Note: In a production system, this would invalidate the token
    by adding it to a blacklist or similar mechanism.
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        Logout confirmation
    """
    return {
        "message": "Successfully logged out",
        "user": current_user["username"]
    }


@router.get("/verify")
async def verify_token(current_user: dict = Depends(get_current_user)):
    """
    Verify if current token is valid.
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        Token verification result
    """
    return {
        "valid": True,
        "user": current_user["username"],
        "permissions": current_user["permissions"]
    }