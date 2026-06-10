from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from ..dependencies import get_db, get_api_key
from ..models import RequestLog, APIKey
from ..schemas import AnalyticsResponse
from ..utils import hash_api_key

router = APIRouter()

@router.get("/analytics/usage", response_model=AnalyticsResponse)
def get_usage(api_key: APIKey = Depends(get_api_key), db: Session = Depends(get_db)):
    logs = db.query(RequestLog).filter(
        RequestLog.api_key_id == api_key.id
    ).all()

    requests_per_endpoint = {}
    for log in logs:
        endpoint = log.endpoint or "unkwown"
        requests_per_endpoint[endpoint] = requests_per_endpoint.get(endpoint, 0) + 1
    
    window_start = datetime.utcnow() - timedelta(seconds=60)
    rate_limit_hits = db.query(RequestLog).filter(
        RequestLog.api_key_id == api_key.id,
        RequestLog.timestamp >= window_start
    ).count()

    return AnalyticsResponse(
        api_key_hash = api_key.key,
        total_requests=len(logs),
        requests_per_endpoint = requests_per_endpoint,
        rate_limit_hits = rate_limit_hits 
    )