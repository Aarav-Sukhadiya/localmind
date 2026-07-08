import asyncio
import tempfile
import os
from tools.registry import BaseTool
from core.schemas import ToolResult

class PythonTool(BaseTool):
    name = "python"
    description = "Execute a Python script and return stdout/stderr"
    parameters = {
        "properties": {
            "code": {"type": "string", "description": "Python code to execute"},
            "timeout": {"type": "integer", "description": "Timeout in seconds", "default": 60}
        },
        "required": ["code"]
    }

    async def execute(self, code: str, timeout: int = 60) -> ToolResult:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
            
        try:
            process = await asyncio.create_subprocess_exec(
                "python3", temp_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            
            out_str = stdout.decode('utf-8', errors='replace')
            err_str = stderr.decode('utf-8', errors='replace')
            
            output = out_str
            if err_str:
                output += f"\nSTDERR:\n{err_str}"
                
            return ToolResult(success=process.returncode == 0, output=output.strip())
        except asyncio.TimeoutError:
            try:
                process.kill()
            except ProcessLookupError:
                pass
            return ToolResult(success=False, output="", error="Script timed out")
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
