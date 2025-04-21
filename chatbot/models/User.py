from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship
from models.Base import Base

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    account_number = Column(String, unique=True)
    phone = Column(String, unique=True)
    latitude = Column(Float)  # changed from String to Float
    longitude = Column(Float)  # changed from String to Float
    password_hash = Column(String)

    queries = relationship("UserQuery", back_populates="user")
