from scapy.layers.inet import IP, TCP
from scapy.all import *


class PortScan:

    def __init__(self):
        # in order: HTTP, FTP, Telnet, SMTP, TFTP, POP3, SNMP
        self._target_ports = [80, 21, 23, 25, 69, 110, 161, 162]
        self.filtered_packets = []

    def packet_filter(self, packet):
        # filters packets to check for TCP packets
        result = ""
        if IP in packet:
            ip_packet = packet[IP]
            if TCP in ip_packet:
                tcp_packet = ip_packet[TCP]
                if tcp_packet.dport in self._target_ports:
                    filtered_packet = f"\nPacket found on port {tcp_packet.dport}: {packet.summary()}"
                    self.filtered_packets.append(filtered_packet)

    def search_for_packets(self):
        sniff(filter="tcp", prn=self.packet_filter, timeout=10)  # change timeout length here to adjust scan time
        result = ""
        for packets in self.filtered_packets:
            result += packets
        if not self.filtered_packets:
            result += "No traffic found on ports 80, 21, 23, 25, 69, 110, 161, 162"
        return result
