from pydantic import BaseModel

class Account(BaseModel):
    username: str
    password: str

class SignUp(BaseModel):
    username: str
    password: str
    business_name: str
