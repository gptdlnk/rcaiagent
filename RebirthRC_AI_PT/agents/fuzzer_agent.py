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
                latest_knowledge = self.redis_manager.get_latest_observations(count=5)

                if not any("RE_KNOWLEDGE" in obs for obs in latest_knowledge):
                    self.log("Waiting for Reverse Engineer to provide protocol knowledge.")
                    time.sleep(10)
                    continue

                request = {
                    "request_type": "fuzzer_payload",
                    "latest_knowledge": latest_knowledge,
                    "target_ip": self.redis_manager.db.get('GAME:SERVER_IP') or '127.0.0.1',
                    "target_port": int(self.redis_manager.db.get('GAME:SERVER_PORT') or 7777),
                    "protocol": "TCP"
                }

                fuzz_payload_str = self.call_ai_model(request)

                try:
                    fuzz_action = json.loads(fuzz_payload_str)
                    payload_hex = fuzz_action.get('payload_hex')
                    target_ip = fuzz_action.get('target_ip')
                    target_port = fuzz_action.get('target_port')

                    if payload_hex and target_ip and target_port:
                        success = NetworkSniffer.send_packet(target_ip, target_port, payload_hex, protocol="TCP")
                        self.redis_manager.log_observation(
                            self.name,
                            f"FUZZ_RESULT: Sent {len(payload_hex)//2} bytes. Success={success}. Waiting for server response."
                        )
                    else:
                        self.log("Fuzz payload incomplete or invalid.")

                except json.JSONDecodeError:
                    self.log(f"Error decoding fuzz payload JSON: {fuzz_payload_str}. Retrying fuzz.")

                time.sleep(random.randint(1, 5))

            except Exception as e:
                self.set_error(f"Unhandled exception in Fuzzer: {e}")
                time.sleep(10)
