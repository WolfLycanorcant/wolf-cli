"""
Wolf CLI Tool Registry

Central registry for all available tools with their schemas and handlers.
"""

from typing import Any, Callable, Dict, List, Optional
from .permission_manager import RiskLevel


class ToolSchema:
    """Schema definition for a tool"""
    
    def __init__(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        returns: str,
        risk_level: RiskLevel,
        handler: Callable,
        required_permissions: Optional[List[str]] = None,
    ):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.returns = returns
        self.risk_level = risk_level
        self.handler = handler
        self.required_permissions = required_permissions or []
    
    def to_openai_tool(self) -> Dict[str, Any]:
        """Convert to OpenAI tool schema format"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            }
        }


class ToolRegistry:
    """Registry of available tools"""
    
    def __init__(self):
        self._tools: Dict[str, ToolSchema] = {}
        self._register_core_tools()
    
    def register(self, tool: ToolSchema) -> None:
        """Register a tool"""
        self._tools[tool.name] = tool
    
    def get(self, name: str) -> Optional[ToolSchema]:
        """Get a tool by name"""
        return self._tools.get(name)
    
    def list_tools(self) -> List[str]:
        """List all registered tool names"""
        return list(self._tools.keys())
    
    def list_by_category(self) -> Dict[str, List[str]]:
        """List tools grouped by category"""
        categories = {
            "File Operations": [],
            "Shell & System": [],
            "Web & Information": [],
        }
        
        for name in self._tools.keys():
            if name.startswith(("create_", "read_", "write_", "delete_", "move_", "copy_", "list_", "compress_", "extract_")):
                categories["File Operations"].append(name)
            elif name.startswith(("execute_", "get_command_", "get_system_")):
                categories["Shell & System"].append(name)
            else:
                categories["Web & Information"].append(name)
        
        return categories
    
    def export_openai_tools(self) -> List[Dict[str, Any]]:
        """Export all tools in OpenAI tool schema format"""
        return [tool.to_openai_tool() for tool in self._tools.values()]
    
    def _register_core_tools(self) -> None:
        """Register core MVP tools"""
        
        # ====================
        # FILE OPERATIONS
        # ====================
        
        self.register(ToolSchema(
            name="create_file",
            description="Create a new file with specified content. If file exists, it will NOT be overwritten (use write_file for that).",
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to create (absolute or relative)",
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write to the file",
                        "default": "",
                    },
                },
                "required": ["path"],
            },
            returns="JSON with keys: path (str), bytes_written (int), success (bool)",
            risk_level=RiskLevel.MODIFYING,
            handler=None,  # Will be set by tool implementations
        ))
        
        self.register(ToolSchema(
            name="read_file",
            description="Read the contents of a file.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to read",
                    },
                },
                "required": ["path"],
            },
            returns="JSON with keys: path (str), content (str), size (int)",
            risk_level=RiskLevel.SAFE,
            handler=None,
        ))
        
        self.register(ToolSchema(
            name="write_file",
            description="Write or overwrite a file with new content. This WILL overwrite existing files.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to write",
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write to the file",
                    },
                },
                "required": ["path", "content"],
            },
            returns="JSON with keys: path (str), bytes_written (int), backed_up (bool)",
            risk_level=RiskLevel.MODIFYING,
            handler=None,
        ))
        
        self.register(ToolSchema(
            name="delete_file",
            description="Delete a file (moves to recycle bin when possible).",
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to delete",
                    },
                },
                "required": ["path"],
            },
            returns="JSON with keys: path (str), deleted (bool), recycled (bool)",
            risk_level=RiskLevel.DESTRUCTIVE,
            handler=None,
        ))
        
        self.register(ToolSchema(
            name="list_directory",
            description="List files and directories in a directory.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the directory to list",
                        "default": ".",
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "List recursively",
                        "default": False,
                    },
                },
                "required": [],
            },
            returns="JSON with keys: path (str), items (list of dicts with name, type, size, modified)",
            risk_level=RiskLevel.SAFE,
            handler=None,
        ))
        
        self.register(ToolSchema(
            name="get_file_info",
            description="Get detailed information about a file.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file",
                    },
                },
                "required": ["path"],
            },
            returns="JSON with keys: path, size, size_human, modified, created, is_file, is_dir",
            risk_level=RiskLevel.SAFE,
            handler=None,
        ))
        
        self.register(ToolSchema(
            name="move_file",
            description="Move or rename a file.",
            parameters={
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "Source file path",
                    },
                    "destination": {
                        "type": "string",
                        "description": "Destination file path",
                    },
                },
                "required": ["source", "destination"],
            },
            returns="JSON with keys: source, destination, success",
            risk_level=RiskLevel.MODIFYING,
            handler=None,
        ))
        
        self.register(ToolSchema(
            name="copy_file",
            description="Copy a file to a new location.",
            parameters={
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "Source file path",
                    },
                    "destination": {
                        "type": "string",
                        "description": "Destination file path",
                    },
                },
                "required": ["source", "destination"],
            },
            returns="JSON with keys: source, destination, bytes_copied",
            risk_level=RiskLevel.MODIFYING,
            handler=None,
        ))
        
        # ====================
        # SHELL & SYSTEM
        # ====================
        
        self.register(ToolSchema(
            name="execute_command",
            description="Execute a shell command (PowerShell on Windows, Bash on Linux/macOS). Use with caution. Subject to allowlist/denylist filtering.",
            parameters={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "PowerShell command to execute",
                    },
                },
                "required": ["command"],
            },
            returns="JSON with keys: command, stdout, stderr, exit_code, success",
            risk_level=RiskLevel.MODIFYING,  # Can vary, checked by permission manager
            handler=None,
        ))
        
        self.register(ToolSchema(
            name="get_system_info",
            description="Get system information (OS, CPU, memory, disk).",
            parameters={
                "type": "object",
                "properties": {},
                "required": [],
            },
            returns="JSON with system information",
            risk_level=RiskLevel.SAFE,
            handler=None,
        ))
        
        # ====================
        # WEB & INFORMATION
        # ====================
        
        self.register(ToolSchema(
            name="search_web",
            description="Search the web using DuckDuckGo and return up to N results with titles, URLs, and snippets.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query text",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 10, min: 1, max: 50)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 50,
                    },
                },
                "required": ["query"],
            },
            returns="JSON with keys: ok (bool), query (str), results (list of dicts with title/url/snippet), count (int), error (str if ok=False)",
            risk_level=RiskLevel.SAFE,
            handler=None,
        ))


# Global registry instance
_registry: Optional[ToolRegistry] = None


def get_registry() -> ToolRegistry:
    """Get or create the global tool registry"""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry
