"""
Wolf CLI File Operations

Tool implementations for file and directory operations.
"""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import send2trash

from ..utils.logging_utils import log_tool, log_error, log_warn
from ..utils.paths import normalize_path, ensure_parent_dir, get_file_size_human


def create_file(path: str, content: str = "") -> Dict[str, Any]:
    """Create a new file"""
    try:
        file_path = normalize_path(path)
        
        log_tool("create_file", f"Creating {file_path}...")
        
        # Check if file already exists
        if file_path.exists():
            return {
                "ok": False,
                "path": str(file_path),
                "error": "File already exists. Use write_file to overwrite.",
            }
        
        # Ensure parent directory exists
        file_path = ensure_parent_dir(file_path)
        
        # Write content
        bytes_written = file_path.write_text(content, encoding='utf-8')
        
        log_tool("create_file", f"Done. bytes_written={bytes_written}")
        
        return {
            "ok": True,
            "path": str(file_path),
            "bytes_written": bytes_written,
            "success": True,
        }
    
    except Exception as e:
        log_error(f"Error creating file: {str(e)}")
        return {
            "ok": False,
            "path": path,
            "error": str(e),
        }


def read_file(path: str) -> Dict[str, Any]:
    """Read a file"""
    try:
        file_path = normalize_path(path)
        
        log_tool("read_file", f"Reading {file_path}...")
        
        if not file_path.exists():
            return {
                "ok": False,
                "path": str(file_path),
                "error": "File not found",
            }
        
        if not file_path.is_file():
            return {
                "ok": False,
                "path": str(file_path),
                "error": "Path is not a file",
            }
        
        content = file_path.read_text(encoding='utf-8')
        size = file_path.stat().st_size
        
        log_tool("read_file", f"Done. size={get_file_size_human(file_path)}")
        
        return {
            "ok": True,
            "path": str(file_path),
            "content": content,
            "size": size,
        }
    
    except Exception as e:
        log_error(f"Error reading file: {str(e)}")
        return {
            "ok": False,
            "path": path,
            "error": str(e),
        }


def write_file(path: str, content: str) -> Dict[str, Any]:
    """Write or overwrite a file"""
    try:
        file_path = normalize_path(path)
        
        log_tool("write_file", f"Writing to {file_path}...")
        
        # Backup if exists
        backed_up = False
        if file_path.exists():
            backup_path = file_path.with_suffix(file_path.suffix + '.bak')
            shutil.copy2(file_path, backup_path)
            backed_up = True
            log_tool("write_file", f"Backed up to {backup_path}")
        
        # Ensure parent directory exists
        file_path = ensure_parent_dir(file_path)
        
        # Write content
        bytes_written = file_path.write_text(content, encoding='utf-8')
        
        log_tool("write_file", f"Done. bytes_written={bytes_written}")
        
        return {
            "ok": True,
            "path": str(file_path),
            "bytes_written": bytes_written,
            "backed_up": backed_up,
        }
    
    except Exception as e:
        log_error(f"Error writing file: {str(e)}")
        return {
            "ok": False,
            "path": path,
            "error": str(e),
        }


def delete_file(path: str) -> Dict[str, Any]:
    """Delete a file (move to recyclebin)"""
    try:
        file_path = normalize_path(path)
        
        log_tool("delete_file", f"Deleting {file_path}...")
        
        if not file_path.exists():
            return {
                "ok": False,
                "path": str(file_path),
                "error": "File not found",
            }
        
        # Try to send to trash first
        recycled = False
        try:
            send2trash.send2trash(str(file_path))
            recycled = True
            log_tool("delete_file", "Moved to Recycle Bin")
        except:
            # Fallback to permanent delete
            file_path.unlink()
            log_warn("Could not move to Recycle Bin, permanently deleted")
        
        return {
            "ok": True,
            "path": str(file_path),
            "deleted": True,
            "recycled": recycled,
        }
    
    except Exception as e:
        log_error(f"Error deleting file: {str(e)}")
        return {
            "ok": False,
            "path": path,
            "error": str(e),
        }


