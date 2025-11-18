"""
Wolf CLI Cursor API Client

Integration with Cursor editor API for code-aware operations.
Connects to Cursor API server running on localhost:5005 by default.
"""

import json
from typing import Dict, Any, Optional, List
import requests
from requests.exceptions import RequestException, Timeout

from ..utils.logging_utils import log_tool, log_error, log_debug, log_warn
from ..config_manager import get_config


class CursorAPI:
    """Client for interacting with Cursor editor API"""
    
    def __init__(self, base_url: Optional[str] = None, timeout: int = 10):
        """
        Initialize Cursor API client
        
        Args:
            base_url: Base URL for Cursor API (defaults to config or http://localhost:5005)
            timeout: Request timeout in seconds
        """
        config = get_config()
        self.base_url = base_url or config.get("cursor_api_url", "http://localhost:5005")
        self.timeout = timeout
        self.is_connected = False
    
    def test_connection(self) -> bool:
        """Test connection to Cursor API"""
        try:
            response = requests.get(
                f"{self.base_url}/api/status",
                timeout=self.timeout
            )
            if response.ok:
                data = response.json()
                self.is_connected = data.get("status") == "ok"
                return self.is_connected
            return False
        except Exception as e:
            log_debug(f"Cursor API connection test failed: {e}")
            self.is_connected = False
            return False
    
    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Make a request to Cursor API"""
        url = f"{self.base_url}{endpoint}"
        timeout = timeout or self.timeout
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, timeout=timeout)
            elif method.upper() == "POST":
                response = requests.post(
                    url,
                    json=data or {},
                    headers={"Content-Type": "application/json"},
                    timeout=timeout
                )
            else:
                log_error(f"Unsupported HTTP method: {method}")
                return None
            
            if response.ok:
                return response.json()
            else:
                log_warn(f"Cursor API error: {response.status_code} - {response.text}")
                return None
                
        except Timeout:
            log_error(f"Cursor API request timed out after {timeout}s")
            return None
        except RequestException as e:
            log_error(f"Cursor API request failed: {e}")
            return None
        except Exception as e:
            log_error(f"Unexpected error in Cursor API request: {e}")
            return None
    
    def get_editor_state(self) -> Dict[str, Any]:
        """
        Get current editor state (current file, cursor position, etc.)
        
        Returns:
            Dictionary with editor state or error info
        """
        log_tool("cursor_get_editor_state", "Getting Cursor editor state...")
        
        result = self._request("GET", "/api/editor-state")
        
        if result:
            return {
                "success": True,
                "current_file": result.get("current_file"),
                "cursor_position": result.get("cursor_position"),
                "selection": result.get("selection"),
                "open_tabs": result.get("open_tabs", []),
                "project_root": result.get("project_root"),
            }
        else:
            return {
                "success": False,
                "error": "Failed to get editor state. Is Cursor API running?",
            }
    
    def get_current_file(self) -> Optional[str]:
        """Get the currently open file path"""
        state = self.get_editor_state()
        if state.get("success"):
            return state.get("current_file")
        return None
    
    def get_file_content(self, file_path: str) -> Dict[str, Any]:
        """
        Get content of a file
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file content or error
        """
        log_tool("cursor_get_file_content", f"Reading file: {file_path}")
        
        result = self._request("POST", "/api/file-content", {"file_path": file_path})
        
        if result and result.get("content"):
            return {
                "success": True,
                "file_path": file_path,
                "content": result.get("content"),
                "size": len(result.get("content", "")),
            }
        else:
            return {
                "success": False,
                "file_path": file_path,
                "error": "File not found or could not be read",
            }
    
    def write_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        Write content to a file
        
        Args:
            file_path: Path to the file
            content: Content to write
            
        Returns:
            Dictionary with success status
        """
        log_tool("cursor_write_file", f"Writing to file: {file_path}")
        
        result = self._request("POST", "/api/write-file", {
            "file_path": file_path,
            "content": content
        })
        
        if result and result.get("success"):
            return {
                "success": True,
                "file_path": file_path,
                "bytes_written": len(content),
            }
        else:
            return {
                "success": False,
                "file_path": file_path,
                "error": "Failed to write file",
            }
    
    def list_files(self, directory: str = ".") -> Dict[str, Any]:
        """
        List files in a directory
        
        Args:
            directory: Directory path (default: current directory)
            
        Returns:
            Dictionary with list of files
        """
        log_tool("cursor_list_files", f"Listing files in: {directory}")
        
        result = self._request("POST", "/api/list-files", {"directory": directory})
        
        if result and result.get("files"):
            return {
                "success": True,
                "directory": directory,
                "files": result.get("files", []),
                "count": len(result.get("files", [])),
            }
        else:
            return {
                "success": False,
                "directory": directory,
                "error": "Failed to list files",
                "files": [],
            }
    
    def search_in_files(self, query: str, directory: str = ".") -> Dict[str, Any]:
        """
        Search for text in files
        
        Args:
            query: Search query
            directory: Directory to search (default: current directory)
            
        Returns:
            Dictionary with search results
        """
        log_tool("cursor_search_files", f"Searching for: {query}")
        
        result = self._request("POST", "/api/search", {
            "query": query,
            "directory": directory
        })
        
        if result and result.get("results"):
            return {
                "success": True,
                "query": query,
                "directory": directory,
                "results": result.get("results", []),
                "count": len(result.get("results", [])),
            }
        else:
            return {
                "success": False,
                "query": query,
                "error": "Search failed or no results found",
                "results": [],
            }
    
    def run_code(self, code: str, language: Optional[str] = None) -> Dict[str, Any]:
        """
        Run code snippet
        
        Args:
            code: Code to execute
            language: Programming language (optional, auto-detect if not provided)
            
        Returns:
            Dictionary with execution results
        """
        log_tool("cursor_run_code", f"Running code ({language or 'auto-detect'})")
        
        result = self._request(
            "POST",
            "/api/run-code",
            {
                "code": code,
                "language": language or "auto"
            },
            timeout=30  # Longer timeout for code execution
        )
        
        if result:
            return {
                "success": True,
                "output": result.get("output", ""),
                "error": result.get("error"),
            }
        else:
            return {
                "success": False,
                "error": "Failed to run code",
            }
    
    def describe_codebase(self) -> Dict[str, Any]:
        """
        Get a description of the codebase structure
        
        Returns:
            Dictionary with codebase description
        """
        log_tool("cursor_describe_codebase", "Analyzing codebase...")
        
        files_result = self.list_files()
        if not files_result.get("success"):
            return {
                "success": False,
                "error": "Failed to list files for codebase analysis",
            }
        
        files = files_result.get("files", [])
        code_files = [
            f for f in files
            if f.get("name", "").endswith((".js", ".ts", ".py", ".jsx", ".tsx", ".vue", ".java", ".cpp", ".c", ".go", ".rs"))
        ]
        
        description = f"Codebase contains {len(code_files)} code files.\n\n"
        
        # Get content of a few key files
        for file_info in code_files[:10]:  # Limit to first 10 files
            file_path = file_info.get("path") or file_info.get("name")
            if file_path:
                content_result = self.get_file_content(file_path)
                if content_result.get("success"):
                    content = content_result.get("content", "")
                    if len(content) < 2000:  # Only analyze small files
                        description += f"**{file_path}**:\n"
                        description += f"Size: {len(content)} bytes\n"
                        description += f"Type: {self._guess_file_type(file_path)}\n\n"
        
        return {
            "success": True,
            "description": description,
            "total_files": len(files),
            "code_files": len(code_files),
        }
    
    def _guess_file_type(self, file_name: str) -> str:
        """Guess file type from extension"""
        ext = file_name.split(".")[-1].lower() if "." in file_name else ""
        type_map = {
            "js": "JavaScript",
            "ts": "TypeScript",
            "jsx": "React JavaScript",
            "tsx": "React TypeScript",
            "py": "Python",
            "vue": "Vue.js",
            "java": "Java",
            "cpp": "C++",
            "c": "C",
            "go": "Go",
            "rs": "Rust",
            "html": "HTML",
            "css": "CSS",
            "json": "JSON",
        }
        return type_map.get(ext, "code")


