import os
import sys
import time
import msvcrt
from pathlib import Path

# Reconfigure stdout/stderr to UTF-8 on Windows to support emojis/unicode
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass


# Rich imports
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.prompt import Prompt, Confirm
from rich.live import Live
from rich.layout import Layout
from rich import box

# Local imports
from src.config_manager import ConfigManager
from src.app_launcher import launch_app
from src.runner import CommandRunner
from src.explorer import FileExplorer
from src.voice import VoiceEngine, VoiceListener, get_programmer_joke

# Initialize console
console = Console()

class YukiTUI:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.runner = CommandRunner()
        self.explorer = FileExplorer(self.config_manager.config["settings"]["start_directory"])
        self.voice_engine = VoiceEngine()
        self.voice_listener = VoiceListener()
        self.running = True
        
        # State tracking
        self.current_screen = "main_menu" # main_menu, apps, commands, scripts, explorer, settings, voice
        self.selected_index = 0
        self.message = ""
        self.message_style = "green"
        
        # Explorer specific state
        self.explorer_items = []
        
    def get_key(self):
        """Reads a keypress from the Windows console. Returns string representation."""
        try:
            ch = msvcrt.getch()
            if ch in (b'\x00', b'\xe0'): # Special key indicator
                ch2 = msvcrt.getch()
                if ch2 == b'H': return 'up'
                if ch2 == b'P': return 'down'
                if ch2 == b'K': return 'left'
                if ch2 == b'M': return 'right'
                if ch2 == b'S': return 'delete' # Delete key
                return 'special'
            if ch == b'\r':
                return 'enter'
            if ch == b'\x1b':
                return 'escape'
            if ch in (b'\x08', b'\x7f'):
                return 'backspace'
            try:
                return ch.decode('utf-8')
            except UnicodeDecodeError:
                return None
        except Exception:
            return None

    def clear_screen(self):
        """Clears the console screen."""
        os.system('cls')

    def set_message(self, text, style="green"):
        """Sets a status message to display in the header/footer."""
        self.message = text
        self.message_style = style

    def render_header(self):
        """Renders the top banner of the application."""
        theme = self.config_manager.config["settings"]["theme"]
        accent = "cyan" if theme == "ocean" else "magenta"
        
        header_text = f"[bold {accent}]❄️  YUKI COMMAND CENTER  ❄️[/bold {accent}]\n[dim]Windows Desktop Helper & Automator[/dim]"
        if self.message:
            header_text += f"\n\n[{self.message_style}]ℹ️ {self.message}[/{self.message_style}]"
            
        console.print(Panel(header_text, style=accent, border_style=accent, box=box.ROUNDED, expand=True))

    def run(self):
        """Main interface loop."""
        while self.running:
            self.clear_screen()
            self.render_header()
            
            if self.current_screen == "main_menu":
                self.render_main_menu()
                self.handle_input()
            elif self.current_screen == "apps":
                self.render_apps_menu()
                self.handle_input()
            elif self.current_screen == "commands":
                self.render_commands_menu()
                self.handle_input()
            elif self.current_screen == "scripts":
                self.render_scripts_menu()
                self.handle_input()
            elif self.current_screen == "explorer":
                self.render_explorer()
                self.handle_input()
            elif self.current_screen == "settings":
                self.render_settings()
                self.handle_input()
            elif self.current_screen == "voice":
                self.start_voice_command_loop()


    # --- MAIN MENU ---
    
    def render_main_menu(self):
        options = [
            ("🚀 Launch Applications", "Open preset or custom desktop apps and folders"),
            ("🖥️  Quick Commands", "Execute registered CLI command lines"),
            ("📜 Run Scripts", "Run python, powershell, or shell scripts"),
            ("📁 File Explorer", "Browse, view, edit files, or execute actions on them"),
            ("🎙️  Voice Command Mode", "Talk to Yuki to launch apps and run commands"),
            ("⚙️  Add Shortcut / Config", "Add new application, command, or script configurations"),
            ("❌ Exit Yuki", "Quit the utility")
        ]
        
        table = Table(show_header=False, box=None, expand=True)
        table.add_column("Selection", width=4, justify="right")
        table.add_column("Option", style="bold white")
        table.add_column("Description", style="dim")
        
        for idx, (title, desc) in enumerate(options):
            if idx == self.selected_index:
                table.add_row("[cyan]>[/cyan]", f"[cyan]{title}[/cyan]", f"[cyan]{desc}[/cyan]")
            else:
                table.add_row("", title, desc)
                
        console.print(Panel(table, title="[bold]Main Menu[/bold]", border_style="dim", box=box.ROUNDED))
        console.print("\n[dim]Use [bold]↑/↓ Arrows[/bold] to navigate, [bold]Enter[/bold] to select, [bold]Esc[/bold] to quit.[/dim]")
        console.print("[dim]Press [bold]V[/bold] as a hotkey to instantly launch Voice Command Mode.[/dim]")

    def handle_main_menu(self, key):
        max_idx = 6
        if key == 'up':
            self.selected_index = (self.selected_index - 1) % (max_idx + 1)
        elif key == 'down':
            self.selected_index = (self.selected_index + 1) % (max_idx + 1)
        elif key == 'enter':
            self.set_message("")
            if self.selected_index == 0:
                self.current_screen = "apps"
                self.selected_index = 0
            elif self.selected_index == 1:
                self.current_screen = "commands"
                self.selected_index = 0
            elif self.selected_index == 2:
                self.current_screen = "scripts"
                self.selected_index = 0
            elif self.selected_index == 3:
                self.current_screen = "explorer"
                self.selected_index = 0
                self.explorer_items = self.explorer.list_contents()
            elif self.selected_index == 4:
                self.current_screen = "voice"
                self.selected_index = 0
            elif self.selected_index == 5:
                self.add_config_wizard()
            elif self.selected_index == 6:
                self.running = False
        elif key in ('v', 'V'):
            self.current_screen = "voice"
            self.selected_index = 0
        elif key == 'escape':
            self.running = False


    # --- APPS MENU ---
    
    def render_apps_menu(self):
        apps = self.config_manager.config["apps"]
        
        table = Table(box=box.ROUNDED, expand=True)
        table.add_column("Sel", justify="center", width=3)
        table.add_column("Application Name", style="bold cyan")
        table.add_column("Path / Binary", style="green")
        table.add_column("Arguments", style="yellow")
        table.add_column("Description", style="dim")
        
        for idx, app in enumerate(apps):
            is_selected = idx == self.selected_index
            sel = "[cyan]>[/cyan]" if is_selected else ""
            style = "bold cyan" if is_selected else "white"
            
            table.add_row(
                sel,
                f"[{style}]{app['name']}[/{style}]",
                app['path'],
                app.get('args', ''),
                app.get('description', '')
            )
            
        console.print(Panel(table, title="[bold]Registered Applications[/bold]", border_style="cyan"))
        console.print("[dim]Use [bold]↑/↓[/bold] to navigate. [bold]Enter[/bold] to launch. [bold]Del[/bold] to delete shortcut. [bold]Esc[/bold] to return.[/dim]")

    def handle_apps_menu(self, key):
        apps = self.config_manager.config["apps"]
        if not apps:
            if key == 'escape':
                self.current_screen = "main_menu"
                self.selected_index = 0
            return
            
        if key == 'up':
            self.selected_index = (self.selected_index - 1) % len(apps)
        elif key == 'down':
            self.selected_index = (self.selected_index + 1) % len(apps)
        elif key == 'enter':
            app = apps[self.selected_index]
            self.set_message(f"Launching {app['name']}...", "yellow")
            self.clear_screen()
            self.render_header()
            
            success, msg = launch_app(app["path"], app.get("args", ""))
            if success:
                self.set_message(msg, "green")
            else:
                self.set_message(msg, "red")
        elif key == 'delete':
            app = apps[self.selected_index]
            self.clear_screen()
            if Confirm.ask(f"Are you sure you want to remove the shortcut for '{app['name']}'?"):
                self.config_manager.remove_app(self.selected_index)
                self.set_message(f"Removed shortcut for '{app['name']}'")
            self.selected_index = 0
        elif key == 'escape':
            self.current_screen = "main_menu"
            self.selected_index = 0

    # --- QUICK COMMANDS MENU ---
    
    def render_commands_menu(self):
        commands = self.config_manager.config["commands"]
        
        table = Table(box=box.ROUNDED, expand=True)
        table.add_column("Sel", justify="center", width=3)
        table.add_column("Command Name", style="bold green")
        table.add_column("Shell Command", style="yellow")
        table.add_column("Description", style="dim")
        
        for idx, cmd in enumerate(commands):
            is_selected = idx == self.selected_index
            sel = "[cyan]>[/cyan]" if is_selected else ""
            style = "bold green" if is_selected else "white"
            
            table.add_row(
                sel,
                f"[{style}]{cmd['name']}[/{style}]",
                cmd['cmd'],
                cmd.get('description', '')
            )
            
        console.print(Panel(table, title="[bold]Quick Commands[/bold]", border_style="green"))
        console.print("[dim]Use [bold]↑/↓[/bold] to navigate. [bold]Enter[/bold] to run. [bold]Del[/bold] to delete command. [bold]Esc[/bold] to return.[/dim]")

    def handle_commands_menu(self, key):
        commands = self.config_manager.config["commands"]
        if not commands:
            if key == 'escape':
                self.current_screen = "main_menu"
                self.selected_index = 1
            return
            
        if key == 'up':
            self.selected_index = (self.selected_index - 1) % len(commands)
        elif key == 'down':
            self.selected_index = (self.selected_index + 1) % len(commands)
        elif key == 'enter':
            cmd = commands[self.selected_index]
            self.execute_and_stream(cmd["name"], cmd["cmd"], cmd.get("shell", True))
        elif key == 'delete':
            cmd = commands[self.selected_index]
            self.clear_screen()
            if Confirm.ask(f"Are you sure you want to remove the command '{cmd['name']}'?"):
                self.config_manager.remove_command(self.selected_index)
                self.set_message(f"Removed command '{cmd['name']}'")
            self.selected_index = 0
        elif key == 'escape':
            self.current_screen = "main_menu"
            self.selected_index = 1

    # --- SCRIPTS MENU ---
    
    def render_scripts_menu(self):
        scripts = self.config_manager.config["scripts"]
        
        table = Table(box=box.ROUNDED, expand=True)
        table.add_column("Sel", justify="center", width=3)
        table.add_column("Script Name", style="bold yellow")
        table.add_column("Script Path", style="cyan")
        table.add_column("Interpreter", style="magenta")
        table.add_column("Description", style="dim")
        
        for idx, scr in enumerate(scripts):
            is_selected = idx == self.selected_index
            sel = "[cyan]>[/cyan]" if is_selected else ""
            style = "bold yellow" if is_selected else "white"
            
            table.add_row(
                sel,
                f"[{style}]{scr['name']}[/{style}]",
                scr['file_path'],
                scr.get('interpreter', 'auto'),
                scr.get('description', '')
            )
            
        console.print(Panel(table, title="[bold]Registered Scripts[/bold]", border_style="yellow"))
        console.print("[dim]Use [bold]↑/↓[/bold] to navigate. [bold]Enter[/bold] to run. [bold]Del[/bold] to delete script. [bold]Esc[/bold] to return.[/dim]")

    def handle_scripts_menu(self, key):
        scripts = self.config_manager.config["scripts"]
        if not scripts:
            if key == 'escape':
                self.current_screen = "main_menu"
                self.selected_index = 2
            return
            
        if key == 'up':
            self.selected_index = (self.selected_index - 1) % len(scripts)
        elif key == 'down':
            self.selected_index = (self.selected_index + 1) % len(scripts)
        elif key == 'enter':
            scr = scripts[self.selected_index]
            
            # Prompt for arguments
            self.clear_screen()
            self.render_header()
            args = Prompt.ask(f"[bold yellow]Enter arguments for '{scr['name']}'[/] (leave blank for none)")
            
            self.execute_script_stream(scr["name"], scr["file_path"], args, scr.get("interpreter", "auto"))
        elif key == 'delete':
            scr = scripts[self.selected_index]
            self.clear_screen()
            if Confirm.ask(f"Are you sure you want to remove the script '{scr['name']}'?"):
                self.config_manager.remove_script(self.selected_index)
                self.set_message(f"Removed script '{scr['name']}'")
            self.selected_index = 0
        elif key == 'escape':
            self.current_screen = "main_menu"
            self.selected_index = 2

    # --- FILE EXPLORER ---
    
    def render_explorer(self):
        items = self.explorer_items
        current_dir = self.explorer.get_current_dir()
        
        table = Table(box=box.MINIMAL_DOUBLE_HEAD, expand=True)
        table.add_column("Sel", justify="center", width=3)
        table.add_column("Name", style="bold")
        table.add_column("Size", justify="right", style="cyan")
        table.add_column("Modified Time", justify="center", style="magenta")
        
        for idx, item in enumerate(items):
            is_selected = idx == self.selected_index
            sel = "[cyan]>[/cyan]" if is_selected else ""
            
            if item["is_dir"]:
                name_str = f"[bold cyan]📁 {item['name']}[/bold cyan]"
            else:
                name_str = f"📄 {item['name']}"
                
            if is_selected:
                table.add_row(sel, f"[reverse]{name_str}[/reverse]", item["size"], item["mtime"])
            else:
                table.add_row("", name_str, item["size"], item["mtime"])
                
        console.print(Panel(table, title=f"[bold]File Explorer - {current_dir}[/bold]", border_style="cyan"))
        console.print("[dim]Use [bold]↑/↓[/bold] to navigate. [bold]Enter[/bold] (folder: open, file: actions). [bold]Backspace[/bold] (go up).[/dim]")
        console.print("[dim][bold]N[/bold]: New File | [bold]D[/bold]: New Dir | [bold]Del[/bold]: Delete item | [bold]Esc[/bold]: Main menu[/dim]")

    def handle_explorer(self, key):
        items = self.explorer_items
        
        if key == 'up':
            if items:
                self.selected_index = (self.selected_index - 1) % len(items)
        elif key == 'down':
            if items:
                self.selected_index = (self.selected_index + 1) % len(items)
        elif key == 'backspace':
            self.explorer.navigate_to("..")
            self.explorer_items = self.explorer.list_contents()
            self.selected_index = 0
            self.set_message("")
        elif key == 'enter':
            if not items:
                return
            selected = items[self.selected_index]
            if selected["is_dir"]:
                success, msg = self.explorer.navigate_to(selected["path"])
                if success:
                    self.explorer_items = self.explorer.list_contents()
                    self.selected_index = 0
                    self.set_message("")
                else:
                    self.set_message(msg, "red")
            else:
                self.file_action_menu(selected)
        elif key in ('n', 'N'):
            self.clear_screen()
            self.render_header()
            filename = Prompt.ask("[bold]Enter new file name[/]")
            if filename:
                success, msg = self.explorer.create_file(filename)
                self.set_message(msg, "green" if success else "red")
                self.explorer_items = self.explorer.list_contents()
                self.selected_index = 0
        elif key in ('d', 'D'):
            self.clear_screen()
            self.render_header()
            dirname = Prompt.ask("[bold]Enter new directory name[/]")
            if dirname:
                success, msg = self.explorer.create_directory(dirname)
                self.set_message(msg, "green" if success else "red")
                self.explorer_items = self.explorer.list_contents()
                self.selected_index = 0
        elif key == 'delete':
            if not items: return
            selected = items[self.selected_index]
            if selected["name"] == "..": return
            
            self.clear_screen()
            self.render_header()
            if Confirm.ask(f"[bold red]WARNING:[/] Are you sure you want to permanently delete '{selected['name']}'?"):
                success, msg = self.explorer.delete_item(selected["path"])
                self.set_message(msg, "green" if success else "red")
                self.explorer_items = self.explorer.list_contents()
                self.selected_index = 0
        elif key == 'escape':
            self.current_screen = "main_menu"
            self.selected_index = 3

    def file_action_menu(self, file_item):
        """Displays options when a file is selected in the explorer."""
        actions_running = True
        
        while actions_running:
            self.clear_screen()
            self.render_header()
            
            details_text = (
                f"[bold cyan]File:[/] {file_item['name']}\n"
                f"[bold cyan]Path:[/] {file_item['path']}\n"
                f"[bold cyan]Size:[/] {file_item['size']}\n"
                f"[bold cyan]Modified:[/] {file_item['mtime']}\n"
            )
            console.print(Panel(details_text, title="File Details", border_style="cyan"))
            
            options = [
                ("[V] View Content", "Show file content in terminal with syntax highlighting"),
                ("[E] Edit File in Default System App", "Launch associated app (e.g. VS Code, Notepad)"),
                ("[O] Quick Overwrite/Write", "Write content to file from console input"),
                ("[R] Run Shell Command on this file", "Execute arbitrary command with this file path as an argument"),
                ("[Esc] Cancel", "Return to file explorer")
            ]
            
            for title, desc in options:
                console.print(f"  [bold cyan]{title[:3]}[/bold cyan] {title[3:]} - [dim]{desc}[/dim]")
                
            console.print("\nPress key corresponding to action:")
            opt_key = self.get_key()
            
            if opt_key in ('v', 'V'):
                self.view_file_content(file_item["path"])
            elif opt_key in ('e', 'E'):
                self.set_message(f"Opening {file_item['name']}...", "yellow")
                launch_app(file_item["path"])
                actions_running = False
            elif opt_key in ('o', 'O'):
                self.edit_file_terminal(file_item["path"])
            elif opt_key in ('r', 'R'):
                self.run_command_on_file(file_item["path"])
                actions_running = False
            elif opt_key in ('escape', 'q', 'Q'):
                actions_running = False
                
        # Refresh listing
        self.explorer_items = self.explorer.list_contents()

    def view_file_content(self, path):
        """Shows highlighted file content, scrolls if it's long."""
        self.clear_screen()
        self.render_header()
        
        success, content, ext = self.explorer.get_file_details(path)
        if not success:
            console.print(f"[bold red]Error:[/] {content}")
            console.print("\nPress any key to return...")
            self.get_key()
            return
            
        # Select syntax highlighter based on extension
        syntax_lang = "python"
        if ext == ".json": syntax_lang = "json"
        elif ext in (".js", ".ts"): syntax_lang = "javascript"
        elif ext == ".html": syntax_lang = "html"
        elif ext == ".css": syntax_lang = "css"
        elif ext in (".bat", ".cmd"): syntax_lang = "batch"
        elif ext == ".ps1": syntax_lang = "powershell"
        elif ext == ".md": syntax_lang = "markdown"
        elif ext in (".txt", ""): syntax_lang = "text"
        
        # Display the file panel
        try:
            syntax = Syntax(content, syntax_lang, theme="monokai", line_numbers=True, word_wrap=True)
            console.print(Panel(syntax, title=f"Content: {Path(path).name}", border_style="cyan"))
        except Exception:
            # Fallback to plain text
            console.print(Panel(content, title=f"Content: {Path(path).name}", border_style="cyan"))
            
        console.print("\n[bold cyan]Press any key to return to details...[/bold cyan]")
        self.get_key()

    def edit_file_terminal(self, path):
        """Allows writing text directly to a file from the console."""
        self.clear_screen()
        self.render_header()
        
        console.print(f"[bold yellow]Writing to: {Path(path).name}[/bold yellow]")
        console.print("[dim]Enter content line-by-line. Type [bold]__SAVE__[/bold] on a new line to save, or [bold]__CANCEL__[/bold] to exit.[/dim]\n")
        
        lines = []
        while True:
            try:
                line = input(f"{len(lines) + 1:3d} | ")
                if line == "__SAVE__":
                    content = "\n".join(lines)
                    success, msg = self.explorer.write_file_content(path, content)
                    self.set_message(msg, "green" if success else "red")
                    break
                elif line == "__CANCEL__":
                    self.set_message("Edit cancelled.")
                    break
                lines.append(line)
            except KeyboardInterrupt:
                self.set_message("Edit cancelled.")
                break

    def run_command_on_file(self, path):
        """Asks user for a shell command, inserts file path, and executes it."""
        self.clear_screen()
        self.render_header()
        
        console.print(f"[bold yellow]Run command on file:[/] {Path(path).name}")
        console.print("Use [bold]{file}[/bold] as a placeholder for the file path.\nExample: [cyan]git add {file}[/cyan] or [cyan]python {file}[/cyan]")
        
        cmd_template = Prompt.ask("\nEnter command template")
        if cmd_template:
            # Escape path properly if there are spaces
            resolved_path = f'"{path}"'
            command = cmd_template.replace("{file}", resolved_path)
            # Execute
            self.execute_and_stream(f"Custom command on {Path(path).name}", command, shell=True)

    # --- WIZARDS & INPUTS ---
    
    def add_config_wizard(self):
        """Walks user through adding a shortcut, command, or script."""
        self.clear_screen()
        self.render_header()
        
        console.print("[bold cyan]Configuration Wizard[/bold cyan]")
        console.print("What would you like to add?")
        options = [
            ("1", "Application shortcut (open a GUI program or path)"),
            ("2", "Quick command (a pre-configured CLI script/command line)"),
            ("3", "Script (reference to an external python, powershell, or shell file)"),
            ("Esc", "Cancel")
        ]
        for idx, desc in options:
            console.print(f"  [bold cyan]{idx}[/bold cyan] - {desc}")
            
        opt = self.get_key()
        
        self.clear_screen()
        self.render_header()
        
        if opt == "1":
            console.print("[bold cyan]Add Application Shortcut[/bold cyan]")
            name = Prompt.ask("Application Name")
            path = Prompt.ask("Executable Path or Shell Command (e.g. calc.exe, C:\\App\\app.exe)")
            args = Prompt.ask("Default Arguments", default="")
            desc = Prompt.ask("Short Description", default="")
            
            if name and path:
                self.config_manager.add_app(name, path, args, desc)
                self.set_message(f"Added app shortcut for '{name}'")
                
        elif opt == "2":
            console.print("[bold cyan]Add Quick Command[/bold cyan]")
            name = Prompt.ask("Command Name")
            cmd = Prompt.ask("CLI Command String (e.g. git status, ipconfig /all)")
            desc = Prompt.ask("Short Description", default="")
            
            if name and cmd:
                self.config_manager.add_command(name, cmd, shell=True, description=desc)
                self.set_message(f"Added command '{name}'")
                
        elif opt == "3":
            console.print("[bold cyan]Add Script Reference[/bold cyan]")
            name = Prompt.ask("Script Name")
            file_path = Prompt.ask("Script File Path")
            interpreter = Prompt.ask("Interpreter", choices=["auto", "python", "powershell", "cmd", "shell"], default="auto")
            desc = Prompt.ask("Short Description", default="")
            
            if name and file_path:
                self.config_manager.add_script(name, file_path, interpreter, desc)
                self.set_message(f"Added script reference for '{name}'")
                
        # Reset selection index
        self.selected_index = 4

    # --- EXECUTION STREAMS ---
    
    def execute_and_stream(self, name, cmd_str, shell=True):
        """Runs command, streams logs live using rich.live, and logs history."""
        self.clear_screen()
        self.render_header()
        
        console.print(Panel(f"[bold yellow]Executing:[/] {cmd_str}\n[dim]Streaming real-time stdout/stderr output below...[/dim]", border_style="yellow"))
        console.print("-" * 80)
        
        collected_output = []
        
        # We start the runner and print lines in real-time
        return_code = 0
        duration = 0.0
        
        try:
            for out_type, content in self.runner.run_command(cmd_str, shell=shell):
                if out_type == "stdout":
                    console.print(content, end="")
                    collected_output.append(content)
                elif out_type == "status":
                    return_code, duration = content
                elif out_type == "error":
                    console.print(f"[bold red]{content}[/bold red]")
                    collected_output.append(content + "\n")
        except KeyboardInterrupt:
            console.print("\n[bold red]Execution interrupted by user (Ctrl+C).[/bold red]")
            return_code = -1
            collected_output.append("Interrupted by user.\n")
            
        console.print("-" * 80)
        
        # Log to history
        full_out_str = "".join(collected_output)
        if self.config_manager.config["settings"]["log_history"]:
            self.runner.log_to_history(name, cmd_str, return_code, full_out_str, duration)
            
        status_msg = f"[bold green]Success[/]" if return_code == 0 else f"[bold red]Failed (Exit Code: {return_code})[/]"
        console.print(f"Process ended. Status: {status_msg} | Duration: {duration:.2f}s")
        console.print("\n[bold cyan]Press any key to return to menu...[/bold cyan]")
        self.get_key()

    def execute_script_stream(self, name, file_path, args, interpreter):
        """Similar to execute_and_stream but handles script translation first."""
        self.clear_screen()
        self.render_header()
        
        console.print(Panel(f"[bold yellow]Running Script:[/] {file_path}\n[bold yellow]Args:[/] {args}\n[dim]Streaming real-time output below...[/dim]", border_style="yellow"))
        console.print("-" * 80)
        
        collected_output = []
        return_code = 0
        duration = 0.0
        
        try:
            for out_type, content in self.runner.run_script(file_path, args, interpreter):
                if out_type == "stdout":
                    console.print(content, end="")
                    collected_output.append(content)
                elif out_type == "status":
                    return_code, duration = content
                elif out_type == "error":
                    console.print(f"[bold red]{content}[/bold red]")
                    collected_output.append(content + "\n")
        except KeyboardInterrupt:
            console.print("\n[bold red]Execution interrupted by user (Ctrl+C).[/bold red]")
            return_code = -1
            collected_output.append("Interrupted by user.\n")
            
        console.print("-" * 80)
        
        full_out_str = "".join(collected_output)
        cmd_representation = f"[{interpreter}] {file_path} {args}"
        if self.config_manager.config["settings"]["log_history"]:
            self.runner.log_to_history(name, cmd_representation, return_code, full_out_str, duration)
            
        status_msg = f"[bold green]Success[/]" if return_code == 0 else f"[bold red]Failed (Exit Code: {return_code})[/]"
        console.print(f"Script ended. Status: {status_msg} | Duration: {duration:.2f}s")
        console.print("\n[bold cyan]Press any key to return to menu...[/bold cyan]")
        self.get_key()

    # --- GENERAL INPUT DISPATCHER ---
    
    def handle_input(self):
        """Reads user key and forwards it to the current screen's handler."""
        key = self.get_key()
        if not key:
            return
            
        if self.current_screen == "main_menu":
            self.handle_main_menu(key)
        elif self.current_screen == "apps":
            self.handle_apps_menu(key)
        elif self.current_screen == "commands":
            self.handle_commands_menu(key)
        elif self.current_screen == "scripts":
            self.handle_scripts_menu(key)
        elif self.current_screen == "explorer":
            self.handle_explorer(key)

    def start_voice_command_loop(self):
        """Starts the interactive voice command listening session."""
        self.set_message("Starting voice command mode...")
        self.clear_screen()
        self.render_header()
        
        # Verify dependencies and output warnings
        from src.voice import SPEECH_REC_AVAILABLE
        if not SPEECH_REC_AVAILABLE:
            self.voice_engine.speak("Voice packages are missing. Starting in text fallback mode.")
        else:
            self.voice_engine.speak("Voice command mode active. I am listening.")
            
        voice_running = True
        status_text = "Idle"
        last_command = ""
        last_response = ""
        
        while voice_running:
            self.clear_screen()
            self.render_header()
            
            # Print voice dashboard
            info_table = Table(show_header=False, box=box.ROUNDED, expand=True)
            info_table.add_column("Key", style="bold cyan", width=15)
            info_table.add_column("Value", style="white")
            
            info_table.add_row("Status", f"[bold yellow]{status_text}[/bold yellow]")
            info_table.add_row("Last Command", f"[bold green]\"{last_command}\"[/bold green]" if last_command else "None")
            info_table.add_row("Response", f"[bold white]{last_response}[/bold white]" if last_response else "None")
            
            help_msg = (
                "🗣️  [bold]Speak commands like:[/bold]\n"
                "  • 'open notepad' / 'launch calculator'\n"
                "  • 'run git status' / 'execute system info'\n"
                "  • 'tell me a joke'\n"
                "  • 'who are you' / 'where am i'\n"
                "  • 'exit' / 'stop' (to close voice mode)"
            )
            
            # Combine into panels
            console.print(Panel(info_table, title="🎙️ Voice Command Dashboard", border_style="yellow"))
            console.print(Panel(help_msg, title="How to Talk to Yuki", border_style="dim"))
            
            # Callback to update the console live
            def update_status(msg):
                nonlocal status_text
                status_text = msg
                self.clear_screen()
                self.render_header()
                
                status_table = Table(show_header=False, box=box.ROUNDED, expand=True)
                status_table.add_row("Status", f"[bold yellow]{status_text}[/bold yellow]")
                status_table.add_row("Last Command", f"[bold green]\"{last_command}\"[/bold green]" if last_command else "None")
                status_table.add_row("Response", f"[bold white]{last_response}[/bold white]" if last_response else "None")
                
                console.print(Panel(status_table, title="🎙️ Voice Command Dashboard", border_style="yellow"))
                console.print(Panel(help_msg, title="How to Talk to Yuki", border_style="dim"))
                
            # Listen
            command = self.voice_listener.listen(update_status)
            if not command:
                status_text = "Idle"
                continue
                
            last_command = command
            status_text = "Processing..."
            
            # Process command and get response
            exit_voice, response_text = self.process_voice_command(command)
            last_response = response_text
            
            if response_text:
                update_status("Responding...")
                self.voice_engine.speak(response_text)
                
            if exit_voice:
                voice_running = False
                
            status_text = "Idle"
            time.sleep(1.0) # Pause briefly so user can see what happened
            
        self.set_message("Exited voice command mode.")
        self.current_screen = "main_menu"
        self.selected_index = 4

    def process_voice_command(self, command):
        """
        Parses voice input and performs matching actions.
        Returns tuple: (bool: should_exit, str: response_text)
        """
        command = command.lower().strip()
        
        # Check exit
        if command in ("exit", "stop", "quit", "close", "bye", "exit voice", "exit voice mode"):
            return True, "Goodbye! Exiting voice command mode."
            
        # Check simple assistant questions
        if "who are you" in command or "your name" in command:
            return False, "I am Yuki, your desktop helper and automation assistant."
            
        if "tell" in command and "joke" in command:
            from src.voice import get_programmer_joke
            return False, get_programmer_joke()
            
        if "where am i" in command or "current directory" in command or "current folder" in command:
            curr_dir = self.explorer.get_current_dir()
            folder_name = Path(curr_dir).name or curr_dir
            return False, f"You are currently in the folder: {folder_name}"
            
        # Launch applications: Match "open X" or "launch X" or "start X"
        for launch_keyword in ("open ", "launch ", "start "):
            if command.startswith(launch_keyword):
                app_name = command[len(launch_keyword):].strip()
                apps = self.config_manager.config["apps"]
                matched_app = next((a for a in apps if app_name in a["name"].lower()), None)
                
                if matched_app:
                    success, msg = launch_app(matched_app["path"], matched_app.get("args", ""))
                    if success:
                        return False, f"Opening {matched_app['name']}."
                    else:
                        return False, f"I tried to open {matched_app['name']}, but encountered an error."
                else:
                    return False, f"I could not find an application named {app_name} in your shortcuts."
                    
        # Execute commands: Match "run X" or "execute X"
        for run_keyword in ("run ", "execute "):
            if command.startswith(run_keyword):
                cmd_name = command[len(run_keyword):].strip()
                commands = self.config_manager.config["commands"]
                scripts = self.config_manager.config["scripts"]
                
                matched_cmd = next((c for c in commands if cmd_name in c["name"].lower()), None)
                if matched_cmd:
                    self.voice_engine.speak(f"Running command: {matched_cmd['name']}")
                    self.execute_and_stream(matched_cmd["name"], matched_cmd["cmd"], matched_cmd.get("shell", True))
                    return False, "Command execution complete."
                    
                matched_scr = next((s for s in scripts if cmd_name in s["name"].lower()), None)
                if matched_scr:
                    self.voice_engine.speak(f"Running script: {matched_scr['name']}")
                    self.execute_script_stream(matched_scr["name"], matched_scr["file_path"], "", matched_scr.get("interpreter", "auto"))
                    return False, "Script execution complete."
                    
                return False, f"I could not find a registered command or script named {cmd_name}."
                
        # File navigation commands
        if command in ("go to parent", "go up", "go back"):
            self.explorer.navigate_to("..")
            self.explorer_items = self.explorer.list_contents()
            return False, "Moved up one directory."
            
        for nav_keyword in ("go to ", "navigate to ", "change directory to ", "open folder "):
            if command.startswith(nav_keyword):
                folder_name = command[len(nav_keyword):].strip()
                folders = [item for item in self.explorer_items if item["is_dir"]]
                matched_folder = next((f for f in folders if folder_name in f["name"].lower()), None)
                
                if matched_folder:
                    success, msg = self.explorer.navigate_to(matched_folder["path"])
                    if success:
                        self.explorer_items = self.explorer.list_contents()
                        return False, f"Navigated into {matched_folder['name']}."
                    else:
                        return False, f"Could not navigate to {matched_folder['name']}: {msg}"
                else:
                    return False, f"I could not find a subfolder named {folder_name} in the current directory."

        return False, f"I heard you say: {command}. Say 'help' or try saying 'open calculator'."

