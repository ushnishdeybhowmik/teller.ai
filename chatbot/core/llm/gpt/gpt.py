from openai import OpenAI
from dotenv import load_dotenv
import os
from ..base import BaseLLM
from typing import Tuple
import json
import logging

logger = logging.getLogger(__name__)

class GPT(BaseLLM):
    def __init__(self):
        try:
            env_path = os.path.join(os.getcwd(), ".env")
            load_dotenv(env_path)
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment variables")
            self.__client = OpenAI(api_key=api_key)
            logger.info("Successfully initialized GPT model")
        except Exception as e:
            logger.error(f"Failed to initialize GPT model: {e}")
            raise
        
    def get_intent_and_response(self, query: str) -> Tuple[str, str]:
        """Get intent and response for a banking query."""
        try:
            response = self.__client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a banking assistant. Analyze queries and respond in JSON format:
{
    "intent": "one of: account_balance, transaction_history, transfer_money, card_issues, loan_inquiry, general_inquiry",
    "response": "your helpful response"
}"""
                    },
                    {"role": "user", "content": query}
                ],
                temperature=0.7,
                max_tokens=300
            )
            
            # Parse and validate the response
            raw_response = response.choices[0].message.content.strip()
            intent, response_text = self._parse_intent_response(raw_response)
            
            # Log successful response
            logger.info(f"Successfully processed query with intent: {intent}")
            
            return intent, response_text
            
        except Exception as e:
            return self._handle_error(e, "get_intent_and_response")
    
    def analyze_sentiment(self, text: str) -> str:
        """Analyze the sentiment of the response."""
        try:
            response = self.__client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "Analyze the sentiment of this banking customer service response. Return ONLY one of these words: POSITIVE, NEGATIVE, or NEUTRAL"
                    },
                    {"role": "user", "content": text}
                ],
                temperature=0.3,
                max_tokens=50
            )
            
            # Validate sentiment
            sentiment = self._validate_sentiment(response.choices[0].message.content.strip())
            
            # Log sentiment analysis
            logger.info(f"Analyzed sentiment: {sentiment}")
            
            return sentiment
            
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return "NEUTRAL"
    
    def __str__(self):
        return "GPT-3.5-Turbo"
        