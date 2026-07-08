import os
import shutil
from tools.registry import BaseTool
from core.schemas import ToolResult

class FileTool(BaseTool):
    name = "file"
    description = "Create, read, update, delete, or list files and directories"
    parameters = {
        "properties": {
            "action": {
                "type": "string",
                "enum": ["read", "write", "append", "delete", "list", "mkdir", "exists", "move", "copy"]
            },
            "path": {"type": "string", "description": "Target file or directory path"},
            "content": {"type": "string", "description": "Content to write (for write/append)"},
            "destination": {"type": "string", "description": "Destination path (for move/copy)"}
        },
        "required": ["action", "path"]
    }

    def __init__(self, base_directory: str = "~/localmind_workspace/"):
        self.base_directory = os.path.expanduser(base_directory)
        os.makedirs(self.base_directory, exist_ok=True)

    def _resolve_path(self, target_path: str) -> str:
        full_path = os.path.abspath(os.path.join(self.base_directory, target_path))
        if not full_path.startswith(os.path.abspath(self.base_directory)):
            raise ValueError("Path traversal attempt blocked")
        return full_path

    async def execute(self, action: str, path: str, content: str = "", destination: str = "") -> ToolResult:
        try:
            full_path = self._resolve_path(path)
            
            if action == "read":
                if not os.path.exists(full_path):
                    return ToolResult(success=False, output="", error="File not found")
                # Simple binary detection
                with open(full_path, 'rb') as f:
                    chunk = f.read(1024)
                    if b'\0' in chunk:
                        return ToolResult(success=True, output=f"Binary file ({os.path.getsize(full_path)} bytes)")
                with open(full_path, 'r', encoding='utf-8') as f:
                    return ToolResult(success=True, output=f.read())
            
            elif action == "write":
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return ToolResult(success=True, output="File written successfully")
                
            elif action == "append":
                with open(full_path, 'a', encoding='utf-8') as f:
                    f.write(content)
                return ToolResult(success=True, output="Content appended successfully")
                
            elif action == "delete":
                if os.path.isfile(full_path):
                    os.remove(full_path)
                elif os.path.isdir(full_path):
                    shutil.rmtree(full_path)
                else:
                    return ToolResult(success=False, output="", error="Path not found")
                return ToolResult(success=True, output="Deleted successfully")
                
            elif action == "list":
                if not os.path.isdir(full_path):
                    return ToolResult(success=False, output="", error="Not a directory")
                items = os.listdir(full_path)
                return ToolResult(success=True, output="\n".join(items) if items else "(empty directory)")
                
            elif action == "mkdir":
                os.makedirs(full_path, exist_ok=True)
                return ToolResult(success=True, output="Directory created")
                
            elif action == "exists":
                exists = os.path.exists(full_path)
                return ToolResult(success=True, output=str(exists))
                
            elif action in ["move", "copy"]:
                if not destination:
                    return ToolResult(success=False, output="", error="Destination required")
                full_dest = self._resolve_path(destination)
                os.makedirs(os.path.dirname(full_dest), exist_ok=True)
                if action == "move":
                    shutil.move(full_path, full_dest)
                else:
                    if os.path.isdir(full_path):
                        shutil.copytree(full_path, full_dest)
                    else:
                        shutil.copy2(full_path, full_dest)
                return ToolResult(success=True, output=f"Successfully {action}d")
                
            else:
                return ToolResult(success=False, output="", error="Unknown action")
                
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))
