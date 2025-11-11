"""
Wolf CLI Wrapper

Main CLI entry point using Click and Rich for Wolf CLI.
Provides the 'wolf' command to chat with LLM and execute tools.
"""

import sys
from typing import List, Optional, Tuple

import click
from rich.console import Console
from rich.table import Table

from .config_manager import get_config
from .permission_manager import PermissionManager, TrustLevel
from .tool_registry import get_registry
from .tool_executor import ToolExecutor
from .orchestrator import Orchestrator
from .utils.logging_utils import setup_logging, console as log_console


console = Console()


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option("--safe", is_flag=True, help="Enable safe mode (strict permissions, read-only).")
@click.option("--auto", is_flag=True, help="Allow automatic tool execution (permissive, no confirmations).")
@click.option("--image", "images", multiple=True, type=click.Path(exists=True, dir_okay=False, readable=True), help="Path(s) to image(s) for vision input.")
@click.option("--provider", type=click.Choice(["ollama", "openrouter"], case_sensitive=False), default="ollama", show_default=True, help="LLM provider to use. #future-use")
@click.option("--model", type=str, default=None, help="LLM model to use (overrides config).")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging (DEBUG level).")
@click.option("--list-tools", is_flag=True, help="List available tools and exit.")
@click.option("--max-iterations", type=int, default=None, help="Maximum number of tool iterations (overrides config).")
@click.argument("prompt", nargs=-1)
@click.pass_context
def wolf(
    ctx: click.Context,
    safe: bool,
    auto: bool,
    images: Tuple[str, ...],
    provider: str,
    model: Optional[str],
    verbose: bool,
    list_tools: bool,
    max_iterations: Optional[int], # Added this parameter
    prompt: Tuple[str, ...]
) -> None:
    """
    Wolf CLI - AI-powered command-line tool with vision and tool calling
    
    Examples:
    
      wolf "create a file named test.txt with hello world"
      
      wolf --image screenshot.png "what's in this image?"
      
      wolf --auto "list all python files in current directory"
      
      wolf --safe "show me system information"
    """
    # Load configuration early to check vision mode state
    config = get_config()
    config.ensure_initialized()
    
    # Handle vision mode restoration if wolf is called directly (not from wolfv)
    # Detect if --model was explicitly passed by the user
    has_explicit_model = model is not None
    
    # If vision mode is active and user didn't specify a model, restore previous model
    if config.get("vision_mode_active") and not has_explicit_model:
        previous = config.get("previous_model") or "gpt-oss:20b"
        config.set("ollama_model", previous)
        config.set("vision_mode_active", False)
        config.set("previous_model", None)
        config.save()
        console.print(f"[dim]Restored model to {previous} (exited vision mode)[/dim]")
    
    # Check for mutually exclusive flags
    if safe and auto:
        console.print("[red]Error:[/red] --safe and --auto are mutually exclusive.")
        sys.exit(2)
    
    try:
        # Setup logging
        log_file = "wolf-cli.log"
        setup_logging(log_file=log_file, verbose=verbose)
        
        # Initialize core components
        registry = get_registry()
        
        # Determine trust level
        if safe:
            trust_level = TrustLevel.SAFE_ONLY
        elif auto:
            trust_level = TrustLevel.AUTO
        else:
            # Use configured default or interactive
            trust_level_str = config.get("default_trust_level", "interactive")
            trust_level = TrustLevel(trust_level_str)
        
        # Initialize permission manager
        permission_manager = PermissionManager(
            trust_level=trust_level,
            custom_allowlist=config.get("custom_allowlist", []),
            custom_denylist=config.get("custom_denylist", []),
        )
        
        # Initialize tool executor
        tool_executor = ToolExecutor(permission_manager=permission_manager)
        
        # Handle --list-tools
        if list_tools:
            _print_tools(registry)
            return
        
        # Validate prompt
        if not prompt:
            console.print("[yellow]No prompt provided.[/yellow]")
            console.print("\nUsage examples:")
            console.print("  wolf \"create a file named test.txt\"")
            console.print("  wolf --image photo.jpg \"describe this image\"")
            console.print("  wolf --list-tools")
            sys.exit(1)
        
        # Join prompt parts
        user_prompt = " ".join(prompt)
        
        # Determine max tool iterations
        orchestrator_max_iterations = max_iterations if max_iterations is not None else config.get("max_tool_iterations", 6)
        
        # Initialize orchestrator
        orchestrator = Orchestrator(
            tool_executor=tool_executor,
            provider=provider,
            model=model,
            max_tool_iterations=orchestrator_max_iterations,
        )
        
        # Run orchestration
        console.print(f"[cyan][Wolf CLI][/cyan] - Provider: {provider}, Model: {orchestrator.model}")
        console.print()
        
        result = orchestrator.run(
            prompt=user_prompt,
            images=list(images) if images else None
        )
        
        # Display result
        if result.get("ok"):
            assistant_text = result.get("text", "")
            if assistant_text:
                console.print("[green]Assistant:[/green]")
                console.print(assistant_text)
            else:
                console.print("[yellow]Assistant provided no text response.[/yellow]")
            sys.exit(0)
        else:
            error_msg = result.get("error", "Unknown error")
            console.print(f"[red]Error:[/red] {error_msg}")
            sys.exit(1)
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(130)
    
    except Exception as exc:
        console.print(f"[red]Fatal error:[/red] {exc}")
        if verbose:
            import traceback
            console.print("\n[dim]Traceback:[/dim]")
            console.print(traceback.format_exc())
        sys.exit(1)


