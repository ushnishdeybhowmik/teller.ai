from llama_cpp import Llama
import os
from ..base import BaseLLM
import json
from typing import Tuple
import logging

logger = logging.getLogger(__name__)

class Mistral(BaseLLM):
    def __init__(self):
        try:
            # Try multiple possible model paths
            model_paths = [
                os.path.join(os.getcwd(), "core", "llm", "mistral", "mistral-7b-instruct-v0.2.Q4_K_M.gguf"),
                os.path.join(os.getcwd(), "chatbot", "core", "llm", "mistral", "mistral-7b-instruct-v0.2.Q4_K_M.gguf"),
                os.path.join(os.path.dirname(__file__), "mistral-7b-instruct-v0.2.Q4_K_M.gguf")
            ]
            
            model_path = None
            for path in model_paths:
                if os.path.exists(path):
                    model_path = path
                    break
                    
            if not model_path:
                raise FileNotFoundError("Could not find Mistral model file in any of the expected locations")
                
            self.llm = Llama(model_path=model_path, 
                           n_ctx=2048, 
                           n_threads=6,
                           n_gpu_layers=20)
            logger.info(f"Successfully initialized Mistral model from {model_path}")
        except Exception as e:
            logger.error(f"Failed to initialize Mistral model: {e}")
            raise
        
    def get_intent_and_response(self, query: str) -> Tuple[str, str]:
        """Get intent and response for a banking query."""
        prompt = f"""You are a banking assistant. Analyze the following query and respond in JSON format:
{{
    "intent": "one of: account_balance, transaction_history, transfer_money, card_issues, loan_inquiry, general_inquiry",
    "response": "your helpful response"
}}

Query: {query}

Response:"""
        
        try:
            response = self.llm(prompt,
                              max_tokens=1024,
                              temperature=0.7,
                              echo=False)
            
            # Parse and validate the response
            intent, response_text = self._parse_intent_response(response)
            
            # Log successful response
            logger.info(f"Successfully processed query with intent: {intent}")
            
            return intent, response_text
            
        except Exception as e:
            return self._handle_error(e, "get_intent_and_response")
    
    def analyze_sentiment(self, text: str) -> str:
        """Analyze the sentiment of the response."""
        prompt = f"""Analyze the sentiment of this banking customer service response. Return ONLY one of these words:
- POSITIVE
- NEGATIVE
- NEUTRAL

Response: "{text}"
"""
        try:
            response = self.llm(prompt,
                              max_tokens=50,
                              temperature=0.3,
                              echo=False)
            
            # Validate sentiment
            sentiment = self._validate_sentiment(response.strip())
            
            # Log sentiment analysis
            logger.info(f"Analyzed sentiment: {sentiment}")
            
            return sentiment
            
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return "NEUTRAL"
    
    def __str__(self):
        return "Mistral\nType: 7b-instruct\nVersion: v0.2.Q4_K_M\nContext: 2048\nThreads: 6"
    
    
    

