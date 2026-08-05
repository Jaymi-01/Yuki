import json
import os
from pathlib import Path

DEFAULT_CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "apps": [
        {
            "name": "Notepad",
            "path": "notepad.exe",
            "args": "",
            "description": "Standard Windows Text Editor"
        },
        {
            "name": "Calculator",
            "path": "calc.exe",
            "args": "",
            "description": "Standard Windows Calculator"
        },
        {
            "name": "Paint",
            "path": "mspaint.exe",
            "args": "",
            "description": "Standard Windows Paint Application"
        },
        {
            "name": "Task Manager",
            "path": "taskmgr.exe",
            "args": "",
            "description": "Windows Task Manager"
        },
        {
            "name": "Command Prompt",
            "path": "cmd.exe",
            "args": "",
            "description": "Windows Command Line"
        },
        {
            "name": "PowerShell",
            "path": "powershell.exe",
            "args": "",
            "description": "Windows PowerShell Command Line"
        }
    ],
    "commands": [
        {
            "name": "Git Status",
            "cmd": "git status",
            "shell": True,
            "description": "Check current Git repository status"
        },
        {
            "name": "System Info",
            "cmd": "systeminfo",
            "shell": True,
            "description": "Display basic Windows operating system configuration"
        },
        {
            "name": "Active Network Connections",
            "cmd": "netstat -an | findstr LISTENING",
            "shell": True,
            "description": "Show all listening ports on this machine"
        },
        {
            "name": "List IP Configuration",
            "cmd": "ipconfig /all",
            "shell": True,
            "description": "Show all current network adapter configurations"
        }
    ],
    "scripts": [],
    "settings": {
        "start_directory": ".",
        "theme": "ocean",
        "log_history": True,
        "max_history_entries": 50
    }
}

class ConfigManager:
    def __init__(self, config_path=None):
        if config_path is None:
            self.config_path = Path(DEFAULT_CONFIG_FILE)
        else:
            self.config_path = Path(config_path)
            
        self.config = {}
        self.load()

    def load(self):
        """Loads config from the JSON file or creates a default one if it doesn't exist."""
        if not self.config_path.exists():
            self.config = DEFAULT_CONFIG.copy()
            self.save()
        else:
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
                # Ensure all key sections exist
                for key, val in DEFAULT_CONFIG.items():
                    if key not in self.config:
                        self.config[key] = val
            except (json.JSONDecodeError, PermissionError) as e:
                # Fallback to default in case of corruption, but keep track
                self.config = DEFAULT_CONFIG.copy()

    def save(self):
        """Saves current config to JSON file."""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4)
            return True
        except PermissionError:
            return False

    def add_app(self, name, path, args="", description=""):
        self.config["apps"].append({
            "name": name,
            "path": path,
            "args": args,
            "description": description
        })
        return self.save()

    def add_command(self, name, cmd, shell=True, description=""):
        self.config["commands"].append({
            "name": name,
            "cmd": cmd,
            "shell": shell,
            "description": description
        })
        return self.save()

    def add_script(self, name, file_path, interpreter="python", description=""):
        self.config["scripts"].append({
            "name": name,
            "file_path": file_path,
            "interpreter": interpreter,
            "description": description
        })
        return self.save()

    def remove_app(self, idx):
        if 0 <= idx < len(self.config["apps"]):
            self.config["apps"].pop(idx)
            return self.save()
        return False

    def remove_command(self, idx):
        if 0 <= idx < len(self.config["commands"]):
            self.config["commands"].pop(idx)
            return self.save()
        return False

    def remove_script(self, idx):
        if 0 <= idx < len(self.config["scripts"]):
            self.config["scripts"].pop(idx)
            return self.save()
        return False
