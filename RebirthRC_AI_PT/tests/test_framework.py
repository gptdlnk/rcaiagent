"""
Testing Framework สำหรับ Multi-Agent System

รองรับ:
- Unit Tests
- Integration Tests
- End-to-End Tests
- Performance Tests
"""

import pytest
import time
import json
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any


class TestConfig:
    """Configuration สำหรับ testing"""
    
    REDIS_CONFIG = {
        'HOST': 'localhost',
        'PORT': 6379,
        'DB': 15  # ใช้ DB แยกสำหรับ testing
    }
    
    TEST_AGENT_CONFIG = {
        'NAME': 'TestAgent',
        'MODEL': 'test-model',
        'TEMPERATURE': 0.0,
        'SYSTEM_PROMPT': 'Test prompt',
        'USE_MCP': True
    }


class MockRedisManager:
    """Mock Redis Manager for testing with extended functionality."""

    def __init__(self):
        self.data = {}
        self.lists = {}
        self.observations = []
        self.actions = []
        self.errors = []
        self.vulnerabilities = []
        # Compatibility for PayloadManager
        self.db = self

    def get(self, key):
        return self.data.get(key)

    def set(self, key, value):
        self.data[key] = value

    def delete(self, key):
        if key in self.lists:
            del self.lists[key]
        if key in self.data:
            del self.data[key]

    def rpush(self, key, *values):
        if key not in self.lists:
            self.lists[key] = []
        self.lists[key].extend(values)

    def lpop(self, key):
        if key in self.lists and self.lists[key]:
            return self.lists[key].pop(0)
        return None

    def lindex(self, key, index):
        if key in self.lists and -len(self.lists[key]) <= index < len(self.lists[key]):
            return self.lists[key][index]
        return None

    def llen(self, key):
        return len(self.lists.get(key, []))

    def ltrim(self, key, start, end):
        if key in self.lists:
            self.lists[key] = self.lists[key][start:end+1]

    def type(self, key):
        if key in self.lists:
            return b'list'
        if key in self.data:
            return b'string'
        return b'none'

    def time(self):
        return (int(time.time()), 0)

    def get_state(self):
        return self.data.get('SYS:STATUS', 'IDLE')

    def set_state(self, state):
        self.data['SYS:STATUS'] = state

    def log_observation(self, agent_name, message):
        self.observations.append({
            'agent': agent_name,
            'message': message,
            'timestamp': time.time()
        })

    def get_latest_observations(self, count=10):
        return self.observations[-count:]

    def push_action(self, action):
        self.actions.append(action)

    def pop_action(self):
        return self.actions.pop(0) if self.actions else None

    def get_queue_size(self):
        return len(self.actions)

    def set_error(self, agent_name, error_message):
        self.errors.append({
            'agent': agent_name,
            'message': error_message,
            'timestamp': time.time()
        })

    def get_last_error(self):
        return self.errors[-1] if self.errors else None

    def clear_error(self):
        self.errors.clear()

    def add_vulnerability(self, vuln):
        self.vulnerabilities.append(vuln)

    def get_vulnerabilities(self):
        return self.vulnerabilities


class AgentTestCase:
    """Base class สำหรับ Agent tests"""
    
    def setup_method(self):
        """Setup ก่อนแต่ละ test"""
        self.redis_manager = MockRedisManager()
        self.agent_config = TestConfig.TEST_AGENT_CONFIG.copy()
    
    def teardown_method(self):
        """Cleanup หลังแต่ละ test"""
        pass
    
    def assert_observation_logged(self, agent_name: str, message_contains: str):
        """ตรวจสอบว่ามี observation ที่ต้องการ"""
        observations = self.redis_manager.get_latest_observations(100)
        for obs in observations:
            if obs['agent'] == agent_name and message_contains in obs['message']:
                return True
        raise AssertionError(f"Observation not found: {agent_name} - {message_contains}")
    
    def assert_action_pushed(self, action_type: str):
        """ตรวจสอบว่ามี action ที่ต้องการ"""
        for action in self.redis_manager.actions:
            if action.get('action_type') == action_type:
                return True
        raise AssertionError(f"Action not found: {action_type}")


