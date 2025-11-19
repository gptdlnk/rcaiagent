from agents.base_agent import BaseAgent
from tools.network_sniffer import NetworkSniffer
from tools.game_client_control import GameClientControl
import time

class ObserverAgent(BaseAgent):
    def run(self):
        self.log("Observer Agent started. Monitoring network traffic.")
        while self.is_running():
            try:
                # 1. Sniff network traffic (using a filter focused on the game server IP/Port)
                # NOTE: The filter needs to be configured in config.py or dynamically set
                # 1. Sniff network traffic (using a filter focused on the game server IP/Port)
                packets = NetworkSniffer.sniff_packets(count=10, filter_str="tcp port 7777") # Example port
                
                # 2. Capture screenshot for Visual Analysis
                screenshot_b64 = GameClientControl.perform_action('get_screenshot_base64', {})
                
                # 3. Combine raw data for 5 Hihg analysis
                raw_data = {
                    "packets": packets,
                    "screenshot_b64": screenshot_b64
                }
                
                if packets or screenshot_b64:
                    # 4. Summarize the raw data using the 5 Hihg model (Multimodal)
                    # This is where the speed of 5 Hihg is crucial
                    prompt = (
                        "Analyze the following raw network packet summaries AND the attached screenshot (Base64). "
                        "Identify any unusual patterns, unencrypted data, or large data transfers. "
                        "Specifically, check the screenshot for visual confirmation of the current game state (e.g., character position, in-game currency, health bar). "
                        "Summarize the findings concisely for the AI Planner, including visual confirmation."
                        f"Raw Data: {raw_data}"
                    )
                    
                    summary = self.call_ai_model(prompt)
                    
                    # 3. Log the summarized observation
                    self.redis_manager.log_observation(self.name, f"NETWORK_SUMMARY: {summary}")
                    
                else:
                    self.log("No new data captured in this cycle.")
                    
                time.sleep(5) # Wait before the next sniffing cycle

            except Exception as e:
                self.set_error(f"Unhandled exception in Observer: {e}")
                time.sleep(10)