def _print_tools(registry) -> None:
    """Print available tools in a formatted table"""
    table = Table(title="Wolf CLI - Available Tools")
    table.add_column("Tool Name", style="cyan", no_wrap=True)
    table.add_column("Description", style="white")
    table.add_column("Risk Level", style="magenta")
    
    # Get tools by category
    categories = registry.list_by_category()
    
    for category, tool_names in categories.items():
        if tool_names:
            # Add category header
            table.add_row(f"[bold]{category}[/bold]", "", "")
            
            # Add tools in category
            for name in sorted(tool_names):
                tool = registry.get(name)
                if tool:
                    risk = tool.risk_level.value if hasattr(tool.risk_level, 'value') else str(tool.risk_level)
                    # Truncate long descriptions
                    desc = tool.description
                    if len(desc) > 80:
                        desc = desc[:77] + "..."
                    table.add_row(f"  {name}", desc, risk)
    
    console.print(table)
    console.print(f"\n[dim]Total tools: {len(registry.list_tools())}[/dim]")


def main_vision():
    """
    Entry point for wolfv console script.
    
    Captures a screenshot automatically and activates vision mode with qwen3-v1:8b model.
    Vision mode persists until 'wolf' is used again without --model flag.
    """
    try:
        # Import screenshot utility
        from .utils.screenshot import take_screenshot
        
        # Capture screenshot first (before any user interaction)
        console.print("[cyan]📸 Capturing screenshot...[/cyan]")
        screenshot_path = take_screenshot()
        console.print(f"[green]✓[/green] Screenshot saved: {screenshot_path}")
        console.print()
        
        # Load config and activate vision mode
        config = get_config()
        config.ensure_initialized()
        
        # Save previous model if not already in vision mode
        if not config.get("vision_mode_active"):
            previous = config.get("ollama_model", "gpt-oss:20b")
            config.set("previous_model", previous)
            console.print(f"[dim]Saved previous model: {previous}[/dim]")
        
        # Activate vision mode
        config.set("vision_mode_active", True)
        config.set("ollama_model", "qwen3-vl:8b")
        config.save()
        
        # Build arguments to forward to wolf()
        # We need to programmatically invoke wolf with additional args
        # Since wolf is a Click command, we use Click's invoke mechanism
        import sys
        
        # Prepare new argv with --image and --model flags injected
        # Original args from command line (excluding 'wolfv' itself)
        original_args = sys.argv[1:]
        
        # Build new args: add --image <path> and --model qwen3-v1:8b
        new_args = original_args + ["--image", screenshot_path, "--model", "qwen3-vl:8b"]
        
        # Temporarily replace sys.argv for Click to parse
        old_argv = sys.argv
        try:
            sys.argv = ["wolf"] + new_args
            wolf(standalone_mode=False)
        finally:
            sys.argv = old_argv
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(130)
    
    except Exception as exc:
        console.print(f"[red]Fatal error in wolfv:[/red] {exc}")
        import traceback
        console.print("\n[dim]Traceback:[/dim]")
        console.print(traceback.format_exc())
        sys.exit(1)


