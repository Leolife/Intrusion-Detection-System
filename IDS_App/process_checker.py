import psutil


class ProcessChecker:

    def __init__(self, process_file_name):
        self.process_list = []
        with open(f"{process_file_name}.txt") as process_file:
            for line in process_file:
                process_instance = line.strip()
                self.process_list.append(process_instance)

    def check_running(self):
        result = ""
        for process in self.process_list:
            process_found = False
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if process.lower() in proc.info['name'].lower():
                        process_found = True
                        result += f"\n{process} process FOUND:\n   Name: {proc.info['name']}\n   PID: {proc.info['pid']}\n"
                except psutil.ZombieProcess:
                    result += f"Zombie process detected for {proc.info['name']}; process in terminated state"
                except psutil.NoSuchProcess:
                    result += f"No suck process: {proc.info['name']}"
                except psutil.AccessDenied:
                    result += "Access denied."
            if not process_found:
                result += f"{process} process not found.\n"
        return result
