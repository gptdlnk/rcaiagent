# config.py: การตั้งค่าระบบและโมเดล AI

# 1. การตั้งค่า Redis (Central Data Hub)
REDIS_CONFIG = {
    "HOST": "localhost",
    "PORT": 6379,
    "DB": 0
}

# 2. การตั้งค่าเกมและเครื่องมือ
GAME_CONFIG = {
    "GAME_PATH": "/path/to/RebirthRC.exe",  # **ต้องแก้ไข**
    "GAME_LOG_PATH": "/path/to/game/logs/", # **ต้องแก้ไข**
    "NMAP_SCAN_RANGE": "192.168.1.0/24",
    "PROXY_SERVER": "http://127.0.0.1:8080" # สำหรับการดักจับ Traffic (เช่น Burp Suite/mitmproxy)
}

# 3. การตั้งค่า AI Agent (Attacker) และการจัดสรรโมเดล
# โมเดลที่คุณมี: GPT, Codex, 5 Hihg
# การจัดสรร: GPT (Planner), Codex (Executor/RE), 5 Hihg (Observer/Fuzzer)

AGENTS = {
    "PLANNER": {
        "NAME": "AI Planner (GPT)",
        "MODEL": "GPT_MODEL_NAME", # เช่น gpt-4-turbo, gemini-2.5-pro
        "TEMPERATURE": 0.7,
        "SYSTEM_PROMPT": "You are the strategic brain. Analyze observations and create the next step plan in natural language."
    },
    "EXECUTOR": {
        "NAME": "AI Executor (Codex)",
        "MODEL": "CODEX_MODEL_NAME", # เช่น gpt-3.5-turbo-instruct (สำหรับโค้ดสั้นๆ)
        "TEMPERATURE": 0.1,
        "SYSTEM_PROMPT": "You are the coder. Convert the Planner's natural language plan into executable Python code or shell commands. Your output MUST be only the code block."
    },
    "OBSERVER": {
        "NAME": "AI Observer (5 Hihg)",
        "MODEL": "5_HIHG_MODEL_NAME", # โมเดลความเร็วสูง
        "TEMPERATURE": 0.0,
        "SYSTEM_PROMPT": "You are the real-time monitor. Analyze raw network traffic and logs, then summarize critical findings for the Planner."
    },
    "REVERSE_ENGINEER": {
        "NAME": "AI Reverse Engineer (Codex)",
        "MODEL": "CODEX_MODEL_NAME",
        "TEMPERATURE": 0.3,
        "SYSTEM_PROMPT": "You are the code analyst. Analyze game binaries and decompile code to extract game logic and protocol structures."
    },
    "FUZZER": {
        "NAME": "AI Fuzzer (5 Hihg)",
        "MODEL": "5_HIHG_MODEL_NAME",
        "TEMPERATURE": 0.9, # High temperature for creative, random payloads
        "SYSTEM_PROMPT": "You are the payload generator. Create large volumes of abnormal and creative data packets based on known protocol structures."
    }
}

# 4. การตั้งค่า API (ตัวอย่าง)
# แนะนำให้ใช้ Environment Variables สำหรับ API Key
# import os
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# HIHG_API_KEY = os.getenv("HIHG_API_KEY")
