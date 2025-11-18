"""
Wolf CLI Screenshot Utility

Captures full-screen screenshots on Windows and saves them to the current working directory.
"""

import os
import sys
import ctypes
from datetime import datetime
from wolf.utils.paths import get_screenshots_dir
from PIL import ImageGrab
import pathlib
import os
from typing import Optional

import base64
from io import BytesIO

def get_most_recent_screenshot(screenshots_dir: Optional[str] = None) -> Optional[tuple[str, str]]:
    """
    Finds the most recently modified file in the screenshots directory.

    Args:
        screenshots_dir (Optional[str]): The directory to search. If None, uses the default.

    Returns:
        Optional[tuple[str, str]]: A tuple containing the absolute path to the most recent file
                                   and the base64-encoded image data, or None if the directory is empty.
    """
    if screenshots_dir is None:
        screenshots_dir = get_screenshots_dir()
    
    try:
        files = [os.path.join(screenshots_dir, f) for f in os.listdir(screenshots_dir) if os.path.isfile(os.path.join(screenshots_dir, f))]
        if not files:
            return None
        
        latest_file = max(files, key=os.path.getmtime)
        
        with open(latest_file, "rb") as f:
            img_base64 = base64.b64encode(f.read()).decode('utf-8')
            
        return os.path.abspath(latest_file), img_base64
    except FileNotFoundError:
        return None

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
    Capture a full-screen screenshot and save it to the wolf-cli-screenshots directory.
    
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
    try:
        img = ImageGrab.grab(all_screens=True)
        if img is None:
            raise Exception("Failed to capture screenshot: ImageGrab returned None")
    except Exception as e:
        raise Exception(f"Failed to capture screenshot: {e}") from e
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"wolf-screenshot_{timestamp}.png"
    
    # Determine the screenshot directory
    screenshot_dir = get_screenshots_dir()
    
    # Create the directory if it doesn't exist
    try:
        screenshot_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise Exception(f"Failed to create screenshot directory '{screenshot_dir}': {e}") from e
    
    # Resolve to absolute path
    path = (screenshot_dir / filename).resolve()
    
    # Save to the designated screenshot directory
    try:
        img.save(str(path), "PNG")
    except Exception as e:
        raise Exception(f"Failed to save screenshot to '{path}': {e}") from e
    
    # Verify the file was actually created
    if not path.exists():
        raise Exception(f"Screenshot file was not created at '{path}'")
    
    if path.stat().st_size == 0:
        raise Exception(f"Screenshot file was created but is empty at '{path}'")
    
    return str(path)

