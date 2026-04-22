from fastapi import FastAPI, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import User, APIKey
from .utils import generate_api_key, hash_api_key
from .database import engine, Base

from . import models

Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_api_key(x_api_key: str = Header(...), db: Session = Depends(get_db)):
    hashed_key = hash_api_key(x_api_key)

    api_key = db.query(APIKey).filter(APIKey.key == hashed_key).first()

    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return api_key 

@app.get("/")
def home():
    return{"message": "API Gateway is running"}

@app.post("/register")
def register_user(email: str, db: Session = Depends(get_db)):
    user = User(email=email)
    db.add(user)
    db.commit()
    db.refresh(user)

    raw_key = generate_api_key()
    hashed_key = hash_api_key(raw_key)

    api_key = APIKey(key = hashed_key, user_id = user.id)
    db.add(api_key)
    db.commit()

    return{
        "api_key": raw_key,
        "message": "Save this key securely. It will not be shown again."
    }