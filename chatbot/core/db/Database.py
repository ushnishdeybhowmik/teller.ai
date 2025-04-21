from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.Base import Base
from models.User import User
from models.UserQuery import UserQuery
from core.processing.security import hash_password
import random
import datetime
class Database:
    def __init__(self):
        self.__engine = create_engine('sqlite:///tellerai.db', echo=True)
        Base.metadata.create_all(self.__engine)

        # Create a session
        SessionLocal = sessionmaker(bind=self.__engine)
        self.__session = SessionLocal()
        self.__user = None
    
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
            self.__user = User(name=name, account_number=account_number, phone=phone, latitude=0, longitude=0, password_hash=hashed_password)
            self.__session.add(self.__user)
            self.__session.commit()
            self.__user = self.__session.query(User).filter_by(account_number=account_number).first()
        return self.__user
    
    def updateLocation(self, latitude, longitude):
        if self.__user:
            self.__user.latitude = latitude
            self.__user.longitude = longitude
            self.__session.commit()
            return True
        return False    
        
    def getUser(self, account_number):
        return self.__session.query(User).filter_by(account_number=account_number).first()
    
    def setUser(self, user):
        self.__user = user
    
    def addQuery(self, query, intent, response):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_query = UserQuery(query=query, intent=intent, response=response, timestamp=timestamp, rating=0, user=self.__user)
        self.__session.add(new_query)
        self.__session.commit()
        return new_query.id  # Return the ID to update rating later
        
    def getUserFromPhoneNo(self, phone):
        return self.__session.query(User).filter_by(phone=phone).first()
    
    def updateRating(self, query_id, rating):
        user_query = self.__session.query(UserQuery).filter_by(id=query_id).first()
        if user_query:
            user_query.rating = rating
            self.__session.commit()
            
    def getEngine(self):
        return self.__engine