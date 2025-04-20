from gtts import gTTS
import os
import playsound
import tempfile
import logging
from enum import Enum
import json
import re
from core.llm.mistral.mistral import Mistral
from core.llm.tinyllama.tinyllama import TinyLlama
from core.llm.gpt.gpt import GPT

class LLM(Enum):
    MISTRAL = 1
    TINYLLAMA = 2
    CHATGPT = 3

class Agent:
    def __init__(self, model: LLM = LLM.MISTRAL):
        self.allowed_intents = [
            "LOGIN_ISSUE",
            "PASSWORD_RESET",
            "ACCOUNT_LOCKED",
            "CUSTOMER_SUPPORT",
            "UNAUTHORIZED_ACTIVITY",
            "CARD_BLOCKED",
            "APP_CRASH",
            "TWO_FA_PROBLEM",
            "ACCOUNT_NOT_FOUND",
            "UNKNOWN"
        ]

        if model.name == LLM.MISTRAL.name:
            self.__llm = Mistral()
            self.agent = "MISTRAL"
        elif model.name == LLM.TINYLLAMA.name:
            self.__llm = TinyLlama()
            self.agent = "TINYLLAMA"
        elif model.name == LLM.CHATGPT.name:
            self.__llm = GPT()
            self.agent = "GPT"

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
You are a smart banking assistant. Return ONLY a single JSON object for the most relevant problem-based customer support intent from this list:

{', '.join(self.allowed_intents[:-1])}

Rules:
- Only one intent should be returned.
- Do NOT include intents that involve transactions or bank approvals.
- Give a generic response that does not elicit ANY FURTHER ACTION FROM USER
- If the query doesn't match any of the allowed intents, return:
  {{
    "intent": "UNKNOWN",
    "response": "Unable to help with this at the moment."
  }}
- You must respond ONLY with the JSON object and nothing else.
User query: "{query}"
""".strip()

        try:
            res = self.__llm(prompt)
            if not self.agent == "GPT":
                output = res["choices"][0]["text"].strip()
            else:
                output = res
            print("=== LLM Raw Output ===\n", output)

            # Extract only the first valid JSON block
            match = re.search(r'(\{\n\s\s\"intent\"\:\s\"(?:LOGIN_ISSUE|PASSWORD_RESET|ACCOUNT_LOCKED|CUSTOMER_SUPPORT|UNAUTHORIZED_ACTIVITY|CARD_BLOCKED|APP_CRASH|TWO_FA_PROBLEM|ACCOUNT_NOT_FOUND|UNKNOWN)\"\,\n\s\s\"response\"\:\s\".+\"\n\})', output)
            intent = "UNKNOWN"
            response = "Unable to help with this at the moment."
            
            if match:
                result = json.loads(match.group(1))
                intent = result.get("intent", "UNKNOWN")
                response = result.get("response", "Unable to help with this at the moment.")
                
            return intent, response

        except Exception as e:
            print(f"[agent.py error]: {e}")
            return "UNKNOWN", "Unable to help with this at the moment."
