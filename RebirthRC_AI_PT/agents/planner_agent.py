from agents.base_agent import BaseAgent
from tools.observability import StructuredLogger, MetricsCollector
import time
import json
import random

class PlannerAgent(BaseAgent):
    def __init__(self, redis_manager, config):
        super().__init__(redis_manager, config)
        
        # Initialize observability
        self.logger = StructuredLogger(self.name, redis_manager=redis_manager)
        self.metrics = MetricsCollector(redis_manager)
        
        # Intelligence: Strategic planning memory
        self.planning_history = []
        self.strategy_effectiveness = {}
        self.current_strategy = 'reconnaissance'
        
        self.logger.info("PlannerAgent initialized with strategic intelligence")
    
    def run(self):
        self.logger.info("Planner Agent started with intelligent planning")
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
                    
                    # Intelligent analysis of situation
                    situation_analysis = self._analyze_situation(
                        observations, vulnerabilities, last_error
                    )
                    
                    # Adapt strategy based on analysis
                    self._adapt_strategy(situation_analysis)

                    request = {
                        "request_type": "plan_action",
                        "state": current_state,
                        "observations": observations,
                        "vulnerabilities": vulnerabilities,
                        "last_error": last_error,
                        "game_server_ip": self.redis_manager.db.get('GAME:SERVER_IP') or '',
                        "game_server_port": int(self.redis_manager.db.get('GAME:SERVER_PORT') or 7777),
                        "situation_analysis": situation_analysis,
                        "current_strategy": self.current_strategy
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

    def _analyze_situation(self, observations: list, vulnerabilities: list, last_error: dict) -> dict:
        """
        Intelligently analyze current situation to inform planning decisions
        """
        analysis = {
            'total_observations': len(observations),
            'total_vulnerabilities': len(vulnerabilities),
            'has_error': last_error is not None,
            'threat_level': 'low',
            'opportunity_score': 0.0,
            'recommended_actions': []
        }
        
        # Analyze observations for patterns
        if observations:
            recent_obs = observations[:10]
            success_indicators = ['SUCCESS', 'VERIFIED', 'DEPLOYED', 'CAPTURED']
            failure_indicators = ['FAILED', 'ERROR', 'DENIED', 'BLOCKED']
            
            successes = sum(1 for obs in recent_obs 
                          if any(ind in str(obs).upper() for ind in success_indicators))
            failures = sum(1 for obs in recent_obs 
                         if any(ind in str(obs).upper() for ind in failure_indicators))
            
            analysis['recent_success_rate'] = successes / max(len(recent_obs), 1)
            analysis['recent_failure_rate'] = failures / max(len(recent_obs), 1)
            
            # Determine threat level
            if failures > successes:
                analysis['threat_level'] = 'high'
                analysis['recommended_actions'].append('increase_stealth')
            elif successes > 2:
                analysis['threat_level'] = 'low'
                analysis['recommended_actions'].append('escalate_attack')
        
        # Analyze vulnerabilities
        if vulnerabilities:
            verified_vulns = [v for v in vulnerabilities if v.get('verified', False)]
            analysis['verified_vulnerabilities'] = len(verified_vulns)
            analysis['opportunity_score'] = len(verified_vulns) / max(len(vulnerabilities), 1)
            
            if verified_vulns:
                analysis['recommended_actions'].append('exploit_vulnerabilities')
        
        # Analyze error state
        if last_error:
            analysis['error_type'] = last_error.get('message', '')[:100]
            analysis['recommended_actions'].append('error_recovery')
        
        self.logger.info(
            f"Situation analysis complete",
            details=analysis
        )
        
        return analysis
    
    def _adapt_strategy(self, situation_analysis: dict):
        """
        Adapt planning strategy based on situation analysis
        This is the "intelligence" - the agent learns and adapts
        """
        threat_level = situation_analysis.get('threat_level', 'low')
        opportunity_score = situation_analysis.get('opportunity_score', 0.0)
        success_rate = situation_analysis.get('recent_success_rate', 0.5)
        
        old_strategy = self.current_strategy
        
        # Strategic decision making
        if threat_level == 'high' and success_rate < 0.3:
            # We're being detected, go stealth
            self.current_strategy = 'stealth_reconnaissance'
            self.logger.warning("Switching to stealth mode due to high threat level")
            
        elif opportunity_score > 0.7 and success_rate > 0.6:
            # We have good opportunities and we're succeeding, escalate
            self.current_strategy = 'aggressive_exploitation'
            self.logger.info("Switching to aggressive exploitation mode")
            
        elif situation_analysis.get('verified_vulnerabilities', 0) > 0:
            # We have verified vulnerabilities, exploit them
            self.current_strategy = 'targeted_exploitation'
            self.logger.info("Switching to targeted exploitation mode")
            
        elif len(self.planning_history) > 10:
            # We've been planning for a while, maybe try something different
            recent_strategies = [p['strategy'] for p in self.planning_history[-10:]]
            if len(set(recent_strategies)) == 1:  # Same strategy for 10 iterations
                # Try something different
                strategies = ['reconnaissance', 'stealth_reconnaissance', 'targeted_exploitation']
                self.current_strategy = random.choice([s for s in strategies if s != self.current_strategy])
                self.logger.info(f"Diversifying strategy to {self.current_strategy}")
        
        # Record strategy change
        if old_strategy != self.current_strategy:
            self.metrics.record_counter('strategy_changes', tags={'from': old_strategy, 'to': self.current_strategy})
            
            # Update effectiveness tracking
            if old_strategy in self.strategy_effectiveness:
                self.strategy_effectiveness[old_strategy]['duration'] += 1
            
            if self.current_strategy not in self.strategy_effectiveness:
                self.strategy_effectiveness[self.current_strategy] = {
                    'successes': 0,
                    'failures': 0,
                    'duration': 0
                }
        
        # Record planning decision
        self.planning_history.append({
            'timestamp': time.time(),
            'strategy': self.current_strategy,
            'threat_level': threat_level,
            'opportunity_score': opportunity_score,
            'success_rate': success_rate
        })
        
        # Keep only last 100 planning decisions
        if len(self.planning_history) > 100:
            self.planning_history = self.planning_history[-100:]
    
    def _evaluate_plan_effectiveness(self, plan_action: dict, execution_result: dict):
        """
        Evaluate how effective our planning was
        This creates a feedback loop for learning
        """
        strategy = self.current_strategy
        success = execution_result.get('success', False)
        
        if strategy in self.strategy_effectiveness:
            if success:
                self.strategy_effectiveness[strategy]['successes'] += 1
            else:
                self.strategy_effectiveness[strategy]['failures'] += 1
        
        # Log effectiveness
        if strategy in self.strategy_effectiveness:
            stats = self.strategy_effectiveness[strategy]
            total = stats['successes'] + stats['failures']
            if total > 0:
                effectiveness = stats['successes'] / total
                self.logger.info(
                    f"Strategy '{strategy}' effectiveness: {effectiveness:.2%}",
                    details=stats
                )
