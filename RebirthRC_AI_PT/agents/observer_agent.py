from agents.base_agent import BaseAgent
from tools.network_sniffer import NetworkSniffer
from tools.observability import StructuredLogger, MetricsCollector, PerformanceMonitor
from config import GAME_CONFIG, AGENT_POLL_INTERVAL
import time
import json
from collections import defaultdict


class ObserverAgent(BaseAgent):
    def __init__(self, redis_manager, config):
        super().__init__(redis_manager, config)

        # Initialize observability
        self.logger = StructuredLogger(self.name, redis_manager=redis_manager)
        self.metrics = MetricsCollector(redis_manager)
        self.monitor = PerformanceMonitor(self.metrics)
        
        # Intelligence: Pattern recognition and anomaly detection
        self.observed_patterns = []
        self.packet_baseline = {
            'avg_size': 0,
            'avg_frequency': 0,
            'common_ports': set(),
            'common_protocols': set()
        }
        self.anomaly_threshold = 0.7
        self.traffic_history = []
        
        self.logger.info("ObserverAgent initialized with intelligent monitoring")
    
    def run(self):
        self.logger.info("Observer Agent started with pattern recognition and anomaly detection")
        while self.is_running():
            try:
                # Capture packets with intelligent filtering
                with self.monitor.measure('packet_capture'):
                    packets = NetworkSniffer.sniff_packets(count=10, filter_str=None)

                if packets:
                    # Intelligent analysis of packets
                    packet_analysis = self._analyze_packets(packets)
                    anomalies = self._detect_anomalies(packet_analysis)
                    patterns = self._identify_patterns(packet_analysis)
                    
                    # Update metrics
                    self.metrics.record_metric('packets_captured', len(packets))
                    self.metrics.record_metric('anomalies_detected', len(anomalies))
                    self.metrics.record_metric('patterns_identified', len(patterns))
                    
                    # Create intelligent summary request
                    request = {
                        "request_type": "observer_summary",
                        "packets": packets,
                        "state": self.redis_manager.get_state(),
                        "packet_analysis": packet_analysis,
                        "anomalies": anomalies,
                        "patterns": patterns
                    }

                    summary = self.call_ai_model(request)

                    if summary and not str(summary).startswith("ERROR"):
                        # Log with structured format
                        self.logger.log_action(
                            'NETWORK_OBSERVATION',
                            target='network_traffic',
                            result='analyzed',
                            packets_count=len(packets),
                            anomalies_count=len(anomalies),
                            patterns_count=len(patterns)
                        )
                        
                        self.redis_manager.log_observation(
                            self.name, 
                            f"NETWORK_SUMMARY: {summary}"
                        )
                        
                        # Handle critical anomalies
                        if anomalies:
                            self._handle_anomalies(anomalies)
                        
                        # Record interesting patterns
                        if patterns:
                            self._record_patterns(patterns)
                        
                        self.logger.info(
                            f"Captured and analyzed {len(packets)} packets",
                            details={
                                'anomalies': len(anomalies),
                                'patterns': len(patterns),
                                'analysis': packet_analysis
                            }
                        )
                    else:
                        self.logger.error(f"MCP summary returned error: {summary}")

                else:
                    self.logger.info("No packets captured in this cycle")

                time.sleep(AGENT_POLL_INTERVAL)

            except Exception as e:
                self.set_error(f"Unhandled exception in Observer: {e}")
                self.logger.error(f"Observer exception: {e}")
                time.sleep(10)
    
    def _analyze_packets(self, packets: list) -> dict:
        """
        Intelligently analyze captured packets
        """
        analysis = {
            'total_packets': len(packets),
            'protocols': defaultdict(int),
            'ports': defaultdict(int),
            'avg_size': 0,
            'suspicious_indicators': [],
            'traffic_type': 'normal'
        }
        
        total_size = 0
        
        for packet in packets:
            # Extract packet info (assuming packet is a dict or object)
            if isinstance(packet, dict):
                protocol = packet.get('protocol', 'UNKNOWN')
                port = packet.get('port', 0)
                size = packet.get('size', 0)
                
                analysis['protocols'][protocol] += 1
                analysis['ports'][port] += 1
                total_size += size
                
                # Check for suspicious indicators
                if port in [4444, 5555, 6666, 7777, 8888, 9999]:  # Common backdoor ports
                    analysis['suspicious_indicators'].append(f"Suspicious port: {port}")
                
                if size > 10000:  # Large packet
                    analysis['suspicious_indicators'].append(f"Large packet: {size} bytes")
        
        if len(packets) > 0:
            analysis['avg_size'] = total_size / len(packets)
        
        # Determine traffic type
        if len(analysis['suspicious_indicators']) > 0:
            analysis['traffic_type'] = 'suspicious'
        elif len(set(analysis['protocols'].keys())) > 5:
            analysis['traffic_type'] = 'diverse'
        
        return analysis
    
    def _detect_anomalies(self, packet_analysis: dict) -> list:
        """
        Detect anomalies in network traffic using baseline comparison
        """
        anomalies = []
        
        # Update baseline if we have enough history
        if len(self.traffic_history) > 10:
            self._update_baseline()
        
        # Check for anomalies
        if self.packet_baseline['avg_size'] > 0:
            size_deviation = abs(packet_analysis['avg_size'] - self.packet_baseline['avg_size']) / self.packet_baseline['avg_size']
            
            if size_deviation > self.anomaly_threshold:
                anomalies.append({
                    'type': 'size_anomaly',
                    'severity': 'medium',
                    'details': f"Packet size deviation: {size_deviation:.2%}",
                    'current': packet_analysis['avg_size'],
                    'baseline': self.packet_baseline['avg_size']
                })
        
        # Check for suspicious indicators
        if packet_analysis['suspicious_indicators']:
            anomalies.append({
                'type': 'suspicious_activity',
                'severity': 'high',
                'details': ', '.join(packet_analysis['suspicious_indicators'][:5]),
                'count': len(packet_analysis['suspicious_indicators'])
            })
        
        # Check for unusual protocols
        current_protocols = set(packet_analysis['protocols'].keys())
        if self.packet_baseline['common_protocols']:
            new_protocols = current_protocols - self.packet_baseline['common_protocols']
            if new_protocols:
                anomalies.append({
                    'type': 'new_protocol',
                    'severity': 'low',
                    'details': f"New protocols detected: {', '.join(new_protocols)}",
                    'protocols': list(new_protocols)
                })
        
        # Record traffic history
        self.traffic_history.append(packet_analysis)
        if len(self.traffic_history) > 100:
            self.traffic_history = self.traffic_history[-100:]
        
        return anomalies
    
    def _identify_patterns(self, packet_analysis: dict) -> list:
        """
        Identify patterns in network traffic
        """
        patterns = []
        
        # Pattern: Repeated port access
        for port, count in packet_analysis['ports'].items():
            if count > 5:
                patterns.append({
                    'type': 'repeated_port_access',
                    'port': port,
                    'count': count,
                    'significance': 'high' if port in [80, 443, 22, 3389] else 'medium'
                })
        
        # Pattern: Protocol dominance
        if packet_analysis['protocols']:
            dominant_protocol = max(packet_analysis['protocols'].items(), key=lambda x: x[1])
            if dominant_protocol[1] > packet_analysis['total_packets'] * 0.7:
                patterns.append({
                    'type': 'protocol_dominance',
                    'protocol': dominant_protocol[0],
                    'percentage': dominant_protocol[1] / packet_analysis['total_packets'],
                    'significance': 'medium'
                })
        
        return patterns
    
    def _update_baseline(self):
        """Update baseline metrics from traffic history"""
        if not self.traffic_history:
            return
        
        # Calculate average size
        avg_sizes = [t['avg_size'] for t in self.traffic_history if t['avg_size'] > 0]
        if avg_sizes:
            self.packet_baseline['avg_size'] = sum(avg_sizes) / len(avg_sizes)
        
        # Collect common protocols
        all_protocols = set()
        for t in self.traffic_history:
            all_protocols.update(t['protocols'].keys())
        self.packet_baseline['common_protocols'] = all_protocols
        
        # Collect common ports
        all_ports = set()
        for t in self.traffic_history:
            all_ports.update(t['ports'].keys())
        self.packet_baseline['common_ports'] = all_ports
    
    def _handle_anomalies(self, anomalies: list):
        """Handle detected anomalies intelligently"""
        for anomaly in anomalies:
            severity = anomaly.get('severity', 'low')
            
            if severity == 'high':
                # Log critical anomaly
                self.logger.log_vulnerability(
                    vuln_type='NETWORK_ANOMALY',
                    severity='high',
                    description=anomaly['details'],
                    proof=json.dumps(anomaly)
                )
                
                # Alert the system
                self.redis_manager.log_observation(
                    self.name,
                    f"⚠️ CRITICAL ANOMALY DETECTED: {anomaly['details']}"
                )
            elif severity == 'medium':
                self.logger.warning(f"Anomaly detected: {anomaly['details']}")
            else:
                self.logger.info(f"Minor anomaly: {anomaly['details']}")
    
    def _record_patterns(self, patterns: list):
        """Record identified patterns for future reference"""
        for pattern in patterns:
            if pattern.get('significance') == 'high':
                self.observed_patterns.append({
                    'pattern': pattern,
                    'timestamp': time.time(),
                    'frequency': 1
                })
        
        # Keep only last 50 patterns
        if len(self.observed_patterns) > 50:
            self.observed_patterns = self.observed_patterns[-50:]
