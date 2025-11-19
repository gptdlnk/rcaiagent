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
                    
                    # 2. Use Codex to generate a Ghidra/IDA script or command
                    prompt = (
                        "The Observer detected critical network traffic. Your task is to analyze the game binary "
                        "to find the function responsible for handling this traffic and determine the protocol structure. "
                        "Generate a command to run a relevant static analysis tool (e.g., 'ghidra_script_runner.sh analyze_packet_handler.py') "
                        "or a Python script to perform a specific binary analysis task. "
                        "Output only the command or the script."
                    )
                    
                    analysis_command = self.call_ai_model(prompt)
                    
                    # 3. Execute the analysis command (using Executor's logic via TerminalWrapper)
                    if analysis_command and not analysis_command.startswith("ERROR"):
                        self.log(f"Executing RE command: {analysis_command}")
                        code, stdout, stderr = TerminalWrapper.run_command(analysis_command, timeout=120) # Longer timeout for RE
                        
                        # 4. Log the raw analysis result
                        self.redis_manager.log_observation(self.name, f"RE_RAW_RESULT: Code={code}. STDOUT: {stdout[:1000]}")
                        
                        # 5. Use Codex again to summarize the raw result into structured knowledge
                        summary_prompt = (
                            f"Analyze the following raw Reverse Engineering output and extract the Game Protocol Structure (e.g., Header: 4 bytes, Command ID: 2 bytes, Payload: JSON/Binary) "
                            f"and any critical Game Logic (e.g., Damage calculation function name). "
                            f"Raw Output: {stdout[:1000]}"
                        )
                        structured_knowledge = self.call_ai_model(summary_prompt)
                        
                        self.redis_manager.log_observation(self.name, f"RE_KNOWLEDGE: {structured_knowledge}")
                        
                    else:
                        self.log("Failed to generate valid RE command.")
                        
                else:
                    self.log("No immediate RE task. Sleeping.")
                    time.sleep(10)

            except Exception as e:
                self.set_error(f"Unhandled exception in Reverse Engineer: {e}")
                time.sleep(10)
