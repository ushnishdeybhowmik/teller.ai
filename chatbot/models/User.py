from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .Base import Base
from core.processing.security import verify_password, hash_password
from typing import Dict, Any

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(100), nullable=False)
    account_number = Column(String(20), unique=True, nullable=False)
    latitude = Column(Float)
    longitude = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    login_count = Column(Integer, default=0)
    last_location = Column(String(200))
    is_admin = Column(Boolean, default=False)

    queries = relationship("UserQuery", back_populates="user")

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if 'password' in kwargs:
            self.password = hash_password(kwargs['password'])

    def verify_password(self, password: str) -> bool:
        """Verify the user's password."""
        return verify_password(password, self.password)

    def to_dict(self) -> Dict[str, Any]:
        """Convert user object to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'email': self.email,
            'account_number': self.account_number,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'created_at': self.created_at,
            'last_login': self.last_login,
            'login_count': self.login_count,
            'last_location': self.last_location,
            'is_admin': self.is_admin
        }

    def __repr__(self):
        return f"<User {self.name} ({self.email})>"
