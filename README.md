# Intrusion-Detection-System
Intrusion detection system to bypass logic checks in malware that check for common malware analysis and monitoring tools.  Anomaly detection is used in attempt to detect fileless malware.

## Features
- CPU, GPU, network, and memory usage monitor that uses machine learning (Isolation Forest algorithm) to detect anomalies in their usage and upon detection will log running processes and 
system metrics for further forensic analysis
- Real time port scanning to check for traffic on insecure ports:
  - HTTP: port 80
  - FTP: port 21
  - Telnet: port 23
  - SMTP: port 25
  - TFTP: port 69
  - POP3: port 110
  - SNMP: port 161/162
- Process checker that accepts text file with list of processes to see if they are being ran.
- Results of any feature to be printed onto a file in a directory of your choice (can be input during runtime of program)

## Setup & Run Instructions
- **If you have not changed anything, locate line 26 of port_scan.py and change the timeout length to desired scan time length**
- This script needs to be run as root in order to access raw sockets for port scanning purposes and for CPU monitoring.  In order to accomplish this, do the following:
  1) On your command line, go to the your folder containing the this Intrusion-Detection-System python files
  2) Install '[scapy](https://github.com/secdev/scapy)', '[pandas](https://github.com/pandas-dev/pandas)', '[scikit-learn](https://github.com/scikit-learn/scikit-learn)', '[pynvml](https://github.com/gpuopenanalytics/pynvml)',
libraries for python in sudo with following commands:
     - sudo pip install scapy
     - sudo pip install pandas
     - sudo pip install scikit-learn
     - sudo pip install pynvml
  3) Run main.py as root with the following command:
     - sudo python3 main.py
