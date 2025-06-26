from pydantic import BaseModel

class Account(BaseModel):
    username: str
    password: str

class SignUp(BaseModel):
    username: str  # This will be used as taxcode
    password: str
