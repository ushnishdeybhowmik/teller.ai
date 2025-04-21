from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from models.Base import Base

class UserQuery(Base):
    __tablename__ = 'user_queries'

    id = Column(Integer, primary_key=True)
    query = Column(String)
    intent = Column(String)
    response = Column(String)            # ✅ New field
    timestamp = Column(String)
    rating = Column(Integer, nullable=True)  # ✅ New field (nullable)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="queries")
