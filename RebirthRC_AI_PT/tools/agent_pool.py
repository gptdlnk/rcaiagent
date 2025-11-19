"""
Agent Pool Implementation
Manages multiple agent instances for scalability and load balancing

Intelligence: Dynamic scaling based on workload
"""

import threading
import queue
import time
from typing import List, Dict, Any, Optional, Callable
from enum import Enum


class AgentStatus(Enum):
    """Agent status in the pool"""
    IDLE = "idle"
    BUSY = "busy"
    FAILED = "failed"
    STOPPED = "stopped"


class PooledAgent:
    """Wrapper for an agent in the pool"""
    
    def __init__(self, agent_id: str, agent_instance: Any):
        self.agent_id = agent_id
        self.agent = agent_instance
        self.status = AgentStatus.IDLE
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.last_active_time = time.time()
        self.current_task = None
    
    def execute_task(self, task: Dict[str, Any]) -> Any:
        """Execute a task with this agent"""
        self.status = AgentStatus.BUSY
        self.current_task = task
        self.last_active_time = time.time()
        
        try:
            # Execute task (assuming agent has execute method)
            if hasattr(self.agent, 'execute'):
                result = self.agent.execute(task)
            elif hasattr(self.agent, 'run_task'):
                result = self.agent.run_task(task)
            else:
                # Generic execution
                result = task.get('action', lambda: None)()
            
            self.tasks_completed += 1
            self.status = AgentStatus.IDLE
            self.current_task = None
            return result
            
        except Exception as e:
            self.tasks_failed += 1
            self.status = AgentStatus.FAILED
            self.current_task = None
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        return {
            'agent_id': self.agent_id,
            'status': self.status.value,
            'tasks_completed': self.tasks_completed,
            'tasks_failed': self.tasks_failed,
            'success_rate': self.tasks_completed / max(self.tasks_completed + self.tasks_failed, 1),
            'last_active': time.time() - self.last_active_time,
            'current_task': self.current_task
        }


