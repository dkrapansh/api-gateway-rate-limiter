from pydantic import BaseModel
from pydantic import ConfigDict
from typing import Dict

class UserCreate(BaseModel):
    email: str

class RegisterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    api_key: str
    message: str

class RevokeResponse(BaseModel):
    message: str

class AnalyticsResponse(BaseModel):
    api_key_hash: str
    total_requests: int
    requests_per_endpoint: Dict[str, int]
    rate_limit_hits: int