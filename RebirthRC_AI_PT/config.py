# config.py: การตั้งค่าระบบและโมเดล AI
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# 1. การตั้งค่า Redis (Central Data Hub)
REDIS_CONFIG = {
    "HOST": os.getenv("REDIS_HOST", "localhost"),
    "PORT": int(os.getenv("REDIS_PORT", "6379")),
    "DB": int(os.getenv("REDIS_DB", "0"))
}

# 2. การตั้งค่าเกมและเครื่องมือ
GAME_CONFIG = {
    "GAME_PATH": os.getenv("GAME_PATH", "C:\\Program Files\\RebirthRC\\RebirthRC.exe"),  # Windows path example
    "GAME_LOG_PATH": os.getenv("GAME_LOG_PATH", "C:\\Users\\%USERNAME%\\Documents\\RebirthRC\\logs\\"),  # Windows path example
    "GAME_PROCESS_NAME": os.getenv("GAME_PROCESS_NAME", "RebirthRC.exe"),
    "NMAP_SCAN_RANGE": os.getenv("NMAP_SCAN_RANGE", "192.168.1.0/24"),
    "PROXY_SERVER": os.getenv("PROXY_SERVER", "http://127.0.0.1:8080"),  # สำหรับการดักจับ Traffic (เช่น Burp Suite/mitmproxy)
    "GAME_SERVER_IP": os.getenv("GAME_SERVER_IP", ""),  # IP ของเกมเซิร์ฟเวอร์ (ถ้ารู้)
    "GAME_SERVER_PORT": int(os.getenv("GAME_SERVER_PORT", "7777"))  # Port ของเกมเซิร์ฟเวอร์
}

# 3. การตั้งค่า API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
HIHG_API_KEY = os.getenv("HIHG_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")  # สำหรับ custom endpoints
HIHG_BASE_URL = os.getenv("HIHG_BASE_URL", "")  # สำหรับ 5 Hihg API endpoint

# 4. การตั้งค่า AI Agent (Attacker) และการจัดสรรโมเดล
# โมเดลที่คุณมี: GPT, Codex, 5 Hihg
# การจัดสรร: GPT (Planner), Codex (Executor/RE), 5 Hihg (Observer/Fuzzer)

AGENTS = {
    "PLANNER": {
        "NAME": "AI Planner (GPT)",
        "MODEL": os.getenv("PLANNER_MODEL", "gpt-4-turbo-preview"),  # Default model name
        "TEMPERATURE": float(os.getenv("PLANNER_TEMPERATURE", "0.7")),
        "SYSTEM_PROMPT": "You are the strategic brain. Analyze observations and create the next step plan in natural language. Always format your response as a JSON object with 'target_agent', 'action_type', and 'payload' fields.",
        "API_KEY": OPENAI_API_KEY,
        "BASE_URL": OPENAI_BASE_URL
    },
    "EXECUTOR": {
        "NAME": "AI Executor (Codex)",
        "MODEL": os.getenv("EXECUTOR_MODEL", "gpt-3.5-turbo-instruct"),  # Codex-like model
        "TEMPERATURE": float(os.getenv("EXECUTOR_TEMPERATURE", "0.1")),
        "SYSTEM_PROMPT": "You are the coder. Convert the Planner's natural language plan into executable Python code or shell commands. Your output MUST be only the code block without markdown formatting.",
        "API_KEY": OPENAI_API_KEY,
        "BASE_URL": OPENAI_BASE_URL
    },
    "OBSERVER": {
        "NAME": "AI Observer (5 Hihg)",
        "MODEL": os.getenv("OBSERVER_MODEL", "gpt-3.5-turbo"),  # Fast model for real-time processing
        "TEMPERATURE": float(os.getenv("OBSERVER_TEMPERATURE", "0.0")),
        "SYSTEM_PROMPT": "You are the real-time monitor. Analyze raw network traffic and logs, then summarize critical findings for the Planner. Be concise and focus on anomalies.",
        "API_KEY": HIHG_API_KEY if HIHG_API_KEY else OPENAI_API_KEY,  # Fallback to OpenAI if 5 Hihg not configured
        "BASE_URL": HIHG_BASE_URL if HIHG_BASE_URL else OPENAI_BASE_URL
    },
    "REVERSE_ENGINEER": {
        "NAME": "AI Reverse Engineer (Codex)",
        "MODEL": os.getenv("REVERSE_ENGINEER_MODEL", "gpt-3.5-turbo-instruct"),
        "TEMPERATURE": float(os.getenv("REVERSE_ENGINEER_TEMPERATURE", "0.3")),
        "SYSTEM_PROMPT": "You are the code analyst. Analyze game binaries and decompile code to extract game logic and protocol structures. Output structured analysis results.",
        "API_KEY": OPENAI_API_KEY,
        "BASE_URL": OPENAI_BASE_URL
    },
    "FUZZER": {
        "NAME": "AI Fuzzer (5 Hihg)",
        "MODEL": os.getenv("FUZZER_MODEL", "gpt-3.5-turbo"),  # Fast model for payload generation
        "TEMPERATURE": float(os.getenv("FUZZER_TEMPERATURE", "0.9")),  # High temperature for creative, random payloads
        "SYSTEM_PROMPT": "You are the payload generator. Create large volumes of abnormal and creative data packets based on known protocol structures. Output ONLY a JSON object with 'payload_hex', 'target_ip', and 'target_port' fields.",
        "API_KEY": HIHG_API_KEY if HIHG_API_KEY else OPENAI_API_KEY,  # Fallback to OpenAI if 5 Hihg not configured
        "BASE_URL": HIHG_BASE_URL if HIHG_BASE_URL else OPENAI_BASE_URL
    }
}

# 5. การตั้งค่าทั่วไป
LOG_DIR = os.getenv("LOG_DIR", "logs")
SCREENSHOT_DIR = os.path.join(LOG_DIR, "screenshots")
MAX_LOG_ENTRIES = int(os.getenv("MAX_LOG_ENTRIES", "1000"))
AGENT_POLL_INTERVAL = float(os.getenv("AGENT_POLL_INTERVAL", "5.0"))  # seconds
