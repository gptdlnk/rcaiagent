from scapy.all import sniff, send, IP, TCP, UDP
from typing import List, Dict, Any

class NetworkSniffer:
    """
    Handles network packet sniffing and injection using Scapy.
    NOTE: Requires root/admin privileges to run sniff/send functions.
    """
    @staticmethod
    def sniff_packets(count: int = 10, filter_str: str = "host 127.0.0.1") -> List[Dict[str, Any]]:
        """
        Sniffs a specified number of packets.
        :param count: Number of packets to sniff.
        :param filter_str: BPF filter string (e.g., "port 80 and host 192.168.1.1").
        :return: List of dictionaries containing packet summaries.
        """
        print(f"Sniffing {count} packets with filter: {filter_str}")
        packets = sniff(count=count, filter=filter_str, timeout=10)
        
        results = []
        for packet in packets:
            summary = {
                "time": str(packet.time),
                "source": packet[IP].src if IP in packet else "N/A",
                "destination": packet[IP].dst if IP in packet else "N/A",
                "protocol": packet.proto,
                "length": len(packet),
                "payload_hex": packet.payload.original.hex() if packet.payload else ""
            }
            results.append(summary)
            
        return results

    @staticmethod
    def send_packet(target_ip: str, target_port: int, payload_hex: str, protocol: str = "TCP") -> bool:
        """
        Sends a custom packet with a raw payload.
        :param target_ip: Destination IP.
        :param target_port: Destination port.
        :param payload_hex: Raw payload in hexadecimal string format.
        :param protocol: 'TCP' or 'UDP'.
        :return: True if successful, False otherwise.
        """
        try:
            payload_bytes = bytes.fromhex(payload_hex)
            
            if protocol.upper() == "TCP":
                packet = IP(dst=target_ip) / TCP(dport=target_port) / payload_bytes
            elif protocol.upper() == "UDP":
                packet = IP(dst=target_ip) / UDP(dport=target_port) / payload_bytes
            else:
                print(f"Unsupported protocol: {protocol}")
                return False
                
            send(packet, verbose=0)
            print(f"Packet sent to {target_ip}:{target_port} via {protocol}")
            return True
        except Exception as e:
            print(f"Error sending packet: {e}")
            return False

# This tool is crucial for Observer (sniff) and Executor/Fuzzer (send)
