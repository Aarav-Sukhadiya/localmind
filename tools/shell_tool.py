import asyncio
from tools.registry import BaseTool
from core.schemas import ToolResult

class ShellTool(BaseTool):
    name = "shell"
    description = "Execute a shell command and return stdout/stderr"
    parameters = {
        "properties": {
            "command": {"type": "string", "description": "The shell command to run"},
            "timeout": {"type": "integer", "description": "Timeout in seconds", "default": 30},
            "cwd": {"type": "string", "description": "Working directory", "default": "."}
        },
        "required": ["command"]
    }
    
    def __init__(self, blocked_commands=None):
        self.blocked_commands = blocked_commands or ["rm -rf /", "mkfs", "dd", ":(){:|:&};:"]

    async def execute(self, command: str, timeout: int = 30, cwd: str = ".") -> ToolResult:
        for blocked in self.blocked_commands:
            if blocked in command:
                return ToolResult(success=False, output="", error=f"Command blocked: contains {blocked}")
                
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            
            out_str = stdout.decode('utf-8', errors='replace')
            err_str = stderr.decode('utf-8', errors='replace')
            
            output = out_str
            if err_str:
                output += f"\nSTDERR:\n{err_str}"
                
            # Truncate at 10000 chars
            if len(output) > 10000:
                output = output[:10000] + "\n...[TRUNCATED]"
                
            return ToolResult(success=process.returncode == 0, output=output.strip())
        except asyncio.TimeoutError:
            try:
                process.kill()
            except ProcessLookupError:
                pass
            return ToolResult(success=False, output="", error="Command timed out")
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))
