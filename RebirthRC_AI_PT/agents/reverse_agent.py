from agents.base_agent import BaseAgent
from tools.terminal_wrapper import TerminalWrapper
import time

class ReverseEngineerAgent(BaseAgent):
    def run(self):
        self.log("Reverse Engineer Agent started. Waiting for analysis tasks.")
        while self.is_running():
            try:
                # RE Agent works primarily on demand or in a continuous loop
                # Here, we simulate a continuous loop of analysis
                
                # 1. Check for new observations from the Observer that need deeper analysis
                latest_observations = self.redis_manager.get_latest_observations(count=5)
                
                if any("unencrypted data" in obs.lower() or "protocol structure" in obs.lower() for obs in latest_observations):
                    self.log("Detected new observations requiring Reverse Engineering.")

                    request = {
                        "request_type": "reverse_generate_command",
                        "focus": "packet_handler",
                        "observations": latest_observations
                    }

                    analysis_command = self.call_ai_model(request)

                    if analysis_command and not str(analysis_command).startswith("ERROR"):
                        self.log(f"Executing RE command: {analysis_command}")
                        code, stdout, stderr = TerminalWrapper.run_command(analysis_command, timeout=120) # Longer timeout for RE
                        
                        # 4. Log the raw analysis result
                        self.redis_manager.log_observation(
                            self.name,
                            f"RE_RAW_RESULT: Code={code}. STDOUT: {stdout[:1000]}"
                        )

                        summary_request = {
                            "request_type": "reverse_summarise",
                            "raw_output": stdout[:2000],
                            "exit_code": code
                        }
                        structured_knowledge = self.call_ai_model(summary_request)

                        self.redis_manager.log_observation(self.name, f"RE_KNOWLEDGE: {structured_knowledge}")

                    else:
                        self.log("Failed to generate valid RE command.")
                        
                else:
                    self.log("No immediate RE task. Sleeping.")
                    time.sleep(10)

            except Exception as e:
                self.set_error(f"Unhandled exception in Reverse Engineer: {e}")
                time.sleep(10)
