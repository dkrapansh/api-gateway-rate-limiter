from fastapi import APIRouter, Depends, HTTPException, Body, Header
from sqlalchemy.orm import Session
from ..dependencies import get_db
from ..models import User, APIKey
from ..utils import generate_api_key, hash_api_key
from ..schemas import UserCreate, RegisterResponse, RevokeResponse

router = APIRouter()

@router.post("/register", response_model=RegisterResponse, status_code=201)
def register_user(user: UserCreate = Body(...), db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    
    user_obj = User(email=user.email)
    db.add(user_obj)
    db.commit()
    db.refresh(user_obj)

    raw_key = generate_api_key()
    hashed_key = hash_api_key(raw_key)

    api_key = APIKey(key = hashed_key, user_id = user_obj.id)
    db.add(api_key)
    db.commit()

    return RegisterResponse(
        api_key=raw_key,
        message="Save this key securely. It will not be shown again."
    )

@router.post("/keys/revoke", response_model=RevokeResponse)
def revoke_key(x_api_key: str = Header(...),  db: Session = Depends(get_db)):
    hashed_key = hash_api_key(x_api_key)
    api_key = db.query(APIKey).filter(APIKey.key == hashed_key).first()

    if not api_key:
        raise HTTPException(status_code = 404, detail="API key not found")
    
    api_key.is_active = False
    db.commit()

    return RevokeResponse(message="API key revoked successfully")
