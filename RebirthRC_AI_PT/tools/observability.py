"""
Observability Tools - Structured Logging และ Metrics Collection

Features:
- Structured JSON Logging
- Metrics Collection และ Aggregation
- Performance Monitoring
- Alert Management
"""

import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import threading


class StructuredLogger:
    """Structured Logger สำหรับ logging แบบมีโครงสร้าง"""
    
    LOG_LEVELS = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
        'critical': logging.CRITICAL
    }
    
    def __init__(self, agent_name: str, log_dir: str = 'logs', 
                 redis_manager=None):
        """
        Initialize Structured Logger
        
        Args:
            agent_name: ชื่อของ agent
            log_dir: ไดเรกทอรีสำหรับเก็บ log files
            redis_manager: RedisManager instance (optional)
        """
        self.agent_name = agent_name
        self.log_dir = Path(log_dir)
        self.redis = redis_manager
        
        # สร้างไดเรกทอรี
        self.log_dir.mkdir(exist_ok=True)
        
        # Setup Python logger
        self.logger = logging.getLogger(agent_name)
        self.logger.setLevel(logging.DEBUG)
        
        # File handler (JSON format)
        log_file = self.log_dir / f"{agent_name}.jsonl"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler (readable format)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Stats
        self.stats = {
            'total_logs': 0,
            'by_level': {level: 0 for level in self.LOG_LEVELS.keys()}
        }
    
    def _create_log_entry(self, level: str, message: str, 
                         details: Dict = None, tags: List[str] = None) -> Dict:
        """
        สร้าง log entry แบบมีโครงสร้าง
        
        Args:
            level: Log level
            message: ข้อความหลัก
            details: รายละเอียดเพิ่มเติม
            tags: Tags สำหรับจัดหมวดหมู่
        
        Returns:
            Log entry dict
        """
        entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'agent': self.agent_name,
            'level': level.upper(),
            'message': message,
            'details': details or {},
            'tags': tags or []
        }
        
        return entry
    
    def log(self, level: str, message: str, details: Dict = None, 
            tags: List[str] = None):
        """
        บันทึก log
        
        Args:
            level: Log level (debug, info, warning, error, critical)
            message: ข้อความ
            details: รายละเอียดเพิ่มเติม
            tags: Tags
        """
        if level not in self.LOG_LEVELS:
            level = 'info'
        
        # สร้าง log entry
        entry = self._create_log_entry(level, message, details, tags)
        
        # บันทึกใน Python logger (JSON format)
        log_json = json.dumps(entry)
        log_level = self.LOG_LEVELS[level]
        self.logger.log(log_level, log_json)
        
        # บันทึกใน Redis ถ้ามี
        if self.redis:
            try:
                self.redis.log_observation(self.agent_name, message)
            except:
                pass
        
        # Update stats
        self.stats['total_logs'] += 1
        self.stats['by_level'][level] += 1
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.log('debug', message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self.log('info', message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.log('warning', message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        self.log('error', message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self.log('critical', message, **kwargs)
    
    def log_action(self, action_type: str, target: str = None, 
                   result: str = None, duration: float = None, **kwargs):
        """
        บันทึก action ที่ทำ
        
        Args:
            action_type: ประเภทของ action
            target: เป้าหมายของ action
            result: ผลลัพธ์
            duration: เวลาที่ใช้ (seconds)
        """
        details = {
            'action_type': action_type,
            'target': target,
            'result': result,
            'duration': duration
        }
        details.update(kwargs)
        
        self.info(f"Action: {action_type}", details=details, tags=['action'])
    
    def log_attack(self, attack_type: str, target: str, payload: str = None,
                   success: bool = False, response: str = None, **kwargs):
        """
        บันทึกการโจมตี
        
        Args:
            attack_type: ประเภทการโจมตี
            target: เป้าหมาย
            payload: Payload ที่ใช้
            success: สำเร็จหรือไม่
            response: Response จาก target
        """
        details = {
            'attack_type': attack_type,
            'target': target,
            'payload': payload[:100] if payload else None,  # เก็บแค่ 100 ตัวอักษร
            'success': success,
            'response': response[:200] if response else None
        }
        details.update(kwargs)
        
        level = 'info' if success else 'warning'
        self.log(level, f"Attack: {attack_type} -> {target}", 
                details=details, tags=['attack', attack_type])
    
    def log_vulnerability(self, vuln_type: str, severity: str, 
                         description: str, proof: str = None, **kwargs):
        """
        บันทึกช่องโหว่ที่พบ
        
        Args:
            vuln_type: ประเภทช่องโหว่
            severity: ความรุนแรง (low, medium, high, critical)
            description: คำอธิบาย
            proof: หลักฐาน/PoC
        """
        details = {
            'vuln_type': vuln_type,
            'severity': severity,
            'description': description,
            'proof': proof
        }
        details.update(kwargs)
        
        self.critical(f"Vulnerability Found: {vuln_type}", 
                     details=details, tags=['vulnerability', severity])
        
        # บันทึกใน Redis
        if self.redis:
            try:
                self.redis.add_vulnerability(details)
            except:
                pass
    
    def get_stats(self) -> Dict:
        """ดึงสถิติ logging"""
        return self.stats.copy()


class MetricsCollector:
    """Metrics Collector สำหรับเก็บและวิเคราะห์ metrics"""
    
    def __init__(self, redis_manager=None):
        """
        Initialize Metrics Collector
        
        Args:
            redis_manager: RedisManager instance
        """
        self.redis = redis_manager
        self.metrics = {}
        self.lock = threading.Lock()
    
    def record_metric(self, metric_name: str, value: float, 
                     tags: Dict[str, str] = None):
        """
        บันทึก metric
        
        Args:
            metric_name: ชื่อ metric
            value: ค่า
            tags: Tags สำหรับจัดหมวดหมู่
        """
        timestamp = time.time()
        
        metric_entry = {
            'name': metric_name,
            'value': value,
            'timestamp': timestamp,
            'tags': tags or {}
        }
        
        # เก็บใน memory
        with self.lock:
            if metric_name not in self.metrics:
                self.metrics[metric_name] = []
            self.metrics[metric_name].append(metric_entry)
            
            # เก็บแค่ 1000 รายการล่าสุด
            if len(self.metrics[metric_name]) > 1000:
                self.metrics[metric_name] = self.metrics[metric_name][-1000:]
        
        # เก็บใน Redis
        if self.redis:
            try:
                redis_key = f"METRICS:{metric_name}"
                self.redis.db.zadd(redis_key, {
                    json.dumps(metric_entry): timestamp
                })
                
                # เก็บแค่ 1 ชั่วโมงล่าสุด
                cutoff = timestamp - 3600
                self.redis.db.zremrangebyscore(redis_key, '-inf', cutoff)
            except:
                pass
    
    def record_counter(self, counter_name: str, increment: int = 1, 
                      tags: Dict[str, str] = None):
        """
        บันทึก counter metric
        
        Args:
            counter_name: ชื่อ counter
            increment: จำนวนที่เพิ่ม
            tags: Tags
        """
        if self.redis:
            try:
                redis_key = f"COUNTER:{counter_name}"
                self.redis.db.incrby(redis_key, increment)
            except:
                pass
        
        self.record_metric(counter_name, increment, tags)
    
    def record_timer(self, timer_name: str, duration: float, 
                    tags: Dict[str, str] = None):
        """
        บันทึก timer metric
        
        Args:
            timer_name: ชื่อ timer
            duration: ระยะเวลา (seconds)
            tags: Tags
        """
        self.record_metric(f"{timer_name}.duration", duration, tags)
    
    def get_metric_stats(self, metric_name: str, 
                        time_range: int = 3600) -> Dict:
        """
        ดึงสถิติของ metric
        
        Args:
            metric_name: ชื่อ metric
            time_range: ช่วงเวลาที่ต้องการ (seconds)
        
        Returns:
            Dictionary ของสถิติ
        """
        with self.lock:
            if metric_name not in self.metrics:
                return {}
            
            # Filter by time range
            cutoff = time.time() - time_range
            values = [
                m['value'] for m in self.metrics[metric_name]
                if m['timestamp'] >= cutoff
            ]
            
            if not values:
                return {}
            
            return {
                'count': len(values),
                'sum': sum(values),
                'avg': sum(values) / len(values),
                'min': min(values),
                'max': max(values),
                'latest': values[-1]
            }
    
    def get_all_metrics(self) -> Dict[str, Dict]:
        """ดึงสถิติของ metrics ทั้งหมด"""
        stats = {}
        with self.lock:
            for metric_name in self.metrics.keys():
                stats[metric_name] = self.get_metric_stats(metric_name)
        return stats


class PerformanceMonitor:
    """Performance Monitor สำหรับติดตามประสิทธิภาพ"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        """
        Initialize Performance Monitor
        
        Args:
            metrics_collector: MetricsCollector instance
        """
        self.metrics = metrics_collector
        self.active_timers = {}
    
    def start_timer(self, name: str) -> str:
        """
        เริ่มจับเวลา
        
        Args:
            name: ชื่อของ timer
        
        Returns:
            Timer ID
        """
        timer_id = f"{name}_{time.time()}"
        self.active_timers[timer_id] = time.time()
        return timer_id
    
    def stop_timer(self, timer_id: str, tags: Dict[str, str] = None) -> float:
        """
        หยุดจับเวลา
        
        Args:
            timer_id: Timer ID จาก start_timer
            tags: Tags
        
        Returns:
            ระยะเวลา (seconds)
        """
        if timer_id not in self.active_timers:
            return 0
        
        start_time = self.active_timers.pop(timer_id)
        duration = time.time() - start_time
        
        # Extract name from timer_id
        name = '_'.join(timer_id.split('_')[:-1])
        
        # Record metric
        self.metrics.record_timer(name, duration, tags)
        
        return duration
    
    def measure(self, name: str, tags: Dict[str, str] = None):
        """
        Context manager สำหรับจับเวลา
        
        Usage:
            with monitor.measure('operation_name'):
                # do something
        """
        class TimerContext:
            def __init__(self, monitor, name, tags):
                self.monitor = monitor
                self.name = name
                self.tags = tags
                self.timer_id = None
            
            def __enter__(self):
                self.timer_id = self.monitor.start_timer(self.name)
                return self
            
            def __exit__(self, *args):
                self.monitor.stop_timer(self.timer_id, self.tags)
        
        return TimerContext(self, name, tags)


# Example usage
if __name__ == "__main__":
    print("\n=== Testing Observability Tools ===\n")
    
    # Test Structured Logger
    logger = StructuredLogger('TestAgent')
    
    logger.info("System started")
    logger.debug("Debug information", details={'key': 'value'})
    logger.warning("Warning message", tags=['test'])
    
    logger.log_action('SCAN', target='192.168.1.1', result='success', duration=1.5)
    logger.log_attack('SQLi', target='login_form', payload="' OR 1=1--", success=True)
    logger.log_vulnerability('SQL Injection', 'high', 'Login bypass vulnerability')
    
    print(f"Logger stats: {logger.get_stats()}")
    
    # Test Metrics Collector
    metrics = MetricsCollector()
    
    metrics.record_metric('cpu_usage', 45.5, tags={'host': 'server1'})
    metrics.record_counter('requests_total', 10)
    metrics.record_timer('request_duration', 0.123)
    
    time.sleep(0.1)
    
    metrics.record_metric('cpu_usage', 50.2, tags={'host': 'server1'})
    metrics.record_counter('requests_total', 5)
    
    print(f"\nMetric stats: {metrics.get_metric_stats('cpu_usage')}")
    print(f"All metrics: {metrics.get_all_metrics()}")
    
    # Test Performance Monitor
    monitor = PerformanceMonitor(metrics)
    
    with monitor.measure('test_operation', tags={'type': 'test'}):
        time.sleep(0.2)
    
    print(f"\nTimer stats: {metrics.get_metric_stats('test_operation.duration')}")
    
    print("\n=== Test Complete ===")
