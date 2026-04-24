from fastapi import FastAPI, Depends, Header, HTTPException, Body
from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import User, APIKey
from .utils import generate_api_key, hash_api_key
from .database import engine, Base

from . import models
from .models import RequestLog

from datetime import datetime, timedelta

from pydantic import BaseModel
class UserCreate(BaseModel):
    email: str

Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

MAX_REQUESTS = 5
WINDOW_SECONDS = 60

def get_api_key(x_api_key: str = Header(...), db: Session = Depends(get_db)):
    hashed_key = hash_api_key(x_api_key)

    api_key = db.query(APIKey).filter(APIKey.key == hashed_key).first()

    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    window_start = datetime.utcnow() - timedelta(seconds=WINDOW_SECONDS)

    request_count = db.query(RequestLog).filter(
        RequestLog.api_key_id == api_key.id,
        RequestLog.timestamp >= window_start
    ).count()

    if request_count > MAX_REQUESTS - 1:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    log = RequestLog(api_key_id=api_key.id)
    db.add(log)
    db.commit()
    
    return api_key

@app.post("/register")
def register_user(user: UserCreate = Body(...), db: Session = Depends(get_db)):
    user_obj = User(email=user.email)
    db.add(user_obj)
    db.commit()
    db.refresh(user_obj)

    raw_key = generate_api_key()
    hashed_key = hash_api_key(raw_key)

    api_key = APIKey(key=hashed_key, user_id=user_obj.id)
    db.add(api_key)
    db.commit()

    return {
        "api_key": raw_key,
        "message": "Save this key securely. It will not be shown again."
    }

@app.get("/protected")
def protected_route(api_key: APIKey = Depends(get_api_key)):
    return {"message": "You have access", "user_id": api_key.user_id}