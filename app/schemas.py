from pydantic import BaseModel
from pydantic import ConfigDict

class UserCreate(BaseModel):
    email: str

class RegisterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    api_key: str
    message: str

class RevokeResponse(BaseModel):
    message: str