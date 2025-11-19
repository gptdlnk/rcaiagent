from agents.base_agent import BaseAgent
from tools.network_sniffer import NetworkSniffer
from config import GAME_CONFIG, AGENT_POLL_INTERVAL
import time

class ObserverAgent(BaseAgent):
    def run(self):
        self.log("Observer Agent started. Monitoring network traffic.")
        while self.is_running():
            try:
                packets = NetworkSniffer.sniff_packets(count=10, filter_str=None)

                if packets:
                    request = {
                        "request_type": "observer_summary",
                        "packets": packets,
                        "state": self.redis_manager.get_state()
                    }

                    summary = self.call_ai_model(request)

                    if summary and not str(summary).startswith("ERROR"):
                        self.redis_manager.log_observation(self.name, f"NETWORK_SUMMARY: {summary}")
                        self.log(f"Captured {len(packets)} packets and generated summary.")
                    else:
                        self.log(f"MCP summary returned error or empty response: {summary}")

                else:
                    self.log("No packets captured in this cycle.")

                time.sleep(AGENT_POLL_INTERVAL)

            except Exception as e:
                self.set_error(f"Unhandled exception in Observer: {e}")
                time.sleep(10)
