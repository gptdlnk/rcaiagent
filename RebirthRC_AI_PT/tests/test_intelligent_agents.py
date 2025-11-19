"""
Comprehensive tests for Intelligent Agents
Tests the intelligence, learning, and decision-making capabilities
"""

import pytest
import sys
import os
import time
import json
from unittest.mock import Mock, MagicMock, patch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.executor_agent import ExecutorAgent
from agents.planner_agent import PlannerAgent
from agents.observer_agent import ObserverAgent


class MockRedisManager:
    """Mock Redis Manager for testing"""
    def __init__(self):
        self.data = {}
        self.observations = []
        self.vulnerabilities = []
        self.actions = []
        self.state = 'DEEP_RECONNAISSANCE'
        self.last_error = None
        
        # Mock db attribute
        self.db = Mock()
        self.db.get = Mock(return_value=None)
        self.db.set = Mock()
        self.db.delete = Mock()
        self.db.rpush = Mock()
        self.db.lpop = Mock(return_value=None)
        self.db.llen = Mock(return_value=0)
        self.db.time = Mock(return_value=(int(time.time()), 0))
    
    def get_state(self):
        return self.state
    
    def set_state(self, state):
        self.state = state
    
    def log_observation(self, agent_name, message):
        self.observations.append({'agent': agent_name, 'message': message, 'time': time.time()})
    
    def get_latest_observations(self, count=10):
        return self.observations[-count:]
    
    def get_vulnerabilities(self):
        return self.vulnerabilities
    
    def add_vulnerability(self, vuln):
        self.vulnerabilities.append(vuln)
    
    def push_action(self, action):
        self.actions.append(action)
    
    def pop_action(self):
        if self.actions:
            return self.actions.pop(0)
        return None
    
    def get_last_error(self):
        return self.last_error
    
    def set_error(self, agent_name, error_message):
        self.last_error = {'agent': agent_name, 'message': error_message, 'time': time.time()}
    
    def clear_error(self):
        self.last_error = None


@pytest.fixture
def mock_redis():
    """Fixture for mock Redis manager"""
    return MockRedisManager()


@pytest.fixture
def executor_config():
    """Configuration for ExecutorAgent"""
    return {
        'NAME': 'TestExecutor',
        'MODEL': 'gpt-4',
        'TEMPERATURE': 0.7,
        'SYSTEM_PROMPT': 'You are a test executor',
        'USE_MCP': True
    }


@pytest.fixture
def planner_config():
    """Configuration for PlannerAgent"""
    return {
        'NAME': 'TestPlanner',
        'MODEL': 'gpt-4',
        'TEMPERATURE': 0.7,
        'SYSTEM_PROMPT': 'You are a test planner',
        'USE_MCP': True
    }


@pytest.fixture
def observer_config():
    """Configuration for ObserverAgent"""
    return {
        'NAME': 'TestObserver',
        'MODEL': 'gpt-4',
        'TEMPERATURE': 0.7,
        'SYSTEM_PROMPT': 'You are a test observer',
        'USE_MCP': True
    }


class TestExecutorAgentIntelligence:
    """Test ExecutorAgent's intelligent capabilities"""
    
    def test_initialization(self, mock_redis, executor_config):
        """Test that ExecutorAgent initializes with intelligent components"""
        agent = ExecutorAgent(mock_redis, executor_config)
        
        assert agent.payload_manager is not None
        assert agent.stego_tool is not None
        assert agent.logger is not None
        assert agent.metrics is not None
        assert agent.monitor is not None
        assert isinstance(agent.attack_history, list)
        assert isinstance(agent.success_patterns, dict)
    
    def test_intelligent_payload_selection(self, mock_redis, executor_config):
        """Test intelligent payload selection based on history"""
        agent = ExecutorAgent(mock_redis, executor_config)
        
        # Simulate attack history
        agent.attack_history = [
            {'type': 'sqli', 'target': '192.168.1.1', 'success': True},
            {'type': 'sqli', 'target': '192.168.1.1', 'success': True},
            {'type': 'sqli', 'target': '192.168.1.1', 'success': False},
        ]
        
        # Test payload selection
        payload = agent._select_intelligent_payload('sqli', '192.168.1.1', 7777)
        
        assert payload is not None
        assert isinstance(payload, str)
    
    def test_encoding_strategy_determination(self, mock_redis, executor_config):
        """Test encoding strategy selection"""
        agent = ExecutorAgent(mock_redis, executor_config)
        
        # Test different attack types
        sqli_strategy = agent._determine_encoding_strategy('sqli', '192.168.1.1')
        assert sqli_strategy in ['url', 'none', 'hex']
        
        xss_strategy = agent._determine_encoding_strategy('xss', '192.168.1.1')
        assert xss_strategy in ['html', 'url', 'none']
        
        rce_strategy = agent._determine_encoding_strategy('rce', '192.168.1.1')
        assert rce_strategy in ['base64', 'url', 'none']
    
    def test_attack_result_recording(self, mock_redis, executor_config):
        """Test that attack results are recorded for learning"""
        agent = ExecutorAgent(mock_redis, executor_config)
        
        # Record successful attack
        agent._record_attack_result('sqli', '192.168.1.1', 7777, True, 'aabbccdd')
        
        assert len(agent.attack_history) == 1
        assert agent.attack_history[0]['success'] is True
        assert '192.168.1.1:7777' in agent.success_patterns
    
    def test_execution_context_analysis(self, mock_redis, executor_config):
        """Test execution context analysis"""
        agent = ExecutorAgent(mock_redis, executor_config)
        
        # Simulate mixed results
        agent.attack_history = [
            {'type': 'sqli', 'target': '192.168.1.1', 'success': True},
            {'type': 'sqli', 'target': '192.168.1.1', 'success': False},
            {'type': 'sqli', 'target': '192.168.1.1', 'success': False},
        ]
        
        action = {
            'action_type': 'SEND_PACKET',
            'target_agent': 'NETWORK',
            'payload': {}
        }
        
        context = agent._analyze_execution_context(action)
        
        assert 'recent_success_rate' in context
        assert 'recommendation' in context
        assert context['recent_success_rate'] < 0.5


