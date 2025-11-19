import time
import threading
import os
from config import AGENTS, REDIS_CONFIG
from data_hub.redis_manager import RedisManager
from agents.planner_agent import PlannerAgent
from agents.executor_agent import ExecutorAgent
from agents.observer_agent import ObserverAgent
from agents.reverse_agent import ReverseEngineerAgent
from agents.fuzzer_agent import FuzzerAgent

# Ensure all agent files are imported so they are available
# from agents import base_agent, planner_agent, executor_agent, observer_agent, reverse_agent, fuzzer_agent

class Orchestrator:
    def __init__(self):
        # 1. Initialize Redis Manager (Central Data Hub)
        self.redis_manager = RedisManager(REDIS_CONFIG)
        self.agents = []
        self.running = True
        self.init_agents()

    def init_agents(self):
        """Initialize all AI Agents based on the configuration."""
        print("Initializing AI Agents...")
        
        # Initialize Agent instances
        self.agents.append(PlannerAgent(self.redis_manager, AGENTS['PLANNER']))
        self.agents.append(ExecutorAgent(self.redis_manager, AGENTS['EXECUTOR']))
        self.agents.append(ObserverAgent(self.redis_manager, AGENTS['OBSERVER']))
        self.agents.append(ReverseEngineerAgent(self.redis_manager, AGENTS['REVERSE_ENGINEER']))
        self.agents.append(FuzzerAgent(self.redis_manager, AGENTS['FUZZER']))

        # Start Agent threads
        for agent in self.agents:
            thread = threading.Thread(target=agent.run, name=agent.name)
            thread.daemon = True
            thread.start()
            print(f"Agent {agent.name} started with model {agent.model_name}")

    def run(self):
        """Main loop for the Orchestrator to monitor system status."""
        print("\nOrchestrator is running. Monitoring system status...")
        # Set initial state to start the process
        self.redis_manager.set_state('DEEP_RECONNAISSANCE') 
        
        try:
            while self.running:
                # Simple status check
                current_state = self.redis_manager.get_state()
                action_queue_size = self.redis_manager.get_queue_size('QUEUE:ACTIONS')
                last_error = self.redis_manager.get_last_error()
                
                print(f"[ORCHESTRATOR] STATE: {current_state} | ACTIONS: {action_queue_size} | ERROR: {'YES' if last_error else 'NO'}")
                
                if current_state == 'ERROR_HANDLING' and not last_error:
                    # Error was handled by Planner, switch back to Analysis
                    self.redis_manager.set_state('ANALYSIS')
                
                time.sleep(5) # Monitor every 5 seconds
        except KeyboardInterrupt:
            print("\nShutting down Orchestrator and Agents...")
            self.running = False
            for agent in self.agents:
                agent.stop()
            time.sleep(2)
            print("Shutdown complete.")

if __name__ == "__main__":
    # Check for API Keys (Basic check)
    # if not os.getenv("OPENAI_OSI_KEY"):
    #     print("WARNING: OPENAI_API_KEY environment variable not set. AI calls will likely fail.")
        
    # Ensure Redis server is running before executing
    orchestrator = Orchestrator()
    orchestrator.run()
