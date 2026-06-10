from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..dependencies import get_db
from datetime import datetime

router = APIRouter()

@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "unreachable"
    
    status = "ok" if db_status == "connected" else "degraded"
    code = 200 if status == "ok" else 503

    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code = code,
        content={
            "status": status,
            "database": db_status,
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat()
        }
    )