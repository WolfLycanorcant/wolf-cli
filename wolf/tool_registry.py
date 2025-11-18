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
            "Email": [],
            "Cursor Editor": [],
        }
        
        for name in self._tools.keys():
            if name.startswith(("create_", "read_", "write_", "delete_", "move_", "copy_", "list_", "compress_", "extract_")):
                categories["File Operations"].append(name)
            elif name.startswith(("execute_", "get_command_", "get_system_")):
                categories["Shell & System"].append(name)
            elif name.startswith("list_email_") or name.startswith("read_email_"):
                categories["Email"].append(name)
            elif name.startswith("cursor_"):
                categories["Cursor Editor"].append(name)
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

        # ====================
        # EMAIL (THUNDERBIRD)
        # ====================

        self.register(ToolSchema(
            name="list_email_mailboxes",
            description="List all available email mailboxes from the local Thunderbird profile.",
            parameters={
                "type": "object",
                "properties": {},
                "required": [],
            },
            returns="JSON with a list of mailbox names.",
            risk_level=RiskLevel.SAFE,
            handler=None,
        ))

        self.register(ToolSchema(
            name="read_email_mailbox",
            description="Read the most recent emails from a specified Thunderbird mailbox.",
            parameters={
                "type": "object",
                "properties": {
                    "mailbox_name": {
                        "type": "string",
                        "description": "The name of the mailbox to read (e.g., 'Inbox').",
                    },
                    "count": {
                        "type": "integer",
                        "description": "The maximum number of emails to read.",
                        "default": 10,
                    },
                },
                "required": ["mailbox_name"],
            },
            returns="JSON with a list of emails, each with id, subject, from, and date.",
            risk_level=RiskLevel.SAFE,
            handler=None,
        ))

        # ====================
        # CURSOR EDITOR API
        # ====================

        self.register(ToolSchema(
            name="cursor_get_editor_state",
            description="Get the current state of the Cursor editor (current file, cursor position, open tabs, project root). Requires Cursor API to be running on port 5005.",
            parameters={
                "type": "object",
                "properties": {},
                "required": [],
            },
            returns="JSON with keys: success (bool), current_file (str), cursor_position (dict), selection (dict), open_tabs (list), project_root (str), error (str if success=False)",
            risk_level=RiskLevel.SAFE,
            handler=None,
        ))

        self.register(ToolSchema(
            name="cursor_get_file_content",
            description="Get the content of a file through Cursor API. This reads files as they appear in the Cursor editor context.",
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to read",
                    },
                },
                "required": ["file_path"],
            },
            returns="JSON with keys: success (bool), file_path (str), content (str), size (int), error (str if success=False)",
            risk_level=RiskLevel.SAFE,
            handler=None,
        ))

        self.register(ToolSchema(
            name="cursor_write_file",
            description="Write content to a file through Cursor API. This will write files in the Cursor editor context.",
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to write",
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write to the file",
                    },
                },
                "required": ["file_path", "content"],
            },
            returns="JSON with keys: success (bool), file_path (str), bytes_written (int), error (str if success=False)",
            risk_level=RiskLevel.MODIFYING,
            handler=None,
        ))

        self.register(ToolSchema(
            name="cursor_list_files",
            description="List files in a directory through Cursor API. This lists files as they appear in the Cursor project context.",
            parameters={
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "Directory path to list (default: current directory)",
                        "default": ".",
                    },
                },
                "required": [],
            },
            returns="JSON with keys: success (bool), directory (str), files (list), count (int), error (str if success=False)",
            risk_level=RiskLevel.SAFE,
            handler=None,
        ))

        self.register(ToolSchema(
            name="cursor_search_files",
            description="Search for text in files through Cursor API. Returns matches with line numbers and context.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Text to search for",
                    },
                    "directory": {
                        "type": "string",
                        "description": "Directory to search in (default: current directory)",
                        "default": ".",
                    },
                },
                "required": ["query"],
            },
            returns="JSON with keys: success (bool), query (str), directory (str), results (list of matches with file, line, content), count (int), error (str if success=False)",
            risk_level=RiskLevel.SAFE,
            handler=None,
        ))

        self.register(ToolSchema(
            name="cursor_run_code",
            description="Execute code snippets through Cursor API. Useful for testing code or running quick scripts.",
            parameters={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Code to execute",
                    },
                    "language": {
                        "type": "string",
                        "description": "Programming language (optional, auto-detect if not provided)",
                    },
                },
                "required": ["code"],
            },
            returns="JSON with keys: success (bool), output (str), error (str if execution failed)",
            risk_level=RiskLevel.MODIFYING,
            handler=None,
        ))

        self.register(ToolSchema(
            name="cursor_describe_codebase",
            description="Get a description of the codebase structure through Cursor API. Analyzes project files and provides an overview.",
            parameters={
                "type": "object",
                "properties": {},
                "required": [],
            },
            returns="JSON with keys: success (bool), description (str), total_files (int), code_files (int), error (str if success=False)",
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
