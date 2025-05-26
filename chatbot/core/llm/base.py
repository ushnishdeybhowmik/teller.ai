from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Optional
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class BaseLLM(ABC):
    """Base class for all LLM models with standardized interface."""
    
    VALID_INTENTS = {
        "account_balance",
        "transaction_history",
        "transfer_money",
        "card_issues",
        "loan_inquiry",
        "general_inquiry"
    }
    
    VALID_SENTIMENTS = {"POSITIVE", "NEGATIVE", "NEUTRAL"}
    
    @abstractmethod
    def get_intent_and_response(self, query: str) -> Tuple[str, str]:
        """
        Get intent and response for a query.
        
        Args:
            query (str): User's query
            
        Returns:
            Tuple[str, str]: (intent, response)
        """
        pass
    
    @abstractmethod
    def analyze_sentiment(self, text: str) -> str:
        """
        Analyze the sentiment of text.
        
        Args:
            text (str): Text to analyze
            
        Returns:
            str: Sentiment (POSITIVE, NEGATIVE, or NEUTRAL)
        """
        pass
    
    def _format_intent_response(self, intent: str, response: str, confidence: float = 1.0) -> Dict[str, Any]:
        """Format intent and response into a standardized structure."""
        return {
            "intent": intent,
            "response": response,
            "metadata": {
                "confidence": confidence,
                "timestamp": datetime.utcnow().isoformat(),
                "model": self.__class__.__name__
            }
        }
    
    def _validate_intent(self, intent: str) -> str:
        """Validate and normalize intent."""
        intent = intent.lower().strip()
        if intent not in self.VALID_INTENTS:
            logger.warning(f"Invalid intent detected: {intent}, defaulting to general_inquiry")
            return "general_inquiry"
        return intent
    
    def _validate_sentiment(self, sentiment: str) -> str:
        """Validate and normalize sentiment."""
        sentiment = sentiment.upper().strip()
        if sentiment not in self.VALID_SENTIMENTS:
            logger.warning(f"Invalid sentiment detected: {sentiment}, defaulting to NEUTRAL")
            return "NEUTRAL"
        return sentiment
    
    def _parse_intent_response(self, raw_response: str) -> Tuple[str, str]:
        """
        Parse raw LLM response into intent and response.
        
        Args:
            raw_response (str): Raw response from LLM
            
        Returns:
            Tuple[str, str]: (intent, response)
        """
        try:
            # Try to parse as JSON first
            data = json.loads(raw_response)
            intent = self._validate_intent(data.get("intent", "unknown"))
            response = data.get("response", "").strip()
            if not response:
                raise ValueError("Empty response")
            return intent, response
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            # If not JSON, try to extract intent from first line
            lines = raw_response.strip().split("\n")
            if len(lines) >= 2:
                intent = self._validate_intent(lines[0].strip())
                response = "\n".join(lines[1:]).strip()
                if not response:
                    raise ValueError("Empty response")
                return intent, response
            raise ValueError("Invalid response format")
    
    def _handle_error(self, error: Exception, context: str) -> Tuple[str, str]:
        """Handle errors consistently across all LLM implementations."""
        logger.error(f"Error in {context}: {str(error)}")
        return "error", f"I apologize, but I'm having trouble processing your request. Please try again." 