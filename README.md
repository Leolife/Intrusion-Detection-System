# Intrusion-Detection-System
Homebrewed intrusion detection system to bypass logic checks in malware that check for common malware analysis and monitoring tools.

## Features
- CPU monitor that takes snapshot of running processes if CPU usage reaches a default threshold of 80%
  - threshold can be changed in main.py on line 58
- Process checker that accepts text file with list of processes to see if they are being ran.
- Port scanning to check for traffic on insecure ports:
  - HTTP: port 80
  - FTP: port 21
  - Telnet: port 23
  - SMTP: port 25
  - TFTP: port 69
  - POP3: port 110
  - SNMP: port 161/162
- Results of any feature will be printed onto a file in a directory of your choice (can be input during runtime of program)

## Setup & Run Instructions
- **If you have not changed anything, locate line 25 of port_scan.py and change the timeout length to desired scan time length**
- This script needs to be run as root in order to access raw sockets for port scanning purposes.  In order to accomplish this, do the following:
  1) On your command line, go to the your folder containing the this Intrusion-Detection-System python files
  2) Install '[scapy](https://github.com/secdev/scapy)' library for python in sudo with following command:
     - sudo pip install scapy
  3) Run main.py as root with the following command:
     - sudo python3 main.py
