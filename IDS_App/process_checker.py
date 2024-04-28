import psutil


class ProcessChecker:

    def __init__(self, process):
        self.process = process

    def check_running(self):
        process_found = False
        for process in psutil.process_iter(['pid', 'name']):
            try:
                if self.process in process.info['name'].lower():
                    process_found = True
                    print(f"-Process found-\n   Name: {process.info['name']}\n   PID: {process.info['pid']}\n")
            except psutil.ZombieProcess:
                print(f"Zombie process detected for {process.info['name']}; process in terminated state")
            except psutil.NoSuchProcess:
                print(f"No suck process: {process.info['name']}")
            except psutil.AccessDenied:
                print("Access denied.")
        if not process_found:
            print("Process not found.")
