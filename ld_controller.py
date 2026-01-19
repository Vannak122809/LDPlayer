import subprocess
import os
import time

class LDPlayerController:
    def __init__(self, console_path=None):
        self.console_path = console_path
        if not self.console_path:
            self.console_path = self.find_console_path()

    def find_console_path(self):
        # Common paths
        potential_paths = [
            r"C:\LDPlayer\LDPlayer9\dnconsole.exe",
            r"D:\LDPlayer\LDPlayer9\dnconsole.exe",
            r"C:\leidian\LDPlayer9\dnconsole.exe",
            r"D:\leidian\LDPlayer9\dnconsole.exe",
            r"C:\XuanZhi\LDPlayer9\dnconsole.exe",
            r"E:\LDPlayer\LDPlayer9\dnconsole.exe" # Added based on screenshot hint if any, though not explicit
        ]
        
        for path in potential_paths:
            if os.path.exists(path):
                return path
        return None

    def execute_command(self, cmd_args):
        if not self.console_path:
            raise FileNotFoundError("LDPlayer console (dnconsole.exe) not found.")
        
        full_cmd = [self.console_path] + cmd_args
        
        # Determine startup flags to hide window
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        try:
            # shell=True sometimes helps with elevation context or path resolution on Windows,
            # but usually for dnconsole, direct execution is better.
            # However, if Admin is needed, the main app should be Admin.
            result = subprocess.run(
                full_cmd, 
                capture_output=True, 
                text=True, 
                startupinfo=startupinfo,
                encoding='gbk', # LDPlayer outputs GBK
                errors='replace'
            )
            return result.stdout.strip()
        except Exception as e:
            print(f"Error executing command {' '.join(full_cmd)}: {e}")
            return ""

    def get_adb_path(self):
        if not self.console_path:
            return None
        # ADB is usually in the same directory as dnconsole.exe, named adb.exe or inside a bin folder
        base_dir = os.path.dirname(self.console_path)
        adb_path = os.path.join(base_dir, "adb.exe")
        if os.path.exists(adb_path):
            return adb_path
        return "adb" # Fallback to system path

    def run_adb_cmd(self, index, cmd_args):
        # adb -s 127.0.0.1:5555 shell ... (simulated via dnconsole adb)
        full_cmd = ['adb', '--index', str(index), '--command', f'"{cmd_args}"']
        return self.execute_command(full_cmd)

    def adb_swipe(self, index, x1, y1, x2, y2, duration=300):
        self.run_adb_cmd(index, f"input swipe {x1} {y1} {x2} {y2} {duration}")

    def adb_tap(self, index, x, y):
        self.run_adb_cmd(index, f"input tap {x} {y}")

    def adb_input_text(self, index, text):
        # Escape spaces
        safe_text = text.replace(" ", "%s")
        self.run_adb_cmd(index, f"input text {safe_text}")
        
    def adb_start_app(self, index, package_name):
        self.run_adb_cmd(index, f"monkey -p {package_name} -c android.intent.category.LAUNCHER 1")
    
    def adb_stop_app(self, index, package_name):
        self.run_adb_cmd(index, f"am force-stop {package_name}")

    def list_instances(self):
        output = self.execute_command(['list2'])
        instances = []
        if output:
            lines = output.split('\n')
            for line in lines:
                parts = line.split(',')
                # list2 format: Index,Title,TopWindowHandle,DedicatedTerminalHandle,EnterAndroid,ProcessID,VBoxProcessID,Status
                if len(parts) >= 8:
                    index = parts[0]
                    name = parts[1]
                    pid = parts[5]
                    vbox_pid = parts[6]
                    
                    is_running = (pid != '0' and pid != '-1') or (vbox_pid != '0' and vbox_pid != '-1')
                    
                    instances.append({
                        'index': index,
                        'name': name,
                        'running': is_running,
                        'pid': pid
                    })
        
        # Sort by index (int)
        instances.sort(key=lambda x: int(x['index']))
        return instances

    def start_instance(self, index):
        self.execute_command(['launch', '--index', str(index)])

    def stop_instance(self, index):
        self.execute_command(['quit', '--index', str(index)])
        
    def quit_all(self):
        self.execute_command(['quitall'])

    def reboot_instance(self, index):
        self.execute_command(['reboot', '--index', str(index)])

    def create_instance(self, name):
        self.execute_command(['add', '--name', name])
        
    def remove_instance(self, index):
        self.execute_command(['remove', '--index', str(index)])

    def modify_instance(self, index, cpu, memory, resolution=None):
        # dnconsole modify --index 0 --cpu 2 --memory 2048 --resolution 720,1280,320
        cmd = ['modify', '--index', str(index), '--cpu', str(cpu), '--memory', str(memory)]
        if resolution:
             cmd.extend(['--resolution', resolution])
        self.execute_command(cmd)

    def sort_windows(self):
        self.execute_command(['sortWnd'])
        
    def global_config(self, fps=60, audio=0, fast_play=1):
        # example global setting
        pass
