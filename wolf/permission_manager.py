"""
Wolf CLI Permission Manager

Handles permission checks, trust levels, and user confirmations for tools.
"""

import re
from enum import Enum
from typing import Any, Dict, List, Optional

from prompt_toolkit import prompt
from prompt_toolkit.validation import Validator, ValidationError

from .utils.logging_utils import log_warn, log_info, log_error, console
from .utils.platform_utils import is_windows


class TrustLevel(Enum):
    """Trust levels for tool execution"""
    SAFE_ONLY = "safe-only"      # Only execute safe tools
    INTERACTIVE = "interactive"  # Ask confirmation for modifying/destructive
    AUTO = "auto"                # Execute automatically (with logging)


class RiskLevel(Enum):
    """Risk levels for tools"""
    SAFE = "safe"                # Read-only, no side effects
    MODIFYING = "modifying"      # Creates/modifies files or system state
    DESTRUCTIVE = "destructive"  # Deletes data or makes irreversible changes


# Windows PowerShell command denylist
WINDOWS_DENYLIST = [
    r"(?i)\b(remove-item|ri)\b.*-recurse",
    r"(?i)\b(del|erase|rd|rmdir)\b.*(/s|/q)",
    r"(?i)\b(format-?volume|diskpart|bcdedit|cipher\s+/w:|takeown|icacls)\b",
    r"(?i)\b(invoke-expression|iex)\b",
    r"(?i)(invoke-webrequest|curl|wget).*\|.*(iex|invoke-expression)",
    r"(?i)\breg(?:\.exe)?\s+delete\b",
    r"(?i)\b(get-credential|convertto-securestring)\b.*-asplaintext",
]

# Linux/Unix command denylist
LINUX_DENYLIST = [
    r"(?i)\brm\s+.*-rf?\s+/",  # rm -rf /
    r"(?i)\brm\s+.*-rf?.*\*",  # rm -rf with wildcards
    r"(?i)\bdd\s+if=.*of=/dev/",  # dd to devices
    r"(?i)\bmkfs\b",  # Format filesystem
    r"(?i)\b(fdisk|parted|gparted)\b",  # Disk partitioning
    r"(?i)\bchmod\s+777\s+-R\s+/",  # Dangerous permissions
    r"(?i):\(\)\{\s*:\|:&\s*\};:",  # Fork bomb
    r"(?i)\bcurl.*\|\s*(bash|sh)",  # Piped web downloads to shell
    r"(?i)\bwget.*\|\s*(bash|sh)",
    r"(?i)\b(shutdown|reboot|init\s+[06])\b",  # System shutdown/reboot
]

# Windows PowerShell command allowlist (safe read-only commands)
WINDOWS_ALLOWLIST = [
    r"(?i)^get-process\b",
    r"(?i)^get-service\b",
    r"(?i)^get-help\b",
    r"(?i)^(get-childitem|gci|dir|ls)\b",
    r"(?i)^(get-content|gc|cat|type)\b",
    r"(?i)^(select-string|findstr|grep)\b",
    r"(?i)^(get-location|pwd|gl)\b",
    r"(?i)^(get-item|gi)\b",
    r"(?i)^(where-object|where|\?)\b",
]

# Linux/Unix command allowlist (safe read-only commands)
LINUX_ALLOWLIST = [
    r"(?i)^(ls|dir)\b",
    r"(?i)^(cat|less|more|head|tail)\b",
    r"(?i)^(grep|egrep|fgrep)\b",
    r"(?i)^(find|locate)\b",
    r"(?i)^(pwd|cd)\b",
    r"(?i)^(echo|printf)\b",
    r"(?i)^(ps|top|htop)\b",
    r"(?i)^(df|du)\b",
    r"(?i)^(uname|hostname)\b",
    r"(?i)^(which|whereis)\b",
]

# Select platform-appropriate defaults
DEFAULT_DENYLIST = WINDOWS_DENYLIST if is_windows() else LINUX_DENYLIST
DEFAULT_ALLOWLIST = WINDOWS_ALLOWLIST if is_windows() else LINUX_ALLOWLIST


class YesValidator(Validator):
    """Validator for YES confirmation"""
    def validate(self, document):
        text = document.text.strip()
        if text not in ['YES', 'yes', 'Yes']:
            raise ValidationError(message='Please type YES to confirm')


