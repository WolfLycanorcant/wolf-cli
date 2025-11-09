"""
Wolf CLI Logging Utilities

Structured logging for console and file with different verbosity levels.
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler

from rich.console import Console
from rich.theme import Theme

# Custom theme for console output
WOLF_THEME = Theme({
    "info": "cyan",
    "tool": "green bold",
    "warn": "yellow",
    "error": "red bold",
    "success": "green",
})

# Global console instance
console = Console(theme=WOLF_THEME)

# Global logger
_logger: Optional[logging.Logger] = None
_verbose = False


def setup_logging(log_file: str = "wolf-cli.log", verbose: bool = False) -> logging.Logger:
    """
    Setup logging configuration
    
    Args:
        log_file: Path to log file
        verbose: Enable verbose console output
        
    Returns:
        Configured logger instance
    """
    global _logger, _verbose
    _verbose = verbose
    
    # Create logger
    logger = logging.getLogger("wolf-cli")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # File handler with rotation (10MB max, keep 3 backups)
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Console handler (minimal, styled output)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    console_handler.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(console_handler)
    
    _logger = logger
    return logger


def get_logger() -> logging.Logger:
    """Get the global logger instance"""
    global _logger
    if _logger is None:
        _logger = setup_logging()
    return _logger


def log_info(message: str, verbose_only: bool = False) -> None:
    """Log info message"""
    if verbose_only and not _verbose:
        return
    console.print(f"[info][Info][/info] {message}")
    get_logger().info(message)


def log_tool(tool_name: str, message: str) -> None:
    """Log tool execution message"""
    console.print(f"[tool][Tool: {tool_name}][/tool] {message}")
    get_logger().info(f"[Tool: {tool_name}] {message}")


def log_warn(message: str) -> None:
    """Log warning message"""
    console.print(f"[warn][Warn][/warn] {message}")
    get_logger().warning(message)


def log_error(message: str, exc_info: bool = False) -> None:
    """Log error message"""
    console.print(f"[error][Error][/error] {message}")
    get_logger().error(message, exc_info=exc_info)


def log_success(message: str) -> None:
    """Log success message"""
    console.print(f"[success][Success][/success] {message}")
    get_logger().info(f"[Success] {message}")


def log_debug(message: str) -> None:
    """Log debug message (verbose only)"""
    if _verbose:
        console.print(f"[dim][Debug] {message}[/dim]")
    get_logger().debug(message)


def print_separator(char: str = "-", length: int = 60) -> None:
    """Print a visual separator"""
    console.print(char * length, style="dim")
