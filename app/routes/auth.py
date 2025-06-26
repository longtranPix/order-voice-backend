from fastapi import APIRouter
from app.schemas.auth import Account, SignUp
from app.services.auth_service import signin_service, signup_service

router = APIRouter()

@router.post("/signin")
async def signin(account: Account):
    """User signin endpoint"""
    return await signin_service(account)

@router.post("/signup")
async def signup(account: SignUp):
    """User signup endpoint"""
    return await signup_service(account)
