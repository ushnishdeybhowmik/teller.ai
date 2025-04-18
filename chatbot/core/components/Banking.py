from core.db.Database import Database

class Banking:
    
    def __init__(self):
        self.db = Database()
        
    def withdraw(self, account_number, amount):
        if amount < self.db.getBalance(account_number):
            self.db.updateBalance(account_number, self.db.getBalance(account_number) - amount)
            text = "Withdrawal successful. Total balance: " + str(self.db.getBalance(account_number))
            return text
        else:
            text = "Insufficient balance. Please try again later."
            return text
        
    def deposit(self, account_number, amount):
        
        self.db.updateBalance(account_number, self.db.getBalance(account_number) + amount)
        text = "Deposit successful. Total balance: " + str(self.db.getBalance(account_number))
        return text
        
    def transfer(self, from_account_number, to_account_number, amount):
        acc_1_bal = self.db.getBalance(from_account_number)
        acc_2_bal = self.db.getBalance(to_account_number)
        to_user = self.db.getUserFromBankAccount(to_account_number)
        try:
            self.db.updateBalance(from_account_number, acc_1_bal - amount)
            self.db.updateBalance(to_account_number, acc_2_bal + amount)
            text = f"Transfer successful to {to_user.name}. Thank you for using our services."
        except Exception as e:
            text = "Sorry! An unforeseen error occurred. Please try again later."
            self.db.updateBalance(from_account_number, acc_1_bal)
            self.db.updateBalance(to_account_number, acc_2_bal)
            
        return text