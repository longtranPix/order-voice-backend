from pydantic import BaseModel, field_validator

class Account(BaseModel):
    """Schema for user authentication."""
    username: str
    password: str

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        return v.strip()

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v

class SignUp(BaseModel):
    """Schema for user registration."""
    username: str
    password: str
    business_name: str

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        return v.strip()

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v

    @field_validator('business_name')
    @classmethod
    def validate_business_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Business name must be at least 2 characters')
        return v.strip()

class AuthResponse(BaseModel):
    """Schema for authentication response."""
    status: str
    accessToken: str
    message: str
    record: list
