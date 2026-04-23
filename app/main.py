from fastapi import FastAPI, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import User, APIKey
from .utils import generate_api_key, hash_api_key
from .database import engine, Base

from . import models
from .models import RequestLog

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
    
    log = RequestLog(api_key_id=api_key.id)
    db.add(log)
    db.commit()
    
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

@app.get("/protected")
def protected_route(api_key: APIKey = Depends(get_api_key)):
    return {"message": "You have access", "user_id": api_key.user_id}