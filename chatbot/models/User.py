from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from models.Base import Base

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    account_number = Column(String, unique=True)
    phone = Column(String, unique=True)
    password_hash = Column(String)

    queries = relationship("UserQuery", back_populates="user")