
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import requests
from app.core.config import settings

logger = logging.getLogger(__name__)

# JWT Configuration from environment
SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES

security = HTTPBearer()

# def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
#     """Create JWT access token"""
#     to_encode = data.copy()
#     if expires_delta:
#         expire = datetime.utcnow() + expires_delta
#     else:
#         expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
#     to_encode.update({"exp": expire})
#     encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
#     return encoded_jwt

# def verify_token(token: str) -> Dict[str, Any]:
#     """Verify JWT token and return payload"""
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         username: str = payload.get("sub")
#         if username is None:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Could not validate credentials",
#                 headers={"WWW-Authenticate": "Bearer"},
#             )
#         return payload
#     except jwt.ExpiredSignatureError:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Token has expired",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#     except jwt.JWTError:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Could not validate credentials",
#             headers={"WWW-Authenticate": "Bearer"},
#         )

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

async def get_username_by_token(token: str) -> str:
    """Get username by token from token list table"""
    try:
        headers = {
            "Authorization": settings.TEABLE_TOKEN,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Query token list table to find username by token
        token_list_url = f"{settings.TEABLE_BASE_URL}/table/{settings.TEABLE_TABLE_ID}/record"
        params = {
            "fieldKeyType": "dbFieldName",
            "filter": json.dumps({
                "conjunction": "and",
                "viewId": settings.TEABLE_USER_TOKEN_VIEW_ID,
                "filterSet": [
                    {"fieldId": "access_token", "operator": "is", "value": token}
                ]
            })
        }
        logger.info(f"Token list url: {token_list_url}")
        logger.info(f"Params: {params}")
        
        response = requests.get(token_list_url, headers=headers, params=params)
        if response.status_code != 200:
            logger.error(f"Failed to get token info: {response.text}")
            return ""
        
        data = response.json()
        records = data.get("records", [])
        
        if not records:
            logger.warning(f"No user found for token: {token[:20]}...")
            return ""
        
        # Get username from the first matching record
        username = records[0].get("fields", {}).get("username", "")
        if username:
            logger.info(f"Found username {username} for token")
            return username
        else:
            logger.warning(f"Username field not found in token record")
            return ""
            
    except Exception as e:
        logger.error(f"Error getting username by token: {str(e)}")
        return ""

async def get_current_active_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Get current active user"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user"
        )
    return current_user

def create_teable_token_payload(username: str, access_token: str) -> str:
    """Create a custom token payload for Teable integration"""
    payload = {
        "sub": username,
        "teable_token": access_token,
        "type": "teable_access",
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(days=30)  # Longer expiry for Teable tokens
    }
    return create_access_token(payload, timedelta(days=30))
