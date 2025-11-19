from agents.base_agent import BaseAgent
from tools.terminal_wrapper import TerminalWrapper
from tools.game_client_control import GameClientControl
from tools.network_sniffer import NetworkSniffer
from tools.verification import get_verification
from tools.stego_builder import create_stego_package
from config import PAYLOAD_CONFIG
import json
import time
import os
import random

class ExecutorAgent(BaseAgent):
    def __init__(self, redis_manager, config):
        super().__init__(redis_manager, config)
        self.payload_lists = self._load_all_payloads()

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
        """Executes a shell command (e.g., Nmap, custom script)."""
        command = payload.get('command')
        if command:
            self.log(f"Running terminal command: {command}")
            code, stdout, stderr = TerminalWrapper.run_command(command)
            
            # Report results back to Redis for the Planner to analyze
            result_message = f"TERMINAL_RESULT: Command '{command}' finished with code {code}. STDOUT: {stdout[:500]} | STDERR: {stderr[:500]}"
            self.redis_manager.log_observation(self.name, result_message)
        else:
            self.log("Terminal command payload missing 'command'.")

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
        """Sends a custom network packet (Exploit/Fuzzing)."""
        if action_type == 'SEND_PACKET':
            target_ip = payload.get('ip')
            target_port = payload.get('port')
            payload_hex = payload.get('payload_hex')
            protocol = payload.get('protocol', 'TCP')
            
            if target_ip and target_port and payload_hex:
                success = NetworkSniffer.send_packet(target_ip, target_port, payload_hex, protocol)
                self.redis_manager.log_observation(self.name, f"NETWORK_SEND_RESULT: Success={success}. Sent {len(payload_hex)//2} bytes to {target_ip}:{target_port}")
            else:
                self.log("Network send command payload incomplete.")
        else:
            self.log(f"Unknown network action type: {action_type}")
    
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
