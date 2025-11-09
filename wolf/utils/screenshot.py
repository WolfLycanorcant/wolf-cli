"""
Wolf CLI Screenshot Utility

Captures full-screen screenshots on Windows and saves them to the current working directory.
"""

import os
import sys
import ctypes
from datetime import datetime
from PIL import ImageGrab
import pathlib


def _ensure_dpi_awareness():
    """
    Enable DPI awareness on Windows to capture high-DPI screenshots correctly.
    Tries per-monitor DPI awareness first, falls back to process DPI aware.
    """
    if sys.platform != "win32":
        return
    
    try:
        # SetProcessDpiAwareness(2) = PROCESS_PER_MONITOR_DPI_AWARE
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            # Fallback to legacy SetProcessDPIAware
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            # If both fail, continue without DPI awareness
            pass


def take_screenshot() -> str:
    """
    Capture a full-screen screenshot and save it to the current working directory.
    
    Returns:
        str: Absolute path to the saved screenshot PNG file.
        
    Raises:
        NotImplementedError: If called on a non-Windows platform.
        Exception: If screenshot capture or save fails.
    """
    if sys.platform != "win32":
        raise NotImplementedError(
            "take_screenshot() is currently implemented for Windows only. "
            "For other platforms, please use platform-specific screenshot tools."
        )
    
    # Ensure proper DPI awareness for high-DPI displays
    _ensure_dpi_awareness()
    
    # Capture all screens
    img = ImageGrab.grab(all_screens=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"wolf-screenshot_{timestamp}.png"
    
    # Determine the screenshot directory
    pictures_dir = pathlib.Path.home() / "Pictures"
    screenshot_dir = pictures_dir / "wolf-cli-screenshots"
    
    # Create the directory if it doesn't exist
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    
    # Save to the designated screenshot directory
    path = screenshot_dir / filename
    img.save(path, "PNG")
    
    return str(path)
