from gtts import gTTS
import os
import playsound
import tempfile
import logging
from core.llm.mistral.mistral import Mistral
from core.llm.tinyllama.tinyllama import TinyLlama
from enum import Enum
import json
import re

class LLM(Enum):
    MISTRAL = 1
    TINYLLAMA = 2

class Agent:
    def __init__(self, model: LLM = LLM.MISTRAL):
        if model.name == LLM.MISTRAL.name:
            self.__llm = Mistral()
        elif model.name == LLM.TINYLLAMA.name:
            self.__llm = TinyLlama()

    def speak(self, text):
        try:
            tts = gTTS(text)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                path = fp.name
                tts.save(path)
            playsound.playsound(path)
            os.remove(path)
        except Exception as e:
            logging.warning(f"TTS playback failed: {e}")
            raise RuntimeError("TTS playback failed")

    def get_intent_and_response(self, query):
        prompt = f"""
        You are a smart banking assistant.

        Given a user's banking query, return ONLY the following JSON:

        {{
        "intent": "...",
        "response": "..."
        }}

        Ensure the response is valid JSON. Do not include any explanation or prefix text.

        User query: "{query}"
        """
        res = self.__llm(prompt)
        output = res["choices"][0]["text"]
        print(output)
        json_match = re.search(r"\{.*?\}", output, re.DOTALL)
        if not json_match:
            return "unknown", "Sorry, couldn't process."
        
        try:
            result = json.loads(output.strip())
            return result.get("intent", "unknown"), result.get("response", "Sorry, couldn't process.")
        except:
            return "unknown", "Sorry, something went wrong."
