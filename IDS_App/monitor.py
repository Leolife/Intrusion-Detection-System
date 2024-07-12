import datetime
import GPUtil
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
        for process in psutil.process_iter(['pid', 'name', 'username', 'memory_percent', 'io_counters']):
            try:
                proc = process.as_dict(attrs=['pid', 'name', 'username', 'memory_percent', 'cpu_times', 'io_counters'])
                processes[proc['pid']] = proc
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        # Wait for a short interval
        time.sleep(1)

        # Get total network I/O
        net_io_before = psutil.net_io_counters()

        # Second pass: collect CPU times again and calculate CPU percentage
        for pid in list(processes.keys()):
            try:
                current_proc = psutil.Process(pid)
                current_cpu_times = current_proc.cpu_times()
                current_io_counters = current_proc.io_counters()

                cpu_diff = sum(current_cpu_times) - sum(processes[pid]['cpu_times'])
                net_diff = sum(current_io_counters) - sum(processes[pid]['io_counters'])

                cpu_percent = cpu_diff * 100
                net_percent = (net_diff / sum(net_io_before)) * 100 if sum(net_io_before) > 0 else 0

                processes[pid]['cpu_percent'] = cpu_percent
                processes[pid]['net_percent'] = net_percent
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                processes[pid]['cpu_percent'] = 0  # Process no longer exists or is inaccessible
                processes[pid]['net_percent'] = 0

        # Get GPU usage per process (approximation b/c it's difficult to get precise per-process GPU usage)
        try:
            gpus = GPUtil.getGPUs()
            for gpu in gpus:
                gpu_processes = gpu.getComputeProcesses()
                for gpu_proc in gpu_processes:
                    if gpu_proc['pid'] in processes:
                        processes[gpu_proc['pid']]['gpu_percent'] = gpu_proc['gpu_memory_percent']
        except:
            pass  # GPUtil might not be available or no GPU present

        # Fill in GPU percent for processes not using GPU
        for pid in processes:
            if 'gpu_percent' not in processes[pid]:
                processes[pid]['gpu_percent'] = 0

        # Sorting processes by CPU usage
        sorted_processes = sorted(processes.values(), key=lambda x: x['cpu_percent'], reverse=True)

        timestamp = datetime.datetime.now()

        result += f"Snapshot taken at {timestamp}\n"
        result += f"{'PID':<10} {'Name':<25} {'User':<20} {'CPU%':<10} {'Memory%':<10} {'Network%':<10} {'GPU%':<10}\n"
        result += "=" * 95 + "\n"
        for proc in sorted_processes:
            result += (f"{proc['pid']:<10} {proc['name']:<25} {proc['username']:<20}"
                       f" {proc['cpu_percent']:<10.2f} {proc['memory_percent']:<10.2f}"
                       f" {proc['net_percent']:<10.2f} {proc['gpu_percent']:<10.2f}\n")

        return result
