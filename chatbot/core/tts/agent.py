from gtts import gTTS
import os
import playsound

class Agent:
    def __init__(self, path=None):
        self.path = path if path else "temp"
        self.base_path = os.path.join(os.getcwd(), self.path)
        self.active = True
        
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)

    def speak(self, text):
        try:
            tts = gTTS(text=text, lang="en")
            file_path = os.path.join(self.base_path, "output.mp3")
            tts.save(file_path)
        except AssertionError:
            text = "I'm sorry, I couldn't understand what you said. Please try again later."
            file_path = os.path.join(self.base_path, "output.mp3")
            tts = gTTS(text=text, lang="en")
            tts.save(file_path)
        except Exception as e:
            text = "Sorry! An unforeseen error occurred. Please try again later."
            file_path = os.path.join(self.base_path, "output.mp3")
            tts = gTTS(text=text, lang="en")
            tts.save(file_path)

        playsound.playsound(file_path)
        os.remove(file_path)
        return

    
    def action(self, data):
        
        
        greetings = ["hello", "hi", "hey"]
        bank_verbs = ["withdraw", "deposit", "transfer", "create", "open", "close"]
        
        if any(greeting in data for greeting in greetings):
            text = "Hello! How can I help you today?"
            self.speak(text)
            return
        elif any(bank_verb in data for bank_verb in bank_verbs):
            if "withdraw" in data:
                text = "Withdrawal is currently unavailable. Please try again later."
                self.speak(text)
                return
            elif "deposit" in data:
                text = "Deposit is currently unavailable. Please try again later."
                self.speak(text)
                return
            elif "transfer" in data:
                text = "Transfer is currently unavailable. Please try again later."
                self.speak(text)
                return
            elif "create" in data:
                text = "Account creation is currently unavailable. Please try again later."
                self.speak(text)
                return
            elif "open" in data:
                text = "Account opening is currently unavailable. Please try again later."
                self.speak(text)
                return
            elif "close" in data:
                text = "Account closing is currently unavailable. Please try again later."
                self.speak(text)
                return
        elif "thank" in data:
            text = "You're welcome! Feel free to come back!"
            self.speak(text)
            self.active = False
            return