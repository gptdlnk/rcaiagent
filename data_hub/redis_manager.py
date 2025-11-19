import redis
import json
import time
from typing import Dict, Any, List

class RedisManager:
    """
    Central Data Hub (Blackboard) for communication between AI Agents.
    Uses Redis for state management, logging, and action queuing.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.db = self._connect()
        self.init_keys()

    def _connect(self):
        """Connect to Redis server."""
        try:
            r = redis.Redis(
                host=self.config['HOST'],
                port=self.config['PORT'],
                db=self.config['DB'],
                decode_responses=True
            )
            r.ping()
            print("Redis connection successful.")
            return r
        except redis.exceptions.ConnectionError as e:
            print(f"Error connecting to Redis: {e}")
            raise

    def init_keys(self):
        """Initialize essential keys if they don't exist."""
        if not self.db.exists('STATE:CURRENT'):
            self.db.set('STATE:CURRENT', 'INITIALIZING')
        if not self.db.exists('KB:VULNERABILITIES'):
            self.db.set('KB:VULNERABILITIES', json.dumps([]))
        if not self.db.exists('ERROR:LAST_MESSAGE'):
            self.db.set('ERROR:LAST_MESSAGE', "")
        
        # Clear action queue from previous runs
        self.db.delete('QUEUE:ACTIONS')
        print("Redis keys initialized.")

    # --- State Management ---
    def get_state(self) -> str:
        return self.db.get('STATE:CURRENT') or 'UNKNOWN'

    def set_state(self, state: str):
        self.db.set('STATE:CURRENT', state)

    # --- Action Queue (FIFO) ---
    def push_action(self, action_json: Dict[str, Any]):
        """Push a new action command to the queue."""
        self.db.rpush('QUEUE:ACTIONS', json.dumps(action_json))

    def pop_action(self) -> Dict[str, Any] | None:
        """Pop the next action command from the queue (blocking pop for efficiency)."""
        # BLPOP waits for 1 second if the list is empty
        item = self.db.blpop('QUEUE:ACTIONS', timeout=1)
        if item:
            # item is (key, value)
            return json.loads(item[1])
        return None

    def get_queue_size(self, key: str) -> int:
        return self.db.llen(key)

    # --- Logging and Observation ---
    def log_observation(self, agent_name: str, message: str):
        """Log an observation message with timestamp."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{agent_name}] {message}"
        self.db.lpush('LOG:OBSERVATION', log_entry)
        # Keep log size manageable (e.g., last 1000 entries)
        self.db.ltrim('LOG:OBSERVATION', 0, 999)

    # --- Self-Improvement / Learning ---
    def log_learning_data(self, data_type: str, data: Dict[str, Any]):
        """Logs data for the Planner to use for self-improvement (e.g., failed attack attempts)."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        entry = {"timestamp": timestamp, "type": data_type, "data": data}
        self.db.lpush('LEARNING:DATA', json.dumps(entry))
        self.db.ltrim('LEARNING:DATA', 0, 99) # Keep the last 100 learning entries

    def get_learning_data(self) -> List[Dict[str, Any]]:
        """Retrieves all learning data for the Planner."""
        raw_data = self.db.lrange('LEARNING:DATA', 0, -1)
        return [json.loads(item) for item in raw_data]

    def clear_learning_data(self):
        """Clears the learning data after the Planner has processed them."""
        self.db.delete('LEARNING:DATA')

    def get_latest_observations(self, count: int = 10) -> List[str]:
        """Retrieve the latest observations."""
        return self.db.lrange('LOG:OBSERVATION', 0, count - 1)

    # --- Knowledge Base (Vulnerabilities) ---
    def add_vulnerability(self, vuln_data: Dict[str, Any]):
        """Add a new confirmed vulnerability to the knowledge base."""
        vulns = json.loads(self.db.get('KB:VULNERABILITIES'))
        vulns.append(vuln_data)
        self.db.set('KB:VULNERABILITIES', json.dumps(vulns))

    def get_vulnerabilities(self) -> List[Dict[str, Any]]:
        """Retrieve all confirmed vulnerabilities."""
        return json.loads(self.db.get('KB:VULNERABILITIES'))

    # --- Error Handling ---
    def set_error(self, agent_name: str, error_message: str):
        """Set the last error message and change state to ERROR_HANDLING."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        full_error = f"[{timestamp}] [{agent_name}] {error_message}"
        self.db.set('ERROR:LAST_MESSAGE', full_error)
        self.set_state('ERROR_HANDLING')
        
        # Log the error for the Planner's learning process
        self.log_learning_data("CRITICAL_ERROR", {"agent": agent_name, "message": error_message})

    def clear_error(self):
        """Clear the last error message."""
        self.db.set('ERROR:LAST_MESSAGE', "")

    def get_last_error(self) -> str:
        return self.db.get('ERROR:LAST_MESSAGE') or ""
