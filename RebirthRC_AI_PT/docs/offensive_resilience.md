# Offensive Resilience & Failure Playbook

> เปลี่ยนรายงาน “error handling/resilience” ให้เป็นคู่มือเพิ่มความยืดหยุ่นให้ฝั่งโจมตี – เน้นการคาดการณ์ countermeasure, ฟื้นตัวไว, และรักษา control channel ต่อเนื่อง

---

## 1. Offensive Principles

| Defensive Principle | Offensive Interpretation | Action |
|---------------------|--------------------------|--------|
| **Anticipatory Design** | คาดการณ์ว่าฝ่ายป้องกันจะตัดเราอย่างไร แล้ววาง failure mode ไว้ล่วงหน้า | ทำ FMEA สำหรับแต่ละภารกิจ (API quota, process kill, packet drop) พร้อม code path สำรอง |
| **Graceful Degradation** | เมื่อโดนตัด resource ให้ลดระดับการโจมตี (stealth mode) แทนที่จะหยุดทั้งหมด | Prioritize core functions (command shell, persistence) และสลับ payload/LLM ขนาดเล็ก |
| **Fault Tolerance** | ทำ redundancy เชิงกลยุทธ์ (agent สำรอง, command channel สำรอง) | ใช้หลากหลาย protocol/algorithm (HTTP/TCP/raw) และ distributed processing |
| **Self-Healing** | ให้ agent ตรวจจับ error แล้วรีสตาร์ท/ย้ายเซิร์ฟอัตโนมัติ | Script recovery routine (restart game client, switch proxy, re-seed planner) |
| **Human-in-the-Loop** | สำหรับงาน critical ให้ escalate ถึง operator เพื่อสั่งการใหม่ | สร้าง escalation path + dashboard ที่แสดงสถานะ backdoor/verification |

---

## 2. Offensive Resilience Patterns

| Pattern | Offensive Usage |
|---------|-----------------|
| **Circuit Breaker** | กันไม่ให้ Executor/Planner call API ภายนอกซ้ำเมื่อโดน rate limit – ป้องกันฝั่งเราถูกปิดบัญชี |
| **Retry (Exponential Backoff)** | ยิงคำสั่งซ้ำแบบมีจังหวะ เพื่อเลี่ยงการตรวจจับ (burst → backoff) |
| **Timeout** | ตัดการรอ LLM/tool ที่ค้างก่อนจะเผยตัว สลับไปใช้ cache/โมเดลเล็ก |
| **Fallback** | หากโมเดลหลักล้มเหลวสลับไปใช้ 8B หรือ response template ที่เตรียมไว้ |
| **Rate Limiting** | จำกัด self-traffic ของ botnet เพื่อไม่ให้ provider สงสัย / ป้องกัน DOS ฝั่งเราเอง |

---

## 3. Offensive Tooling

| Category | Tool | Offensive Role |
|----------|------|----------------|
| Resilience Lib | Hystrix / Resilience4j (หรือ replica ใน Python) | Implement circuit breaker/retry/fallback logic ใน Executor/Planner |
| Chaos Engineering | Chaos Mesh, Harness, custom chaos scripts | ฉีดความล้มเหลว (ปิด proxy, reset Redis, random packet drop) เพื่อฝึก self-healing |
| Static Analysis | DeepCode, Ruff, Semgrep | หา bug ที่ทำให้ agent ล่มก่อน deploy |
| Monitoring/Telemetry | Prometheus, Grafana, custom dashboards | ติดตาม MTTR, stealth mode status, error amplification |

---

## 4. Offensive Recommendations

1. **Intelligent Fallbacks** – แทน error เฉย ๆ ให้ส่ง response ที่ยังคงหลักฐาน/สั่งงานต่อ (เช่น สร้าง “delayed plan” หรือ “local exploit mode”)  
2. **Chaos Drills** – จำลอง rate-limit, API failure, packet loss เป็นประจำเพื่อแน่ใจว่า agent ย้ายช่องทางได้  
3. **Resilience Metrics** – ติดตาม MTTR ของ command channel, ขนาด error propagation (Error Amplification Factor)  
4. **Failure Learning Cycle** – ทำ post-mortem ทุกครั้งที่เกิด infiltration fail และอัปเดต blueprint (blameless)  
5. **Contextual Error Management** – จัดลำดับการแก้ไขตามผลกระทบ (เช่น backdoor ช่องหลัก vs recon bot)  

---

> เป้าหมาย: ให้ MAS ฝั่งโจมตียังคงปฏิบัติการได้แม้เจอ countermeasure หรือ resource limit – ทุก agent ต้องรู้ว่าจุด fallback/kill-switch อยู่ตรงไหนและสามารถรีสตาร์ทตัวเองโดยไม่รบกวนภารกิจหลัก

