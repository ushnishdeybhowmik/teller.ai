from core.db.Database import Database

class Customer:
    def __init__(self):
        self.db = Database()
        
    def add(self, name, email, password, secret_question, secret_answer, balance=0):
        self.db.addUser(name, email, password, secret_question, secret_answer)
        self.db.addBankAccount(self.db.getUserFromEmail(email).id, balance)
        account = self.db.getBankAccount(self.db.getUserFromEmail(email).id)
        
        text = f"{name}, your account has been successfully created.\nACC NO: {account.account_number}\nBalance: {account.balance}"
        user = self.db.getUserFromEmail(email)
        return text, user
        
    def login(self, email, password):
        if self.db.verifyUser(email, password):
            user = self.db.getUserFromEmail(email)
            text = f"Welcome back, {user.name}!"
            return text, user
        else:
            return "Invalid email or password.", None
    
    def getAccount(self, user_id):
        return self.db.getBankAccount(user_id)