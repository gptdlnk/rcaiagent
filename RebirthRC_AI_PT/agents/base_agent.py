import time
import threading
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
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
        
        # Get API key and base URL from config
        api_key = config.get('API_KEY', '')
        base_url = config.get('BASE_URL', 'https://api.openai.com/v1')
        
        # Initialize OpenAI Client with API key and base URL
        # For 5 Hihg or custom endpoints, base_url can be overridden
        client_kwargs = {}
        if api_key:
            client_kwargs['api_key'] = api_key
        if base_url and base_url != 'https://api.openai.com/v1':
            client_kwargs['base_url'] = base_url
        
        try:
            self.ai_client = OpenAI(**client_kwargs) if client_kwargs else OpenAI()
        except Exception as e:
            print(f"Warning: Failed to initialize AI client for {self.name}: {e}")
            self.ai_client = None 

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

    def call_ai_model(self, user_prompt: str, max_retries: int = 3) -> str:
        """
        Generic function to call the assigned AI model.
        This is where the actual API call to GPT, Codex, or 5 Hihg happens.
        Includes retry logic for transient failures.
        """
        if not self.ai_client:
            error_msg = f"AI client not initialized for {self.name}. Check API keys."
            self.set_error(error_msg)
            return f"ERROR: {error_msg}"
        
        self.log(f"Calling AI model {self.model_name}...")
        
        for attempt in range(max_retries):
            try:
                # OpenAI API call structure
                response = self.ai_client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=self.temperature,
                    timeout=60  # 60 second timeout
                )
                result = response.choices[0].message.content.strip()
                self.log(f"AI model {self.model_name} responded successfully.")
                return result
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2  # Exponential backoff: 2s, 4s, 6s
                    self.log(f"AI Model API call failed (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    error_msg = f"AI Model API call failed for {self.model_name} after {max_retries} attempts: {e}"
                    self.set_error(error_msg)
                    return f"ERROR: {error_msg}"
        
        return "ERROR: Unexpected error in call_ai_model"

    @abstractmethod
    def run(self):
        """The main loop for the agent's logic."""
        pass

# --- Agent Specific Implementations (Stubs) ---
# The actual logic for each agent will be in their respective files.
