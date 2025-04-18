from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.Base import Base
from models.User import User
from models.UserQuery import UserQuery
from core.processing.security import hash_password
import random
class Database:
    def __init__(self):
        self.__engine = create_engine('sqlite:///tellerai.db', echo=True)
        Base.metadata.create_all(self.__engine)

        # Create a session
        SessionLocal = sessionmaker(bind=self.__engine)
        self.__session = SessionLocal()
    
    def __generateAccountNumber(self):
        while True:
            acc_num = str(random.randint(10**9, 10**10 - 1))  # 10-digit number
            if not self.__session.query(User).filter_by(account_number=acc_num).first():
                return acc_num
    def userExistOrCreate(self, name, phone, password, account_number=0):
        self.__user = self.__session.query(User).filter_by(account_number=account_number).first()
        if not self.__user:
            account_number = self.__generateAccountNumber()
            hashed_password = hash_password(password)
            self.__user = User(name=name, account_number=account_number, phone=phone, password_hash=hashed_password)
            self.__session.add(self.__user)
            self.__session.commit()
            self.__user = self.__session.query(User).filter_by(account_number=account_number).first()
        return self.__user
        
        
    def getUser(self, account_number):
        return self.__session.query(User).filter_by(account_number=account_number).first()
    
    def addQuery(self, query, intent):
        new_query = UserQuery(query=query, intent=intent, user=self.__user)
        self.__session.add(new_query)
        self.__session.commit()
        
    def getUserFromPhoneNo(self, phone):
        return self.__session.query(User).filter_by(phone=phone).first()