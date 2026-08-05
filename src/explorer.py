import os
import sys
from pathlib import Path
from datetime import datetime
import shutil

class FileExplorer:
    def __init__(self, start_dir="."):
        self.current_path = Path(start_dir).resolve()
        
    def get_current_dir(self):
        return str(self.current_path)

    def list_contents(self):
        """
        Scans current directory and returns a sorted list of directories and files.
        Includes a parent directory indicator if not at root.
        """
        folders = []
        files = []
        
        # Add parent directory reference if we're not at the root drive
        if self.current_path.parent != self.current_path:
            folders.append({
                "name": "..",
                "path": str(self.current_path.parent),
                "is_dir": True,
                "size": "-",
                "mtime": "-"
            })

        try:
            for entry in os.scandir(self.current_path):
                try:
                    stats = entry.stat()
                    # Convert size to readable format
                    size_bytes = stats.st_size
                    if entry.is_dir():
                        size_str = "<DIR>"
                    else:
                        if size_bytes < 1024:
                            size_str = f"{size_bytes} B"
                        elif size_bytes < 1024 * 1024:
                            size_str = f"{size_bytes / 1024:.1f} KB"
                        else:
                            size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
                            
                    mtime = datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                except OSError:
                    size_str = "Error"
                    mtime = "Unknown"
                    
                item = {
                    "name": entry.name,
                    "path": str(Path(entry.path).resolve()),
                    "is_dir": entry.is_dir(),
                    "size": size_str,
                    "mtime": mtime
                }
                
                if entry.is_dir():
                    folders.append(item)
                else:
                    files.append(item)
                    
            # Sort folders and files separately
            # We want parent directory (if present) to stay first
            has_parent = folders and folders[0]["name"] == ".."
            parent_item = [folders.pop(0)] if has_parent else []
            
            folders.sort(key=lambda x: x["name"].lower())
            files.sort(key=lambda x: x["name"].lower())
            
            return parent_item + folders + files
            
        except PermissionError:
            # Return empty or parent-only if access denied
            return folders
        except FileNotFoundError:
            # Directory might have been deleted, reset to root or parent
            self.current_path = self.current_path.parent
            return self.list_contents()

    def navigate_to(self, path_str):
        """Navigates to a specific directory path."""
        target_path = Path(path_str).resolve()
        if target_path.is_dir():
            if os.access(target_path, os.R_OK):
                self.current_path = target_path
                return True, f"Navigated to: {self.current_path}"
                
            return False, f"Access denied to: {target_path}"
        return False, f"Not a valid directory: {target_path}"

    def create_directory(self, name):
        """Creates a subdirectory."""
        try:
            target = self.current_path / name
            target.mkdir(parents=True, exist_ok=False)
            return True, f"Directory created: {name}"
        except Exception as e:
            return False, f"Error creating directory: {str(e)}"

    def create_file(self, name, content=""):
        """Creates a new text file."""
        try:
            target = self.current_path / name
            with open(target, "w", encoding="utf-8") as f:
                f.write(content)
            return True, f"File created: {name}"
        except Exception as e:
            return False, f"Error creating file: {str(e)}"

    def delete_item(self, path_str):
        """Deletes a file or directory recursively."""
        target = Path(path_str).resolve()
        if not target.exists():
            return False, f"Item does not exist: {target}"
            
        try:
            if target.is_dir():
                shutil.rmtree(target)
                return True, f"Deleted directory: {target.name}"
            else:
                target.unlink()
                return True, f"Deleted file: {target.name}"
        except Exception as e:
            return False, f"Error deleting item: {str(e)}"

    def get_file_details(self, path_str):
        """Returns details and content of a file."""
        target = Path(path_str).resolve()
        if not target.is_file():
            return False, "Path is not a file", ""
            
        try:
            # Check file size (limit to 1MB for preview in console)
            stat = target.stat()
            size = stat.st_size
            if size > 1024 * 1024:
                return True, f"File is too large for terminal preview ({size / 1024 / 1024:.1f} MB). Open it with an external editor.", ""
                
            # Try to read file as text
            with open(target, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
                
            return True, content, target.suffix.lower()
        except Exception as e:
            return False, f"Error reading file: {str(e)}", ""

    def write_file_content(self, path_str, content):
        """Overwrites or saves content to a file."""
        target = Path(path_str).resolve()
        try:
            with open(target, "w", encoding="utf-8") as f:
                f.write(content)
            return True, "File saved successfully."
        except Exception as e:
            return False, f"Error writing file: {str(e)}"
