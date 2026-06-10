from fastapi import FastAPI
from .database import engine, Base
from . routes import auth, gateway, health
from .middleware import CorreltaionIDMiddleware

app = FastAPI(title="API Gateway with Rate Limiting")

app.add_middleware(CorreltaionIDMiddleware)
app.include_router(auth.router)
app.include_router(gateway.router)
app.include_router(health.router)