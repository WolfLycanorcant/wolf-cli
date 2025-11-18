"""
Wolf CLI Configuration Manager

Loads and merges configuration from multiple sources:
1. Defaults (hardcoded)
2. Config file (.wolf-cli-config.json)
3. .env file
4. Environment variables
5. CLI flags (passed at runtime)
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv

from .utils.paths import get_config_dir

# Default system prompt for Wolf CLI  
DEFAULT_SYSTEM_PROMPT = """You are Wolf, a helpful command-line assistant.

You have access to tools for file operations and command execution. However, you should ONLY use tools when the user explicitly requests an action on files or commands.

For casual conversation, greetings, questions about your capabilities, or general help requests, respond conversationally WITHOUT using any tools.

Examples:

User: "hey there"
Assistant: Hi! I'm Wolf, your command-line assistant. I can help you with file operations and running commands. What can I do for you?

User: "what can you do?"
Assistant: I can help you manage files (list, create, read, write, delete) and execute shell commands. Just ask me to perform any of these tasks!

User: "list files"
Assistant: [calls list_directory tool]

User: "create a file called test.txt"
Assistant: [calls create_file tool with path="test.txt"]

Remember: Only use tools for explicit file/command requests, not for conversation.
"""

# Default configuration
# Note: These defaults can be overridden by .env file or environment variables
DEFAULT_CONFIG = {
    "model_provider": "ollama",
    "ollama_model": "granite3.1-moe:3b",
    "vision_model": "qwen3-vl:8b",  # Vision model for wolfv command
    "ollama_base_url": "http://localhost:11434",
    "openrouter_api_key": "",
    "openrouter_model": "openrouter/auto",
    "cursor_api_url": "http://localhost:5005",  # Cursor API base URL
    "default_trust_level": "interactive",  # safe-only, interactive, auto
    "custom_allowlist": [],
    "custom_denylist": [],
    "enable_logging": True,
    "log_file": "wolf-cli.log",
    "max_tool_iterations": 6,
    "timeout_sec": 120,
    "system_prompt": DEFAULT_SYSTEM_PROMPT,
    # Vision mode persistence (for wolfv command)
    "vision_mode_active": False,
    "previous_model": None,
}


class WolfConfig:
    """Wolf CLI configuration manager"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager
        
        Args:
            config_path: Optional path to config file. If None, uses default location.
        """
        self.config_path = config_path or self._get_default_config_path()
        self.config: Dict[str, Any] = {}
        self.load()
    
    def _get_default_config_path(self) -> Path:
        """Get default configuration file path (OS-appropriate location)"""
        # Use OS-appropriate config directory
        # Windows: %APPDATA%\wolf-cli
        # Linux/macOS: $XDG_CONFIG_HOME/wolf-cli or ~/.config/wolf-cli
        config_dir = get_config_dir("wolf-cli")
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "config.json"
    
    def load(self) -> None:
        """Load configuration from all sources in priority order"""
        # Start with defaults
        self.config = DEFAULT_CONFIG.copy()
        
        # Load .env file from multiple possible locations
        # Priority: current directory, installation directory, user home
        env_paths = [
            Path.cwd() / ".env",  # Current working directory
            Path(__file__).parent.parent.parent / ".env",  # Project root (if running from source)
            Path.home() / ".wolf-cli" / ".env",  # User home directory
            self.config_path.parent / ".env",  # Config directory
        ]
        
        env_loaded = False
        for env_path in env_paths:
            if env_path.exists():
                load_dotenv(env_path, override=True)  # override=True ensures .env takes precedence
                env_loaded = True
                break
        
        # Load from config.json file if exists (but env vars will override it)
        if Path(self.config_path).exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    self.config.update(file_config)
            except Exception as e:
                print(f"[Warn] Failed to load config from {self.config_path}: {e}")
        
        # Override with environment variables (this should override config.json)
        # Environment variables have highest priority (except CLI flags)
        self._load_from_env()
    
    def _load_from_env(self) -> None:
        """Load configuration from environment variables"""
        env_mappings = {
            "WOLF_MODEL_PROVIDER": "model_provider",
            "WOLF_OLLAMA_MODEL": "ollama_model",
            "WOLF_VISION_MODEL": "vision_model",
            "WOLF_OLLAMA_BASE_URL": "ollama_base_url",
            "WOLF_OPENROUTER_API_KEY": "openrouter_api_key",
            "WOLF_OPENROUTER_MODEL": "openrouter_model",
            "WOLF_CURSOR_API_URL": "cursor_api_url",
            "WOLF_TRUST_LEVEL": "default_trust_level",
            "WOLF_TIMEOUT": "timeout_sec",
        }
        
        for env_var, config_key in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Type conversion
                if config_key == "timeout_sec":
                    value = int(value)
                elif config_key == "enable_logging":
                    value = value.lower() in ('true', '1', 'yes')
                # Always override config.json with environment variables
                self.config[config_key] = value
    
    def save(self) -> None:
        """Save current configuration to file"""
        try:
            # Ensure directory exists
            Path(self.config_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Don't save values that come from environment variables
            # This prevents .env values from being overwritten by saved config
            config_to_save = self.config.copy()
            
            # Check which values are set by environment variables
            env_mappings = {
                "WOLF_MODEL_PROVIDER": "model_provider",
                "WOLF_OLLAMA_MODEL": "ollama_model",
                "WOLF_VISION_MODEL": "vision_model",
                "WOLF_OLLAMA_BASE_URL": "ollama_base_url",
                "WOLF_OPENROUTER_API_KEY": "openrouter_api_key",
                "WOLF_OPENROUTER_MODEL": "openrouter_model",
                "WOLF_CURSOR_API_URL": "cursor_api_url",
                "WOLF_TRUST_LEVEL": "default_trust_level",
                "WOLF_TIMEOUT": "timeout_sec",
            }
            
            # Remove env-set values from saved config (they'll be loaded from .env on next load)
            for env_var, config_key in env_mappings.items():
                if os.getenv(env_var) is not None:
                    # Don't save this value - it comes from .env
                    if config_key in config_to_save:
                        del config_to_save[config_key]
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, indent=2)
        except Exception as e:
            print(f"[Error] Failed to save config to {self.config_path}: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value"""
        self.config[key] = value
    
    def update(self, updates: Dict[str, Any]) -> None:
        """Update multiple configuration values"""
        self.config.update(updates)
    
    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as dictionary"""
        return self.config.copy()
    
    def ensure_initialized(self) -> None:
        """Ensure config file exists; create with defaults if not"""
        if not Path(self.config_path).exists():
            self.save()
            print(f"[Info] Created default config at {self.config_path}")


# Singleton instance
_config_instance: Optional[WolfConfig] = None


def get_config(config_path: Optional[str] = None) -> WolfConfig:
    """Get or create the global configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = WolfConfig(config_path)
    return _config_instance
