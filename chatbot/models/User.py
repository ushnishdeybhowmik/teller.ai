from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from models.Base import Base

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password = Column(String(120), nullable=False)
    secret_question = Column(String(120), nullable=False)
    secret_answer = Column(String(120), nullable=False)

    bank_account = relationship('BankAccount', back_populates='user', uselist=False)
