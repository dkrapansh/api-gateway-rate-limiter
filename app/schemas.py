from pydantic import BaseModel

class UserCreate(BaseModel):
    email: str

class RegisterResponse(BaseModel):
    api_key: str
    message: str

class RevokeResponse(BaseModel):
    message: str