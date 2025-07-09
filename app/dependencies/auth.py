"""
Authentication dependencies for API authorization
"""
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.auth_service import get_username_by_token
import logging

logger = logging.getLogger(__name__)

# Security scheme for Bearer token
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Dependency to get current user from token
    Returns username if token is valid, raises HTTPException if not
    """
    try:
        token = credentials.credentials
        
        # Get username by token from token list table
        username = await get_username_by_token(token)
        logger.info(f"Authenticated user {username} with token {token[:20]}...")
        
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token or token not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return username
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_current_user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_optional_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Optional dependency to get current user from token
    Returns username if token is valid, returns empty string if not (doesn't raise exception)
    """
    try:
        token = credentials.credentials
        username = await get_username_by_token(token)
        return username or ""
        
    except Exception as e:
        logger.warning(f"Optional auth failed: {str(e)}")
        return ""
