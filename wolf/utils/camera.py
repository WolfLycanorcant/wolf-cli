"""
Wolf CLI Camera Capture Utility

Captures single frames from USB camera (device index 0) silently and saves them
to the wolf-cli-screenshots directory.
"""

import sys
from datetime import datetime
from pathlib import Path
from wolf.utils.paths import get_screenshots_dir
import cv2


class CameraError(RuntimeError):
    """Exception raised when camera capture fails"""
    pass


import base64

def capture_single_frame() -> tuple[str, str]:
    """
    Captures a single frame from USB camera index 0 silently (no preview, no delay)
    and saves it as wolf-camera_YYYY-MM-DD_HH-MM-SS.png under the screenshots dir.
    
    Returns:
        tuple[str, str]: A tuple containing the absolute file path to the saved image
                         and the base64-encoded image data.
        
    Raises:
        CameraError: If camera cannot be opened or frame cannot be captured/saved.
    """
    save_dir = get_screenshots_dir()
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_path = save_dir / f"wolf-camera_{timestamp}.png"
    
    cap = None
    try:
        # Try default backend first
        cap = cv2.VideoCapture(0)
        if not cap or not cap.isOpened():
            # Windows-specific fallback using DirectShow
            if cap:
                cap.release()
            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        
        if not cap or not cap.isOpened():
            raise CameraError(
                "Could not open camera device index 0. "
                "Check permissions and device availability."
            )
        
        # Capture a single frame
        ok, frame = cap.read()
        if not ok or frame is None:
            raise CameraError("Failed to capture a frame from camera device index 0.")
        
        # Save the frame
        if not cv2.imwrite(str(out_path), frame):
            raise CameraError(f"Failed to save image to {out_path}")
        
        # Encode the image as base64
        _, buffer = cv2.imencode('.png', frame)
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return str(out_path.resolve()), img_base64
    
    except Exception as e:
        # Normalize all exceptions to CameraError
        if isinstance(e, CameraError):
            raise
        raise CameraError(str(e)) from e
    
    finally:
        # Always release the camera
        try:
            if cap is not None:
                cap.release()
        except Exception:
            pass
