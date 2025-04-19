from gtts import gTTS
import os
import playsound
from core.llm.mistral.mistral import Mistral

class Agent:
    def __init__(self):
        self.__llm = Mistral()

    def speak(self, text):
        self.__tts = gTTS(text)
        self.__tts.save("temp/temp.mp3")
        playsound.playsound("temp/temp.mp3")
        os.remove("temp/temp.mp3")
    
    def get_intent_and_response(self, query):
        prompt = f"""
            You are a smart banking assistant. Analyze the following user query and:
            1. Identify the user's intent (e.g., check balance, transfer money, open account, etc.)
            2. Provide a helpful and professional banking-related response.
            3. Reply in this JSON format:
            {{"intent": "...", "response": "..."}}

            User query: "{query}"
            """
        res = self.__llm(prompt, stop=["</s>"])
        output = res["choices"][0]["text"]
        try:
            result = self.__json.loads(output.strip())
            return result.get("intent", "unknown"), result.get("response", "Sorry, couldn't process.")
        except:
            return "unknown", "Sorry, something went wrong."