import sys
import os
import subprocess

# Reconfigure stdout/stderr to UTF-8 on Windows to support emojis/unicode
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Auto-dependency installer for 'rich'
try:
    import rich
except ImportError:
    print("Yuki Helper requires 'rich' for its interactive terminal dashboard.")
    print("Installing 'rich' library using pip...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "rich"])
        import rich
        print("rich library installed successfully!\n")
    except Exception as e:
        print(f"Failed to automatically install 'rich': {e}")
        print("Please execute 'pip install rich' manually in your command line, then try again.")
        sys.exit(1)

import argparse
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Local module imports
from src.config_manager import ConfigManager
from src.app_launcher import launch_app
from src.runner import CommandRunner
from src.tui import YukiTUI

console = Console()

def list_registry(config):
    """Prints all configured shortcuts, commands, and scripts."""
    # Apps
    app_table = Table(title="🚀 Registered Applications", box=rich.box.ROUNDED, expand=True)
    app_table.add_column("Index", justify="center", style="cyan")
    app_table.add_column("Name", style="bold white")
    app_table.add_column("Path", style="green")
    app_table.add_column("Args", style="yellow")
    app_table.add_column("Description", style="dim")
    for idx, app in enumerate(config.config["apps"]):
        app_table.add_row(str(idx), app["name"], app["path"], app.get("args", ""), app.get("description", ""))
    
    # Commands
    cmd_table = Table(title="🖥️  Quick Commands", box=rich.box.ROUNDED, expand=True)
    cmd_table.add_column("Index", justify="center", style="cyan")
    cmd_table.add_column("Name", style="bold white")
    cmd_table.add_column("Command", style="yellow")
    cmd_table.add_column("Description", style="dim")
    for idx, cmd in enumerate(config.config["commands"]):
        cmd_table.add_row(str(idx), cmd["name"], cmd["cmd"], cmd.get("description", ""))
        
    # Scripts
    scr_table = Table(title="📜 Registered Scripts", box=rich.box.ROUNDED, expand=True)
    scr_table.add_column("Index", justify="center", style="cyan")
    scr_table.add_column("Name", style="bold white")
    scr_table.add_column("Script Path", style="green")
    scr_table.add_column("Interpreter", style="magenta")
    scr_table.add_column("Description", style="dim")
    for idx, scr in enumerate(config.config["scripts"]):
        scr_table.add_row(str(idx), scr["name"], scr["file_path"], scr.get("interpreter", "auto"), scr.get("description", ""))

    console.print(app_table)
    console.print(cmd_table)
    console.print(scr_table)

def main():
    parser = argparse.ArgumentParser(
        description="❄️  Yuki: Desktop Helper, Command Launcher & Automator CLI",
        epilog="If run without arguments, Yuki starts in interactive dashboard mode."
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Subcommand to execute directly")
    
    # Launch sub-command
    launch_parser = subparsers.add_parser("launch", help="Launch a registered application")
    launch_parser.add_argument("name", help="Name of the application to launch")
    launch_parser.add_argument("--args", default="", help="Override default launch arguments")
    
    # Run sub-command
    run_parser = subparsers.add_parser("run", help="Run a registered command line")
    run_parser.add_argument("name", help="Name of the quick command to execute")
    
    # Script sub-command
    script_parser = subparsers.add_parser("script", help="Run a registered script")
    script_parser.add_argument("name", help="Name of the script to execute")
    script_parser.add_argument("--args", default="", help="Arguments to pass to the script")
    
    # List sub-command
    subparsers.add_parser("list", help="List all registered apps, commands, and scripts")
    
    # Add items sub-commands
    add_app_parser = subparsers.add_parser("add-app", help="Register a new application shortcut")
    add_app_parser.add_argument("name", help="Display name of the application")
    add_app_parser.add_argument("path", help="Path to executable or command name")
    add_app_parser.add_argument("--args", default="", help="Default CLI arguments for the app")
    add_app_parser.add_argument("--desc", default="", help="Short description")
    
    add_cmd_parser = subparsers.add_parser("add-cmd", help="Register a new quick CLI command")
    add_cmd_parser.add_argument("name", help="Display name of the command")
    add_cmd_parser.add_argument("cmd", help="Command string to run")
    add_cmd_parser.add_argument("--desc", default="", help="Short description")

    # Voice sub-command
    subparsers.add_parser("voice", help="Start Yuki directly in Voice Command Mode")

    args = parser.parse_args()
    
    # Initialize Config Manager and Runner
    config = ConfigManager()
    runner = CommandRunner()

    if not args.command:
        # No arguments given -> run interactive TUI
        try:
            tui = YukiTUI()
            tui.run()
        except KeyboardInterrupt:
            console.print("\n[bold red]Yuki session exited.[/bold red]")
        except Exception as e:
            console.print(f"\n[bold red]Fatal TUI Error:[/] {str(e)}")
            import traceback
            traceback.print_exc()
        sys.exit(0)

    # Handle direct CLI commands
    if args.command == "voice":
        try:
            tui = YukiTUI()
            tui.current_screen = "voice"
            tui.run()
        except KeyboardInterrupt:
            console.print("\n[bold red]Yuki session exited.[/bold red]")
        except Exception as e:
            console.print(f"\n[bold red]Fatal TUI Error:[/] {str(e)}")
            import traceback
            traceback.print_exc()
        sys.exit(0)
        
    elif args.command == "list":
        list_registry(config)

        
    elif args.command == "launch":
        # Find app
        app = next((a for a in config.config["apps"] if a["name"].lower() == args.name.lower()), None)
        if app:
            launch_args = args.args or app.get("args", "")
            success, msg = launch_app(app["path"], launch_args)
            if success:
                console.print(f"[bold green]Success:[/] Launched {app['name']}.")
            else:
                console.print(f"[bold red]Error:[/] {msg}")
        else:
            console.print(f"[bold red]Error:[/] Application '{args.name}' not found in registry.")
            
    elif args.command == "run":
        # Find command
        cmd = next((c for c in config.config["commands"] if c["name"].lower() == args.name.lower()), None)
        if cmd:
            console.print(f"[bold yellow]Executing command:[/] {cmd['cmd']}\n")
            collected_output = []
            return_code = 0
            duration = 0.0
            
            try:
                for out_type, content in runner.run_command(cmd["cmd"], shell=cmd.get("shell", True)):
                    if out_type == "stdout":
                        print(content, end="")
                        collected_output.append(content)
                    elif out_type == "status":
                        return_code, duration = content
                    elif out_type == "error":
                        console.print(f"[bold red]{content}[/bold red]")
                        collected_output.append(content + "\n")
            except KeyboardInterrupt:
                console.print("\n[bold red]Interrupted by user.[/bold red]")
                return_code = -1
                
            # Log
            if config.config["settings"]["log_history"]:
                runner.log_to_history(cmd["name"], cmd["cmd"], return_code, "".join(collected_output), duration)
        else:
            console.print(f"[bold red]Error:[/] Quick command '{args.name}' not found.")
            
    elif args.command == "script":
        # Find script
        scr = next((s for s in config.config["scripts"] if s["name"].lower() == args.name.lower()), None)
        if scr:
            script_args = args.args or scr.get("args", "")
            console.print(f"[bold yellow]Running script:[/] {scr['file_path']} with args: {script_args}\n")
            collected_output = []
            return_code = 0
            duration = 0.0
            
            try:
                for out_type, content in runner.run_script(scr["file_path"], script_args, scr.get("interpreter", "auto")):
                    if out_type == "stdout":
                        print(content, end="")
                        collected_output.append(content)
                    elif out_type == "status":
                        return_code, duration = content
                    elif out_type == "error":
                        console.print(f"[bold red]{content}[/bold red]")
                        collected_output.append(content + "\n")
            except KeyboardInterrupt:
                console.print("\n[bold red]Interrupted by user.[/bold red]")
                return_code = -1
                
            # Log
            cmd_representation = f"[{scr.get('interpreter', 'auto')}] {scr['file_path']} {script_args}"
            if config.config["settings"]["log_history"]:
                runner.log_to_history(scr["name"], cmd_representation, return_code, "".join(collected_output), duration)
        else:
            console.print(f"[bold red]Error:[/] Script '{args.name}' not found.")
            
    elif args.command == "add-app":
        if config.add_app(args.name, args.path, args.args, args.desc):
            console.print(f"[bold green]Success:[/] Registered application shortcut for '{args.name}'.")
        else:
            console.print("[bold red]Error:[/] Failed to write to config.json.")
            
    elif args.command == "add-cmd":
        if config.add_command(args.name, args.cmd, shell=True, description=args.desc):
            console.print(f"[bold green]Success:[/] Registered quick command '{args.name}'.")
        else:
            console.print("[bold red]Error:[/] Failed to write to config.json.")

if __name__ == "__main__":
    main()
