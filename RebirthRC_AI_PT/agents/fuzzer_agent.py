from agents.base_agent import BaseAgent
from tools.network_sniffer import NetworkSniffer
from config import PAYLOAD_CONFIG, AGENT_POLL_INTERVAL
import time
import random
import json
import os

class FuzzerAgent(BaseAgent):
    def __init__(self, redis_manager, config):
        super().__init__(redis_manager, config)
        self.file_payloads = self._load_payloads_from_file()

    def _load_payloads_from_file(self):
        """Load fuzzing payloads from the configured file."""
        payload_file = PAYLOAD_CONFIG.get("FUZZ_FILE")
        if not payload_file or not os.path.exists(payload_file):
            self.log(f"Fuzzing payload file not found at {payload_file}. Will use MCP only.")
            return []
        
        try:
            with open(payload_file, 'r', encoding='utf-8') as f:
                payloads = [line.strip() for line in f if line.strip()]
            self.log(f"Loaded {len(payloads)} payloads from {payload_file}")
            return payloads
        except Exception as e:
            self.log(f"Error loading payloads from {payload_file}: {e}")
            return []
    def run(self):
        self.log("Fuzzer Agent started. Waiting for protocol knowledge.")
        while self.is_running():
            try:
                latest_knowledge = self.redis_manager.get_latest_observations(count=5)

                if not any("RE_KNOWLEDGE" in obs for obs in latest_knowledge):
                    self.log("Waiting for Reverse Engineer to provide protocol knowledge.")
                    time.sleep(AGENT_POLL_INTERVAL)
                    continue

                # Decide whether to use a file-based payload or an MCP-generated one
                use_file_payload = self.file_payloads and random.random() < 0.7  # 70% chance to use file payloads

                target_ip = self.redis_manager.db.get('GAME:SERVER_IP') or '127.0.0.1'
                target_port = int(self.redis_manager.db.get('GAME:SERVER_PORT') or 7777)

                if use_file_payload:
                    # Use a payload from the pre-loaded file
                    payload_hex = random.choice(self.file_payloads)
                    self.log(f"Using payload from file: {payload_hex[:40]}...")
                    
                    if payload_hex and target_ip and target_port:
                        success = NetworkSniffer.send_packet(target_ip, target_port, payload_hex, protocol="TCP")
                        self.redis_manager.log_observation(
                            self.name,
                            f"FUZZ_RESULT (File): Sent {len(payload_hex)//2} bytes. Success={success}."
                        )
                else:
                    # Use MCP to generate a dynamic, context-aware payload
                    self.log("Using MCP to generate a dynamic payload...")
                    request = {
                        "request_type": "fuzzer_payload",
                        "latest_knowledge": latest_knowledge,
                        "target_ip": target_ip,
                        "target_port": target_port,
                        "protocol": "TCP"
                    }

                    fuzz_payload_str = self.call_ai_model(request)

                    try:
                        fuzz_action = json.loads(fuzz_payload_str)
                        payload_hex = fuzz_action.get('payload_hex')
                        
                        # MCP might return a different target, respect that
                        mcp_target_ip = fuzz_action.get('target_ip', target_ip)
                        mcp_target_port = fuzz_action.get('target_port', target_port)

                        if payload_hex and mcp_target_ip and mcp_target_port:
                            success = NetworkSniffer.send_packet(mcp_target_ip, mcp_target_port, payload_hex, protocol="TCP")
                            self.redis_manager.log_observation(
                                self.name,
                                f"FUZZ_RESULT (MCP): Sent {len(payload_hex)//2} bytes. Success={success}."
                            )
                        else:
                            self.log("MCP-generated fuzz payload was incomplete.")

                    except json.JSONDecodeError:
                        self.log(f"Error decoding MCP fuzz payload JSON: {fuzz_payload_str}")

                # Use a variable, shorter sleep time for more unpredictable fuzzing patterns
                time.sleep(random.uniform(0.5, 2.0))

            except Exception as e:
                self.set_error(f"Unhandled exception in Fuzzer: {e}")
                time.sleep(10)
