from scapy.layers.inet import IP, TCP
from scapy.all import *


class PortScan:

    def __init__(self, file_handle):
        # in order: HTTP, FTP, Telnet, SMTP, TFTP, POP3, SNMP
        self._target_ports = [80, 21, 23, 25, 69, 110, 161, 162]
        self.file_handle = file_handle

    def packet_filter(self, packet):
        # filters packets to check for TCP packets
        result = ""
        if IP in packet:
            ip_packet = packet[IP]
            if TCP in ip_packet:
                tcp_packet = ip_packet[TCP]
                if tcp_packet.dport in self._target_ports:
                    timestamp = datetime.now()
                    filtered_packet = f"\n{timestamp}: Packet found on port {tcp_packet.dport}: {packet.summary()}"
                    self.file_handle.write(filtered_packet)
                    self.file_handle.flush()  # ensures data is written to file immediately

    def search_for_packets(self):
        sniff(filter="tcp", prn=self.packet_filter, timeout=10)  # change timeout length here to adjust scan time
        if self.file_handle.tell() == 0:  # Check if nothing has been written to the file
            timestamp = datetime.now()
            self.file_handle.write(f"{timestamp}: No traffic found on ports 80, 21, 23, 25, 69, 110, 161, 162")
            self.file_handle.flush()
