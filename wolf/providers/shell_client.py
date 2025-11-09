"""
Wolf CLI Shell Client

Cross-platform wrapper for executing shell commands with safety and timeout controls.
Supports PowerShell (Windows), Bash (Linux/macOS), and fallback shells.
"""

import subprocess
from typing import Dict, Any
import psutil

from ..utils.logging_utils import log_tool, log_error, log_debug
from ..utils.validation import sanitize_command
from ..utils.platform_utils import (
    get_shell_command,
    get_root_disk_path,
    get_platform_name,
    get_shell_name,
    is_windows
)


def execute_shell_command(
    command: str,
    timeout: int = 120,
    capture_output: bool = True
) -> Dict[str, Any]:
    """
    Execute a shell command on the appropriate platform shell.
    
    Args:
        command: Shell command to execute
        timeout: Timeout in seconds
        capture_output: Whether to capture stdout/stderr
        
    Returns:
        Dictionary with keys: command, stdout, stderr, exit_code, success, shell
    """
    # Sanitize command
    command = sanitize_command(command)
    
    log_tool("execute_command", f"Preparing: {command}")
    
    try:
        # Get platform-appropriate shell
        shell_exe, shell_flags = get_shell_command()
        shell_name = get_shell_name()
        
        # Build command
        cmd = [shell_exe] + shell_flags + [command]
        
        log_tool("execute_command", f"Running via {shell_name}...")
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
            "shell": shell_name,
        }
    
    except subprocess.TimeoutExpired:
        log_error(f"Command timed out after {timeout} seconds")
        return {
            "command": command,
            "stdout": "",
            "stderr": f"Command timed out after {timeout} seconds",
            "exit_code": -1,
            "success": False,
            "shell": get_shell_name(),
        }
    
    except FileNotFoundError:
        shell_name = get_shell_name()
        log_error(f"{shell_name} not found. Make sure it is installed and in PATH.")
        return {
            "command": command,
            "stdout": "",
            "stderr": f"{shell_name} not found",
            "exit_code": -1,
            "success": False,
            "shell": shell_name,
        }
    
    except Exception as e:
        log_error(f"Error executing command: {str(e)}", exc_info=True)
        return {
            "command": command,
            "stdout": "",
            "stderr": str(e),
            "exit_code": -1,
            "success": False,
            "shell": get_shell_name(),
        }


def get_system_info() -> Dict[str, Any]:
    """
    Get system information using psutil (cross-platform).
    
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
        disk_path = get_root_disk_path()
        disk = psutil.disk_usage(disk_path)
        
        platform_name = get_platform_name()
        shell_name = get_shell_name()
        
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
                "path": disk_path,
                "total_gb": round(disk.total / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "percent": disk.percent,
            },
            "platform": platform_name,
            "shell": shell_name,
        }
    
    except Exception as e:
        log_error(f"Error getting system info: {str(e)}")
        return {"error": str(e)}


# Backwards compatibility aliases
execute_powershell_command = execute_shell_command
