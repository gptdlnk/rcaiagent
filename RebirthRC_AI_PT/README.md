# Rebirth RC AI Offensive Security Tool

ระบบ AI Multi-Agent สำหรับการค้นหาช่องโหว่ในเกม Rebirth RC โดยใช้ AI Agents หลายตัวทำงานร่วมกันผ่าน Redis Blackboard Architecture

## 📋 สารบัญ

- [ภาพรวม](#ภาพรวม)
- [สถาปัตยกรรม](#สถาปัตยกรรม)
- [การติดตั้ง](#การติดตั้ง)
- [การตั้งค่า](#การตั้งค่า)
- [การใช้งาน](#การใช้งาน)
- [โครงสร้างโปรเจกต์](#โครงสร้างโปรเจกต์)
- [การทดสอบ](#การทดสอบ)
- [การแก้ปัญหา](#การแก้ปัญหา)

## 🎯 ภาพรวม

โปรเจกต์นี้เป็นระบบ AI-Driven Offensive Security Tool ที่ใช้ Multi-Agent System เพื่อค้นหา Logic Flaws และช่องโหว่ในเกม Rebirth RC โดยอัตโนมัติ

### คุณสมบัติหลัก

- **Multi-Agent Architecture**: ใช้ AI Agents 5 ตัวทำงานร่วมกัน
- **Redis Blackboard**: ใช้ Redis เป็น Central Data Hub สำหรับการสื่อสารระหว่าง Agents
- **MCP RoleEngine (No External API)**: ระบบตัดสินใจภายในผ่าน RoleEngine โดยไม่ต้องพึ่งพาโมเดลภายนอก
- **Automated Reconnaissance**: ดักจับและวิเคราะห์ Network Traffic อัตโนมัติ
- **Reverse Engineering**: วิเคราะห์ Binary และ Protocol Structure
- **Automated Fuzzing**: สร้างและส่ง Payload ที่ผิดปกติเพื่อค้นหาช่องโหว่
- **Error Recovery**: ระบบสามารถกู้คืนจากข้อผิดพลาดได้อัตโนมัติ

## 🏗️ สถาปัตยกรรม

### AI Agents

| Agent | บทบาท | MCP Objectives | ตัวอย่างผลลัพธ์ |
|-------|--------|----------------|------------------|
| **Planner** | Strategic Brain | สร้าง action plan จาก observations, จัดการ error | JSON action สำหรับ Executor / Observer / Reverse / Fuzzer |
| **Executor** | Action Runner | แปลงแผนเป็นคำสั่ง terminal/game/network | รายงานผลการรันคำสั่งกลับไปที่ Redis |
| **Observer** | Real-time Monitor | สรุป anomaly จาก packet log และแจ้ง Planner | LOG: `NETWORK_SUMMARY` |
| **Reverse Engineer** | Code Analyst | สร้างคำสั่งวิเคราะห์ binary และสรุป protocol | LOG: `RE_RAW_RESULT`, `RE_KNOWLEDGE` |
| **Fuzzer** | Payload Generator | สร้าง payload ผิดปกติจากความรู้ล่าสุด | LOG: `FUZZ_RESULT` + JSON payload |

### System Flow

```
Orchestrator
    ↓
Redis (Blackboard)
    ↓
┌─────────────────────────────────────┐
│  Observer → Planner → Executor      │
│  Reverse Engineer → Fuzzer          │
└─────────────────────────────────────┘
```

## 📦 การติดตั้ง

### ความต้องการของระบบ

- Python 3.8 หรือสูงกว่า
- Redis Server
- Windows หรือ Linux
- API Keys: OpenAI API Key (จำเป็น), 5 Hihg API Key (ไม่บังคับ)

### ขั้นตอนการติดตั้ง

1. **Clone หรือดาวน์โหลดโปรเจกต์**

```bash
cd rcaiagent/RebirthRC_AI_PT
```

2. **ติดตั้ง Dependencies**

```bash
pip install -r requirements.txt
```

3. **ติดตั้ง Redis**

**Windows:**
- ดาวน์โหลด Redis for Windows จาก [GitHub](https://github.com/microsoftarchive/redis/releases)
- หรือใช้ WSL: `wsl sudo apt-get install redis-server`

**Linux:**
```bash
sudo apt-get update
sudo apt-get install redis-server
sudo systemctl start redis-server
```

4. **ตั้งค่า Environment Variables**

```bash
# คัดลอกไฟล์ตัวอย่าง
cp .env.example .env

# แก้ไขไฟล์ .env และใส่ API Keys ของคุณ
nano .env  # หรือใช้ text editor อื่น
```

## ⚙️ การตั้งค่า

### 1. ตั้งค่า API Keys

แก้ไขไฟล์ `.env`:

```env
OPENAI_API_KEY=sk-your-actual-key-here
HIHG_API_KEY=your-hihg-key-here  # Optional
```

### 2. ตั้งค่า Game Path

โปรเจกต์นี้มาพร้อมกับไฟล์เกมที่จำเป็น:
- **RebirthClient.exe**: ไฟล์เกมหลัก (อยู่ในโฟลเดอร์โปรเจกต์)
- **RebithPatcher.lnk**: Shortcut ไปที่ `C:\RebirthRC\content\RebirthRC.exe`

ระบบจะใช้ `RebirthClient.exe` เป็นค่าเริ่มต้น หากไม่พบจะลองใช้ alternative path

แก้ไขไฟล์ `.env` หรือ `config.py` (ถ้าต้องการใช้ path อื่น):

```env
# ใช้ RebirthClient.exe ในโฟลเดอร์โปรเจกต์ (ค่าเริ่มต้น)
# GAME_PATH=./RebirthClient.exe

# หรือใช้ path จาก RebithPatcher.lnk
# GAME_PATH=C:\RebirthRC\content\RebirthRC.exe

# หรือใช้ path อื่น
# GAME_PATH=C:\Program Files\RebirthRC\RebirthRC.exe

GAME_PROCESS_NAME=RebirthClient.exe
GAME_SERVER_IP=192.168.1.100  # ถ้ารู้ IP ของเกมเซิร์ฟเวอร์
GAME_SERVER_PORT=7777
```

### 3. ตั้งค่า Redis

ถ้า Redis ทำงานบนเครื่องอื่นหรือพอร์ตอื่น:

```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

### 4. ตั้งค่า AI Models

แก้ไขโมเดลที่ต้องการใช้ใน `.env`:

```env
PLANNER_MODEL=gpt-4-turbo-preview
EXECUTOR_MODEL=gpt-3.5-turbo-instruct
OBSERVER_MODEL=gpt-3.5-turbo
REVERSE_ENGINEER_MODEL=gpt-3.5-turbo-instruct
FUZZER_MODEL=gpt-3.5-turbo
```

## 🚀 การใช้งาน

### 1. เริ่มต้น Redis Server

**Windows:**
```bash
redis-server
```

**Linux:**
```bash
sudo systemctl start redis-server
# หรือ
redis-server
```

### 2. รัน Game Client

เปิดเกม Rebirth RC และเข้าสู่ระบบด้วยตัวเอง (ตามที่คุณทำได้แล้ว)

### 3. เริ่มต้น AI System

```bash
python main.py
```

ระบบจะทำการตรวจสอบ prerequisites และเริ่มต้น Agents ทั้งหมด

### 4. ตรวจสอบสถานะ

ระบบจะแสดงสถานะทุก 5 วินาที:

```
[ORCHESTRATOR] STATE: DEEP_RECONNAISSANCE | ACTIONS:   0 | VULNS:  0 | ERROR: NO
```

### 5. หยุดระบบ

กด `Ctrl+C` เพื่อหยุดระบบอย่างปลอดภัย

## 📁 โครงสร้างโปรเจกต์

```
RebirthRC_AI_PT/
├── agents/                  # AI Agents
│   ├── __init__.py
│   ├── base_agent.py        # Base class สำหรับ Agents
│   ├── planner_agent.py     # Strategic Planner (GPT)
│   ├── executor_agent.py    # Code Executor (Codex)
│   ├── observer_agent.py    # Network Observer (5 Hihg)
│   ├── reverse_agent.py     # Reverse Engineer (Codex)
│   └── fuzzer_agent.py      # Payload Fuzzer (5 Hihg)
├── data_hub/                # Redis Manager
│   ├── __init__.py
│   └── redis_manager.py     # Central Data Hub
├── tools/                   # Utility Tools
│   ├── __init__.py
│   ├── terminal_wrapper.py  # Shell command executor
│   ├── game_client_control.py  # Game automation
│   └── network_sniffer.py  # Packet capture/injection
├── logs/                    # Logs and screenshots
│   └── screenshots/
├── main.py                  # Orchestrator & Entry point
├── config.py                # System configuration
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
└── README.md               # This file
```

## 🧪 การทดสอบ

### ทดสอบ Redis Connection

```python
from data_hub.redis_manager import RedisManager
from config import REDIS_CONFIG

redis_manager = RedisManager(REDIS_CONFIG)
print(f"State: {redis_manager.get_state()}")
```

### ทดสอบ Game Client Control

```python
from tools.game_client_control import GameClientControl

# ตรวจสอบว่าเกมกำลังรันอยู่หรือไม่
if GameClientControl.is_game_running():
    print("Game is running!")
else:
    print("Game is not running.")
```

### ทดสอบ Network Sniffer

**หมายเหตุ:** ต้องรันด้วยสิทธิ์ Administrator/Root

```python
from tools.network_sniffer import NetworkSniffer

packets = NetworkSniffer.sniff_packets(count=5, filter_str="tcp port 7777")
print(f"Captured {len(packets)} packets")
```

## 🔧 การแก้ปัญหา

### Redis Connection Error

**ปัญหา:** `Error connecting to Redis`

**วิธีแก้:**
1. ตรวจสอบว่า Redis กำลังรันอยู่: `redis-cli ping` (ควรได้ `PONG`)
2. ตรวจสอบ HOST และ PORT ใน config
3. ตรวจสอบ Firewall settings

### API Key Error

**ปัญหา:** `AI Model API call failed`

**วิธีแก้:**
1. ตรวจสอบว่า API Key ถูกตั้งค่าใน `.env` แล้ว
2. ตรวจสอบว่า API Key ถูกต้องและยังใช้งานได้
3. ตรวจสอบ Network connection

### Permission Denied (Network Sniffer)

**ปัญหา:** `Permission denied` เมื่อใช้ Network Sniffer

**วิธีแก้:**
- **Windows:** ติดตั้ง Npcap หรือ WinPcap
- **Linux:** รันด้วย `sudo python main.py`

### Game Not Found

**ปัญหา:** `Game executable not found`

**วิธีแก้:**
1. ตรวจสอบ `GAME_PATH` ใน `.env` หรือ `config.py`
2. ตรวจสอบว่า path ถูกต้องและไฟล์มีอยู่จริง
3. ใช้ absolute path แทน relative path

## 📝 หมายเหตุสำคัญ

1. **สิทธิ์การใช้งาน:** ใช้เครื่องมือนี้เฉพาะในสภาพแวดล้อมที่ได้รับอนุญาตเท่านั้น
2. **Network Sniffing:** ต้องมีสิทธิ์ Administrator/Root
3. **API Costs:** การใช้ AI Models อาจมีค่าใช้จ่าย ตรวจสอบ pricing ของ API provider
4. **Game Server:** อย่าใช้เครื่องมือนี้กับเกมเซิร์ฟเวอร์จริงโดยไม่ได้รับอนุญาต

## 🤝 การสนับสนุน

หากพบปัญหาหรือต้องการความช่วยเหลือ:
1. ตรวจสอบ Logs ใน `logs/` directory
2. ตรวจสอบ Redis keys: `redis-cli KEYS "*"`
3. ตรวจสอบ Error messages ใน console output

## 📄 License

โปรเจกต์นี้เป็นตัวอย่างสำหรับการศึกษาและวิจัยเท่านั้น

---

**สร้างโดย:** AI Development Team  
**เวอร์ชัน:** 1.0.0  
**อัปเดตล่าสุด:** 2025

