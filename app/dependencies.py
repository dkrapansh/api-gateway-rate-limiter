from fastapi import Depends, Header, HTTPException, Request, Response
from sqlalchemy.orm import Session
from datetime import datetime,  timedelta
from .database import SessionLocal
from .models import APIKey, RequestLog
from .utils import hash_api_key
from .config import settings
from sqlalchemy import func

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_api_key(
        request: Request,
        response:  Response,
        x_api_key: str = Header(...),
        db: Session = Depends(get_db)
):
    hashed_key = hash_api_key(x_api_key)
    api_key = db.query(APIKey).filter(APIKey.key == hashed_key).first()

    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    
    if not api_key.is_active:
        raise HTTPException(status_code=403, detail="API key been revoked")
    
    now = datetime.utcnow()
    window_start = now - timedelta(seconds=settings.window_seconds)
    db.query(APIKey).filter(APIKey.id == api_key.id).with_for_update().first()
    request_count = db.query(RequestLog).filter(
        RequestLog.api_key_id == api_key.id,
        RequestLog.timestamp >= window_start,
        RequestLog.timestamp <= now
    ).count()

    remaining = settings.max_requests - request_count - 1
    reset_time = int((datetime.utcnow() + timedelta(seconds=settings.window_seconds)).timestamp())

    if request_count >= settings.max_requests:
        raise HTTPException(
            status_code = 429,
            detail="Rate limit exceeded",
            headers={
                "X-RateLimit-Limit": str(settings.max_requests),
                "X-Ratelimit-Remining": "0",
                "X-RateLimit-Reset": str(reset_time),
                "Retry-After": str(settings.window_seconds)
            }
        )
    
    log = RequestLog(api_key_id = api_key.id, endpoint=request.url.path)
    db.add(log)
    db.commit()

    response.headers["X-RateLimit-Limit"] = str(settings.max_requests)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(reset_time)

    return api_key