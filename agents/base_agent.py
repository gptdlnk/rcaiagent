import time
import threading
import json
from abc import ABC, abstractmethod
from typing import Dict, Any
from openai import OpenAI # ใช้ OpenAI client สำหรับ GPT/Codex

class BaseAgent(ABC):
    """
    Abstract base class for all AI Agents.
    Handles common functionalities like Redis connection, logging, and AI model initialization.
    """
    def __init__(self, redis_manager, config: Dict[str, Any]):
        self.redis_manager = redis_manager
        self.name = config['NAME']
        self.model_name = config['MODEL']
        self.temperature = config['TEMPERATURE']
        self.system_prompt = config['SYSTEM_PROMPT']
        self._running = threading.Event()
        self._running.set()
        
        # Initialize OpenAI Client (assuming all models use OpenAI-compatible API)
        # For 5 Hihg, you might need a custom client/API call
        self.ai_client = OpenAI() 

    def is_running(self):
        return self._running.is_set()

    def stop(self):
        self._running.clear()
        print(f"Agent {self.name} stopped.")

    def log(self, message: str):
        """Log a message to the Redis observation log."""
        self.redis_manager.log_observation(self.name, message)
        print(f"[{self.name}] {message}")

    def set_error(self, error_message: str):
        """Set a critical error in the system."""
        self.redis_manager.set_error(self.name, error_message)
        self.log(f"CRITICAL ERROR: {error_message}")

    def call_ai_model(self, user_prompt: str) -> str:
        """
        Generic function to call the assigned AI model.
        This is where the actual API call to GPT, Codex, or 5 Hihg happens.
        """
        self.log(f"Calling AI model {self.model_name}...")
        try:
            # Simple OpenAI API call structure
            response = self.ai_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            self.set_error(f"AI Model API call failed for {self.model_name}: {e}")
            return f"ERROR: AI Model call failed: {e}"

    @abstractmethod
    def run(self):
        """The main loop for the agent's logic."""
        pass

# --- Agent Specific Implementations (Stubs) ---
# The actual logic for each agent will be in their respective files.
