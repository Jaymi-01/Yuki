# ❄️ Yuki Command Center

**Yuki** is an interactive, highly aesthetic console helper, desktop launcher, and automator written in Python for Windows systems. It operates in two modes: a gorgeous interactive Terminal User Interface (TUI) and a direct Command Line Interface (CLI) runner.

---

## ✨ Features

- **🚀 Application Launcher**: Start your favorite applications (Notepad, Calculator, VS Code, Browser, etc.) or open directories directly without locking your terminal window.
- **🖥️ Command Runner**: Execute command sequences (e.g., `git status`, system lookups, clean temp, netstat monitoring) with real-time, line-buffered output streaming and duration tracking.
- **📜 Script Runner**: Run external python (`.py`), PowerShell (`.ps1`), or batch/cmd (`.bat`/`.cmd`) scripts, stream output in real-time, and supply custom arguments.
- **📁 Interactive File Explorer**:
  - Browse files and folders using arrow keys and Enter.
  - **Syntax-Highlighted Viewer**: View file contents (Python, JSON, JavaScript, Batch, PowerShell, Markdown, HTML, etc.) with custom themes directly in the console.
  - **Terminal Text Editor**: Overwrite or append file lines quickly from inside the terminal.
  - **Default Application Integration**: Instantly open files in their associated desktop apps (e.g. edit in VS Code, open images in Paint).
  - **Custom Shell Actions**: Select a file and execute templates like `python {file}` or `git add {file}`.
  - **File Operations**: Create files/folders and delete them with confirmation dialogs.
- **🎙️ Voice Command Mode**: Control Yuki hands-free by speaking. Launch applications, run CLI commands or scripts, navigate folders, hear text-to-speech feedback, or ask for programmer jokes.
- **🛡️ Execution Logs**: Automatically tracks process exit codes and duration, logging output history to `history.json`.
- **⚙️ Setup Wizard**: Add apps, commands, or scripts interactively directly from the dashboard.

---

## 🚀 Getting Started

### 📋 Prerequisites
- **Python 3.7+**
- Python libraries will be automatically installed on first run (uses the `rich` library for terminal rendering).
- **For Voice Features (Optional)**:
  ```bash
  pip install pyttsx3 speechrecognition pyaudio
  ```
  *(If voice packages are missing or no mic is detected, Yuki automatically falls back to offline speech synthesis via Windows PowerShell and keyboard command input, ensuring zero-crash startup).*

### 🖥️ Running Interactive Dashboard
Simply run Yuki from the workspace directory:
```bash
python yuki.py
```
*(Yuki automatically sets output streams to UTF-8 to display gorgeous emojis and layouts on Windows PowerShell and Command Prompt).*

### 🕹️ Keyboard Controls in TUI
- **↑ / ↓ Arrow Keys**: Navigate menu items, lists, and directories.
- **Enter**: Select options, navigate into folders, open files, or trigger menus.
- **Backspace**: Go up one directory in the File Explorer.
- **Esc**: Go back to the previous screen or exit Yuki.
- **Del**: Delete a registered shortcut or delete a file/folder in the explorer.
- **N**: Create a new file in the current explorer directory.
- **D**: Create a new folder in the current explorer directory.
- **V**: Hotkey to instantly launch Voice Command Mode from the Main Menu.

---

## ⚡ CLI Direct Commands

You can bypass the TUI to run registered items instantly from other CLI scripts or shortcuts:

### 1. List registered commands, scripts, and apps:
```bash
python yuki.py list
```

### 2. Launch an application:
```bash
python yuki.py launch "Notepad"
# Pass arguments:
python yuki.py launch "Notepad" --args "myfile.txt"
```

### 3. Run a quick command:
```bash
python yuki.py run "Git Status"
```

### 4. Run a script with arguments:
```bash
python yuki.py script "My Script" --args "--verbose --output clean"
```

### 5. Register new shortcuts directly:
```bash
python yuki.py add-app "Chrome" "chrome.exe" --args "https://google.com" --desc "Open Google in Chrome"
python yuki.py add-cmd "Ports" "netstat -ano" --desc "Show active TCP connections"
```

### 6. Start directly in Voice Command Mode:
```bash
python yuki.py voice
```

---

## 📂 Project Structure

- `yuki.py`: The entry point script and CLI parser.
- `config.json`: Persistent storage for your apps, commands, and settings.
- `history.json`: Truncating log for past task command/script runs.
- `src/`:
  - `config_manager.py`: Settings loader, saver, and modifier.
  - `app_launcher.py`: Asynchronous desktop process execution.
  - `runner.py`: Stream processing command and script subprocess handler.
  - `explorer.py`: Directory crawling, file manipulation, and file-details retriever.
  - `voice.py`: Speech recognition (STT) and speech synthesis (TTS) handlers with fallback setups.
  - `tui.py`: Core UI keyboard listener, layout panels, tables, and page routers.

