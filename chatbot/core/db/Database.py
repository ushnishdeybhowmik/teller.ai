from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.Base import Base
from models.User import User
from models.BankAccount import BankAccount
from datetime import datetime
class Database:
    def __init__(self):
        self.engine = create_engine('sqlite:///tellerai.db', echo=True)
        Base.metadata.create_all(self.engine)

        # Create a session
        SessionLocal = sessionmaker(bind=self.engine)
        self.session = SessionLocal()
        
    def __generate_account_number(self):
        time = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"{time}{self.session.query(BankAccount).count()+1}"
        
    def addUser(self, name, email, password, secret_question, secret_answer):
        user = User(name=name, email=email, password=password, secret_question=secret_question, secret_answer=secret_answer)
        self.session.add(user)
        self.session.commit()
        
    def updateUser(self, user_id, name=None, email=None):
        user = self.session.query(User).filter_by(id=user_id).first()
        user.name = name if not None else user.name
        user.email = email if not None else user.email
        self.session.commit()
        
    def verifyUser(self, email, password):
        return self.session.query(User).filter_by(email=email).first().password == password
    
    def updatePassword(self, email, password):
        user = self.session.query(User).filter_by(email=email).first()
        user.password = password
        self.session.commit()
        
    def verifySecretAnswer(self, email, secret_answer):
        return str(self.session.query(User).filter_by(email=email).first().secret_answer).lower().rstrip() == str(secret_answer).lower().rstrip()
    
    def getSecretQuestion(self, email):
        return self.session.query(User).filter_by(email=email).first().secret_question
        
    def getUser(self, user_id):
        return self.session.query(User).filter_by(id=user_id).first()
    
    def getUserFromEmail(self, email):
        return self.session.query(User).filter_by(email=email).first()
        
    def addBankAccount(self, user_id, balance=0):
        account_number = self.__generate_account_number()
        bank_account = BankAccount(account_number=account_number, balance=balance, user_id=user_id)
        self.session.add(bank_account)
        self.session.commit()
        
    def updateBalance(self, account_number, balance):
        bank_account = self.session.query(BankAccount).filter_by(account_number=account_number).first()
        bank_account.balance = balance
        self.session.commit()
        
    def getBalance(self, account_number):
        return self.session.query(BankAccount).filter_by(account_number=account_number).first().balance
    
    def getUserFromBankAccount(self, account_number):
        return self.session.query(User).filter_by(id=self.session.query(BankAccount).filter_by(account_number=account_number).first().user_id).first() 
    
    def getBankAccount(self, user_id):
        return self.session.query(BankAccount).filter_by(user_id=user_id).first()     
    