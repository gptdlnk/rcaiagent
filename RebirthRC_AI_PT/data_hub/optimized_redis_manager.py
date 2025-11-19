"""
Optimized Redis Manager - ปรับปรุงประสิทธิภาพการใช้งาน Redis

Features:
- Connection Pooling
- Pipeline Operations
- Pub/Sub Support
- Caching Layer
- Retry Mechanism
- Health Monitoring
"""

import json
import time
import threading
from typing import List, Dict, Any, Optional, Callable
from redis import Redis, ConnectionPool
from redis.exceptions import RedisError, ConnectionError as RedisConnectionError
import logging


class OptimizedRedisManager:
    """Redis Manager ที่ปรับปรุงประสิทธิภาพ"""
    
    def __init__(self, config: Dict[str, Any], pool_size: int = 50):
        """
        Initialize Optimized Redis Manager
        
        Args:
            config: Redis configuration dict
            pool_size: ขนาดของ connection pool
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # สร้าง Connection Pool
        self.pool = ConnectionPool(
            host=config.get('HOST', 'localhost'),
            port=config.get('PORT', 6379),
            db=config.get('DB', 0),
            max_connections=pool_size,
            decode_responses=True,
            socket_keepalive=True,
            socket_connect_timeout=5,
            retry_on_timeout=True
        )
        
        # สร้าง Redis client
        self.db = Redis(connection_pool=self.pool)
        
        # Local cache
        self.cache = {}
        self.cache_ttl = {}
        self.cache_lock = threading.Lock()
        
        # Pub/Sub
        self.pubsub = self.db.pubsub()
        self.subscribers = {}
        
        # Health monitoring
        self.health_status = {
            'connected': False,
            'last_check': 0,
            'errors': 0,
            'operations': 0
        }
        
        # ทดสอบการเชื่อมต่อ
        self._test_connection()
    
    def _test_connection(self):
        """ทดสอบการเชื่อมต่อกับ Redis"""
        try:
            self.db.ping()
            self.health_status['connected'] = True
            self.health_status['last_check'] = time.time()
            self.logger.info("Redis connection established")
        except RedisError as e:
            self.health_status['connected'] = False
            self.health_status['errors'] += 1
            self.logger.error(f"Redis connection failed: {e}")
            raise
    
    def retry_operation(self, func: Callable, *args, max_retries: int = 3, **kwargs) -> Any:
        """
        ลองทำ operation ซ้ำถ้าเกิด error
        
        Args:
            func: Function ที่จะรัน
            max_retries: จำนวนครั้งที่ลองใหม่
            *args, **kwargs: Arguments สำหรับ function
        
        Returns:
            ผลลัพธ์จาก function
        """
        last_error = None
        for attempt in range(max_retries):
            try:
                result = func(*args, **kwargs)
                self.health_status['operations'] += 1
                return result
            except RedisConnectionError as e:
                last_error = e
                self.health_status['errors'] += 1
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt)  # Exponential backoff
                    self.logger.warning(f"Redis operation failed, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    self._test_connection()  # ลองเชื่อมต่อใหม่
            except Exception as e:
                self.health_status['errors'] += 1
                raise
        
        raise last_error
    
    # ===== State Management =====
    
    def get_state(self) -> str:
        """ดึงสถานะปัจจุบันของระบบ"""
        return self.retry_operation(self.db.get, 'SYS:STATUS') or 'IDLE'
    
    def set_state(self, state: str):
        """ตั้งสถานะของระบบ"""
        self.retry_operation(self.db.set, 'SYS:STATUS', state)
        self.logger.info(f"System state changed to: {state}")
    
    # ===== Caching Layer =====
    
    def get_cached(self, key: str, ttl: int = 60) -> Optional[Any]:
        """
        ดึงข้อมูลจาก cache ก่อน ถ้าไม่มีค่อยดึงจาก Redis
        
        Args:
            key: Redis key
            ttl: Time to live ของ cache (seconds)
        
        Returns:
            ค่าที่เก็บไว้ หรือ None
        """
        with self.cache_lock:
            # ตรวจสอบ cache
            if key in self.cache:
                if time.time() - self.cache_ttl.get(key, 0) < ttl:
                    return self.cache[key]
            
            # ดึงจาก Redis
            value = self.retry_operation(self.db.get, key)
            
            # เก็บใน cache
            if value is not None:
                self.cache[key] = value
                self.cache_ttl[key] = time.time()
            
            return value
    
    def set_cached(self, key: str, value: Any, redis_ttl: int = None):
        """
        ตั้งค่าทั้งใน cache และ Redis
        
        Args:
            key: Redis key
            value: ค่าที่จะเก็บ
            redis_ttl: TTL ใน Redis (seconds)
        """
        with self.cache_lock:
            # อัปเดต cache
            self.cache[key] = value
            self.cache_ttl[key] = time.time()
        
        # เก็บใน Redis
        if redis_ttl:
            self.retry_operation(self.db.setex, key, redis_ttl, value)
        else:
            self.retry_operation(self.db.set, key, value)
    
    def invalidate_cache(self, key: str = None):
        """
        ลบ cache
        
        Args:
            key: Redis key ที่จะลบ (ถ้าไม่ระบุจะลบทั้งหมด)
        """
        with self.cache_lock:
            if key:
                self.cache.pop(key, None)
                self.cache_ttl.pop(key, None)
            else:
                self.cache.clear()
                self.cache_ttl.clear()
    
    # ===== Pipeline Operations =====
    
    def batch_log_observations(self, observations: List[Dict]):
        """
        บันทึก observations หลายรายการพร้อมกัน
        
        Args:
            observations: List ของ observation dicts
        """
        pipe = self.db.pipeline()
        for obs in observations:
            obs_json = json.dumps(obs)
            pipe.lpush('LOG:OBSERVATIONS', obs_json)
        pipe.ltrim('LOG:OBSERVATIONS', 0, 999)  # เก็บแค่ 1000 รายการ
        self.retry_operation(pipe.execute)
        self.logger.debug(f"Logged {len(observations)} observations")
    
    def batch_push_actions(self, actions: List[Dict]):
        """
        เพิ่ม actions หลายรายการพร้อมกัน
        
        Args:
            actions: List ของ action dicts
        """
        pipe = self.db.pipeline()
        for action in actions:
            action_json = json.dumps(action)
            pipe.rpush('QUEUE:ACTIONS', action_json)
        self.retry_operation(pipe.execute)
        self.logger.debug(f"Pushed {len(actions)} actions")
    
    def batch_get_keys(self, keys: List[str]) -> Dict[str, Any]:
        """
        ดึงค่าหลาย keys พร้อมกัน
        
        Args:
            keys: List ของ Redis keys
        
        Returns:
            Dictionary ของ key-value pairs
        """
        pipe = self.db.pipeline()
        for key in keys:
            pipe.get(key)
        
        values = self.retry_operation(pipe.execute)
        return dict(zip(keys, values))
    
    # ===== Pub/Sub Support =====
    
    def publish(self, channel: str, message: Any):
        """
        Publish message ไปยัง channel
        
        Args:
            channel: ชื่อ channel
            message: ข้อความ (จะถูกแปลงเป็น JSON)
        """
        if not isinstance(message, str):
            message = json.dumps(message)
        
        self.retry_operation(self.db.publish, channel, message)
        self.logger.debug(f"Published to {channel}: {message[:100]}")
    
    def subscribe(self, channel: str, callback: Callable):
        """
        Subscribe to channel
        
        Args:
            channel: ชื่อ channel
            callback: Function ที่จะเรียกเมื่อได้รับ message
        """
        if channel not in self.subscribers:
            self.pubsub.subscribe(channel)
            self.subscribers[channel] = []
        
        self.subscribers[channel].append(callback)
        self.logger.info(f"Subscribed to channel: {channel}")
    
    def start_listening(self):
        """เริ่ม listen to subscribed channels (blocking)"""
        def listen_thread():
            for message in self.pubsub.listen():
                if message['type'] == 'message':
                    channel = message['channel']
                    data = message['data']
                    
                    # เรียก callbacks
                    if channel in self.subscribers:
                        for callback in self.subscribers[channel]:
                            try:
                                callback(data)
                            except Exception as e:
                                self.logger.error(f"Callback error: {e}")
        
        thread = threading.Thread(target=listen_thread, daemon=True)
        thread.start()
        self.logger.info("Started listening to pub/sub channels")
    
    # ===== Observation & Action Management =====
    
    def log_observation(self, agent_name: str, message: str):
        """บันทึก observation"""
        obs = {
            'agent': agent_name,
            'message': message,
            'timestamp': time.time()
        }
        self.retry_operation(self.db.lpush, 'LOG:OBSERVATIONS', json.dumps(obs))
        self.retry_operation(self.db.ltrim, 'LOG:OBSERVATIONS', 0, 999)
        
        # Publish to real-time channel
        self.publish('OBSERVATIONS', obs)
    
    def get_latest_observations(self, count: int = 10) -> List[Dict]:
        """ดึง observations ล่าสุด"""
        obs_list = self.retry_operation(self.db.lrange, 'LOG:OBSERVATIONS', 0, count - 1)
        return [json.loads(obs) for obs in obs_list]
    
    def push_action(self, action: Dict):
        """เพิ่ม action เข้า queue"""
        self.retry_operation(self.db.rpush, 'QUEUE:ACTIONS', json.dumps(action))
        
        # Publish to real-time channel
        self.publish('ACTIONS', action)
    
    def pop_action(self) -> Optional[Dict]:
        """ดึง action จาก queue"""
        action_json = self.retry_operation(self.db.lpop, 'QUEUE:ACTIONS')
        return json.loads(action_json) if action_json else None
    
    def get_queue_size(self) -> int:
        """ดึงจำนวน actions ใน queue"""
        return self.retry_operation(self.db.llen, 'QUEUE:ACTIONS')
    
    # ===== Error Management =====
    
    def set_error(self, agent_name: str, error_message: str):
        """บันทึก error"""
        error_data = {
            'agent': agent_name,
            'message': error_message,
            'timestamp': time.time()
        }
        self.retry_operation(self.db.set, 'ERROR:LAST_MESSAGE', json.dumps(error_data))
        
        # Publish to alert channel
        self.publish('ALERTS', error_data)
    
    def get_last_error(self) -> Optional[Dict]:
        """ดึง error ล่าสุด"""
        error_json = self.retry_operation(self.db.get, 'ERROR:LAST_MESSAGE')
        return json.loads(error_json) if error_json else None
    
    def clear_error(self):
        """ลบ error"""
        self.retry_operation(self.db.delete, 'ERROR:LAST_MESSAGE')
    
    # ===== Vulnerability Management =====
    
    def add_vulnerability(self, vuln: Dict):
        """เพิ่มช่องโหว่ที่พบ"""
        self.retry_operation(self.db.rpush, 'KB:VULNERABILITIES', json.dumps(vuln))
        
        # Publish to alerts
        self.publish('VULNERABILITIES', vuln)
    
    def get_vulnerabilities(self) -> List[Dict]:
        """ดึงรายการช่องโหว่ทั้งหมด"""
        vulns = self.retry_operation(self.db.lrange, 'KB:VULNERABILITIES', 0, -1)
        return [json.loads(v) for v in vulns]
    
    # ===== Health Monitoring =====
    
    def get_health_status(self) -> Dict:
        """ดึงสถานะสุขภาพของ Redis connection"""
        status = self.health_status.copy()
        
        # ทดสอบการเชื่อมต่อ
        try:
            self.db.ping()
            status['connected'] = True
            status['last_check'] = time.time()
        except:
            status['connected'] = False
        
        # เพิ่มข้อมูล pool
        status['pool_size'] = self.pool.max_connections
        status['pool_available'] = self.pool.max_connections - len(self.pool._available_connections)
        
        return status
    
    def get_stats(self) -> Dict:
        """ดึงสถิติการใช้งาน Redis"""
        info = self.retry_operation(self.db.info, 'stats')
        
        return {
            'total_connections': info.get('total_connections_received', 0),
            'total_commands': info.get('total_commands_processed', 0),
            'ops_per_sec': info.get('instantaneous_ops_per_sec', 0),
            'used_memory': info.get('used_memory_human', 'N/A'),
            'connected_clients': info.get('connected_clients', 0)
        }
    
    # ===== Cleanup =====
    
    def cleanup(self):
        """ทำความสะอาดและปิด connections"""
        try:
            self.pubsub.close()
            self.pool.disconnect()
            self.logger.info("Redis connections closed")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


# Example usage
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Configuration
    config = {
        'HOST': 'localhost',
        'PORT': 6379,
        'DB': 0
    }
    
    # Initialize
    redis_manager = OptimizedRedisManager(config, pool_size=20)
    
    # Test operations
    print("\n=== Testing Optimized Redis Manager ===\n")
    
    # Test state
    redis_manager.set_state('TESTING')
    print(f"State: {redis_manager.get_state()}")
    
    # Test caching
    redis_manager.set_cached('test_key', 'test_value', redis_ttl=60)
    print(f"Cached value: {redis_manager.get_cached('test_key')}")
    
    # Test batch operations
    observations = [
        {'agent': 'TestAgent', 'message': f'Test observation {i}'}
        for i in range(5)
    ]
    redis_manager.batch_log_observations(observations)
    print(f"Latest observations: {len(redis_manager.get_latest_observations())}")
    
    # Test pub/sub
    def on_message(data):
        print(f"Received: {data}")
    
    redis_manager.subscribe('TEST_CHANNEL', on_message)
    redis_manager.start_listening()
    redis_manager.publish('TEST_CHANNEL', {'test': 'message'})
    
    time.sleep(1)
    
    # Test health
    health = redis_manager.get_health_status()
    print(f"\nHealth Status: {health}")
    
    stats = redis_manager.get_stats()
    print(f"Stats: {stats}")
    
    # Cleanup
    redis_manager.cleanup()
    
    print("\n=== Test Complete ===")
