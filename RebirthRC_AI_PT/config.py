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
# Game Client Files:
# - RebirthClient.exe: Main game client executable (located in project directory)
# - RebithPatcher.lnk: Shortcut to game launcher (points to C:\RebirthRC\content\RebirthRC.exe)

# Get the directory where this config file is located
_CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))

GAME_CONFIG = {
    # Primary game executable path (check local directory first, then environment variable, then default)
    "GAME_PATH": os.getenv("GAME_PATH", os.path.join(_CONFIG_DIR, "RebirthClient.exe")),
    # Alternative game path from shortcut (RebithPatcher.lnk points to this)
    "GAME_ALTERNATIVE_PATH": os.getenv("GAME_ALTERNATIVE_PATH", "C:\\RebirthRC\\content\\RebirthRC.exe"),
    "GAME_LOG_PATH": os.getenv("GAME_LOG_PATH", "C:\\Users\\%USERNAME%\\Documents\\RebirthRC\\logs\\"),  # Windows path example
    "GAME_PROCESS_NAME": os.getenv("GAME_PROCESS_NAME", "RebirthClient.exe"),  # Updated to match actual executable
    "GAME_PATCHER_LNK": os.path.join(_CONFIG_DIR, "RebithPatcher.lnk"),  # Patcher shortcut
    "NMAP_SCAN_RANGE": os.getenv("NMAP_SCAN_RANGE", "192.168.1.0/24"),
    "PROXY_SERVER": os.getenv("PROXY_SERVER", "http://127.0.0.1:8080"),  # สำหรับการดักจับ Traffic (เช่น Burp Suite/mitmproxy)
    "GAME_SERVER_IP": os.getenv("GAME_SERVER_IP", ""),  # IP ของเกมเซิร์ฟเวอร์ (ถ้ารู้)
    "GAME_SERVER_PORT": int(os.getenv("GAME_SERVER_PORT", "7777"))  # Port ของเกมเซิร์ฟเวอร์
}

# 3. โหมดการทำงานของระบบ AI (MCP vs External API)
USE_MCP = os.getenv("USE_MCP", "true").lower() == "true"

# 4. โปรไฟล์บทบาทสำหรับ MCP
ROLE_PROFILES = {
    "PLANNER": {
        "objectives": [
            "กำหนดขั้นตอนถัดไปสู่ช่องโหว่ logic flaw",
            "รักษาความต่อเนื่องของ flow และจัดการ error"
        ],
        "fallback_actions": ["CAPTURE_TRAFFIC", "ANALYSE"]
    },
    "OBSERVER": {
        "objectives": [
            "ตรวจจับความผิดปกติใน packet",
            "แจ้งเตือน planner เมื่อพบ anomaly"
        ]
    },
    "REVERSE": {
        "objectives": [
            "วิเคราะห์ binary/packet handler",
            "จัดทำ protocol structure"
        ]
    },
    "FUZZER": {
        "objectives": [
            "สร้าง payload ผิดปกติ",
            "กระตุ้น logic flaw / buffer overflow"
        ]
    }
}

# 5. การตั้งค่า (Legacy) API Keys - เผื่อสลับกลับไปใช้ภายนอกภายหลัง
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
HIHG_API_KEY = os.getenv("HIHG_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")  # สำหรับ custom endpoints
HIHG_BASE_URL = os.getenv("HIHG_BASE_URL", "")  # สำหรับ 5 Hihg API endpoint

# 6. การตั้งค่า AI Agent (Attacker) และการจัดสรรโมเดล
# หาก USE_MCP = True ระบบจะใช้ RoleEngine แทน API ภายนอก

AGENTS = {
    "PLANNER": {
        "NAME": "AI Planner",
        "MODEL": os.getenv("PLANNER_MODEL", "mcp-planner"),
        "TEMPERATURE": float(os.getenv("PLANNER_TEMPERATURE", "0.2")),
        "SYSTEM_PROMPT": "Planner role in MCP.",
        "API_KEY": OPENAI_API_KEY,
        "BASE_URL": OPENAI_BASE_URL,
        "USE_MCP": USE_MCP
    },
    "EXECUTOR": {
        "NAME": "AI Executor",
        "MODEL": os.getenv("EXECUTOR_MODEL", "mcp-executor"),
        "TEMPERATURE": float(os.getenv("EXECUTOR_TEMPERATURE", "0.1")),
        "SYSTEM_PROMPT": "Executor role in MCP.",
        "API_KEY": OPENAI_API_KEY,
        "BASE_URL": OPENAI_BASE_URL,
        "USE_MCP": USE_MCP
    },
    "OBSERVER": {
        "NAME": "AI Observer",
        "MODEL": os.getenv("OBSERVER_MODEL", "mcp-observer"),
        "TEMPERATURE": float(os.getenv("OBSERVER_TEMPERATURE", "0.0")),
        "SYSTEM_PROMPT": "Observer role in MCP.",
        "API_KEY": HIHG_API_KEY if HIHG_API_KEY else OPENAI_API_KEY,
        "BASE_URL": HIHG_BASE_URL if HIHG_BASE_URL else OPENAI_BASE_URL,
        "USE_MCP": USE_MCP
    },
    "REVERSE_ENGINEER": {
        "NAME": "AI Reverse Engineer",
        "MODEL": os.getenv("REVERSE_ENGINEER_MODEL", "mcp-reverse"),
        "TEMPERATURE": float(os.getenv("REVERSE_ENGINEER_TEMPERATURE", "0.3")),
        "SYSTEM_PROMPT": "Reverse engineer role in MCP.",
        "API_KEY": OPENAI_API_KEY,
        "BASE_URL": OPENAI_BASE_URL,
        "USE_MCP": USE_MCP
    },
    "FUZZER": {
        "NAME": "AI Fuzzer",
        "MODEL": os.getenv("FUZZER_MODEL", "mcp-fuzzer"),
        "TEMPERATURE": float(os.getenv("FUZZER_TEMPERATURE", "0.9")),
        "SYSTEM_PROMPT": "Fuzzer role in MCP.",
        "API_KEY": HIHG_API_KEY if HIHG_API_KEY else OPENAI_API_KEY,
        "BASE_URL": HIHG_BASE_URL if HIHG_BASE_URL else OPENAI_BASE_URL,
        "USE_MCP": USE_MCP
    }
}

# 7. การตั้งค่าทั่วไป
LOG_DIR = os.getenv("LOG_DIR", "logs")
SCREENSHOT_DIR = os.path.join(LOG_DIR, "screenshots")
MAX_LOG_ENTRIES = int(os.getenv("MAX_LOG_ENTRIES", "1000"))
AGENT_POLL_INTERVAL = float(os.getenv("AGENT_POLL_INTERVAL", "5.0"))  # seconds
