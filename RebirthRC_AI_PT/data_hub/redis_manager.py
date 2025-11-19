import redis
from redis.connection import ConnectionPool
import json
import time
from typing import Dict, Any, List, Optional

class RedisManager:
    """
    Central Data Hub (Blackboard) for communication between AI Agents.
    Uses Redis for state management, logging, and action queuing.
    Includes connection pooling and retry logic for reliability.
    """
    def __init__(self, config: Dict[str, Any], max_retries: int = 3, retry_delay: float = 2.0):
        self.config = config
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.pool = None
        self.db = self._connect_with_retry()

    def _create_connection_pool(self) -> ConnectionPool:
        """Create a Redis connection pool for better performance."""
        return ConnectionPool(
            host=self.config['HOST'],
            port=self.config['PORT'],
            db=self.config['DB'],
            decode_responses=True,
            max_connections=10,
            retry_on_timeout=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )

    def _connect(self) -> redis.Redis:
        """Create a Redis connection from the pool."""
        if not self.pool:
            self.pool = self._create_connection_pool()
        
        return redis.Redis(connection_pool=self.pool)

    def _connect_with_retry(self) -> redis.Redis:
        """Connect to Redis server with retry logic."""
        for attempt in range(self.max_retries):
            try:
                db = self._connect()
                db.ping()
                print(f"Redis connection successful (attempt {attempt + 1}/{self.max_retries}).")
                return db
            except redis.exceptions.ConnectionError as e:
                if attempt < self.max_retries - 1:
                    print(f"Redis connection failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                    print(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    print(f"Error: Failed to connect to Redis after {self.max_retries} attempts.")
                    print(f"Please ensure Redis is running on {self.config['HOST']}:{self.config['PORT']}")
                    raise
            except Exception as e:
                print(f"Unexpected error connecting to Redis: {e}")
                raise
        
        raise redis.exceptions.ConnectionError("Failed to connect to Redis")

    def _ensure_connection(self):
        """Ensure Redis connection is alive, reconnect if needed."""
        try:
            self.db.ping()
        except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError):
            print("Redis connection lost. Reconnecting...")
            self.db = self._connect_with_retry()

    def init_keys(self):
        """Initialize essential keys if they don't exist."""
        self._ensure_connection()
        
        if not self.db.exists('STATE:CURRENT'):
            self.db.set('STATE:CURRENT', 'INITIALIZING')
        if not self.db.exists('KB:VULNERABILITIES'):
            self.db.set('KB:VULNERABILITIES', json.dumps([]))
        if not self.db.exists('ERROR:LAST_MESSAGE'):
            self.db.set('ERROR:LAST_MESSAGE', "")
        
        # Clear action queue from previous runs (optional - comment out to preserve queue)
        self.db.delete('QUEUE:ACTIONS')
        print("Redis keys initialized.")

    # --- State Management ---
    def get_state(self) -> str:
        self._ensure_connection()
        return self.db.get('STATE:CURRENT') or 'UNKNOWN'

    def set_state(self, state: str):
        self._ensure_connection()
        self.db.set('STATE:CURRENT', state)

    # --- Action Queue (FIFO) ---
    def push_action(self, action_json: Dict[str, Any]):
        """Push a new action command to the queue."""
        self._ensure_connection()
        try:
            self.db.rpush('QUEUE:ACTIONS', json.dumps(action_json))
        except Exception as e:
            print(f"Error pushing action to queue: {e}")
            raise

    def pop_action(self) -> Optional[Dict[str, Any]]:
        """Pop the next action command from the queue (blocking pop for efficiency)."""
        self._ensure_connection()
        try:
            # BLPOP waits for 1 second if the list is empty
            item = self.db.blpop('QUEUE:ACTIONS', timeout=1)
            if item:
                # item is (key, value)
                return json.loads(item[1])
            return None
        except Exception as e:
            print(f"Error popping action from queue: {e}")
            return None

    def get_queue_size(self, key: str = 'QUEUE:ACTIONS') -> int:
        """Get the size of a queue."""
        self._ensure_connection()
        try:
            return self.db.llen(key)
        except:
            return 0

    # --- Logging and Observation ---
    def log_observation(self, agent_name: str, message: str):
        """Log an observation message with timestamp."""
        self._ensure_connection()
        try:
            from config import MAX_LOG_ENTRIES
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] [{agent_name}] {message}"
            self.db.lpush('LOG:OBSERVATION', log_entry)
            # Keep log size manageable
            self.db.ltrim('LOG:OBSERVATION', 0, MAX_LOG_ENTRIES - 1)
        except Exception as e:
            print(f"Error logging observation: {e}")

    def get_latest_observations(self, count: int = 10) -> List[str]:
        """Retrieve the latest observations."""
        self._ensure_connection()
        try:
            return self.db.lrange('LOG:OBSERVATION', 0, count - 1)
        except:
            return []

    # --- Knowledge Base (Vulnerabilities) ---
    def add_vulnerability(self, vuln_data: Dict[str, Any]):
        """Add a new confirmed vulnerability to the knowledge base."""
        self._ensure_connection()
        try:
            vulns_str = self.db.get('KB:VULNERABILITIES')
            if vulns_str:
                vulns = json.loads(vulns_str)
            else:
                vulns = []
            
            vulns.append(vuln_data)
            self.db.set('KB:VULNERABILITIES', json.dumps(vulns))
        except Exception as e:
            print(f"Error adding vulnerability: {e}")

    def get_vulnerabilities(self) -> List[Dict[str, Any]]:
        """Retrieve all confirmed vulnerabilities."""
        self._ensure_connection()
        try:
            vulns_str = self.db.get('KB:VULNERABILITIES')
            if vulns_str:
                return json.loads(vulns_str)
            return []
        except:
            return []

    # --- Error Handling ---
    def set_error(self, agent_name: str, error_message: str):
        """Set the last error message and change state to ERROR_HANDLING."""
        self._ensure_connection()
        try:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            full_error = f"[{timestamp}] [{agent_name}] {error_message}"
            self.db.set('ERROR:LAST_MESSAGE', full_error)
            self.set_state('ERROR_HANDLING')
        except Exception as e:
            print(f"Error setting error state: {e}")

    def clear_error(self):
        """Clear the last error message."""
        self._ensure_connection()
        try:
            self.db.set('ERROR:LAST_MESSAGE', "")
        except Exception as e:
            print(f"Error clearing error: {e}")

    def get_last_error(self) -> str:
        """Get the last error message."""
        self._ensure_connection()
        try:
            return self.db.get('ERROR:LAST_MESSAGE') or ""
        except:
            return ""
