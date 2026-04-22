from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)

    api_keys = relationship("APIKey", back_populates="user")

class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="api_keys")
    requests = relationship("RequestLog", back_populates="api_key")

class RequestLog(Base):
    __tablename__ = "request_logs"

    id = Column(Integer, primary_key=True, index=True)
    api_key_id = Column(Integer, ForeignKey("api_keys.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)

    api_key = relationship("APIKey", back_populates="requests")