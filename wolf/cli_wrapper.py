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


def _print_wolf_help():
    """
    Display a custom help panel showing all wolf command variants.
    Uses Rich for formatted output with fallback to plain text.
    """
    try:
        from rich.panel import Panel
        
        help_console = Console()
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Command", style="cyan bold", no_wrap=True)
        table.add_column("Description", style="white")
        table.add_column("Example", style="dim")
        
        table.add_row(
            "wolf",
            "Chat with the default LLM model",
            'wolf "Explain this code"'
        )
        table.add_row(
            "wolfv",
            "Vision mode - takes screenshot and analyzes with qwen3-vl:8b",
            'wolfv "What\'s on my screen?"'
        )
        table.add_row(
            "wolfc / wolfcamera",
            "Camera mode - captures from USB camera (device 0) with qwen3-vl:8b",
            'wolfc "What do you see?"'
        )
        table.add_row(
            "wolfw",
            "Web search mode - searches DuckDuckGo and summarizes results",
            'wolfw "AI trends 2024"'
        )
        table.add_row(
            "wolfem",
            "Email management mode - interact with Thunderbird emails",
            'wolfem "list my mailboxes"'
        )
        
        panel = Panel(
            table,
            title="[bold cyan]Wolf CLI Command Reference[/bold cyan]",
            border_style="cyan",
            subtitle="[dim]Tip: Use 'wolf --help' for Click's built-in options[/dim]"
        )
        help_console.print(panel)
        
    except Exception:
        # Fallback to plain text if Rich fails
        print(
            "\nWolf CLI Command Reference\n"
            "=========================\n\n"
            "wolf   - Chat with the default LLM model\n"
            '         Example: wolf "Explain this code"\n\n'
            "wolfv  - Vision mode - takes screenshot and analyzes with qwen3-vl:8b\n"
            '         Example: wolfv "What\'s on my screen?"\n\n'
            "wolfc / wolfcamera  - Camera mode - captures from USB camera (device 0) with qwen3-vl:8b\n"
            '         Example: wolfc "What do you see?"\n\n'
            "wolfw  - Web search mode - searches DuckDuckGo and summarizes results\n"
            '         Example: wolfw "AI trends 2024"\n\n'
            "wolfem - Email management mode - interact with Thunderbird emails\n"
            '         Example: wolfem "list my mailboxes"\n\n'
            "Tip: Use 'wolf --help' for Click's built-in options\n"
        )


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option("--safe", is_flag=True, help="Enable safe mode (strict permissions, read-only).")
@click.option("--auto", is_flag=True, help="Allow automatic tool execution (permissive, no confirmations).")
@click.option("--image", "images", multiple=True, type=click.Path(exists=True, dir_okay=False, readable=True), help="Path(s) to image(s) for vision input.")
@click.option("--provider", type=click.Choice(["ollama", "openrouter"], case_sensitive=False), default="ollama", show_default=True, help="LLM provider to use. #future-use")
@click.option("--model", type=str, default=None, help="LLM model to use (overrides config).")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging (DEBUG level).")
@click.option("--list-tools", is_flag=True, help="List available tools and exit.")
@click.option("--max-iterations", type=int, default=None, help="Maximum number of tool iterations (overrides config).")
@click.option("--image-base64", "images_base64", multiple=True, type=str, help="Base64-encoded image(s) for vision input.")
@click.argument("prompt", nargs=-1)
@click.pass_context
def wolf(
    ctx: click.Context,
    safe: bool,
    auto: bool,
    images: Tuple[str, ...],
    images_base64: Tuple[str, ...],
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
        previous = config.get("previous_model") or config.get("ollama_model", "granite3.1-moe:3b")
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
        
        # Check for help command
        if prompt and len(prompt) == 1 and prompt[0].strip().lower() == "help":
            _print_wolf_help()
            return
        
        # Validate prompt
        if not prompt:
            console.print("[yellow]No prompt provided.[/yellow]")
            console.print("\nUsage examples:")
            console.print("  wolf \"create a file named test.txt\"")
            console.print("  wolf --image photo.jpg \"describe this image\"")
            console.print("  wolf --list-tools")
            console.print("  wolf help  # Show all wolf commands")
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
        
        # Resolve image paths to absolute paths
        resolved_images = None
        if images:
            from pathlib import Path
            resolved_images = []
            for img_path in images:
                try:
                    resolved_path = Path(img_path).resolve()
                    if not resolved_path.exists():
                        console.print(f"[red]Warning: Image not found: {resolved_path}[/red]")
                        continue
                    resolved_images.append(str(resolved_path))
                    console.print(f"[dim]Image: {resolved_path}[/dim]")
                except Exception as e:
                    console.print(f"[red]Warning: Could not resolve image path '{img_path}': {e}[/red]")
                    continue
            
            if not resolved_images:
                console.print("[red]Error: No valid images found![/red]")
                sys.exit(1)
        
        # Run orchestration
        console.print(f"[cyan][Wolf CLI][/cyan] - Provider: {provider}, Model: {orchestrator.model}")
        if resolved_images:
            console.print(f"[dim]Processing {len(resolved_images)} image(s) with vision model...[/dim]")
        console.print()
        
        result = orchestrator.run(
            prompt=user_prompt,
            images=resolved_images,
            images_base64=images_base64
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
        
        # Activate vision mode - use vision_model from config
        vision_model = config.get("vision_model", "qwen3-vl:8b")
        config.set("vision_mode_active", True)
        config.set("ollama_model", vision_model)
        config.save()
        
        # Build arguments to forward to wolf()
        # We need to programmatically invoke wolf with additional args
        # Since wolf is a Click command, we use Click's invoke mechanism
        import sys
        
        # Prepare new argv with --image and --model flags injected
        # Original args from command line (excluding 'wolfv' itself)
        original_args = sys.argv[1:]
        
        # Build new args: add --image <path> and --model (from config)
        new_args = original_args + ["--image", screenshot_path, "--model", vision_model]
        
        # Temporarily replace sys.argv for Click to parse
        old_argv = sys.argv
        try:
            sys.argv = ["wolf"] + new_args
            # Directly invoke the wolf command with the arguments
            ctx = wolf.make_context(info_name='wolf', args=new_args)
            with ctx:
                wolf.invoke(ctx)
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


def main_email():
    """
    Entry point for wolfem console script.
    
    Provides a focused interface for email management.
    """
    try:
        # Get the prompt from command line
        original_args = sys.argv[1:]
        
        if not original_args:
            console.print("[yellow]No prompt provided.[/yellow]")
            console.print("\nUsage examples:")
            console.print("  wolfem \"list my mailboxes\"")
            console.print("  wolfem \"read my inbox\"")
            sys.exit(1)
        
        # Join all arguments as the user prompt
        user_prompt = " ".join(original_args)
        
        console.print("[cyan]Email Management[/cyan]")
        console.print()
        
        # Load configuration
        config = get_config()
        config.ensure_initialized()
        
        # Prepare an email-focused system prompt
        email_system_prompt = (
            "You are in email management mode. Use the available tools to manage Thunderbird emails. "
            "You can list mailboxes and read emails from them. "
            "Be concise and helpful in your responses."
        )
        original_system_prompt = config.get("system_prompt")
        config.set("system_prompt", email_system_prompt)
        config.save()
        
        try:
            # Setup logging
            log_file = "wolf-cli.log"
            setup_logging(log_file=log_file, verbose=False)
            
            # Initialize core components
            registry = get_registry()
            
            # Use interactive trust level for email
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
            console.print(f"[cyan]Email[/cyan] - Provider: ollama, Model: {orchestrator.model}")
            console.print()
            
            result = orchestrator.run(
                prompt=user_prompt,
                images=None,
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
        finally:
            # Restore original system prompt
            config.set("system_prompt", original_system_prompt)
            config.save()
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(130)
    
    except Exception as exc:
        console.print(f"[red]Fatal error in wolfem:[/red] {exc}")
        import traceback
        console.print("\n[dim]Traceback:[/dim]")
        console.print(traceback.format_exc())
        sys.exit(1)


def main_camera():
    """
    Entry point for wolfcamera console script.
    
    Captures a photo from USB camera (device index 0), gets the most recent screenshot, 
    and activates vision mode with qwen3-vl:8b model.
    """
    try:
        # Import utilities
        from .utils.camera import capture_single_frame, CameraError
        from .utils.screenshot import get_most_recent_screenshot
        
        # Capture from camera
        console.print("[cyan]📸 Capturing from camera...[/cyan]")
        camera_image_path, camera_image_base64 = capture_single_frame()
        console.print(f"[green]✓[/green] Camera image saved: {camera_image_path}")
        
        # Get most recent screenshot
        console.print("[cyan]📸 Getting most recent screenshot...[/cyan]")
        screenshot_data = get_most_recent_screenshot()
        if screenshot_data:
            screenshot_path, screenshot_base64 = screenshot_data
            console.print(f"[green]✓[/green] Found screenshot: {screenshot_path}")
        else:
            screenshot_path, screenshot_base64 = None, None
            console.print("[yellow]No recent screenshot found.[/yellow]")
        console.print()
        
        # Load config and activate vision mode
        config = get_config()
        config.ensure_initialized()
        
        # Save previous model if not already in vision mode
        if not config.get("vision_mode_active"):
            previous = config.get("ollama_model", "gpt-oss:20b")
            config.set("previous_model", previous)
            console.print(f"[dim]Saved previous model: {previous}[/dim]")
        
        # Activate vision mode - use llava-llama3:8b for camera mode
        vision_model = "llava-llama3:8b"
        config.set("vision_mode_active", True)
        config.set("ollama_model", vision_model)
        config.save()
        
        console.print(f"[dim]Using vision model: {vision_model}[/dim]")
        console.print()
        
        # Build arguments to forward to wolf()
        original_args = sys.argv[1:]
        
        # Build new args: add --image for file paths (not base64 - too large for command line)
        new_args = original_args + ["--model", vision_model]
        if camera_image_path:
            new_args.extend(["--image", camera_image_path])
        if screenshot_path:
            new_args.extend(["--image", screenshot_path])
            
        # Temporarily replace sys.argv for Click to parse
        old_argv = sys.argv
        try:
            sys.argv = ["wolf"] + new_args
            # Directly invoke the wolf command with the arguments
            ctx = wolf.make_context(info_name='wolf', args=new_args)
            with ctx:
                wolf.invoke(ctx)
        finally:
            sys.argv = old_argv
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(130)
    
    except Exception as exc:
        # Check if it's a CameraError specifically
        from .utils.camera import CameraError
        if isinstance(exc, CameraError):
            console.print(f"[red]Camera error:[/red] {exc}")
        else:
            console.print(f"[red]Fatal error in wolfcamera:[/red] {exc}")
        import traceback
        console.print("\n[dim]Traceback:[/dim]")
        console.print(traceback.format_exc())
        sys.exit(1)


def main():
    """Entry point for console script."""
    wolf()


if __name__ == "__main__":
    wolf()
