from pydantic import BaseModel

class Account(BaseModel):
    username: str
    password: str

class SignUp(BaseModel):
    username: str  # This will be used as taxcode
    password: str

class ChangePasswordRequest(BaseModel):
    username: str
    old_password: str
    new_password: str

class ChangePasswordResponse(BaseModel):
    status: str
    detail: str
    username: str
