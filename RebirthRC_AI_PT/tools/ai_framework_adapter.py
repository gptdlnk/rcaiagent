"""
AI Framework Adapter
Provides integration with modern AI frameworks (LangChain, CrewAI)
while maintaining our intelligent agent architecture

This adapter allows us to leverage powerful AI frameworks without losing
our custom intelligence and offensive security capabilities
"""

import os
import json
from typing import Dict, Any, List, Optional, Callable
from abc import ABC, abstractmethod


class AIFrameworkAdapter(ABC):
    """Base adapter for AI frameworks"""
    
    @abstractmethod
    def create_agent(self, config: Dict[str, Any]) -> Any:
        """Create an agent using the framework"""
        pass
    
    @abstractmethod
    def execute_task(self, agent: Any, task: Dict[str, Any]) -> Any:
        """Execute a task with the agent"""
        pass
    
    @abstractmethod
    def get_agent_response(self, agent: Any, prompt: str) -> str:
        """Get response from agent"""
        pass


class LangChainAdapter(AIFrameworkAdapter):
    """
    Adapter for LangChain framework
    
    Integrates LangChain's powerful LLM orchestration with our
    offensive security intelligence
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self._langchain_available = False
        
        try:
            from langchain.agents import AgentExecutor, create_openai_functions_agent
            from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
            from langchain_openai import ChatOpenAI
            from langchain.tools import Tool
            
            self._langchain_available = True
            self.ChatOpenAI = ChatOpenAI
            self.Tool = Tool
            self.create_openai_functions_agent = create_openai_functions_agent
            self.AgentExecutor = AgentExecutor
            self.ChatPromptTemplate = ChatPromptTemplate
            self.MessagesPlaceholder = MessagesPlaceholder
            
            print("[LangChainAdapter] LangChain successfully loaded")
            
        except ImportError:
            print("[LangChainAdapter] LangChain not available. Install with: pip install langchain langchain-openai")
    
    def is_available(self) -> bool:
        """Check if LangChain is available"""
        return self._langchain_available
    
    def create_agent(self, config: Dict[str, Any]) -> Any:
        """
        Create a LangChain agent with offensive security tools
        """
        if not self._langchain_available:
            raise RuntimeError("LangChain not available")
        
        # Create LLM
        llm = self.ChatOpenAI(
            model=config.get('model', 'gpt-4'),
            temperature=config.get('temperature', 0.7),
            api_key=self.api_key
        )
        
        # Define tools for offensive operations
        tools = self._create_offensive_tools(config)
        
        # Create prompt
        prompt = self.ChatPromptTemplate.from_messages([
            ("system", config.get('system_prompt', 'You are an intelligent offensive security agent.')),
            ("human", "{input}"),
            self.MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Create agent
        agent = self.create_openai_functions_agent(llm, tools, prompt)
        agent_executor = self.AgentExecutor(agent=agent, tools=tools, verbose=True)
        
        return agent_executor
    
    def _create_offensive_tools(self, config: Dict[str, Any]) -> List:
        """Create LangChain tools for offensive operations"""
        tools = []
        
        # Reconnaissance tool
        def reconnaissance_tool(target: str) -> str:
            """Perform reconnaissance on target"""
            return f"Reconnaissance results for {target}: [simulated data]"
        
        tools.append(self.Tool(
            name="reconnaissance",
            func=reconnaissance_tool,
            description="Perform reconnaissance on a target to gather information"
        ))
        
        # Vulnerability scanning tool
        def vuln_scan_tool(target: str) -> str:
            """Scan for vulnerabilities"""
            return f"Vulnerability scan for {target}: [simulated results]"
        
        tools.append(self.Tool(
            name="vulnerability_scan",
            func=vuln_scan_tool,
            description="Scan target for vulnerabilities"
        ))
        
        # Exploitation tool
        def exploit_tool(target: str, exploit_type: str) -> str:
            """Execute exploitation"""
            return f"Exploitation attempt on {target} using {exploit_type}: [simulated]"
        
        tools.append(self.Tool(
            name="exploit",
            func=exploit_tool,
            description="Execute exploitation against target"
        ))
        
        return tools
    
    def execute_task(self, agent: Any, task: Dict[str, Any]) -> Any:
        """Execute task with LangChain agent"""
        if not self._langchain_available:
            raise RuntimeError("LangChain not available")
        
        input_text = task.get('input', task.get('prompt', ''))
        result = agent.invoke({"input": input_text})
        
        return result
    
    def get_agent_response(self, agent: Any, prompt: str) -> str:
        """Get response from LangChain agent"""
        result = self.execute_task(agent, {'input': prompt})
        return result.get('output', str(result))


class CrewAIAdapter(AIFrameworkAdapter):
    """
    Adapter for CrewAI framework
    
    Integrates CrewAI's multi-agent orchestration with our
    offensive security operations
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self._crewai_available = False
        
        try:
            from crewai import Agent, Task, Crew, Process
            from crewai_tools import tool
            
            self._crewai_available = True
            self.Agent = Agent
            self.Task = Task
            self.Crew = Crew
            self.Process = Process
            self.tool = tool
            
            print("[CrewAIAdapter] CrewAI successfully loaded")
            
        except ImportError:
            print("[CrewAIAdapter] CrewAI not available. Install with: pip install crewai crewai-tools")
    
    def is_available(self) -> bool:
        """Check if CrewAI is available"""
        return self._crewai_available
    
    def create_agent(self, config: Dict[str, Any]) -> Any:
        """
        Create a CrewAI agent for offensive operations
        """
        if not self._crewai_available:
            raise RuntimeError("CrewAI not available")
        
        agent = self.Agent(
            role=config.get('role', 'Offensive Security Specialist'),
            goal=config.get('goal', 'Identify and exploit vulnerabilities'),
            backstory=config.get('backstory', 'Expert in offensive security operations'),
            verbose=True,
            allow_delegation=config.get('allow_delegation', False)
        )
        
        return agent
    
    def create_crew(self, agents: List[Any], tasks: List[Any]) -> Any:
        """Create a crew of agents"""
        if not self._crewai_available:
            raise RuntimeError("CrewAI not available")
        
        crew = self.Crew(
            agents=agents,
            tasks=tasks,
            process=self.Process.sequential,
            verbose=True
        )
        
        return crew
    
    def execute_task(self, agent: Any, task: Dict[str, Any]) -> Any:
        """Execute task with CrewAI agent"""
        if not self._crewai_available:
            raise RuntimeError("CrewAI not available")
        
        # Create task
        crew_task = self.Task(
            description=task.get('description', ''),
            agent=agent,
            expected_output=task.get('expected_output', 'Task completed')
        )
        
        # Create crew with single agent and task
        crew = self.Crew(
            agents=[agent],
            tasks=[crew_task],
            verbose=True
        )
        
        # Execute
        result = crew.kickoff()
        
        return result
    
    def get_agent_response(self, agent: Any, prompt: str) -> str:
        """Get response from CrewAI agent"""
        result = self.execute_task(agent, {'description': prompt})
        return str(result)


