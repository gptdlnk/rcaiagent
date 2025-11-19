from agents.base_agent import BaseAgent
from tools.network_sniffer import NetworkSniffer
import time
import random
import json

class FuzzerAgent(BaseAgent):
    def run(self):
        self.log("Fuzzer Agent started. Waiting for protocol knowledge.")
        while self.is_running():
            try:
                # 1. Check if we have enough knowledge to start fuzzing
                latest_knowledge = self.redis_manager.get_latest_observations(count=5)
                
                # Simple check: look for RE_KNOWLEDGE
                if not any("RE_KNOWLEDGE" in obs for obs in latest_knowledge):
                    self.log("Waiting for Reverse Engineer to provide protocol knowledge.")
                    time.sleep(10)
                    continue
                
                # 2. Use 5 Hihg (Fuzzer) to generate a creative payload based on knowledge
                # The Fuzzer is high-temperature, meaning it will generate random/creative data
                fuzz_prompt = (
                    "Based on the latest RE_KNOWLEDGE, generate a highly abnormal but structurally plausible "
                    "network packet payload (in hexadecimal string format) designed to cause a Logic Flaw "
                    "or a Buffer Overflow in the game server. Focus on exceeding expected integer limits or "
                    "corrupting known data fields. Output ONLY the hexadecimal string and the target IP/Port in a JSON format."
                    f"Latest Knowledge: {latest_knowledge}"
                )
                
                fuzz_payload_str = self.call_ai_model(fuzz_prompt)
                
                # 3. Parse and execute the fuzzing action (using NetworkSniffer.send_packet)
                try:
                    fuzz_action = json.loads(fuzz_payload_str)
                    payload_hex = fuzz_action.get('payload_hex')
                    target_ip = fuzz_action.get('target_ip')
                    target_port = fuzz_action.get('target_port')
                    
                    if payload_hex and target_ip and target_port:
                        success = NetworkSniffer.send_packet(target_ip, target_port, payload_hex, protocol="TCP")
                        self.redis_manager.log_observation(self.name, f"FUZZ_RESULT: Sent {len(payload_hex)//2} bytes. Success={success}. Waiting for server response.")
                    else:
                        self.log("Fuzz payload incomplete or invalid.")
                        
                except json.JSONDecodeError:
                    self.log(f"Error decoding fuzz payload JSON: {fuzz_payload_str}. Retrying fuzz.")
                    
                time.sleep(random.randint(1, 5)) # Fuzzing should be fast and continuous

            except Exception as e:
                self.set_error(f"Unhandled exception in Fuzzer: {e}")
                time.sleep(10)