def main_web():
    """
    Entry point for wolfw console script.
    
    Performs a web search using DuckDuckGo and has the LLM summarize results.
    """
    try:
        # Get the prompt from command line
        original_args = sys.argv[1:]
        
        if not original_args:
            console.print("[yellow]No search query provided.[/yellow]")
            console.print("\nUsage examples:")
            console.print("  wolfw \"artificial intelligence trends\"")
            console.print("  wolfw \"python programming best practices\"")
            sys.exit(1)
        
        # Join all arguments as the search query
        user_prompt = " ".join(original_args)
        
        console.print("[cyan]Searching the web...[/cyan]")
        console.print()
        
        # Load configuration
        config = get_config()
        config.ensure_initialized()
        
        # Prepare a web-search-focused system prompt and temporarily override config
        web_system_prompt = (
            "You are in web-search mode. Use the search_web tool to retrieve up to 10 DuckDuckGo results for the user's query. "
            "Then synthesize a clear, helpful summary with the most relevant findings. Include key takeaways as bullet points and "
            "provide source URLs. If no results are found, explain and suggest alternative queries. Be concise and informative."
        )
        original_system_prompt = config.get("system_prompt")
        config.set("system_prompt", web_system_prompt)
        config.save()
        
        try:
            # Setup logging
            log_file = "wolf-cli.log"
            setup_logging(log_file=log_file, verbose=False)
            
            # Initialize core components
            registry = get_registry()
            
            # Use interactive trust level for web searches
            permission_manager = PermissionManager(
                trust_level=TrustLevel.INTERACTIVE,
                custom_allowlist=config.get("custom_allowlist", []),
                custom_denylist=config.get("custom_denylist", []),
            )
            
            # Initialize tool executor
            tool_executor = ToolExecutor(permission_manager=permission_manager)
            
            # Initialize orchestrator
            orchestrator = Orchestrator(
                tool_executor=tool_executor,
                provider="ollama",
                model=None,
                max_tool_iterations=config.get("max_tool_iterations", 6),
            )
            
            # Run orchestration
            console.print(f"[cyan]Web Search[/cyan] - Provider: ollama, Model: {orchestrator.model}")
            console.print()
            
            result = orchestrator.run(
                prompt=user_prompt,
                images=None,
            )
            
            # Display result
            if result.get("ok"):
                assistant_text = result.get("text", "")
                if assistant_text:
                    console.print("[green]Results:[/green]")
                    console.print(assistant_text)
                else:
                    console.print("[yellow]No results found.[/yellow]")
                sys.exit(0)
            else:
                error_msg = result.get("error", "Unknown error")
                console.print(f"[red]Error:[/red] {error_msg}")
                sys.exit(1)
        finally:
            # Restore original system prompt
            config.set("system_prompt", original_system_prompt)
            config.save()
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(130)
    
    except Exception as exc:
        console.print(f"[red]Fatal error in wolfw:[/red] {exc}")
        import traceback
        console.print("\n[dim]Traceback:[/dim]")
        console.print(traceback.format_exc())
        sys.exit(1)


def main():
    """Entry point for console script."""
    wolf()


if __name__ == "__main__":
    wolf()
