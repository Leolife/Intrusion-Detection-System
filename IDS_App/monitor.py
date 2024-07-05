import datetime
import psutil
import time


class Monitor:

    def monitor_cpu(self, threshold):
        while True:
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > threshold:
                return self.snapshot_processes()

    def snapshot_processes(self):
        result = ""
        processes = {}

        # First pass: collect initial CPU times
        for process in psutil.process_iter(['pid', 'name', 'username', 'memory_percent']):
            try:
                proc = process.as_dict(attrs=['pid', 'name', 'username', 'memory_percent', 'cpu_times'])
                processes[proc['pid']] = proc
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        # Wait for a short interval
        time.sleep(1)

        # Second pass: collect CPU times again and calculate CPU percentage
        for pid in list(processes.keys()):
            try:
                current_proc = psutil.Process(pid)
                current_cpu_times = current_proc.cpu_times()
                cpu_diff = sum(current_cpu_times) - sum(processes[pid]['cpu_times'])
                cpu_percent = cpu_diff * 100
                processes[pid]['cpu_percent'] = cpu_percent
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                processes[pid]['cpu_percent'] = 0  # Process no longer exists or is inaccessible

        # Sorting processes by CPU usage
        sorted_processes = sorted(processes.values(), key=lambda x: x['cpu_percent'], reverse=True)

        timestamp = datetime.datetime.now()

        result += f"Snapshot taken at {timestamp}\n"
        result += f"{'PID':<10} {'Name':<25} {'User':<20} {'CPU%':<10} {'Memory%':<10}\n"  # neatly formatted
        result += "=" * 75 + "\n"
        for proc in sorted_processes:
            result += (f"{proc['pid']:<10} {proc['name']:<25} {proc['username']:<20}"
                       f" {proc['cpu_percent']:<10.2f} {proc['memory_percent']:<10.2f}\n")

        return result
