from agents.base_agent import BaseAgent
from tools.terminal_wrapper import TerminalWrapper
from tools.game_client_control import GameClientControl
from tools.network_sniffer import NetworkSniffer
import json
import time

class ExecutorAgent(BaseAgent):
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
