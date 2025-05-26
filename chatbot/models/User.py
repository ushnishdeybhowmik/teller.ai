from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .Base import Base

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(15), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(100), nullable=False)
    account_number = Column(String(12), unique=True, nullable=False)
    latitude = Column(Float)
    longitude = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    login_count = Column(Integer, default=0)
    last_location = Column(String(100))  # Store city/region
    is_admin = Column(Boolean, default=False)

    queries = relationship("UserQuery", back_populates="user", cascade="all, delete-orphan")
