import platform
from scapy.all import sniff, send, IP, TCP, UDP, conf
from typing import List, Dict, Any, Optional
from config import GAME_CONFIG

class NetworkSniffer:
    """
    Handles network packet sniffing and injection using Scapy.
    NOTE: Requires root/admin privileges to run sniff/send functions on most systems.
    On Windows, may require Npcap or WinPcap to be installed.
    """
    
    @staticmethod
    def _check_permissions() -> bool:
        """Check if we have sufficient permissions for packet operations."""
        try:
            # Try to get network interfaces (requires privileges)
            if platform.system() == 'Windows':
                # On Windows, check if Npcap/WinPcap is available
                try:
                    interfaces = conf.ifaces
                    return len(interfaces) > 0
                except:
                    return False
            else:
                # On Linux/Unix, we need root
                import os
                return os.geteuid() == 0
        except:
            return False
    
    @staticmethod
    def sniff_packets(count: int = 10, filter_str: str = None, timeout: int = 10) -> List[Dict[str, Any]]:
        """
        Sniffs a specified number of packets.
        :param count: Number of packets to sniff.
        :param filter_str: BPF filter string (e.g., "port 80 and host 192.168.1.1").
                          If None, uses game server IP/port from config.
        :param timeout: Timeout in seconds.
        :return: List of dictionaries containing packet summaries.
        """
        # Use game server config if filter not provided
        if filter_str is None:
            game_ip = GAME_CONFIG.get('GAME_SERVER_IP', '')
            game_port = GAME_CONFIG.get('GAME_SERVER_PORT', 7777)
            if game_ip:
                filter_str = f"host {game_ip} and port {game_port}"
            else:
                filter_str = "tcp port 7777"  # Default fallback
        
        print(f"Sniffing {count} packets with filter: {filter_str}")
        
        if not NetworkSniffer._check_permissions():
            print("Warning: May not have sufficient permissions for packet sniffing.")
            print("On Windows: Install Npcap. On Linux: Run with sudo.")
        
        try:
            packets = sniff(count=count, filter=filter_str, timeout=timeout, store=True)
            
            results = []
            for packet in packets:
                try:
                    summary = {
                        "time": str(packet.time),
                        "source": packet[IP].src if IP in packet else "N/A",
                        "destination": packet[IP].dst if IP in packet else "N/A",
                        "protocol": packet.proto if hasattr(packet, 'proto') else "N/A",
                        "length": len(packet),
                        "payload_hex": ""
                    }
                    
                    # Safely extract payload
                    if hasattr(packet, 'payload') and packet.payload:
                        try:
                            if hasattr(packet.payload, 'original'):
                                summary["payload_hex"] = packet.payload.original.hex()
                            elif hasattr(packet.payload, 'load'):
                                summary["payload_hex"] = bytes(packet.payload.load).hex()
                        except:
                            pass
                    
                    # Add port information if available
                    if TCP in packet:
                        summary["src_port"] = packet[TCP].sport
                        summary["dst_port"] = packet[TCP].dport
                    elif UDP in packet:
                        summary["src_port"] = packet[UDP].sport
                        summary["dst_port"] = packet[UDP].dport
                    
                    results.append(summary)
                except Exception as e:
                    print(f"Error processing packet: {e}")
                    continue
            
            print(f"Successfully captured {len(results)} packets.")
            return results
            
        except PermissionError:
            print("Error: Permission denied. Run with administrator/root privileges.")
            return []
        except Exception as e:
            print(f"Error sniffing packets: {e}")
            return []

    @staticmethod
    def send_packet(target_ip: str, target_port: int, payload_hex: str, protocol: str = "TCP", 
                   src_port: Optional[int] = None) -> bool:
        """
        Sends a custom packet with a raw payload.
        :param target_ip: Destination IP.
        :param target_port: Destination port.
        :param payload_hex: Raw payload in hexadecimal string format.
        :param protocol: 'TCP' or 'UDP'.
        :param src_port: Optional source port (for TCP/UDP).
        :return: True if successful, False otherwise.
        """
        if not target_ip or not target_port:
            print("Error: target_ip and target_port are required.")
            return False
        
        try:
            # Validate and convert hex payload
            try:
                payload_bytes = bytes.fromhex(payload_hex.replace(' ', '').replace('-', ''))
            except ValueError as e:
                print(f"Error: Invalid hex payload: {e}")
                return False
            
            # Build packet based on protocol
            if protocol.upper() == "TCP":
                if src_port:
                    packet = IP(dst=target_ip) / TCP(sport=src_port, dport=target_port) / payload_bytes
                else:
                    packet = IP(dst=target_ip) / TCP(dport=target_port) / payload_bytes
            elif protocol.upper() == "UDP":
                if src_port:
                    packet = IP(dst=target_ip) / UDP(sport=src_port, dport=target_port) / payload_bytes
                else:
                    packet = IP(dst=target_ip) / UDP(dport=target_port) / payload_bytes
            else:
                print(f"Error: Unsupported protocol: {protocol}. Use 'TCP' or 'UDP'.")
                return False
            
            # Send packet
            send(packet, verbose=0)
            print(f"Packet sent successfully: {len(payload_bytes)} bytes to {target_ip}:{target_port} via {protocol}")
            return True
            
        except PermissionError:
            print("Error: Permission denied. Run with administrator/root privileges.")
            return False
        except Exception as e:
            print(f"Error sending packet: {e}")
            return False

# This tool is crucial for Observer (sniff) and Executor/Fuzzer (send)
