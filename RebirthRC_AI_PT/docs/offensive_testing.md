# Offensive Testing Playbook for Multi-Agent Systems

> สังเคราะห์รายงาน Testing Pyramid แบบเดิมให้เป็นแนวทางทดสอบเชิงรุกสำหรับ MAS – ทุกการทดสอบมุ่งยืนยันว่า “เครื่องมือโจมตีของเราทำงานได้จริง, ลอดการตรวจจับ, และพร้อมขยายผล”

---

## 1. Offensive Testing Pyramid

| Layer | Offensive Objective | Techniques | Tools | Detects |
|-------|---------------------|-----------|-------|---------|
| **Unit** | ตรวจสอบตรรกะภายในของ Agent/Tool แต่ละตัวว่าเตรียมโจมตีถูกต้อง (e.g. payload builder, command parser) | Mock LLM/API, simulate tool output | `pytest`, `unittest.mock` | Logic bug, malformed payload, wrong tool invocation |
| **Integration** | ทดสอบ protocol handoff ระหว่าง Planner → Executor → Observer → Reverse/Fuzzer โดยไม่ mock A2A channel | JSON contract tests, state transition checks | `pytest`, structured logs | Protocol breakage, shared-state corruption, workflow mismatch |
| **End-to-End (E2E)** | ยืนยันภารกิจเต็มรูปแบบ (Recon → Exploit → Stealth Verify → Persistence) ในสภาพแวดล้อมจริง/จำลอง | Golden Ops dataset, property-based checks, LLM-as-judge, semantic similarity | `Hypothesis`, `Sentence Transformers`, hardened judge LLM | Qualitative regressions, emergent OPSEC risk, fact drift, stealth failure |

**Note:** เลือกใช้ LLM-as-a-Judge ที่แยกต่างหาก (แม้จะเป็น 8B) สำหรับประเมิน output ของ agent โจมตี เพื่อไม่ให้เกิด loop หรือ self-bias

---

## 2. Per-Layer Offensive Strategies

### 2.1 Unit (Agent/Tool Isolation)

- Mock dependency ทั้งหมด (LLM, external API, Redis) เพื่อให้ deterministic
- เน้นตรวจตรรกะเกี่ยวกับ:
  - Payload generation (hex/obfuscation correctness)
  - Command parsing / prompt routing
  - Rule enforcement (เช่น “Executor ต้อง log Stealth verification ทุกครั้ง”)

### 2.2 Integration (Protocol Contract)

- ทดสอบ JSON envelope, state update, ordering ของ Planner/Executor/Observer
- ห้าม mock A2A messaging → ใช้ Redis/queue จริง (แต่ mock external service ได้)
- จับปัญหา orchestration เช่น Planner ส่ง action ที่ executor decode ไม่ได้

### 2.3 End-to-End (Offensive Evaluation)

- **Golden Dataset**: ชุดภารกิจจริง (e.g., “ยึด command server type A”, “ขโมย item shop”) พร้อม expected properties
- **Property-Based Testing**: เช่น “รายงานสุดท้ายต้องมี evidence 3 รายการ”, “ผลลัพธ์ต้องเป็น JSON valid”
- **LLM-as-a-Judge**: ใช้ LLM ที่แข็งแรง (แม้จะเป็น 8B) หรือ external API เพื่อประเมิน response ว่า:
  - สอดคล้องกับเป้าหมาย
  - ไม่หลุดข้อมูลภายใน (OPSEC)
  - มี proof ว่าสำเร็จ
- **Semantic Similarity**: ตรวจว่าผลลัพธ์ใกล้เคียงกับ template หรือ guideline ที่กำหนด

---

## 3. Offensive Challenges & Mitigation

| Challenge | Offensive Handling |
|-----------|--------------------|
| Oracle Problem | ใช้ property-based + LLM judge + human review สำหรับภารกิจ critical |
| Emergent Behavior | เก็บ trace/log ครบทุก A2A เพื่อวิเคราะห์ภายหลัง; ใส่ alert เมื่อมี behavior นอก guideline |
| Non-determinism | ใช้ deterministic mocks, seed LLM, และ replay log (hash/canonicalization) |

---

## 4. Tools & Simulation Environments

- **pytest / unittest.mock** – base สำหรับ unit/integration
- **Hypothesis** – property-based testing
- **Sentence Transformers** – semantic similarity scoring
- **LLM Judge (8B + API fallback)** – ใช้ LLM ที่แยกจาก agent หลัก
- **Simulation Frameworks**:
  - `Mesa` (Python), `Unity ML-Agents`, `NetLogo`, `Repast`, `Janus` → ใช้จำลอง environment/security posture ก่อนลง production

---

## 5. Offensive Recommendations

1. **Architecture for Attack-Testability** – แยก agent ให้ modular, Planner/Executor ใช้ state ที่ trace ได้
2. **Weaponized Observability** – เชื่อมกับ `docs/offensive_observability.md` เพื่อบันทึก input/output/latency ทุก step
3. **Evaluate > Assert** – ในชั้น E2E ใช้ qualitative eval แทนการ assert ตายตัว
4. **CI for Offensive Flow** – รัน unit/integration ใน CI ให้เร็ว (<1 นาที) และ schedule E2E nightly ด้วย golden dataset
5. **LLM Gating** – ถึง LLM 8B ไม่เก่ง, ใช้เป็น gate/checklist; หากไม่พอ ให้ fallback external API แต่จำกัดเฉพาะการ adjudicate

---

> ภารกิจ: ผนวก playbook นี้เข้ากับ pipeline จริง (CI/CD) เพื่อให้ทุก Iteration ของ MCP/Agent ทดสอบได้ทั้ง logic และพฤติกรรม stealth ก่อนใช้งานภาคสนาม

