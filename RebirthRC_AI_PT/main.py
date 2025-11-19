import time
import threading
import os
import sys
from config import (
    AGENTS,
    REDIS_CONFIG,
    LOG_DIR,
    SCREENSHOT_DIR,
    USE_MCP,
    ROLE_PROFILES,
    OPENAI_API_KEY,
    HIHG_API_KEY
)
from data_hub.redis_manager import RedisManager
from mcp import RoleEngine
from agents.planner_agent import PlannerAgent
from agents.executor_agent import ExecutorAgent
from agents.observer_agent import ObserverAgent
from agents.reverse_agent import ReverseEngineerAgent
from agents.fuzzer_agent import FuzzerAgent

def check_prerequisites():
    """Check if all prerequisites are met before starting."""
    print("=" * 60)
    print("Rebirth RC AI Offensive Security Tool - Startup Checks")
    print("=" * 60)
    
    errors = []
    warnings = []
    
    # Check Redis connection
    print("\n[1/3] Checking Redis connection...")
    try:
        test_redis = RedisManager(REDIS_CONFIG)
        test_redis.get_state()
        print("✓ Redis connection successful")
    except Exception as e:
        errors.append(f"Redis connection failed: {e}")
        print(f"✗ Redis connection failed: {e}")
        print("  Please ensure Redis is running on {}:{}".format(
            REDIS_CONFIG['HOST'], REDIS_CONFIG['PORT']))
    
    # Check directories
    print("\n[2/3] Checking directory structure...")
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        print(f"✓ Log directory: {LOG_DIR}")
        print(f"✓ Screenshot directory: {SCREENSHOT_DIR}")
    except Exception as e:
        errors.append(f"Failed to create directories: {e}")
        print(f"✗ Failed to create directories: {e}")
    
    # Check agent configurations
    print("\n[3/3] Checking agent configurations...")
    for agent_name, agent_config in AGENTS.items():
        model = agent_config.get('MODEL', 'NOT_SET')
        mode = 'MCP' if agent_config.get('USE_MCP') else 'External Model'
        print(f"✓ {agent_name}: {model} (mode: {mode})")
    
    # Summary
    print("\n" + "=" * 60)
    if errors:
        print("ERRORS FOUND:")
        for error in errors:
            print(f"  ✗ {error}")
        print("\nPlease fix the errors above before continuing.")
        return False
    
    if warnings:
        print("WARNINGS:")
        for warning in warnings:
            print(f"  ⚠ {warning}")
        print("\nSystem will start but some features may not work correctly.")
    
    print("\n✓ All checks passed. Starting system...")
    print("=" * 60 + "\n")
    return True

class Orchestrator:
    def __init__(self):
        # 1. Initialize Redis Manager (Central Data Hub)
        print("Initializing Redis Manager...")
        self.redis_manager = RedisManager(REDIS_CONFIG)
        self.agents = []
        self.agent_threads = []
        self.running = True
        self.init_agents()

    def init_agents(self):
        """Initialize all AI Agents based on the configuration."""
        print("\nInitializing AI Agents...")
        
        try:
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
                self.agent_threads.append(thread)
                print(f"✓ Agent {agent.name} started with model {agent.model_name}")
            
            print(f"\n✓ All {len(self.agents)} agents initialized and running")
        except Exception as e:
            print(f"✗ Error initializing agents: {e}")
            raise

    def run(self):
        """Main loop for the Orchestrator to monitor system status."""
        print("\n" + "=" * 60)
        print("Orchestrator is running. Monitoring system status...")
        print("Press Ctrl+C to stop the system gracefully.")
        print("=" * 60 + "\n")
        
        # Set initial state to start the process
        self.redis_manager.set_state('DEEP_RECONNAISSANCE')
        self.redis_manager.log_observation("ORCHESTRATOR", "System started. Initial state: DEEP_RECONNAISSANCE")
        
        try:
            while self.running:
                # Status check
                current_state = self.redis_manager.get_state()
                action_queue_size = self.redis_manager.get_queue_size()
                last_error = self.redis_manager.get_last_error()
                vulnerabilities = len(self.redis_manager.get_vulnerabilities())
                
                status_line = (
                    f"[ORCHESTRATOR] STATE: {current_state:20s} | "
                    f"ACTIONS: {action_queue_size:3d} | "
                    f"VULNS: {vulnerabilities:2d} | "
                    f"ERROR: {'YES' if last_error else 'NO':3s}"
                )
                print(status_line)
                
                if current_state == 'ERROR_HANDLING' and not last_error:
                    # Error was handled by Planner, switch back to Analysis
                    self.redis_manager.set_state('ANALYSIS')
                    self.redis_manager.log_observation("ORCHESTRATOR", "Error resolved. Switching to ANALYSIS state.")
                
                time.sleep(5)  # Monitor every 5 seconds
                
        except KeyboardInterrupt:
            print("\n\n" + "=" * 60)
            print("Shutting down Orchestrator and Agents...")
            print("=" * 60)
            self.running = False
            
            # Stop all agents
            for agent in self.agents:
                agent.stop()
            
            # Wait for threads to finish
            for thread in self.agent_threads:
                thread.join(timeout=2)
            
            time.sleep(1)
            print("✓ Shutdown complete.")
            print("=" * 60)

if __name__ == "__main__":
    # Run prerequisite checks
    if not check_prerequisites():
        print("\nStartup checks failed. Exiting.")
        sys.exit(1)
    
    try:
        # Ensure Redis server is running before executing
        orchestrator = Orchestrator()
        orchestrator.run()
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
