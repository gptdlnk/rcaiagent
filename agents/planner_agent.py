from agents.base_agent import BaseAgent
import time

class PlannerAgent(BaseAgent):
    def run(self):
        self.log("Planner Agent started.")
        while self.is_running():
            try:
                current_state = self.redis_manager.get_state()
                
                if current_state == 'ERROR_HANDLING':
                    self.handle_error_state()
                    continue

                if current_state == 'DEEP_RECONNAISSANCE' or current_state == 'ANALYSIS':
                    # 1. Get latest observations and learning data from Redis
                    observations = self.redis_manager.get_latest_observations(count=50)
                    learning_data = self.redis_manager.get_learning_data()
                    
                    # 2. Construct the prompt for GPT
                    prompt = (
                        f"Current System State: {current_state}\n"
                        f"Latest Observations (from Observer/RE): {observations}\n"
                        f"Known Vulnerabilities: {self.redis_manager.get_vulnerabilities()}\n"
                        f"Learning Data (Failed Attempts/Errors): {learning_data}\n\n"
                        "Based on the above, what is the single most critical next step to find a Logic Flaw in Rebirth RC? "
                        "If Learning Data is present, your primary task is to analyze it and formulate a new, improved strategy to overcome the previous failure. "
                        "The plan must be a single, concise action command for the Executor or Fuzzer. "
                        "Format the output as a JSON object with 'target_agent', 'action_type', and 'payload'."
                    )
                    
                    # 3. Call GPT (The Planner)
                    plan_json_str = self.call_ai_model(prompt)
                    
                    # 3. Clear learning data after processing (to prevent re-analysis in the next cycle)
                    if learning_data:
                        self.redis_manager.clear_learning_data()
                        
                    # 4. Parse and push the action
                    try:
                        # In a real system, robust JSON parsing and validation is needed
                        plan_action = json.loads(plan_json_str)
                        self.redis_manager.push_action(plan_action)
                        self.log(f"New action planned for {plan_action.get('target_agent')}: {plan_action.get('action_type')}")
                        self.redis_manager.set_state('PLANNING')
                    except json.JSONDecodeError:
                        self.log(f"Error decoding plan JSON: {plan_json_str}. Retrying plan.")
                        self.redis_manager.set_state('ERROR_HANDLING') # Trigger error handling for bad JSON
                        
                elif current_state == 'PLANNING':
                    # Wait for Executor to finish the action
                    self.log("Waiting for Executor to complete the planned action...")
                    time.sleep(5)
                    
                else:
                    self.log(f"System in state {current_state}. Waiting...")
                    time.sleep(5)

            except Exception as e:
                self.set_error(f"Unhandled exception in Planner: {e}")
                time.sleep(10)

    def handle_error_state(self):
        """Logic for the Planner to recover from an error."""
        last_error = self.redis_manager.get_last_error()
        self.log(f"Handling error: {last_error}")
        
        # GPT's role: Analyze the error and propose a recovery plan
        recovery_prompt = (
            f"The system encountered a critical error: {last_error}. "
            "Propose a recovery plan. This plan must be a single action for the Executor "
            "to execute (e.g., 'restart game', 'clear network cache', 'try a different IP'). "
            "Format the output as a JSON object with 'target_agent', 'action_type', and 'payload'."
        )
        
        recovery_action_str = self.call_ai_model(recovery_prompt)
        
        try:
            recovery_action = json.loads(recovery_action_str)
            self.redis_manager.push_action(recovery_action)
            self.redis_manager.clear_error()
            self.redis_manager.set_state('RECOVERY')
            self.log("Recovery action planned. State set to RECOVERY.")
        except json.JSONDecodeError:
            self.log("Failed to decode recovery plan. System remains in ERROR_HANDLING.")
            time.sleep(10)
