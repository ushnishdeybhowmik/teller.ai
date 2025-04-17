from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from models.Base import Base

class BankAccount(Base):
    __tablename__ = 'bank_accounts'

    id = Column(Integer, primary_key=True)
    account_number = Column(String(20), unique=True, nullable=False)
    balance = Column(Integer, default=0)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True, nullable=False)

    user = relationship('User', back_populates='bank_account')
    