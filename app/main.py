from fastapi import FastAPI
from .database import engine, Base
from . routes import auth, gateway

app = FastAPI(title="API Gateway with Rate Limiting")

app.include_router(auth.router)
app.include_router(gateway.router)