class PermissionManager:
    """Manages permissions and confirmations for tool execution"""
    
    def __init__(
        self,
        trust_level: TrustLevel = TrustLevel.INTERACTIVE,
        custom_allowlist: Optional[List[str]] = None,
        custom_denylist: Optional[List[str]] = None,
    ):
        """
        Initialize permission manager
        
        Args:
            trust_level: Default trust level
            custom_allowlist: Custom command allowlist patterns
            custom_denylist: Custom command denylist patterns
        """
        self.trust_level = trust_level
        
        # Compile regex patterns
        self.denylist_patterns = [
            re.compile(pattern) for pattern in (DEFAULT_DENYLIST + (custom_denylist or []))
        ]
        self.allowlist_patterns = [
            re.compile(pattern) for pattern in (DEFAULT_ALLOWLIST + (custom_allowlist or []))
        ]
    
    def set_trust_level(self, trust_level: TrustLevel) -> None:
        """Set the current trust level"""
        self.trust_level = trust_level
        log_info(f"Trust level set to: {trust_level.value}")
    
    def check_command(self, command: str) -> tuple[bool, str]:
        """
        Check if a command is allowed based on allow/deny lists
        
        Args:
            command: Command to check
            
        Returns:
            Tuple of (is_allowed, reason)
        """
        # Check denylist first (takes precedence)
        for pattern in self.denylist_patterns:
            if pattern.search(command):
                return False, f"Command matches denylist pattern: {pattern.pattern}"
        
        # Check allowlist
        for pattern in self.allowlist_patterns:
            if pattern.search(command):
                return True, "Command matches allowlist"
        
        # Not in either list - depends on trust level
        return True, "Command not in denylist"
    
    def requires_confirmation(
        self,
        risk_level: RiskLevel,
        tool_name: str,
        params: Dict[str, Any]
    ) -> tuple[bool, str]:
        """
        Determine if a tool call requires user confirmation
        
        Args:
            risk_level: Risk level of the tool
            tool_name: Name of the tool
            params: Tool parameters
            
        Returns:
            Tuple of (requires_confirmation, confirmation_type)
            confirmation_type is one of: 'none', 'yn', 'yes'
        """
        # SAFE_ONLY mode: block modifying and destructive
        if self.trust_level == TrustLevel.SAFE_ONLY:
            if risk_level != RiskLevel.SAFE:
                return True, 'block'
        
        # AUTO mode: allow everything (with logging)
        if self.trust_level == TrustLevel.AUTO:
            return False, 'none'
        
        # INTERACTIVE mode: check risk level
        if risk_level == RiskLevel.SAFE:
            return False, 'none'
        elif risk_level == RiskLevel.MODIFYING:
            return True, 'yn'  # Y/n confirmation
        elif risk_level == RiskLevel.DESTRUCTIVE:
            return True, 'yes'  # Explicit YES required
        
        return False, 'none'
    
    def prompt_confirmation(
        self,
        tool_name: str,
        params: Dict[str, Any],
        confirmation_type: str,
        description: str = ""
    ) -> bool:
        """
        Prompt user for confirmation
        
        Args:
            tool_name: Name of the tool
            params: Tool parameters
            confirmation_type: Type of confirmation ('block', 'yn', 'yes')
            description: Optional description of what will happen
            
        Returns:
            True if user confirms, False otherwise
        """
        # If blocked in SAFE_ONLY mode
        if confirmation_type == 'block':
            console.print(f"\n[error]⚠ Tool '{tool_name}' is blocked in safe-only mode[/error]")
            return False
        
        # Show what will happen
        console.print(f"\n[warn]Tool:[/warn] {tool_name}")
        if description:
            console.print(f"[dim]{description}[/dim]")
        
        # Show parameters
        console.print("[warn]Parameters:[/warn]")
        for key, value in params.items():
            # Truncate long values
            value_str = str(value)
            if len(value_str) > 100:
                value_str = value_str[:97] + "..."
            console.print(f"  [dim]{key}:[/dim] {value_str}")
        
        try:
            if confirmation_type == 'yn':
                # Y/n confirmation (default yes)
                response = prompt("\nProceed? (Y/n): ", default="y").strip().lower()
                return response in ['y', 'yes', '']
            
            elif confirmation_type == 'yes':
                # Explicit YES required
                console.print("[error]⚠ This action is DESTRUCTIVE and cannot be undone![/error]")
                response = prompt("\nType YES to confirm: ", validator=YesValidator()).strip()
                return response in ['YES', 'yes', 'Yes']
        
        except (KeyboardInterrupt, EOFError):
            console.print("\n[warn]Cancelled by user[/warn]")
            return False
        
        return False
    
    def check_and_confirm(
        self,
        tool_name: str,
        risk_level: RiskLevel,
        params: Dict[str, Any],
        description: str = ""
    ) -> bool:
        """
        Check permissions and get confirmation if needed
        
        Args:
            tool_name: Name of the tool
            risk_level: Risk level of the tool
            params: Tool parameters
            description: Description of what the tool will do
            
        Returns:
            True if execution is allowed, False otherwise
        """
        # Special handling for execute_command - check against allow/deny lists
        if tool_name == "execute_command" and "command" in params:
            command = params["command"]
            is_allowed, reason = self.check_command(command)
            
            if not is_allowed:
                # Command in denylist - require explicit confirmation even in auto mode
                if self.trust_level == TrustLevel.AUTO:
                    log_warn(f"Command in denylist: {reason}")
                    return self.prompt_confirmation(tool_name, params, 'yes', description)
                else:
                    return self.prompt_confirmation(tool_name, params, 'yes', f"{description}\n{reason}")
        
        # Check if confirmation is required
        requires_conf, conf_type = self.requires_confirmation(risk_level, tool_name, params)
        
        if not requires_conf:
            # Log execution in auto mode
            if self.trust_level == TrustLevel.AUTO:
                log_info(f"Auto-executing: {tool_name}", verbose_only=True)
            return True
        
        # Get confirmation from user
        return self.prompt_confirmation(tool_name, params, conf_type, description)
