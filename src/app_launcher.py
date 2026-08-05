import os
import subprocess
from pathlib import Path

def launch_app(path, args=""):
    """
    Launches an application or file on Windows without blocking the main TUI.
    Uses os.startfile for native Windows file execution when possible,
    and falls back to subprocess.Popen.
    """
    expanded_path = os.path.expandvars(path)
    
    try:
        # If it's a directory, open it in explorer
        if os.path.isdir(expanded_path):
            os.startfile(expanded_path)
            return True, f"Opened directory: {expanded_path}"
            
        if args:
            # Launch with arguments. We use subprocess.Popen and let Windows shell resolve standard path commands
            # Using creationflags=0x00000008 (DETACHED_PROCESS) to prevent locking
            try:
                # 0x00000008 is DETACHED_PROCESS, 0x00000010 is CREATE_NEW_CONSOLE
                # We use CREATE_NEW_CONSOLE if it's a CLI program or standard process creation
                # but start "" path args is standard and safe on Windows shell.
                cmd = f'start "" "{expanded_path}" {args}'
                subprocess.Popen(cmd, shell=True)
                return True, f"Launched: {expanded_path} {args}"
            except Exception as e:
                # Direct invocation fallback
                subprocess.Popen([expanded_path] + args.split(), shell=True)
                return True, f"Launched: {expanded_path} {args}"
        else:
            # Check if file exists or it's in the system path
            # We can use os.startfile which handles system path, protocol links (e.g. http://), shortcuts (.lnk), etc.
            try:
                os.startfile(expanded_path)
                return True, f"Launched: {expanded_path}"
            except FileNotFoundError:
                # If startfile fails because it's not an absolute path, try starting via system shell
                subprocess.Popen(f'start "" "{expanded_path}"', shell=True)
                return True, f"Launched via shell: {expanded_path}"
                
    except Exception as e:
        return False, f"Failed to launch '{path}': {str(e)}"