class HybridIntelligentAgent:
    """
    Hybrid agent that combines our custom intelligence with AI frameworks
    
    This maintains our offensive security capabilities while leveraging
    the power of modern AI frameworks
    """
    
    def __init__(
        self,
        name: str,
        framework: str = 'langchain',
        custom_intelligence: Optional[Any] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.framework = framework
        self.custom_intelligence = custom_intelligence
        self.config = config or {}
        
        # Initialize adapter
        if framework == 'langchain':
            self.adapter = LangChainAdapter()
        elif framework == 'crewai':
            self.adapter = CrewAIAdapter()
        else:
            raise ValueError(f"Unknown framework: {framework}")
        
        # Create framework agent if available
        self.framework_agent = None
        if self.adapter.is_available():
            try:
                self.framework_agent = self.adapter.create_agent(self.config)
                print(f"[HybridAgent:{name}] Initialized with {framework}")
            except Exception as e:
                print(f"[HybridAgent:{name}] Failed to initialize framework agent: {e}")
    
    def execute(self, task: Dict[str, Any]) -> Any:
        """
        Execute task using hybrid intelligence
        
        1. Use custom intelligence for offensive-specific logic
        2. Use framework for general reasoning and orchestration
        """
        # Step 1: Custom intelligence pre-processing
        if self.custom_intelligence and hasattr(self.custom_intelligence, 'analyze_task'):
            task = self.custom_intelligence.analyze_task(task)
        
        # Step 2: Framework execution
        if self.framework_agent:
            try:
                result = self.adapter.execute_task(self.framework_agent, task)
            except Exception as e:
                print(f"[HybridAgent:{self.name}] Framework execution failed: {e}")
                result = self._fallback_execution(task)
        else:
            result = self._fallback_execution(task)
        
        # Step 3: Custom intelligence post-processing
        if self.custom_intelligence and hasattr(self.custom_intelligence, 'process_result'):
            result = self.custom_intelligence.process_result(result)
        
        return result
    
    def _fallback_execution(self, task: Dict[str, Any]) -> Any:
        """Fallback to custom intelligence only"""
        if self.custom_intelligence and hasattr(self.custom_intelligence, 'execute'):
            return self.custom_intelligence.execute(task)
        
        return {"status": "fallback", "message": "Executed with fallback logic"}
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities"""
        return {
            'name': self.name,
            'framework': self.framework,
            'framework_available': self.framework_agent is not None,
            'custom_intelligence': self.custom_intelligence is not None,
            'hybrid_mode': self.framework_agent is not None and self.custom_intelligence is not None
        }


# Example usage and integration guide
if __name__ == '__main__':
    print("=== AI Framework Integration Demo ===\n")
    
    # Test LangChain adapter
    print("1. Testing LangChain Adapter:")
    langchain_adapter = LangChainAdapter()
    print(f"   Available: {langchain_adapter.is_available()}\n")
    
    # Test CrewAI adapter
    print("2. Testing CrewAI Adapter:")
    crewai_adapter = CrewAIAdapter()
    print(f"   Available: {crewai_adapter.is_available()}\n")
    
    # Test Hybrid Agent
    print("3. Testing Hybrid Agent:")
    
    class MockCustomIntelligence:
        """Mock custom intelligence for demo"""
        def analyze_task(self, task):
            print("   [Custom Intelligence] Analyzing task...")
            task['analyzed'] = True
            return task
        
        def process_result(self, result):
            print("   [Custom Intelligence] Processing result...")
            return {'custom_processed': True, 'result': result}
        
        def execute(self, task):
            print("   [Custom Intelligence] Executing task...")
            return {'status': 'success', 'data': 'custom execution'}
    
    custom_intel = MockCustomIntelligence()
    
    hybrid_agent = HybridIntelligentAgent(
        name='TestAgent',
        framework='langchain',
        custom_intelligence=custom_intel,
        config={
            'model': 'gpt-4',
            'system_prompt': 'You are an offensive security agent'
        }
    )
    
    print(f"   Capabilities: {hybrid_agent.get_capabilities()}")
    
    # Execute test task
    print("\n4. Executing test task:")
    task = {'description': 'Test reconnaissance', 'target': '192.168.1.1'}
    result = hybrid_agent.execute(task)
    print(f"   Result: {result}")
    
    print("\n=== Integration Demo Complete ===")
    print("\nIntegration Guide:")
    print("1. Install frameworks: pip install langchain langchain-openai crewai crewai-tools")
    print("2. Set OPENAI_API_KEY environment variable")
    print("3. Use HybridIntelligentAgent to combine custom + framework intelligence")
    print("4. Maintain offensive security capabilities while leveraging AI frameworks")
