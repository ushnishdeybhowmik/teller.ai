from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .Base import Base

class UserQuery(Base):
    __tablename__ = 'user_queries'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    query = Column(Text, nullable=False)
    intent = Column(String(100))
    response = Column(Text)
    rating = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)
    location = Column(String(100))  # Store city/region
    sentiment = Column(String(20))  # Positive, Negative, Neutral
    resolution_time = Column(Float)  # Time taken to resolve query
    follow_up_required = Column(Boolean, default=False, nullable=False)
    query_metadata = Column(JSON)  # Store additional analytics data
    
    user = relationship("User", back_populates="queries")
