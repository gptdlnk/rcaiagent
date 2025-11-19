# Offensive Redis Optimization Playbook

> ตีความแนวทางปรับจูน Redis สำหรับระบบกระจายให้เป็นคู่มือโจมตี/บำรุงรักษา command center ของเรา: ลด latency, เพิ่ม throughput, และยืดอายุ backdoor/agent network

---

## 1. Key Findings (Attacker POV)

| Focus | Offensive Objective |
|-------|---------------------|
| Memory Management | เก็บข้อมูลภารกิจ/credential/stealth log ได้มากขึ้นโดยไม่ OOM |
| Efficient Command Usage | ลด latency spike ที่ทำให้โดน Defender สังเกต |
| Scalability Architecture | รองรับ bot/agent จำนวนมาก, ป้องกัน single point of failure |

---

## 2. Offensive Memory Management

- **Use Hashes** for session/object metadata → ใช้ ziplist/listpack ประหยัด 50-70% เทียบกับ string หลาย key  
- **Avoid large JSON blobs**: เก็บ payload ใหญ่ (เช่น exfil data) ใน storage อื่น (S3/minio) แล้วใช้ Redis เป็น index/reference  
- **Compression**: บีบข้อมูลก่อนเก็บ (gzip/lz4) ถ้า CPU เอื้อ  
- **TTL & Eviction**: 
  - ใส่ TTL ให้ key ชั่วคราวทุกตัว (Recon cache, temp token)  
  - เลือก eviction policy ให้เหมาะ: `volatile-lru` สำหรับ cache, `allkeys-lru` เมื่อทุก key ต้อง evict ได้  
  - หลีกเลี่ยง `noeviction` (จะ error เมื่อเต็ม)  
- **Fragmentation Control**: 
  - monitor `mem_fragmentation_ratio`, ใช้ `MEMORY PURGE` หลังลบ batch ใหญ่  
  - หลีกเลี่ยงการเขียน big value บ่อย ๆ

---

## 3. Command Usage Guidelines

- ห้ามใช้ `KEYS`/`HGETALL` (ไม่มี limit) – ใช้ `SCAN`/range มีขอบเขตแทน  
- Monitor big/hot keys (`redis-cli --bigkeys`, `--hotkeys`) เพื่อลด hotspot  
- ใช้ `UNLINK` แทน `DEL` เพื่อไม่ block event loop เมื่อถอนข้อมูลขนาดใหญ่

---

## 4. Distributed Patterns

### 4.1 Connection & Pipelining
- ใช้ connection pooling เสมอ (ลด RTT)  
- ใช้ pipelining สำหรับ batch commands (record/log) เพื่อประหยัด network trips  
- วาง Redis ใกล้ Agent host เพื่อลด latency

### 4.2 Scalability & Sharding
- ใช้ Redis Cluster/Sharding เพื่อกระจายโหลด agent  
- Balance shard ป้องกัน hot node (watch big keys)  
- Replication (master/replica) เพื่อเพิ่ม read throughput และ fault tolerance  
- ทำ persistence/backup บน replica เพื่อลด latency master

---

## 5. Tooling

| Tool | Use |
|------|-----|
| `redis-cli`, `--bigkeys`, `--hotkeys` | Find problematic keys |
| `INFO memory`, `MEMORY USAGE` | Inspect memory/fragmentation |
| `CONFIG SET slowlog...` | Capture slow commands |
| Redis Insight, Prometheus/Grafana | Monitor usage/latency |

---

## 6. Offensive Recommendations

1. **Design data model up front** – Hash per object, avoid storing unused payloads.  
2. **TTL by default** – all temp cache/log entries expire automatically.  
3. **Enable slowlog** – detect heavy commands that might expose us.  
4. **Connection pooling + pipelining** – enforce in all agent tooling (executor/observer).  
5. **Continuous monitoring** – alert on `mem_fragmentation_ratio`, total memory, latency.  
6. **UNLINK over DEL** – prevent blocking when clearing traces.  
7. **Consider Redis Cluster** – if mission needs > single node throughput/memory.  
8. **Disable swapping** – ensure Linux swap off to avoid latency spikes.

---

> ทำให้ command center เราลื่นไหล: ลด footprint, ปรับตัวเมื่อโดน stress, และเตรียมพร้อม scale ให้ agent ทำงานต่อเนื่องโดยไม่โดน Defender มองเห็นจาก latency ที่ผิดปกติ

