"""
Wolf CLI Path Utilities

Cross-platform path resolution and validation (Windows, Linux, macOS).
"""

import os
import platform
from pathlib import Path
from typing import Union


def get_screenshots_dir() -> Path:
    """
    Get the screenshots directory path.
    Same directory as screenshots: ~/Pictures/wolf-cli-screenshots
    Creates the directory if it doesn't exist.
    
    Returns:
        Path: Absolute path to the screenshots directory
    """
    base = Path.home() / "Pictures" / "wolf-cli-screenshots"
    base.mkdir(parents=True, exist_ok=True)
    return base


def get_config_dir(app_name: str = "wolf-cli") -> Path:
    """
    Get the OS-appropriate configuration directory for the application.
    
    Args:
        app_name: Name of the application (default: "wolf-cli")
        
    Returns:
        Path to config directory:
        - Windows: %APPDATA%\\{app_name} (falls back to ~\\{app_name})
        - Linux/macOS: $XDG_CONFIG_HOME/{app_name} (falls back to ~/.config/{app_name})
    
    Examples:
        >>> get_config_dir("wolf-cli")  # Windows
        WindowsPath('C:/Users/User/AppData/Roaming/wolf-cli')
        
        >>> get_config_dir("wolf-cli")  # Linux
        PosixPath('/home/user/.config/wolf-cli')
    """
    home = Path.home()
    system = platform.system()
    
    if system == "Windows":
        # Use APPDATA on Windows, fallback to home
        appdata = os.getenv("APPDATA")
        base = Path(appdata) if appdata else home
    else:
        # Use XDG_CONFIG_HOME on Linux/macOS, fallback to ~/.config
        xdg = os.getenv("XDG_CONFIG_HOME")
        base = Path(xdg) if xdg else (home / ".config")
    
    return base / app_name


def normalize_path(path: Union[str, Path], base_dir: Union[str, Path, None] = None) -> Path:
    """
    Normalize and resolve a path safely
    
    Args:
        path: Path to normalize (can be relative or absolute)
        base_dir: Base directory for relative paths (defaults to cwd)
        
    Returns:
        Resolved absolute Path object
    """
    path = Path(path)
    
    # If already absolute, just resolve
    if path.is_absolute():
        return path.resolve()
    
    # Resolve relative to base_dir or cwd
    if base_dir:
        return (Path(base_dir) / path).resolve()
    else:
        return path.resolve()


def ensure_parent_dir(path: Union[str, Path]) -> Path:
    """
    Ensure parent directory exists for a file path
    
    Args:
        path: File path
        
    Returns:
        Resolved path with parent directory created
    """
    path = Path(path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def is_safe_path(path: Union[str, Path], allowed_base: Union[str, Path, None] = None) -> bool:
    """
    Check if a path is safe (doesn't escape allowed base via .. tricks)
    
    Args:
        path: Path to check
        allowed_base: Base directory that must contain the path (optional)
        
    Returns:
        True if path is safe, False otherwise
    """
    try:
        path = Path(path).resolve()
        
        if allowed_base:
            allowed_base = Path(allowed_base).resolve()
            # Check if path is within allowed_base
            return path.is_relative_to(allowed_base)
        
        return True
    except (ValueError, OSError):
        return False


def get_file_size_human(path: Union[str, Path]) -> str:
    """
    Get human-readable file size
    
    Args:
        path: File path
        
    Returns:
        Human-readable size string (e.g., "1.5 MB")
    """
    try:
        size_bytes = Path(path).stat().st_size
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        
        return f"{size_bytes:.1f} PB"
    except OSError:
        return "unknown"


def safe_filename(filename: str) -> str:
    """
    Sanitize a filename to remove invalid characters
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename safe for Windows
    """
    # Windows invalid filename characters
    invalid_chars = '<>:"/\\|?*'
    
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    
    # Ensure not empty
    if not filename:
        filename = "unnamed"
    
    return filename
