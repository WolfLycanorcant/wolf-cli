"""
Wolf CLI Platform Utilities

Cross-platform detection and configuration utilities.
"""

import platform
import shutil
from typing import Tuple, List


def get_os_type() -> str:
    """
    Get the current operating system type.
    
    Returns:
        'windows', 'linux', or 'darwin' (macOS)
    """
    system = platform.system().lower()
    if system == 'darwin':
        return 'darwin'
    elif system in ('linux', 'freebsd', 'openbsd'):
        return 'linux'
    else:
        return 'windows'


def is_windows() -> bool:
    """Check if running on Windows."""
    return get_os_type() == 'windows'


def is_linux() -> bool:
    """Check if running on Linux."""
    return get_os_type() == 'linux'


def is_macos() -> bool:
    """Check if running on macOS."""
    return get_os_type() == 'darwin'


def get_shell_command() -> Tuple[str, List[str]]:
    """
    Get the appropriate shell command and default flags for the platform.
    
    Returns:
        Tuple of (shell_executable, default_flags)
        
    Examples:
        Windows: ('pwsh', ['-NoProfile', '-NonInteractive', '-Command'])
        Linux/macOS: ('bash', ['-c'])
    """
    os_type = get_os_type()
    
    if os_type == 'windows':
        # Try PowerShell 7+ first, fall back to older powershell
        if shutil.which('pwsh'):
            return ('pwsh', ['-NoProfile', '-NonInteractive', '-Command'])
        elif shutil.which('powershell'):
            return ('powershell', ['-NoProfile', '-NonInteractive', '-Command'])
        else:
            # Fallback to cmd if no PowerShell
            return ('cmd', ['/c'])
    else:
        # Unix-like systems (Linux, macOS, BSD)
        # Try bash first, fall back to sh
        if shutil.which('bash'):
            return ('bash', ['-c'])
        else:
            return ('sh', ['-c'])


def get_root_disk_path() -> str:
    """
    Get the root disk path for the platform.
    
    Returns:
        'C:\\' for Windows, '/' for Unix-like systems
    """
    return 'C:\\' if is_windows() else '/'


def get_platform_name() -> str:
    """
    Get a human-readable platform name.
    
    Returns:
        Platform name like 'Windows', 'Linux', 'macOS'
    """
    os_type = get_os_type()
    if os_type == 'windows':
        return 'Windows'
    elif os_type == 'linux':
        return 'Linux'
    elif os_type == 'darwin':
        return 'macOS'
    else:
        return platform.system()


def get_shell_name() -> str:
    """
    Get the name of the shell being used.
    
    Returns:
        Shell name like 'PowerShell', 'Bash', 'sh', 'cmd'
    """
    shell_cmd, _ = get_shell_command()
    
    shell_names = {
        'pwsh': 'PowerShell',
        'powershell': 'PowerShell',
        'bash': 'Bash',
        'sh': 'sh',
        'cmd': 'cmd',
    }
    
    return shell_names.get(shell_cmd, shell_cmd)


def format_path_for_os(path: str) -> str:
    """
    Format a path string for the current OS.
    
    Args:
        path: Path string (can use forward slashes)
        
    Returns:
        Properly formatted path for the OS
    """
    if is_windows():
        return path.replace('/', '\\')
    else:
        return path.replace('\\', '/')
