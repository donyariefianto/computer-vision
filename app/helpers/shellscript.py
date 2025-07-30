import os
import platform
path_app = os.getcwd()
system = platform.system()

class ShellScript:
    def init_drive():
        if system == "Windows":
            script_path = path_app + "\\app\\helpers\\ShellScript\\" + "setup_drive_win.ps1"
            data_path = path_app + "\\data\\drive"
            command = [
                "powershell",
                "-ExecutionPolicy", "Bypass",  # Lewati kebijakan eksekusi
                "-NoProfile",  # Mencegah muatan profile tambahan di PowerShell
                "-File", script_path,
                "-DataPath", data_path,
                "-Action", "start",
            ]
            return ShellScript.execute_shellscript(command)