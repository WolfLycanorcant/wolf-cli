"""
Wolf CLI Tool Executor

Executes tool calls with validation, permission checks, and error handling.
"""

import json
from typing import Any, Dict

from .permission_manager import PermissionManager, RiskLevel
from .tool_registry import get_registry, ToolSchema
from .utils.validation import validate_tool_params
from .utils.logging_utils import log_tool, log_error, log_warn, log_debug
from .providers import file_ops, shell_client, search_web, email
from .providers.cursor_client import (
    cursor_get_editor_state,
    cursor_get_file_content,
    cursor_write_file,
    cursor_list_files,
    cursor_search_files,
    cursor_run_code,
    cursor_describe_codebase,
)


class ToolExecutor:
    """Executes validated tool calls"""
    
    def __init__(self, permission_manager: PermissionManager):
        self.permission_manager = permission_manager
        self.registry = get_registry()
        self._bind_handlers()
    
    def _bind_handlers(self) -> None:
        """Bind tool handlers to registry"""
        # File operations
        self.registry.get("create_file").handler = file_ops.create_file
        self.registry.get("read_file").handler = file_ops.read_file
        self.registry.get("write_file").handler = file_ops.write_file
        self.registry.get("delete_file").handler = file_ops.delete_file
        self.registry.get("list_directory").handler = file_ops.list_directory
        self.registry.get("get_file_info").handler = file_ops.get_file_info
        self.registry.get("move_file").handler = file_ops.move_file
        self.registry.get("copy_file").handler = file_ops.copy_file
        
        # Shell & system
        self.registry.get("execute_command").handler = lambda command, **kwargs: shell_client.execute_shell_command(command, **kwargs)
        self.registry.get("get_system_info").handler = lambda: shell_client.get_system_info()
        
        # Web & information
        self.registry.get("search_web").handler = lambda query, max_results=10: search_web(query=query, max_results=max_results)

        # Email
        self.registry.get("list_email_mailboxes").handler = email.list_mailboxes
        self.registry.get("read_email_mailbox").handler = email.read_mailbox
        
        # Cursor Editor API
        self.registry.get("cursor_get_editor_state").handler = cursor_get_editor_state
        self.registry.get("cursor_get_file_content").handler = cursor_get_file_content
        self.registry.get("cursor_write_file").handler = cursor_write_file
        self.registry.get("cursor_list_files").handler = cursor_list_files
        self.registry.get("cursor_search_files").handler = cursor_search_files
        self.registry.get("cursor_run_code").handler = cursor_run_code
        self.registry.get("cursor_describe_codebase").handler = cursor_describe_codebase
    
    def execute(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool call
        
        Args:
            tool_name: Name of the tool
            params: Tool parameters
            
        Returns:
            Result dictionary
        """
        # Get tool schema
        tool = self.registry.get(tool_name)
        if not tool:
            error_msg = f"Unknown tool: {tool_name}"
            log_error(error_msg)
            return {
                "ok": False,
                "tool": tool_name,
                "error": error_msg,
            }
        
        # Parse arguments if they're a string
        if isinstance(params, str):
            try:
                params = json.loads(params) if params.strip() else {}
            except json.JSONDecodeError as e:
                log_error(f"Failed to parse tool arguments as JSON: {e}")
                return {
                    "ok": False,
                    "tool": tool_name,
                    "error": f"Invalid JSON arguments: {e}",
                }
        
        # Ensure params is a dict
        if not isinstance(params, dict):
            return {
                "ok": False,
                "tool": tool_name,
                "error": f"Parameters must be a dict, got {type(params).__name__}",
            }
        
        # Validate parameters
        is_valid, error_msg = validate_tool_params(params, tool.parameters)
        if not is_valid:
            log_error(f"Invalid parameters for {tool_name}: {error_msg}")
            return {
                "ok": False,
                "tool": tool_name,
                "input": params,
                "error": f"Invalid parameters: {error_msg}",
            }
        
        # Check permissions
        if not self.permission_manager.check_and_confirm(
            tool_name=tool_name,
            risk_level=tool.risk_level,
            params=params,
            description=tool.description
        ):
            log_warn(f"Permission denied for {tool_name}")
            return {
                "ok": False,
                "tool": tool_name,
                "input": params,
                "error": "Permission denied by user",
            }
        
        # Execute handler
        try:
            log_debug(f"Executing {tool_name} with params: {params}")
            result = tool.handler(**params)
            
            # Ensure result has 'ok' field
            if "ok" not in result:
                result["ok"] = result.get("success", True)
            
            return {
                "ok": result.get("ok", True),
                "tool": tool_name,
                "input": params,
                "result": result,
                "error": result.get("error"),
            }
        
        except Exception as e:
            log_error(f"Error executing {tool_name}: {str(e)}", exc_info=True)
            return {
                "ok": False,
                "tool": tool_name,
                "input": params,
                "error": str(e),
            }