def list_directory(path: str = ".", recursive: bool = False) -> Dict[str, Any]:
    """List directory contents"""
    try:
        dir_path = normalize_path(path)
        
        log_tool("list_directory", f"Listing {dir_path}...")
        
        if not dir_path.exists():
            return {
                "ok": False,
                "path": str(dir_path),
                "error": "Directory not found",
            }
        
        if not dir_path.is_dir():
            return {
                "ok": False,
                "path": str(dir_path),
                "error": "Path is not a directory",
            }
        
        items = []
        
        if recursive:
            pattern = "**/*"
        else:
            pattern = "*"
        
        for item in dir_path.glob(pattern):
            try:
                stat = item.stat()
                items.append({
                    "name": item.name,
                    "path": str(item),
                    "type": "file" if item.is_file() else "directory",
                    "size": stat.st_size if item.is_file() else 0,
                    "size_human": get_file_size_human(item) if item.is_file() else "-",
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                })
            except:
                # Skip files we can't access
                continue
        
        log_tool("list_directory", f"Found {len(items)} items")
        
        return {
            "ok": True,
            "path": str(dir_path),
            "items": items,
            "count": len(items),
        }
    
    except Exception as e:
        log_error(f"Error listing directory: {str(e)}")
        return {
            "ok": False,
            "path": path,
            "error": str(e),
        }


def get_file_info(path: str) -> Dict[str, Any]:
    """Get file information"""
    try:
        file_path = normalize_path(path)
        
        if not file_path.exists():
            return {
                "ok": False,
                "path": str(file_path),
                "error": "File not found",
            }
        
        stat = file_path.stat()
        
        return {
            "ok": True,
            "path": str(file_path),
            "name": file_path.name,
            "size": stat.st_size,
            "size_human": get_file_size_human(file_path),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "is_file": file_path.is_file(),
            "is_dir": file_path.is_dir(),
        }
    
    except Exception as e:
        log_error(f"Error getting file info: {str(e)}")
        return {
            "ok": False,
            "path": path,
            "error": str(e),
        }


def move_file(source: str, destination: str) -> Dict[str, Any]:
    """Move or rename a file"""
    try:
        src_path = normalize_path(source)
        dest_path = normalize_path(destination)
        
        log_tool("move_file", f"Moving {src_path} to {dest_path}...")
        
        if not src_path.exists():
            return {
                "ok": False,
                "source": str(src_path),
                "destination": str(dest_path),
                "error": "Source file not found",
            }
        
        # Ensure destination parent exists
        dest_path = ensure_parent_dir(dest_path)
        
        shutil.move(str(src_path), str(dest_path))
        
        log_tool("move_file", "Done")
        
        return {
            "ok": True,
            "source": str(src_path),
            "destination": str(dest_path),
            "success": True,
        }
    
    except Exception as e:
        log_error(f"Error moving file: {str(e)}")
        return {
            "ok": False,
            "source": source,
            "destination": destination,
            "error": str(e),
        }


def copy_file(source: str, destination: str) -> Dict[str, Any]:
    """Copy a file"""
    try:
        src_path = normalize_path(source)
        dest_path = normalize_path(destination)
        
        log_tool("copy_file", f"Copying {src_path} to {dest_path}...")
        
        if not src_path.exists():
            return {
                "ok": False,
                "source": str(src_path),
                "destination": str(dest_path),
                "error": "Source file not found",
            }
        
        # Ensure destination parent exists
        dest_path = ensure_parent_dir(dest_path)
        
        shutil.copy2(str(src_path), str(dest_path))
        
        bytes_copied = dest_path.stat().st_size
        
        log_tool("copy_file", f"Done. bytes_copied={bytes_copied}")
        
        return {
            "ok": True,
            "source": str(src_path),
            "destination": str(dest_path),
            "bytes_copied": bytes_copied,
        }
    
    except Exception as e:
        log_error(f"Error copying file: {str(e)}")
        return {
            "ok": False,
            "source": source,
            "destination": destination,
            "error": str(e),
        }
