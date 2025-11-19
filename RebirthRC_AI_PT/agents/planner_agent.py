from agents.base_agent import BaseAgent
import time
import json

class PlannerAgent(BaseAgent):
    def run(self):
        self.log("Planner Agent started.")
        while self.is_running():
            try:
                current_state = self.redis_manager.get_state()
                
                if current_state == 'ERROR_HANDLING':
                    self.handle_error_state()
                    continue

                if current_state in ('DEEP_RECONNAISSANCE', 'ANALYSIS'):
                    observations = self.redis_manager.get_latest_observations(count=50)
                    vulnerabilities = self.redis_manager.get_vulnerabilities()
                    last_error = self.redis_manager.get_last_error()

                    request = {
                        "request_type": "plan_action",
                        "state": current_state,
                        "observations": observations,
                        "vulnerabilities": vulnerabilities,
                        "last_error": last_error,
                        "game_server_ip": self.redis_manager.db.get('GAME:SERVER_IP') or '',
                        "game_server_port": int(self.redis_manager.db.get('GAME:SERVER_PORT') or 7777)
                    }

                    plan_json_str = self.call_ai_model(request)

                    try:
                        plan_action = json.loads(plan_json_str)
                        self.redis_manager.push_action(plan_action)
                        self.log(
                            f"New action planned for {plan_action.get('target_agent')}: "
                            f"{plan_action.get('action_type')}"
                        )
                        self.redis_manager.set_state('PLANNING')
                    except json.JSONDecodeError:
                        self.log(f"Error decoding plan JSON: {plan_json_str}. Retrying plan.")
                        self.redis_manager.set_state('ERROR_HANDLING')
                        
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
        recovery_request = {
            "request_type": "error_recovery",
            "last_error": last_error
        }

        recovery_action_str = self.call_ai_model(recovery_request)

        try:
            recovery_action = json.loads(recovery_action_str)
            self.redis_manager.push_action(recovery_action)
            self.redis_manager.clear_error()
            self.redis_manager.set_state('RECOVERY')
            self.log("Recovery action planned. State set to RECOVERY.")
        except json.JSONDecodeError:
            self.log("Failed to decode recovery plan. System remains in ERROR_HANDLING.")
            time.sleep(10)
