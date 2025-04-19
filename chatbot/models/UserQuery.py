from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from models.Base import Base

class UserQuery(Base):
    __tablename__ = 'user_queries'

    id = Column(Integer, primary_key=True)
    query = Column(String)            # 👈 stores the actual user query
    intent = Column(String)           # 👈 stores extracted intent
    user_id = Column(Integer, ForeignKey('users.id'))  # 👈 links to User table

    user = relationship("User", back_populates="queries") 