class TestPlannerAgentIntelligence:
    """Test PlannerAgent's intelligent capabilities"""
    
    def test_initialization(self, mock_redis, planner_config):
        """Test that PlannerAgent initializes with strategic intelligence"""
        agent = PlannerAgent(mock_redis, planner_config)
        
        assert agent.logger is not None
        assert agent.metrics is not None
        assert isinstance(agent.planning_history, list)
        assert isinstance(agent.strategy_effectiveness, dict)
        assert agent.current_strategy == 'reconnaissance'
    
    def test_situation_analysis(self, mock_redis, planner_config):
        """Test situation analysis capabilities"""
        agent = PlannerAgent(mock_redis, planner_config)
        
        # Create test data
        observations = [
            {'message': 'SCAN SUCCESS'},
            {'message': 'ATTACK FAILED'},
            {'message': 'VERIFIED VULNERABILITY'},
        ]
        
        vulnerabilities = [
            {'type': 'SQLi', 'verified': True},
            {'type': 'XSS', 'verified': False},
        ]
        
        analysis = agent._analyze_situation(observations, vulnerabilities, None)
        
        assert 'total_observations' in analysis
        assert 'total_vulnerabilities' in analysis
        assert 'threat_level' in analysis
        assert 'opportunity_score' in analysis
        assert 'recommended_actions' in analysis
    
    def test_strategy_adaptation(self, mock_redis, planner_config):
        """Test strategy adaptation based on situation"""
        agent = PlannerAgent(mock_redis, planner_config)
        
        # Test high threat scenario
        high_threat_analysis = {
            'threat_level': 'high',
            'opportunity_score': 0.2,
            'recent_success_rate': 0.1
        }
        
        agent._adapt_strategy(high_threat_analysis)
        assert agent.current_strategy == 'stealth_reconnaissance'
        
        # Test high opportunity scenario
        high_opportunity_analysis = {
            'threat_level': 'low',
            'opportunity_score': 0.8,
            'recent_success_rate': 0.7,
            'verified_vulnerabilities': 3
        }
        
        agent._adapt_strategy(high_opportunity_analysis)
        assert agent.current_strategy in ['aggressive_exploitation', 'targeted_exploitation']
    
    def test_planning_history_tracking(self, mock_redis, planner_config):
        """Test that planning decisions are tracked"""
        agent = PlannerAgent(mock_redis, planner_config)
        
        analysis = {
            'threat_level': 'medium',
            'opportunity_score': 0.5,
            'recent_success_rate': 0.5
        }
        
        agent._adapt_strategy(analysis)
        
        assert len(agent.planning_history) > 0
        assert 'strategy' in agent.planning_history[0]
        assert 'timestamp' in agent.planning_history[0]