# ===== Unit Tests =====

class TestPayloadManager(AgentTestCase):
    """Unit tests สำหรับ PayloadManager"""
    
    def test_load_payloads(self):
        """ทดสอบการโหลด payloads"""
        from tools.payload_manager import PayloadManager
        
        pm = PayloadManager(self.redis_manager)
        
        # Generate sample payloads
        pm.generate_sample_payloads('sqli', 10)
        
        # Load payloads
        count = pm.load_payloads('sqli')
        assert count == 10
    
    def test_get_payload(self):
        """ทดสอบการดึง payload"""
        from tools.payload_manager import PayloadManager
        
        pm = PayloadManager(self.redis_manager)
        pm.generate_sample_payloads('sqli', 10)
        pm.load_payloads('sqli')
        
        # Get payload
        payload = pm.get_payload('sqli')
        assert payload is not None
        assert isinstance(payload, str)
    
    def test_validate_payload(self):
        """ทดสอบการ validate payload"""
        from tools.payload_manager import PayloadManager
        
        pm = PayloadManager(self.redis_manager)
        
        # Valid SQLi payload
        assert pm.validate_payload("' OR 1=1--", 'sqli') == True
        
        # Invalid SQLi payload
        assert pm.validate_payload("hello world", 'sqli') == False


class TestSteganographyTool(AgentTestCase):
    """Unit tests สำหรับ SteganographyTool"""
    
    def test_embed_and_extract_lsb(self):
        """ทดสอบการฝังและดึง payload ด้วย LSB"""
        from tools.steganography_tool import SteganographyTool
        from PIL import Image
        import os
        
        # สร้างภาพทดสอบ
        test_img = Image.new('RGB', (100, 100), color='red')
        test_img_path = 'test_image.png'
        test_img.save(test_img_path)
        
        # ทดสอบ embed
        payload = "Secret message"
        stego_path = SteganographyTool.embed_payload_lsb(
            test_img_path, payload, 'test_stego.png'
        )
        
        assert os.path.exists(stego_path)
        
        # ทดสอบ extract
        extracted = SteganographyTool.extract_payload_lsb(stego_path)
        assert extracted == payload
        
        # Cleanup
        os.remove(test_img_path)
        os.remove(stego_path)
    
    def test_create_reverse_shell_payload(self):
        """ทดสอบการสร้าง reverse shell payload"""
        from tools.steganography_tool import SteganographyTool
        
        payload = SteganographyTool.create_reverse_shell_payload(
            '192.168.1.100', 4444, obfuscate=True
        )
        
        assert payload is not None
        assert 'powershell' in payload.lower()


class TestOptimizedRedisManager(AgentTestCase):
    """Unit tests สำหรับ OptimizedRedisManager"""
    
    @pytest.mark.skipif(True, reason="Requires Redis server")
    def test_connection(self):
        """ทดสอบการเชื่อมต่อ Redis"""
        from data_hub.optimized_redis_manager import OptimizedRedisManager
        
        manager = OptimizedRedisManager(TestConfig.REDIS_CONFIG)
        
        # Test connection
        health = manager.get_health_status()
        assert health['connected'] == True
    
    @pytest.mark.skipif(True, reason="Requires Redis server")
    def test_caching(self):
        """ทดสอบ caching layer"""
        from data_hub.optimized_redis_manager import OptimizedRedisManager
        
        manager = OptimizedRedisManager(TestConfig.REDIS_CONFIG)
        
        # Set cached value
        manager.set_cached('test_key', 'test_value')
        
        # Get cached value
        value = manager.get_cached('test_key')
        assert value == 'test_value'


# ===== Integration Tests =====

