import subprocess
import sys
import os
import time
from datetime import datetime
import json
from pathlib import Path

class CommandRunner:
    def __init__(self, history_file="history.json", max_history=50):
        self.history_file = Path(history_file)
        self.max_history = max_history

    def log_to_history(self, name, cmd_str, return_code, output, duration):
        """Logs execution results to local history.json file."""
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "name": name,
            "command": cmd_str,
            "return_code": return_code,
            "duration_seconds": round(duration, 2),
            "output_preview": output[-1000:] if output else "" # Log the end of the output (up to 1000 chars)
        }
        
        history = []
        if self.history_file.exists():
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    history = json.load(f)
                    if not isinstance(history, list):
                        history = []
            except Exception:
                history = []
                
        history.insert(0, history_entry)
        # Truncate
        history = history[:self.max_history]
        
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=4)
        except Exception:
            pass

    def run_command(self, cmd_str, shell=True, env=None, cwd=None):
        """
        Runs a command and yields stdout/stderr lines in real-time.
        Yields:
            ('stdout', line_content)
            ('status', (return_code, duration_seconds))
            ('error', error_message)
        """
        start_time = time.time()
        try:
            # We merge stderr into stdout for simple terminal-like streaming
            # and line buffer (bufsize=1) to read output as it is printed
            process = subprocess.Popen(
                cmd_str,
                shell=shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                encoding="utf-8",
                errors="replace",
                env=env or os.environ.copy(),
                cwd=cwd
            )
            
            # Read stdout line by line
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    yield "stdout", line
                    
            return_code = process.wait()
            duration = time.time() - start_time
            yield "status", (return_code, duration)
            
        except Exception as e:
            duration = time.time() - start_time
            yield "error", f"Command failed to start: {str(e)}"
            yield "status", (-1, duration)

    def run_script(self, script_path, args="", interpreter="auto", cwd=None):
        """
        Resolves the script interpreter and runs the script, streaming output.
        """
        expanded_path = os.path.expandvars(script_path)
        path_obj = Path(expanded_path)
        
        if not path_obj.exists():
            yield "error", f"Script file not found at: {expanded_path}"
            yield "status", (-1, 0.0)
            return

        # Auto-detect interpreter if requested
        if interpreter == "auto":
            ext = path_obj.suffix.lower()
            if ext == ".py":
                interpreter = "python"
            elif ext == ".ps1":
                interpreter = "powershell"
            elif ext in [".bat", ".cmd"]:
                interpreter = "cmd"
            else:
                interpreter = "shell"

        # Construct the execution command
        if interpreter == "python":
            # Using sys.executable guarantees it uses the same python environment
            cmd = f'"{sys.executable}" "{expanded_path}" {args}'
        elif interpreter == "powershell":
            cmd = f'powershell -ExecutionPolicy Bypass -File "{expanded_path}" {args}'
        elif interpreter == "cmd":
            cmd = f'"{expanded_path}" {args}'
        else:
            # Fallback direct execution (will let shell resolve it)
            cmd = f'"{expanded_path}" {args}'

        # Execute using standard shell environment
        yield from self.run_command(cmd, shell=True, cwd=cwd or str(path_obj.parent))
