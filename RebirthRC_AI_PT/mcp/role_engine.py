import json
import random
from typing import Any, Dict, List, Optional, Union


class RoleEngine:
    """Real-time Adaptive Multi-role Coordination Processor (MCP).

    AI Engine ที่ปรับตามสถานการณ์หน้างานแบบเรียลไทม์ ไม่ใช้ flow เดียวกัน
    แต่วิเคราะห์สถานการณ์และเลือก strategy ที่เหมาะสมที่สุด
    """

    _instance: Optional["RoleEngine"] = None

    def __init__(self, role_profiles: Optional[Dict[str, Dict[str, Any]]] = None):
        self.role_profiles = role_profiles or {}
        # Real-time adaptive state - เก็บสถานการณ์ปัจจุบันและปรับ strategy
        self.shared_state: Dict[str, Any] = {
            "last_observer_summary": "",
            "protocol_insights": [],
            "fuzz_history": [],
            "recovery_actions": [],
            "current_situation": "UNKNOWN",  # Real-time situation awareness
            "detected_vulnerabilities": [],
            "verification_status": {},
            "attack_surface": {},
            "adaptive_strategy": "BASELINE"  # Current strategy based on situation
        }
        # Strategy patterns for different situations
        self.strategy_patterns = {
            "INITIAL_RECON": {"focus": "traffic_analysis", "intensity": "low"},
            "PROTOCOL_DISCOVERED": {"focus": "reverse_engineering", "intensity": "medium"},
            "VULNERABILITY_DETECTED": {"focus": "exploitation", "intensity": "high"},
            "VERIFICATION_NEEDED": {"focus": "stealth_verification", "intensity": "critical"},
            "BACKDOOR_DEPLOYMENT": {"focus": "persistence", "intensity": "critical"},
            "SOCIAL_ENGINEERING_OPPORTUNITY": {"focus": "payload_delivery", "intensity": "high"}, # New Strategy
            "ERROR_RECOVERY": {"focus": "resilience", "intensity": "medium"}
        }

    # ------------------------------------------------------------------
    # Singleton helpers
    # ------------------------------------------------------------------
    @classmethod
    def initialize(cls, role_profiles: Dict[str, Dict[str, Any]] | None = None) -> None:
        cls._instance = cls(role_profiles)

    @classmethod
    def instance(cls) -> "RoleEngine":
        if cls._instance is None:
            raise RuntimeError("RoleEngine has not been initialized.")
        return cls._instance

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------
    def respond(self, agent_name: str, payload: Any) -> Any:
        """Return a response for the given agent based on payload metadata."""
        handler_name = None
        context: Dict[str, Any]

        if isinstance(payload, dict):
            context = payload
            handler_name = context.get("request_type")
        else:
            # Fallback for legacy usage – treat as generic request
            context = {"request_type": "generic", "prompt": str(payload)}
            handler_name = "generic"

        # Normalise agent key (e.g., "AI Planner (GPT)" -> "PLANNER")
        agent_key = self._normalise_agent_name(agent_name)

        if handler_name == "plan_action":
            return self._handle_planner_plan(context)
        if handler_name == "error_recovery":
            return self._handle_planner_recovery(context)
        if handler_name == "observer_summary":
            return self._handle_observer_summary(context)
        if handler_name == "reverse_generate_command":
            return self._handle_reverse_generate_command(context)
        if handler_name == "reverse_summarise":
            return self._handle_reverse_summarise(context)
        if handler_name == "fuzzer_payload":
            return self._handle_fuzzer_payload(context)
        if handler_name == "generic_action":
            return self._handle_generic_action(context)

        # Default generic response
        return self._handle_default(agent_key, context)

    # ------------------------------------------------------------------
    # Planner logic
    # ------------------------------------------------------------------
    def _handle_planner_plan(self, context: Dict[str, Any]) -> str:
        """Real-time adaptive planning - วิเคราะห์สถานการณ์และเลือก strategy"""
        state = context.get("state", "UNKNOWN")
        observations: List[str] = context.get("observations", [])
        vulnerabilities: List[Dict[str, Any]] = context.get("vulnerabilities", [])
        
        # Real-time situation analysis
        situation = self._analyze_current_situation(observations, vulnerabilities, state)
        self.shared_state["current_situation"] = situation
        
        # Adaptive strategy selection based on situation
        strategy = self._select_adaptive_strategy(situation, context)
        self.shared_state["adaptive_strategy"] = strategy
        
        # Generate action based on real-time situation
        if situation == "SOCIAL_ENGINEERING_OPPORTUNITY":
            # High priority: Deliver steganography payload
            action = {
                "target_agent": "EXECUTOR",
                "action_type": "DELIVER_STEGO_PAYLOAD",
                "payload": {
                    "delivery_channel": "Discord",
                    "target_user": "general_chat",
                    "message_template": "Check out this new texture pack!"
                }
            }
        elif situation == "VULNERABILITY_DETECTED":
            # Critical: Need stealth verification
            action = {
                "target_agent": "EXECUTOR",
                "action_type": "STEALTH_VERIFY",
                "payload": {
                    "vulnerability": vulnerabilities[0] if vulnerabilities else {},
                    "verification_type": "multi_vector",
                    "stealth_mode": True
                }
            }
        elif situation == "VERIFICATION_NEEDED":
            # Deploy backdoor and verify 100%
            action = {
                "target_agent": "EXECUTOR",
                "action_type": "DEPLOY_BACKDOOR",
                "payload": {
                    "target_ip": context.get("game_server_ip", "127.0.0.1"),
                    "target_port": context.get("game_server_port", 7777),
                    "backdoor_type": "persistent",
                    "verify_100_percent": True
                }
            }
        elif situation == "PROTOCOL_DISCOVERED":
            # Exploit protocol knowledge
            action = {
                "target_agent": "FUZZER",
                "action_type": "ADVANCED_FUZZ",
                "payload": {
                    "ip": context.get("game_server_ip", "127.0.0.1"),
                    "port": context.get("game_server_port", 7777),
                    "technique": "protocol_manipulation"
                }
            }
        elif situation == "INITIAL_RECON":
            # Baseline reconnaissance
            action = {
                "target_agent": "OBSERVER",
                "action_type": "CAPTURE_TRAFFIC",
                "payload": {
                    "duration": 10,
                    "description": "Collect baseline packet samples for analysis."
                }
            }
        else:
            # Default adaptive action
            action = {
                "target_agent": "OBSERVER",
                "action_type": "CAPTURE_TRAFFIC",
                "payload": {
                    "duration": 5,
                    "description": "Continuing reconnaissance based on current situation."
                }
            }
        
        return json.dumps(action)
    
    def _analyze_current_situation(self, observations: List[str], 
                                   vulnerabilities: List[Dict[str, Any]],
                                   state: str) -> str:
        """วิเคราะห์สถานการณ์ปัจจุบันแบบเรียลไทม์"""
        # Highest priority: Social engineering opportunity
        if any("DISCORD_CHANNEL_ACTIVE" in obs or "SOCIAL_ENGINEERING_OPPORTUNITY" in obs for obs in observations):
            return "SOCIAL_ENGINEERING_OPPORTUNITY"

        # Check for verification needs
        if any("VERIFICATION_NEEDED" in obs or "VULN_DETECTED" in obs for obs in observations):
            return "VERIFICATION_NEEDED"
        
        # Check for confirmed vulnerabilities
        if vulnerabilities:
            return "VULNERABILITY_DETECTED"
        
        # Check for protocol knowledge
        if any("RE_KNOWLEDGE" in obs for obs in observations):
            return "PROTOCOL_DISCOVERED"
        
        # Check for network activity
        if any("NETWORK_SUMMARY" in obs for obs in observations):
            return "NETWORK_ANALYSIS"
        
        # Default
        return "INITIAL_RECON"
    
    def _select_adaptive_strategy(self, situation: str, context: Dict[str, Any]) -> str:
        """เลือก strategy ที่เหมาะสมตามสถานการณ์"""
        if situation in self.strategy_patterns:
            pattern = self.strategy_patterns[situation]
            return f"{situation}_{pattern['focus']}"
        return "BASELINE"

    def _handle_planner_recovery(self, context: Dict[str, Any]) -> str:
        recovery_steps = [
            {
                "target_agent": "GAME_CLIENT",
                "action_type": "LAUNCH",
                "payload": {}
            },
            {
                "target_agent": "TERMINAL",
                "action_type": "RUN_COMMAND",
                "payload": {
                    "command": "echo 'Re-established connection after failure'"
                }
            }
        ]
        # Persist recovery for audit
        self.shared_state["recovery_actions"].append(recovery_steps[0])
        return json.dumps(recovery_steps[0])

    # ------------------------------------------------------------------
    # Observer logic
    # ------------------------------------------------------------------
    def _handle_observer_summary(self, context: Dict[str, Any]) -> str:
        packets: List[Dict[str, Any]] = context.get("packets", [])
        if not packets:
            return "No packets captured."

        interesting = [
            pkt for pkt in packets
            if int(pkt.get("length", 0)) > 200 or "ffff" in pkt.get("payload_hex", "").lower()
        ]

        summary_lines = [
            f"Captured {len(packets)} packets; {len(interesting)} flagged as anomalous."
        ]
        for pkt in interesting[:3]:
            summary_lines.append(
                f"Anomaly -> src:{pkt.get('source')} dst:{pkt.get('destination')} "
                f"len:{pkt.get('length')} payload_head:{pkt.get('payload_hex', '')[:16]}"
            )

        summary = "\n".join(summary_lines)
        self.shared_state["last_observer_summary"] = summary
        return summary

    # ------------------------------------------------------------------
    # Reverse engineer logic
    # ------------------------------------------------------------------
    def _handle_reverse_generate_command(self, context: Dict[str, Any]) -> str:
        focus = context.get("focus", "packet_handler")
        base_command = (
            "python tools/terminal_wrapper.py --analyze "
            f"--focus {focus}"
        )
        return base_command

    def _handle_reverse_summarise(self, context: Dict[str, Any]) -> str:
        raw_output = context.get("raw_output", "")
        lines = raw_output.splitlines()
        insight = "Identified command dispatcher" if any("dispatch" in ln.lower() for ln in lines) else ""
        summary = {
            "protocol_structure": "Header(4) | CommandID(2) | Payload(variable)",
            "insights": insight or "Further static analysis recommended."
        }
        self.shared_state["protocol_insights"].append(summary)
        return json.dumps(summary)

    # ------------------------------------------------------------------
    # Fuzzer logic
    # ------------------------------------------------------------------
    def _handle_fuzzer_payload(self, context: Dict[str, Any]) -> str:
        target_ip = context.get("target_ip", "127.0.0.1")
        target_port = context.get("target_port", 7777)
        protocol = context.get("protocol", "TCP")

        fuzz_value = random.randint(2**31, 2**32 - 1)
        payload_hex = f"DEADBEEF{fuzz_value:08X}FFFFFFFF"

        payload = {
            "target_ip": target_ip,
            "target_port": target_port,
            "protocol": protocol,
            "payload_hex": payload_hex
        }
        self.shared_state["fuzz_history"].append(payload)
        return json.dumps(payload)

    # ------------------------------------------------------------------
    # Generic helpers
    # ------------------------------------------------------------------
    def _handle_generic_action(self, context: Dict[str, Any]) -> str:
        command = context.get("command", "echo 'Generic MCP response'")
        return command

    def _handle_default(self, agent_key: str, context: Dict[str, Any]) -> str:
        prompt = context.get("prompt", "")
        return f"[{agent_key}] MCP received request: {prompt}".strip()

    def _normalise_agent_name(self, agent_name: str) -> str:
        upper = agent_name.upper()
        if "PLANNER" in upper:
            return "PLANNER"
        if "EXECUTOR" in upper:
            return "EXECUTOR"
        if "OBSERVER" in upper:
            return "OBSERVER"
        if "REVERSE" in upper:
            return "REVERSE"
        if "FUZZER" in upper:
            return "FUZZER"
        return agent_name.upper()