class TestObserverAgentIntelligence:
    """Test ObserverAgent's intelligent capabilities"""
    
    def test_initialization(self, mock_redis, observer_config):
        """Test that ObserverAgent initializes with pattern recognition"""
        agent = ObserverAgent(mock_redis, observer_config)
        
        assert agent.logger is not None
        assert agent.metrics is not None
        assert isinstance(agent.observed_patterns, list)
        assert isinstance(agent.packet_baseline, dict)
        assert agent.anomaly_threshold == 0.7
    
    def test_packet_analysis(self, mock_redis, observer_config):
        """Test packet analysis capabilities"""
        agent = ObserverAgent(mock_redis, observer_config)
        
        # Create test packets
        packets = [
            {'protocol': 'TCP', 'port': 80, 'size': 1024},
            {'protocol': 'TCP', 'port': 443, 'size': 2048},
            {'protocol': 'UDP', 'port': 53, 'size': 512},
            {'protocol': 'TCP', 'port': 4444, 'size': 15000},  # Suspicious
        ]
        
        analysis = agent._analyze_packets(packets)
        
        assert analysis['total_packets'] == 4
        assert 'protocols' in analysis
        assert 'ports' in analysis
        assert 'avg_size' in analysis
        assert len(analysis['suspicious_indicators']) > 0  # Should detect port 4444 and large packet
    
    def test_anomaly_detection(self, mock_redis, observer_config):
        """Test anomaly detection"""
        agent = ObserverAgent(mock_redis, observer_config)
        
        # Set baseline
        agent.packet_baseline['avg_size'] = 1000
        agent.packet_baseline['common_protocols'] = {'TCP', 'UDP'}
        
        # Test with anomalous traffic
        analysis = {
            'total_packets': 10,
            'protocols': {'TCP': 5, 'ICMP': 5},  # New protocol
            'ports': {80: 10},
            'avg_size': 5000,  # Much larger than baseline
            'suspicious_indicators': ['Suspicious port: 4444'],
            'traffic_type': 'suspicious'
        }
        
        anomalies = agent._detect_anomalies(analysis)
        
        assert len(anomalies) > 0
        assert any(a['type'] == 'size_anomaly' for a in anomalies)
        assert any(a['type'] == 'suspicious_activity' for a in anomalies)
    
    def test_pattern_identification(self, mock_redis, observer_config):
        """Test pattern identification"""
        agent = ObserverAgent(mock_redis, observer_config)
        
        analysis = {
            'total_packets': 20,
            'protocols': {'TCP': 18, 'UDP': 2},
            'ports': {80: 15, 443: 5},  # Repeated port access
            'avg_size': 1024,
            'suspicious_indicators': [],
            'traffic_type': 'normal'
        }
        
        patterns = agent._identify_patterns(analysis)
        
        assert len(patterns) > 0
        assert any(p['type'] == 'repeated_port_access' for p in patterns)
        assert any(p['type'] == 'protocol_dominance' for p in patterns)


class TestAgentIntegration:
    """Test integration between intelligent agents"""
    
    def test_executor_planner_communication(self, mock_redis, executor_config, planner_config):
        """Test communication between Executor and Planner"""
        executor = ExecutorAgent(mock_redis, executor_config)
        planner = PlannerAgent(mock_redis, planner_config)
        
        # Planner creates action
        action = {
            'target_agent': 'NETWORK',
            'action_type': 'SEND_PACKET',
            'payload': {
                'ip': '192.168.1.1',
                'port': 7777,
                'attack_type': 'sqli'
            }
        }
        
        mock_redis.push_action(action)
        
        # Executor should be able to retrieve it
        retrieved_action = mock_redis.pop_action()
        
        assert retrieved_action == action
    
    def test_learning_feedback_loop(self, mock_redis, executor_config, planner_config):
        """Test that agents learn from each other's results"""
        executor = ExecutorAgent(mock_redis, executor_config)
        planner = PlannerAgent(mock_redis, planner_config)
        
        # Executor records successful attack
        executor._record_attack_result('sqli', '192.168.1.1', 7777, True, 'payload123')
        
        # Planner should be able to see the observation
        observations = mock_redis.get_latest_observations()
        
        # The recording should have created some observable state
        assert len(executor.attack_history) > 0
        assert '192.168.1.1:7777' in executor.success_patterns


# Performance tests
class TestAgentPerformance:
    """Test performance and scalability"""
    
    def test_attack_history_memory_limit(self, mock_redis, executor_config):
        """Test that attack history doesn't grow unbounded"""
        agent = ExecutorAgent(mock_redis, executor_config)
        
        # Add 2000 attacks
        for i in range(2000):
            agent._record_attack_result('sqli', f'192.168.1.{i%255}', 7777, True, 'payload')
        
        # Should be limited to 1000
        assert len(agent.attack_history) == 1000
    
    def test_planning_history_memory_limit(self, mock_redis, planner_config):
        """Test that planning history doesn't grow unbounded"""
        agent = PlannerAgent(mock_redis, planner_config)
        
        # Add 200 planning decisions
        for i in range(200):
            analysis = {
                'threat_level': 'low',
                'opportunity_score': 0.5,
                'recent_success_rate': 0.5
            }
            agent._adapt_strategy(analysis)
        
        # Should be limited to 100
        assert len(agent.planning_history) == 100


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
