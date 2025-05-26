from gtts import gTTS
import os
import playsound
import tempfile
import logging
from enum import Enum
import json
import re
from datetime import datetime
from core.llm.mistral.mistral import Mistral
from core.llm.tinyllama.tinyllama import TinyLlama
from core.llm.gpt.gpt import GPT
from typing import Tuple, Optional, Dict
import time

logger = logging.getLogger(__name__)

# Global model cache
_model_cache: Dict[str, object] = {}

class LLM(Enum):
    MISTRAL = "mistral"
    GPT = "gpt"
    TINYLLAMA = "tinyllama"

    @classmethod
    def from_name(cls, name: str) -> 'LLM':
        """Get LLM enum value from name (case-insensitive)."""
        try:
            return next(llm for llm in cls if llm.value.lower() == name.lower())
        except StopIteration:
            logger.warning(f"Unknown LLM name: {name}, defaulting to MISTRAL")
            return cls.MISTRAL

    @classmethod
    def get_values(cls) -> list[str]:
        """Get list of all LLM values."""
        return [llm.value for llm in cls]

    @classmethod
    def get_index(cls, llm: 'LLM') -> int:
        """Get index of LLM in the list of values."""
        try:
            if isinstance(llm, str):
                llm = cls.from_name(llm)
            return list(cls).index(llm)
        except (ValueError, AttributeError):
            logger.warning(f"Invalid LLM value: {llm}, defaulting to MISTRAL")
            return 0  # Default to MISTRAL index

class Agent:
    def __init__(self, model: LLM = LLM.MISTRAL):
        """Initialize the agent with specified model."""
        self.model = model
        self._initialize_model()
        logger.info(f"Initialized agent with model: {model.value}")

    def _get_cached_model(self, model_name: str) -> Optional[object]:
        """Get model from cache if available."""
        return _model_cache.get(model_name)

    def _cache_model(self, model_name: str, model: object):
        """Cache a model instance."""
        _model_cache[model_name] = model
        logger.info(f"Cached {model_name} model")

    def _initialize_model(self):
        """Initialize the selected model with caching."""
        try:
            # Check cache first
            cached_model = self._get_cached_model(self.model.value)
            if cached_model:
                self.agent = cached_model
                logger.info(f"Using cached {self.model.value} model")
                return

            # Initialize new model if not in cache
            if self.model == LLM.MISTRAL:
                self.agent = Mistral()
            elif self.model == LLM.GPT:
                self.agent = GPT()
            elif self.model == LLM.TINYLLAMA:
                self.agent = TinyLlama()
            else:
                raise ValueError(f"Unsupported model: {self.model}")

            # Cache the initialized model
            self._cache_model(self.model.value, self.agent)
            logger.info(f"Successfully initialized and cached {self.model.value} model")

        except Exception as e:
            logger.error(f"Failed to initialize {self.model.value} model: {e}")
            # Try to get any available model from cache
            for model_name in LLM.get_values():
                cached_model = self._get_cached_model(model_name)
                if cached_model:
                    self.agent = cached_model
                    self.model = LLM.from_name(model_name)
                    logger.info(f"Falling back to cached {model_name} model")
                    return

            # If no cached models available, fallback to Mistral
            if self.model != LLM.MISTRAL:
                logger.info("No cached models available, falling back to Mistral")
                self.model = LLM.MISTRAL
                self.agent = Mistral()
                self._cache_model(self.model.value, self.agent)

    def speak(self, text: str) -> bool:
        """
        Convert text to speech and play it.
        
        Args:
            text (str): Text to convert to speech
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create a temporary file with a unique name
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                temp_filename = temp_file.name

            # Generate speech
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(temp_filename)

            # Play the audio
            playsound(temp_filename)

            # Clean up
            try:
                os.unlink(temp_filename)
            except Exception as e:
                logger.warning(f"Failed to delete temporary file {temp_filename}: {e}")

            return True

        except Exception as e:
            logger.error(f"TTS playback failed: {e}")
            return False

    def analyze_sentiment(self, text: str) -> str:
        """Analyze the sentiment of the response."""
        try:
            return self.agent.analyze_sentiment(text)
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return "NEUTRAL"

    def get_intent_and_response(self, query: str) -> Tuple[str, str]:
        """
        Get intent and response for a query.
        
        Args:
            query (str): User's query
            
        Returns:
            Tuple[str, str]: (intent, response)
        """
        try:
            return self.agent.get_intent_and_response(query)
        except Exception as e:
            logger.error(f"Error getting intent and response: {e}")
            return "error", "I apologize, but I'm having trouble processing your request. Please try again."

    def __str__(self):
        return f"Agent using {self.agent}"

    @classmethod
    def clear_cache(cls):
        """Clear the model cache."""
        global _model_cache
        _model_cache.clear()
        logger.info("Model cache cleared")