class TestAgentCommunication(AgentTestCase):
    """Integration tests สำหรับการสื่อสารระหว่าง Agents"""
    
    def test_planner_to_executor_flow(self):
        """ทดสอบ flow จาก Planner ไป Executor"""
        # Planner สร้าง action
        action = {
            'action_type': 'SCAN_NETWORK',
            'target_agent': 'Executor',
            'parameters': {
                'target': '192.168.1.0/24'
            }
        }
        
        self.redis_manager.push_action(action)
        
        # Executor ดึง action
        retrieved_action = self.redis_manager.pop_action()
        
        assert retrieved_action == action
        assert retrieved_action['action_type'] == 'SCAN_NETWORK'
    
    def test_observer_to_planner_flow(self):
        """ทดสอบ flow จาก Observer ไป Planner"""
        # Observer log observation
        self.redis_manager.log_observation(
            'Observer',
            'Detected anomaly in network traffic'
        )
        
        # Planner ดึง observations
        observations = self.redis_manager.get_latest_observations(10)
        
        assert len(observations) > 0
        assert observations[0]['agent'] == 'Observer'


# ===== End-to-End Tests =====

class TestFullAttackWorkflow(AgentTestCase):
    """E2E tests สำหรับ workflow การโจมตีแบบเต็มรูปแบบ"""
    
    def test_reconnaissance_to_exploit(self):
        """ทดสอบ workflow จาก Reconnaissance ไป Exploit"""
        # 1. Initial state
        self.redis_manager.set_state('DEEP_RECONNAISSANCE')
        
        # 2. Observer logs network traffic
        self.redis_manager.log_observation(
            'Observer',
            'Captured 100 packets from target'
        )
        
        # 3. Planner creates action
        action = {
            'action_type': 'ANALYZE_PROTOCOL',
            'target_agent': 'ReverseEngineer',
            'parameters': {}
        }
        self.redis_manager.push_action(action)
        
        # 4. Reverse Engineer analyzes
        self.redis_manager.log_observation(
            'ReverseEngineer',
            'Protocol structure identified'
        )
        
        # 5. Planner creates exploit action
        exploit_action = {
            'action_type': 'EXECUTE_EXPLOIT',
            'target_agent': 'Executor',
            'parameters': {
                'exploit_type': 'SQLi',
                'target': 'login_form'
            }
        }
        self.redis_manager.push_action(exploit_action)
        
        # 6. Verify workflow
        assert self.redis_manager.get_state() == 'DEEP_RECONNAISSANCE'
        assert len(self.redis_manager.observations) >= 2
        assert self.redis_manager.get_queue_size() >= 1


# ===== Performance Tests =====

class TestPerformance:
    """Performance tests"""
    
    def test_payload_loading_performance(self):
        """ทดสอบประสิทธิภาพการโหลด payloads"""
        from tools.payload_manager import PayloadManager
        
        redis_manager = MockRedisManager()
        pm = PayloadManager(redis_manager)
        
        # Generate large payload set
        start_time = time.time()
        pm.generate_sample_payloads('sqli', 1000)
        pm.load_payloads('sqli')
        duration = time.time() - start_time
        
        # Should complete in reasonable time
        assert duration < 5.0  # 5 seconds
        
        print(f"Loaded 1000 payloads in {duration:.2f} seconds")
    
    def test_redis_batch_operations(self):
        """ทดสอบประสิทธิภาพ batch operations"""
        redis_manager = MockRedisManager()
        
        # Batch log observations
        observations = [
            {'agent': 'TestAgent', 'message': f'Observation {i}'}
            for i in range(100)
        ]
        
        start_time = time.time()
        for obs in observations:
            redis_manager.log_observation(obs['agent'], obs['message'])
        duration = time.time() - start_time
        
        assert duration < 1.0  # Should be fast
        assert len(redis_manager.observations) == 100
        
        print(f"Logged 100 observations in {duration:.2f} seconds")


# ===== Test Utilities =====

def run_all_tests():
    """รัน tests ทั้งหมด"""
    print("\n" + "="*60)
    print("Running All Tests")
    print("="*60 + "\n")
    
    # Run pytest
    pytest.main([__file__, '-v', '--tb=short'])


if __name__ == "__main__":
    run_all_tests()
