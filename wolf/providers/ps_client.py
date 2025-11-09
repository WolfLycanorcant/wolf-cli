"""
Wolf CLI PowerShell Client

Wrapper for executing PowerShell commands with safety and timeout controls.
"""

import subprocess
from typing import Dict, Any, Optional
import psutil

from ..utils.logging_utils import log_tool, log_error, log_debug
from ..utils.validation import sanitize_command
from ..utils.platform_utils import get_root_disk_path


def execute_powershell_command(
    command: str,
    timeout: int = 120,
    capture_output: bool = True
) -> Dict[str, Any]:
    """
    Execute a PowerShell command
    
    Args:
        command: PowerShell command to execute
        timeout: Timeout in seconds
        capture_output: Whether to capture stdout/stderr
        
    Returns:
        Dictionary with keys: command, stdout, stderr, exit_code, success
    """
    # Sanitize command
    command = sanitize_command(command)
    
    log_tool("execute_command", f"Preparing: {command}")
    
    try:
        # Execute via PowerShell with non-interactive mode
        cmd = [
            'pwsh',
            '-NoProfile',
            '-NonInteractive',
            '-Command',
            command
        ]
        
        log_tool("execute_command", "Running...")
        log_debug(f"Full command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            timeout=timeout,
            encoding='utf-8',
            errors='replace'
        )
        
        log_tool("execute_command", f"ExitCode={result.returncode}")
        
        return {
            "command": command,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
            "success": result.returncode == 0,
        }
    
    except subprocess.TimeoutExpired:
        log_error(f"Command timed out after {timeout} seconds")
        return {
            "command": command,
            "stdout": "",
            "stderr": f"Command timed out after {timeout} seconds",
            "exit_code": -1,
            "success": False,
        }
    
    except FileNotFoundError:
        log_error("PowerShell (pwsh) not found. Make sure PowerShell 7+ is installed.")
        return {
            "command": command,
            "stdout": "",
            "stderr": "PowerShell (pwsh) not found",
            "exit_code": -1,
            "success": False,
        }
    
    except Exception as e:
        log_error(f"Error executing command: {str(e)}", exc_info=True)
        return {
            "command": command,
            "stdout": "",
            "stderr": str(e),
            "exit_code": -1,
            "success": False,
        }


def get_system_info() -> Dict[str, Any]:
    """
    Get system information using psutil
    
    Returns:
        Dictionary with system information
    """
    try:
        # CPU info
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Memory info
        memory = psutil.virtual_memory()
        
        # Disk info - use platform-appropriate root path
        disk = psutil.disk_usage(get_root_disk_path())
        
        return {
            "cpu": {
                "percent": cpu_percent,
                "count": cpu_count,
            },
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "percent": memory.percent,
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "percent": disk.percent,
            },
            "platform": "Windows",
        }
    
    except Exception as e:
        log_error(f"Error getting system info: {str(e)}")
        return {"error": str(e)}
