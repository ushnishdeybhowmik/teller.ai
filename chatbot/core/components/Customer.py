from core.db.Database import Database

class Customer:
    def __init__(self):
        self.db = Database()
        
    def add(self, name, email, password, secret_question, secret_answer):
        self.db.addUser(name, email, password, secret_question, secret_answer)
        self.db.addBankAccount(self.db.getUser(email=email).id, self.db.getUser(email=email).id)