# Global Cursor API instance
_cursor_api: Optional[CursorAPI] = None


def get_cursor_api() -> Optional[CursorAPI]:
    """Get or create the global Cursor API instance"""
    global _cursor_api
    if _cursor_api is None:
        _cursor_api = CursorAPI()
        # Test connection but don't fail if unavailable
        _cursor_api.test_connection()
    return _cursor_api


def ensure_cursor_available() -> bool:
    """Check if Cursor API is available, return False if not"""
    api = get_cursor_api()
    if api and api.is_connected:
        return True
    return False


# Tool functions for tool_executor
def cursor_get_editor_state() -> Dict[str, Any]:
    """Get current Cursor editor state"""
    api = get_cursor_api()
    if not api:
        return {"success": False, "error": "Cursor API not initialized"}
    return api.get_editor_state()


def cursor_get_file_content(file_path: str) -> Dict[str, Any]:
    """Get content of a file via Cursor API"""
    api = get_cursor_api()
    if not api:
        return {"success": False, "error": "Cursor API not initialized"}
    return api.get_file_content(file_path)


def cursor_write_file(file_path: str, content: str) -> Dict[str, Any]:
    """Write to a file via Cursor API"""
    api = get_cursor_api()
    if not api:
        return {"success": False, "error": "Cursor API not initialized"}
    return api.write_file(file_path, content)


def cursor_list_files(directory: str = ".") -> Dict[str, Any]:
    """List files via Cursor API"""
    api = get_cursor_api()
    if not api:
        return {"success": False, "error": "Cursor API not initialized"}
    return api.list_files(directory)


def cursor_search_files(query: str, directory: str = ".") -> Dict[str, Any]:
    """Search in files via Cursor API"""
    api = get_cursor_api()
    if not api:
        return {"success": False, "error": "Cursor API not initialized"}
    return api.search_in_files(query, directory)


def cursor_run_code(code: str, language: Optional[str] = None) -> Dict[str, Any]:
    """Run code via Cursor API"""
    api = get_cursor_api()
    if not api:
        return {"success": False, "error": "Cursor API not initialized"}
    return api.run_code(code, language)


def cursor_describe_codebase() -> Dict[str, Any]:
    """Describe codebase via Cursor API"""
    api = get_cursor_api()
    if not api:
        return {"success": False, "error": "Cursor API not initialized"}
    return api.describe_codebase()

