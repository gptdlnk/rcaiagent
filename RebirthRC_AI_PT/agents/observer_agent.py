from agents.base_agent import BaseAgent
from tools.network_sniffer import NetworkSniffer
from config import GAME_CONFIG, AGENT_POLL_INTERVAL
import time

class ObserverAgent(BaseAgent):
    def run(self):
        self.log("Observer Agent started. Monitoring network traffic.")
        while self.is_running():
            try:
                # 1. Sniff network traffic (using filter from config or default)
                # NetworkSniffer will use GAME_CONFIG if filter_str is None
                packets = NetworkSniffer.sniff_packets(count=10, filter_str=None)
                
                if packets:
                    # 2. Summarize the raw data using the AI model
                    # This is where the speed of the model is crucial
                    prompt = (
                        "Analyze the following raw network packet summaries. "
                        "Identify any unusual patterns, unencrypted data, large data transfers, "
                        "or potential security issues. Summarize the findings concisely for the AI Planner. "
                        "Focus on anomalies and interesting patterns.\n\n"
                        f"Raw Packets (count: {len(packets)}):\n{str(packets)[:2000]}"  # Limit to avoid token limits
                    )
                    
                    summary = self.call_ai_model(prompt)
                    
                    # 3. Log the summarized observation
                    if summary and not summary.startswith("ERROR"):
                        self.redis_manager.log_observation(self.name, f"NETWORK_SUMMARY: {summary}")
                        self.log(f"Captured {len(packets)} packets and generated summary.")
                    else:
                        self.log(f"AI model returned error or empty summary: {summary[:100]}")
                    
                else:
                    self.log("No packets captured in this cycle.")
                    
                time.sleep(AGENT_POLL_INTERVAL)  # Wait before the next sniffing cycle

            except Exception as e:
                self.set_error(f"Unhandled exception in Observer: {e}")
                time.sleep(10)
