"""
Wolf CLI Orchestrator

Runs the LLM conversation loop, handles tool calls, executes tools,
feeds results back, and returns the final assistant text.
"""

import json
from typing import Any, Dict, List, Optional

from .tool_executor import ToolExecutor
from .tool_registry import get_registry
from .permission_manager import PermissionManager
from .config_manager import get_config
from .utils.logging_utils import log_info, log_error, log_debug, log_warn
from .llm import ollama


class Orchestrator:
    """
    Orchestrates multi-turn chat with tool execution
    
    Provider support:
    - Ollama: chat with tools/function-calling
    - OpenRouter: TODO in Phase 2 #future-use
    """
    
    def __init__(
        self,
        tool_executor: ToolExecutor,
        provider: str = "ollama",
        model: Optional[str] = None,
        max_tool_iterations: int = 6,
    ):
        self.tool_executor = tool_executor
        self.provider = provider.lower()
        self.config = get_config()
        self.registry = get_registry()
        
        # Determine model
        if model:
            self.model = model
        elif self.provider == "ollama":
            self.model = self.config.get("ollama_model", "llama3.2:latest")
        else: #future-use
            self.model = self.config.get("openrouter_model", "openrouter/auto") #future-use
        
        self.max_tool_iterations = max_tool_iterations
        self.base_url = self.config.get("ollama_base_url", "http://localhost:11434")
        
        # Export tool schemas for LLM
        self.tool_schemas = self.registry.export_openai_tools()
        
        log_debug(f"Orchestrator initialized: provider={self.provider}, model={self.model}, tools={len(self.tool_schemas)}")
    
    def _format_user_message(self, prompt: str, images: Optional[List[str]]) -> Dict[str, Any]:
        """Format user message with optional images"""
        msg = {"role": "user", "content": prompt}
        # Images will be handled by provider adapter
        return msg
    
    def _call_llm(self, messages: List[Dict[str, Any]], images: Optional[List[str]] = None) -> Dict[str, Any]:
        """Call LLM provider"""
        if self.provider == "ollama":
            return ollama.chat(
                model=self.model,
                messages=messages,
                tools=self.tool_schemas,
                base_url=self.base_url,
                images=images,
            )
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def _extract_tool_calls(self, assistant_message: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract tool calls from assistant message
        
        Returns:
            List of tool calls with structure: [{"id": str|None, "name": str, "arguments": dict|str}]
        """
        calls = []
        
        # OpenAI-style tool_calls
        if "tool_calls" in assistant_message and assistant_message["tool_calls"]:
            for call in assistant_message["tool_calls"]:
                function = call.get("function", {})
                calls.append({
                    "id": call.get("id"),
                    "name": function.get("name"),
                    "arguments": function.get("arguments"),
                })
        
        # Single function_call (older format)
        elif "function_call" in assistant_message:
            fc = assistant_message["function_call"]
            if fc:
                calls.append({
                    "id": None,
                    "name": fc.get("name"),
                    "arguments": fc.get("arguments"),
                })
        
        return calls
    
    def run(self, prompt: str, images: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Run the orchestration loop
        
        Args:
            prompt: User prompt
            images: Optional list of image paths
            
        Returns:
            Dictionary with keys:
            - ok: bool (success/failure)
            - text: str (final assistant response) - if ok=True
            - error: str (error message) - if ok=False
            - messages: List[Dict] (full conversation history)
        """
        messages = []
        
        # Add system prompt if configured
        system_prompt = self.config.get("system_prompt")
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
            log_debug(f"System prompt loaded ({len(system_prompt)} chars)")
        else:
            log_warn("No system prompt configured!")
        
        # Add user message
        user_msg = self._format_user_message(prompt, images)
        messages.append(user_msg)
        
        log_info(f"Starting orchestration loop (max {self.max_tool_iterations} iterations)")
        
        # Tool-call loop
        for iteration in range(self.max_tool_iterations):
            log_debug(f"Iteration {iteration + 1}/{self.max_tool_iterations}")
            
            try:
                # Call LLM (pass images only on first iteration)
                response = self._call_llm(messages, images if iteration == 0 else None)
                
                # Check for errors
                if "error" in response:
                    return {
                        "ok": False,
                        "error": f"LLM error: {response['error']}",
                        "messages": messages,
                    }
                
                # Get response message
                choices = response.get("choices", [])
                if not choices:
                    return {
                        "ok": False,
                        "error": "No response choices from LLM",
                        "messages": messages,
                    }
                
                assistant_message = choices[0].get("message", {})
                
                # Extract tool calls
                tool_calls = self._extract_tool_calls(assistant_message)
                
                if tool_calls:
                    log_debug(f"Assistant requested {len(tool_calls)} tool call(s)")
                    
                    # Add assistant message with tool calls to history
                    messages.append(assistant_message)
                    
                    # Execute each tool
                    for call in tool_calls:
                        tool_name = call.get("name")
                        arguments = call.get("arguments")
                        call_id = call.get("id")
                        
                        if not tool_name:
                            log_warn("Tool call missing name, skipping")
                            continue
                        
                        log_info(f"Executing tool: {tool_name}")
                        
                        # Parse arguments if string
                        if isinstance(arguments, str):
                            try:
                                arguments = json.loads(arguments) if arguments.strip() else {}
                            except json.JSONDecodeError:
                                log_error(f"Failed to parse tool arguments for {tool_name}")
                                arguments = {}
                        
                        # Execute tool
                        result = self.tool_executor.execute(tool_name, arguments or {})
                        
                        # Create tool response message
                        tool_response = {
                            "role": "tool",
                            "name": tool_name,
                            "content": json.dumps(result),
                        }
                        
                        # Add tool_call_id if provided
                        if call_id:
                            tool_response["tool_call_id"] = call_id
                        
                        messages.append(tool_response)
                        
                        log_debug(f"Tool {tool_name} result: ok={result.get('ok')}")

                        # If tool execution failed due to an unknown tool, log and continue
                        if not result.get("ok") and "Unknown tool" in result.get("error", ""):
                            log_warn(f"LLM attempted to call unknown tool '{tool_name}'. Providing feedback and continuing.")
                            # The tool_response has already been added to messages, so the LLM will see the error.
                            # We just need to ensure the loop continues.
                            continue
                    
                    # Continue loop to let LLM process tool results
                    continue
                
                # No tool calls - this is the final response
                assistant_text = assistant_message.get("content", "")
                
                # Add final assistant message to history
                if assistant_text:
                    messages.append({"role": "assistant", "content": assistant_text})
                
                log_info("Orchestration complete")
                
                return {
                    "ok": True,
                    "text": assistant_text,
                    "messages": messages,
                }
            
            except Exception as e:
                log_error(f"Error in orchestration loop iteration {iteration + 1}: {str(e)}", exc_info=True)
                return {
                    "ok": False,
                    "error": str(e),
                    "messages": messages,
                }
        
        # Max iterations reached
        log_warn(f"Max tool iterations ({self.max_tool_iterations}) reached")
        return {
            "ok": False,
            "error": f"Max tool iterations ({self.max_tool_iterations}) reached without final answer",
            "messages": messages,
        }
