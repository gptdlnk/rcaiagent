from agents.base_agent import BaseAgent
from tools.network_sniffer import NetworkSniffer
import time

class ObserverAgent(BaseAgent):
    def run(self):
        self.log("Observer Agent started. Monitoring network traffic.")
        while self.is_running():
            try:
                # 1. Sniff network traffic (using a filter focused on the game server IP/Port)
                # NOTE: The filter needs to be configured in config.py or dynamically set
                # For simplicity, we use a placeholder filter
                packets = NetworkSniffer.sniff_packets(count=10, filter_str="tcp port 7777") # Example port
                
                if packets:
                    # 2. Summarize the raw data using the 5 Hihg model
                    # This is where the speed of 5 Hihg is crucial
                    prompt = (
                        "Analyze the following raw network packet summaries. "
                        "Identify any unusual patterns, unencrypted data, or large data transfers. "
                        "Summarize the findings concisely for the AI Planner."
                        f"Raw Packets: {packets}"
                    )
                    
                    summary = self.call_ai_model(prompt)
                    
                    # 3. Log the summarized observation
                    self.redis_manager.log_observation(self.name, f"NETWORK_SUMMARY: {summary}")
                    
                else:
                    self.log("No packets captured in this cycle.")
                    
                time.sleep(5) # Wait before the next sniffing cycle

            except Exception as e:
                self.set_error(f"Unhandled exception in Observer: {e}")
                time.sleep(10)
