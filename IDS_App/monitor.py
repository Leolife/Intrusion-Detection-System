import datetime
import psutil


class Monitor:

    def monitor_cpu(self, threshold):
        while True:
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > threshold:
                return self.snapshot_processes()

    def snapshot_processes(self):
        result = ""
        processes = []
        for process in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(process.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        timestamp = datetime.datetime.now()
        filename = f"process_snapshot_{timestamp}.txt"

        result += f"Snapshot taken at {timestamp}\n"
        result += f"{'PID':<10} {'Name':<25} {'User':<20} {'CPU%':<10} {'Memory%':<10}\n"  # neatly formatted
        result += "=" * 75 + "\n"
        for proc in processes:
            result += (f"{proc['pid']:<10} {proc['name']:<25} {proc['username']:<20}"
                       f" {proc['cpu_percent']:<10} {proc['memory_percent']:<10}\n")

        print(f"Snapshot saved to {filename}")
        return result
