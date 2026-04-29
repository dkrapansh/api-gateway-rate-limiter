from fastapi import FastAPI, Depends, Header, HTTPException, Body, Request, Response
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

def get_api_key(request : Request, x_api_key: str = Header(...), db: Session = Depends(get_db), response: Response = None):
    hashed_key = hash_api_key(x_api_key)

    api_key = db.query(APIKey).filter(APIKey.key == hashed_key).first()

    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    if not api_key.is_active:
        raise HTTPException(status_code=403, detail="API key has been revoked")

    window_start = datetime.utcnow() - timedelta(seconds=WINDOW_SECONDS)

    request_count = db.query(RequestLog).filter(
        RequestLog.api_key_id == api_key.id,
        RequestLog.timestamp >= window_start
    ).count()

    remaining = MAX_REQUESTS - request_count - 1
    reset_time = int((datetime.utcnow() + timedelta(seconds=WINDOW_SECONDS)).timestamp())
    endpoint = Column(String, default="unknown")

    if request_count >= MAX_REQUESTS:
        raise HTTPException(status_code=429, 
                            detail="Rate limit exceeded",
                            headers={
                                "X-RateLimit-Limit": str(MAX_REQUESTS),
                                "X-RateLimit-Remaining":"0",
                                "X-Ratelimit-Reset": str(reset_time),
                                "Retru-After": str(WINDOW_SECONDS)
                            }
                        )
    
    log = RequestLog(api_key_id=api_key.id, endpoint=request.url.path)
    db.add(log)
    db.commit()
    
    if response:
        response.headers["X-RateLimit-Limit"] = str(MAX_REQUESTS)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-Ratelimit-Reset"] = str(reset_time)

    return api_key

@app.post("/register")
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

    api_key = APIKey(key=hashed_key, user_id=user_obj.id)
    db.add(api_key)
    db.commit()

    return {
        "api_key": raw_key,
        "message": "Save this key securely. It will not be shown again."
    }

@app.post("/keys/revoke")
def revoke_key(x_api_key: str = Header(...), db: Session = Depends(get_db)):
    hashed_key = hash_api_key(x_api_key)
    api_key = db.query(APIKey).filter(APIKey.key == hashed_key).first()

    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    api_key.is_active = False
    db.commit()

    return {"message" : "API key revoked successfully"}

@app.get("/protected")
def protected_route(api_key: APIKey = Depends(get_api_key)):
    return {"message": "You have access", "user_id": api_key.user_id}

@app.get("/gateway/users")
def get_users(api_key: APIKey = Depends(get_api_key)):
    return {"service": "user-service", "data": [{"id": 1, "name": "Amy"}, {"id" : "2", "name" : "Ben"}]}

@app.get("/gateway/orders")
def get_orders(api_key: APIKey = Depends(get_api_key)):
    return {"service" : "order_service", "data" : [{"order_id" : 101, "status" : "shipped"}, {"order_id" : 102, "status" : "pending"}]}

@app.get("/gateway/products")
def get_products(api_key: APIKey = Depends(get_api_key)):
    return {"service" : "product-service", "data": [{"product_id" : 1, "name" : "Laptop", "price" : 999}, {"product_id" : 2, "name" : "Mouse", "price": 29}]}