class AgentPool:
    """
    Pool of agents for parallel task execution
    
    Intelligence:
    - Dynamic scaling based on queue size
    - Load balancing across agents
    - Automatic failure recovery
    """
    
    def __init__(
        self,
        name: str,
        agent_factory: Callable,
        min_agents: int = 2,
        max_agents: int = 10,
        scale_threshold: int = 5
    ):
        self.name = name
        self.agent_factory = agent_factory
        self.min_agents = min_agents
        self.max_agents = max_agents
        self.scale_threshold = scale_threshold
        
        # Pool management
        self.agents: List[PooledAgent] = []
        self.task_queue = queue.Queue()
        self.result_queue = queue.Queue()
        
        # Control
        self.running = False
        self.worker_threads: List[threading.Thread] = []
        
        # Intelligence: Metrics
        self.total_tasks = 0
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.scale_up_count = 0
        self.scale_down_count = 0
        
        # Lock for thread safety
        self.lock = threading.Lock()
    
    def start(self):
        """Start the agent pool"""
        if self.running:
            print(f"[AgentPool:{self.name}] Already running")
            return
        
        self.running = True
        
        # Create initial agents
        for i in range(self.min_agents):
            self._add_agent()
        
        # Start worker threads
        for agent in self.agents:
            thread = threading.Thread(target=self._worker, args=(agent,), daemon=True)
            thread.start()
            self.worker_threads.append(thread)
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=self._monitor_and_scale, daemon=True)
        monitor_thread.start()
        self.worker_threads.append(monitor_thread)
        
        print(f"[AgentPool:{self.name}] Started with {len(self.agents)} agents")
    
    def stop(self):
        """Stop the agent pool"""
        self.running = False
        
        # Wait for threads to finish
        for thread in self.worker_threads:
            thread.join(timeout=5)
        
        print(f"[AgentPool:{self.name}] Stopped")
    
    def submit_task(self, task: Dict[str, Any]) -> str:
        """Submit a task to the pool"""
        task_id = f"task_{self.total_tasks}_{time.time()}"
        task['task_id'] = task_id
        
        self.task_queue.put(task)
        self.total_tasks += 1
        
        return task_id
    
    def get_result(self, timeout: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """Get a completed task result"""
        try:
            return self.result_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def _add_agent(self) -> bool:
        """Add a new agent to the pool"""
        with self.lock:
            if len(self.agents) >= self.max_agents:
                return False
            
            agent_id = f"{self.name}_agent_{len(self.agents)}"
            
            try:
                agent_instance = self.agent_factory()
                pooled_agent = PooledAgent(agent_id, agent_instance)
                self.agents.append(pooled_agent)
                
                # Start worker thread for new agent
                if self.running:
                    thread = threading.Thread(target=self._worker, args=(pooled_agent,), daemon=True)
                    thread.start()
                    self.worker_threads.append(thread)
                
                print(f"[AgentPool:{self.name}] Added agent: {agent_id}")
                return True
                
            except Exception as e:
                print(f"[AgentPool:{self.name}] Failed to add agent: {e}")
                return False
    
    def _remove_agent(self) -> bool:
        """Remove an idle agent from the pool"""
        with self.lock:
            if len(self.agents) <= self.min_agents:
                return False
            
            # Find idle agent
            for agent in self.agents:
                if agent.status == AgentStatus.IDLE:
                    agent.status = AgentStatus.STOPPED
                    self.agents.remove(agent)
                    print(f"[AgentPool:{self.name}] Removed agent: {agent.agent_id}")
                    return True
            
            return False
    
    def _worker(self, agent: PooledAgent):
        """Worker thread for an agent"""
        while self.running and agent.status != AgentStatus.STOPPED:
            try:
                # Get task from queue
                task = self.task_queue.get(timeout=1)
                
                # Execute task
                try:
                    result = agent.execute_task(task)
                    
                    # Put result in result queue
                    self.result_queue.put({
                        'task_id': task.get('task_id'),
                        'status': 'success',
                        'result': result,
                        'agent_id': agent.agent_id
                    })
                    
                    self.completed_tasks += 1
                    
                except Exception as e:
                    # Task failed
                    self.result_queue.put({
                        'task_id': task.get('task_id'),
                        'status': 'failed',
                        'error': str(e),
                        'agent_id': agent.agent_id
                    })
                    
                    self.failed_tasks += 1
                    
                    # Reset agent status if it failed
                    if agent.status == AgentStatus.FAILED:
                        time.sleep(5)  # Cool down
                        agent.status = AgentStatus.IDLE
                
            except queue.Empty:
                # No tasks available
                continue
            except Exception as e:
                print(f"[AgentPool:{self.name}] Worker error: {e}")
                time.sleep(1)
    
    def _monitor_and_scale(self):
        """Monitor pool and scale dynamically"""
        while self.running:
            try:
                queue_size = self.task_queue.qsize()
                active_agents = sum(1 for a in self.agents if a.status == AgentStatus.BUSY)
                idle_agents = sum(1 for a in self.agents if a.status == AgentStatus.IDLE)
                
                # Intelligence: Scale up if queue is growing
                if queue_size > self.scale_threshold and idle_agents == 0:
                    if self._add_agent():
                        self.scale_up_count += 1
                        print(f"[AgentPool:{self.name}] Scaled UP (queue: {queue_size}, agents: {len(self.agents)})")
                
                # Intelligence: Scale down if too many idle agents
                elif idle_agents > 2 and queue_size == 0:
                    if self._remove_agent():
                        self.scale_down_count += 1
                        print(f"[AgentPool:{self.name}] Scaled DOWN (idle: {idle_agents}, agents: {len(self.agents)})")
                
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                print(f"[AgentPool:{self.name}] Monitor error: {e}")
                time.sleep(5)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics"""
        with self.lock:
            agent_stats = [agent.get_stats() for agent in self.agents]
            
            return {
                'name': self.name,
                'total_agents': len(self.agents),
                'idle_agents': sum(1 for a in self.agents if a.status == AgentStatus.IDLE),
                'busy_agents': sum(1 for a in self.agents if a.status == AgentStatus.BUSY),
                'failed_agents': sum(1 for a in self.agents if a.status == AgentStatus.FAILED),
                'queue_size': self.task_queue.qsize(),
                'total_tasks': self.total_tasks,
                'completed_tasks': self.completed_tasks,
                'failed_tasks': self.failed_tasks,
                'success_rate': self.completed_tasks / max(self.total_tasks, 1),
                'scale_up_count': self.scale_up_count,
                'scale_down_count': self.scale_down_count,
                'agents': agent_stats
            }


# Example usage
if __name__ == '__main__':
    print("=== Testing Agent Pool ===\n")
    
    # Mock agent factory
    class MockAgent:
        def execute(self, task):
            time.sleep(0.5)  # Simulate work
            return f"Completed: {task.get('data', 'N/A')}"
    
    def agent_factory():
        return MockAgent()
    
    # Create pool
    pool = AgentPool('test_pool', agent_factory, min_agents=2, max_agents=5, scale_threshold=3)
    pool.start()
    
    # Submit tasks
    print("1. Submitting 10 tasks...")
    for i in range(10):
        task_id = pool.submit_task({'data': f'task_{i}'})
        print(f"   Submitted: {task_id}")
    
    # Wait and collect results
    print("\n2. Collecting results...")
    time.sleep(2)
    
    results_collected = 0
    while results_collected < 10:
        result = pool.get_result(timeout=1)
        if result:
            print(f"   Result: {result['task_id']} - {result['status']}")
            results_collected += 1
    
    # Show stats
    print(f"\n3. Pool Statistics:")
    stats = pool.get_stats()
    for key, value in stats.items():
        if key != 'agents':
            print(f"   {key}: {value}")
    
    # Stop pool
    pool.stop()
    print("\n=== Agent Pool Test Complete ===")
