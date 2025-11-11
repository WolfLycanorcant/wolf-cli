# Changelog

All notable changes to Wolf CLI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.2] - 2025-11-10

### Added
- **Web Search Tool (`wolfw` command)**: New DuckDuckGo-powered web search functionality
  - Search the web for up to 10 results by default (configurable 1-50)
  - LLM synthesizes results into organized summaries
  - Includes source URLs and key takeaways
  - Safe operation - no confirmation prompts required
  - Privacy-respecting searches via DuckDuckGo
- **New Provider**: `wolf/providers/web_search.py`
  - Implements `search_web(query, max_results=10)` function
  - Uses `ddgs` library
  - Robust error handling and graceful fallbacks
  - Normalizes results to consistent schema (title, url, snippet)
- **Web & Information Category**: New tool category in registry
- **Three CLI Variants**: Wolf CLI now provides three commands
  - `wolf` - Standard AI assistant with tools
  - `wolfv` - Vision mode with auto screenshot capture
  - `wolfw` - Web search mode with DuckDuckGo
- **Dependencies**: Added `ddgs>=3.1.0` for DuckDuckGo integration

### Changed
- **Tool Count**: Increased from 10 to 11 tools
- **Tool Categories**: Added new "Web & Information" category
- **System Prompt (Web Mode)**: Specialized prompt for `wolfw` to ensure LLM:
  - Calls search_web tool
  - Synthesizes results (not raw JSON)
  - Includes source URLs
  - Provides helpful fallback suggestions

### Improved
- **Research Capabilities**: Wolf CLI can now search the web for current information
- **Information Access**: Users can get up-to-date answers to research questions
- **Flexibility**: Multiple command modes for different use cases

### Documentation
- Added "Web Search Mode with `wolfw`" section to README.md
- Added "Web Search & Research" examples section to README.md
- Updated TASK_SUMMARY.md:
  - Marked Web & Network Tools as ✅ Complete
  - Added `wolfw` to CLI flags section
  - Updated completed tasks checklist
  - Added web search examples to Live Tests
- Updated TEST_GUIDE.md:
  - Added Test #11: Web Search Test (wolfw)
  - Updated tool count from 10 to 11
  - Updated success criteria to include wolfw
- Created docs/V0.3.2_SUMMARY.md with comprehensive release notes

### Testing
- ✅ Web search tool functionality verified
- ✅ DuckDuckGo integration tested
- ✅ LLM result summarization verified
- ✅ Tool registry correctly shows 11 tools
- ✅ `wolfw` CLI command functional
- ✅ System prompt override working correctly
- **Confidence Level**: 95%

### Breaking Changes
None - this is a purely additive release

---

## [0.3.1] - 2025-11-08

### Added
- **Bash Launcher Script**: Added `wolf.sh` for Linux/macOS users as equivalent to `wolf.ps1`
- **Cross-Platform Configuration Paths**: Implemented OS-appropriate config directories
  - Windows: `%APPDATA%\wolf-cli\config.json`
  - Linux: `$XDG_CONFIG_HOME/wolf-cli/config.json` or `~/.config/wolf-cli/config.json`
  - macOS: `~/.config/wolf-cli/config.json`
- New utility function `get_config_dir()` in `paths.py` for platform-aware config directory resolution

### Changed
- **Configuration Path**: Removed hardcoded Windows path in `config_manager.py`
- **Disk Usage Detection**: Fixed hardcoded `C:\` in `ps_client.py` to use `get_root_disk_path()`
- **setup.py Classifiers**: Added Linux and macOS to supported operating systems
  - `Operating System :: POSIX :: Linux`
  - `Operating System :: MacOS :: MacOS X`

### Improved
- **Linux/macOS Installation**: Wolf CLI now properly installs and runs on Linux and macOS
- **Documentation**: Updated README with platform-specific installation instructions
- **Path Utilities**: Updated `paths.py` docstring to reflect cross-platform support

### Fixed
- Config files no longer created in Windows-specific paths on Linux/macOS
- Disk usage information now correctly uses root path (`/`) on Unix-like systems

## [0.3.0] - 2025-11-08

### Added
- **Cross-Platform Architecture**: Wolf CLI designed to run on Windows, Linux, and macOS
  - Platform detection utilities (`platform_utils.py`)
  - Automatic shell selection (PowerShell on Windows, Bash on Linux/macOS)
  - Platform-specific command filtering
  - **Status**: Windows fully tested, Linux/macOS pending real-world validation
- **Linux/Unix Command Filtering**: Added Linux-specific denylist and allowlist
  - Dangerous commands: rm -rf, dd, mkfs, fork bomb, etc.
  - Safe commands: ls, cat, grep, ps, df, etc.
- System info now includes platform and shell information

### Changed
- **Renamed `ps_client.py` to `shell_client.py`** for platform-agnostic naming
- `execute_powershell_command` → `execute_shell_command` (with backward compatibility alias)
- Tool descriptions updated to mention "shell" instead of "PowerShell"
- System prompt updated to be platform-agnostic
- Disk usage detection now uses appropriate root path per platform (C:\ or /)

### Improved
- Better error messages that mention the detected shell
- Shell commands automatically use the correct shell for the platform
- Command filtering adapts to the current platform

### Documentation
- README updated to reflect cross-platform support
- Platform-specific prerequisites clearly documented

## [0.2.0] - 2025-11-07

### Added
- **Configurable System Prompt**: Added `system_prompt` field to configuration that guides LLM behavior
  - Instructs the model to respond conversationally to greetings and questions
  - Only uses tools when explicitly requested for file operations or commands
  - Customizable via config file for different use cases
- Debug logging to verify system prompt is loaded and sent to LLM

### Changed
- **Default Model**: Changed from `llama3.2:latest` to `gpt-oss:20b` for better instruction-following
  - Larger 20B parameter model provides more reliable tool usage
  - Better understanding of when to use tools vs conversational responses
- Updated DEFAULT_CONFIG in `config_manager.py` to include system prompt

### Improved
- **More Intuitive Prompting**: Wolf now correctly distinguishes between:
  - Casual conversation (greetings, capability questions) → No tools used
  - Explicit action requests (list files, create file) → Appropriate tools used
- Better user experience with more natural, context-aware responses

### Documentation
- Updated README.md with:
  - System prompt configuration section
  - Recommended models for tool calling
  - Model size vs instruction-following quality notes
  - Updated troubleshooting for model compatibility

### Fixed
- Wolf no longer calls tools unnecessarily for simple greetings like "hey there"
- Improved tool selection logic through better prompt engineering

## [0.1.0] - 2025-11-07

### Added
- Initial release of Wolf CLI
- Core tool system with 10 tools for file operations and system tasks
- Ollama integration with tool-calling support
- Three-tier permission system (safe/interactive/auto)
- Safety controls and command filtering
- Rich console output with color-coded logging
- Configuration management with .env support
- PowerShell integration for Windows
