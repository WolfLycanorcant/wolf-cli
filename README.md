# 🐺 Wolf CLI

**A powerful Windows 11 AI-powered command-line assistant with tool-calling, safety controls, and local LLM support.**

Wolf CLI is a production-ready terminal assistant that combines the power of Large Language Models (LLMs) with safe, controlled system access through a comprehensive tool ecosystem. It runs locally using Ollama and provides intelligent automation for file operations, system tasks, and more.

**Platform Support**: 
- ✅ **Windows 11** - Fully supported with cross-platform config paths

> **Note:** This project is a fork of [shell_gpt](https://github.com/TheR1D/shell_gpt) by TheR1D, extended with comprehensive tool-calling capabilities, enhanced safety controls, and cross-platform shell integration.

---

## ✨ Features

### 🛠️ **Comprehensive Tool Suite**
- **File Operations**: Create, read, write, delete, move, copy files
- **System Integration**: Execute PowerShell commands, get system info
- **Safety First**: Three-tier permission system (safe/interactive/auto)
- **Smart Confirmations**: Automatic for safe operations, prompts for risky ones

### 🔒 **Safety & Security**
- **Risk-Based Permissions**: Safe, modifying, and destructive operation levels
- **Command Filtering**: Platform-specific denylists (PowerShell)
- **Recycle Bin Integration**: Safe deletion with recovery option
- **Safe Mode**: Read-only operations when you need maximum safety

### 🎨 **Developer Experience**
- **Rich Console Output**: Color-coded, structured logging
- **Verbose Mode**: Detailed debug information when needed
- **Configuration**: Flexible config system with .env support
- **Transparent**: See exactly what tools are being called and why

---

## 🚀 Quick Start



### Prerequisites



1.  **Python 3.11+**

2.  **Shell**: PowerShell 7+ (Windows)

3.  **Ollama**: Download and install the latest version from [ollama.com](https://ollama.com/).



### Installation

# 3. Install dependencies and the project in editable mode
#    'pip install -r requirements.txt' installs all necessary libraries.
#    'pip install -e .' allows you to run the 'wolf' command directly from this directory
#    and ensures any changes to the source code are immediately reflected.
pip install -r requirements.txt
pip install -e .



# 4. Pull the required Ollama models







ollama pull gpt-oss:20b (Context Length: 131072)







ollama pull qwen3-vl:8b



# 5. Start using Wolf!

wolf --list-tools

```





### First Run

```bash
# List available tools
wolf --list-tools

# Try a simple query
wolf 'what files are in the current directory?'

# Create a file (will ask for confirmation)
wolf 'create a file named hello.txt with \'Hello World!\''
```


---

## 📚 Usage

### Basic Commands

```bash
# Standard interactive mode (default)
wolf 'your prompt here'

# Safe mode (read-only operations only)
wolf --safe 'list all python files'

# Auto mode (no confirmations, use with caution!)
wolf --auto 'create test files'

# Verbose logging
wolf -v 'show system info'

# List all available tools
wolf --list-tools

# Include images for vision capabilities
wolf --image photo.jpg 'describe this image'

# Vision mode with automatic screenshot (Windows only)
wolfv "what's on my screen?"
```

### Vision Mode with `wolfv` (Windows)

The `wolfv` command automatically captures a screenshot and analyzes it using the vision model:

```bash
# Automatically capture and analyze your screen
wolfv 'describe what you see'

# Ask specific questions about your screen
wolfv 'what application is open?'

# Vision mode persists - subsequent wolfv calls continue using vision model
wolfv 'what changed since last time?'

# Exit vision mode by using regular wolf command
wolf 'hello'  # This restores the previous model
```

**How it works:**
- Takes a full-screen screenshot automatically
- Saves to current directory as `wolf-screenshot_YYYY-MM-DD_HH-MM-SS.png`
- Switches to vision model (`qwen3-v1:8b` by default)
- Vision mode persists across calls until you use `wolf` again
- Screenshots are kept locally for your reference

**Requirements:**
- Currently Windows-only (uses Windows APIs for screenshot capture)
- Requires vision model: `ollama pull qwen3-v1:8b` (or similar vision-capable model)
- Pillow (PIL) for image handling (already in requirements)

**Note:** Each `wolfv` invocation captures a new screenshot, so you can track changes over time.

### Web Search Mode with `wolfw`

The `wolfw` command performs DuckDuckGo web searches and has the LLM synthesize and summarize the results:

```bash
# Search the web for a topic
wolfw 'artificial intelligence trends 2025'

# Ask a question that requires web research
wolfw 'what are the best Python web frameworks in 2024?'

# Multi-word queries work naturally
wolfw 'machine learning best practices'
```

**How it works:**
- Automatically searches DuckDuckGo for up to 10 results by default
- Returns results with titles, URLs, and snippets
- LLM synthesizes findings into a clear, organized summary
- Includes source URLs and key takeaways
- No confirmation prompts required (safe read-only operation)

**Features:**
- Fast, privacy-respecting searches via DuckDuckGo
- Intelligent result summarization by LLM
- Graceful fallback if no results found
- Respects system prompt and model settings

---

## 🎯 Examples

### File Operations

```bash
# Create a file
wolf 'create a file named notes.txt with my meeting notes'

# Read a file
wolf 'read the contents of config.json'

# List directory contents
wolf 'show me all markdown files in this folder'

# Move files
wolf 'move all .log files to the logs folder'
```

### System Tasks

```bash
# Get system information
wolf 'show me system information'

# Run shell commands (PowerShell/Bash depending on platform)
wolf 'get the top 5 processes by CPU usage'

# List running services
wolf 'show me all running services'
```

### Multi-Step Tasks

```bash
# Chain multiple operations
wolf 'create a file named test.txt with \'hello\', then read it back to me'

# Complex workflows
wolf 'list all .py files, then create a summary.txt with their names'
```

### Web Search & Research

```bash
# Search for latest technology trends
wolfw 'artificial intelligence trends 2025'

# Compare programming frameworks
wolfw 'best Python web frameworks comparison'

# Find solutions and best practices
wolfw 'how to optimize database queries'

# Research specific topics
wolfw 'machine learning for beginners'

# Get current information
wolfw 'latest developments in quantum computing'

# Find tutorials and guides
wolfw 'React hooks tutorial for beginners'
```

---

## ⚙️ Configuration

### Configuration File

Wolf CLI uses a platform-appropriate configuration file:

**Windows:**
```
%APPDATA%\wolf-cli\config.json
```
Example: `C:\Users\YourName\AppData\Roaming\wolf-cli\config.json`

**Linux:**
```
$XDG_CONFIG_HOME/wolf-cli/config.json
```
Or `~/.config/wolf-cli/config.json` if `XDG_CONFIG_HOME` is not set

**macOS:**
```
~/.config/wolf-cli/config.json
```

> **Note:** You can override the config location on Linux/macOS by setting the `XDG_CONFIG_HOME` environment variable.

**Default Configuration:**
```json
{
  "model_provider": "ollama",
  "ollama_model": "gpt-oss:20b (Context Length: 131072)",
  "ollama_base_url": "http://localhost:11434",
  "openrouter_api_key": "", #future-use
  "openrouter_model": "openrouter/auto", #future-use
  "default_trust_level": "interactive",
  "custom_allowlist": [],
  "custom_denylist": [],
  "enable_logging": true,
  "log_file": "wolf-cli.log",
  "max_tool_iterations": 6,
  "timeout_sec": 120,
  "system_prompt": "<default system prompt - see below>"
}
```

### System Prompt

Wolf CLI uses a system prompt to guide the LLM's behavior. The prompt instructs the model to:
- Respond conversationally to greetings, questions, and casual conversation (without using tools)
- Only use tools when explicitly asked to perform file operations or execute commands
- Be concise and helpful

**You can customize the system prompt** by editing the `system_prompt` field in your config file. This allows you to:
- Make Wolf more or less proactive
- Add domain-specific instructions
- Adjust the assistant's personality

**Note:** The system prompt is automatically included in the default config. Larger models (13B+ parameters) follow instructions more reliably than smaller models.

### Environment Variables

You can also configure Wolf CLI using environment variables or a `.env` file:

```bash
WOLF_MODEL_PROVIDER=ollama
WOLF_OLLAMA_MODEL=gpt-oss:20b (Context Length: 131072)
WOLF_OLLAMA_BASE_URL=http://localhost:11434
WOLF_OPENROUTER_API_KEY= #future-use
WOLF_TRUST_LEVEL=interactive
WOLF_TIMEOUT=120

```

### Trust Levels

| Level | Description | Use Case |
|-------|-------------|----------|
| **safe** | Only read-only operations | Exploring unfamiliar codebases |
| **interactive** | Confirms before modifying (default) | Daily development work |
| **auto** | Executes automatically | Automation scripts, trusted tasks |

---

## 🛡️ Safety System

### Risk Levels

Wolf CLI categorizes all tools by risk level:

| Risk | Examples | Confirmation |
|------|----------|--------------|
| **Safe** | read_file, list_directory, get_system_info | None (auto-execute) |
| **Modifying** | create_file, write_file, execute_command | Y/n prompt |
| **Destructive** | delete_file | Must type "YES" |

### Command Filtering

Dangerous PowerShell commands are automatically filtered:
- `Remove-Item -Recurse`
- `Format-Volume`, `diskpart`
- `Invoke-Expression` with web downloads
- Registry deletions
- And more...

### Safe Deletion

Files are moved to the Recycle Bin instead of permanent deletion, allowing recovery if needed.

---

## 🧰 Available Tools

| Tool | Description | Risk Level |
|------|-------------|------------|
| `create_file` | Create a new file | Modifying |
| `read_file` | Read file contents | Safe |
| `write_file` | Write/overwrite file | Modifying |
| `delete_file` | Delete file (to recycle bin) | Destructive |
| `move_file` | Move or rename file | Modifying |
| `copy_file` | Copy file to new location | Modifying |
| `list_directory` | List directory contents | Safe |
| `get_file_info` | Get file metadata | Safe |
| `execute_command` | Run PowerShell command | Modifying |
| `get_system_info` | Get system information | Safe |

---

## 🐛 Troubleshooting

### Ollama Connection Error

```
Error: Ollama API error: Connection refused
```

**Solution:**
```powershell
# Start Ollama server
ollama serve

# Verify it's running
ollama list
```

### Model Not Found or Doesn't Support Tools

```
Error: Model doesn't support tools
Error: 400 Client Error: Bad Request
```

**Solution:**
Not all Ollama models support function calling. Recommended models:
- `gpt-oss:20b` (default, best instruction-following, Context Length: 131072)
- `llama3.2:latest` (smaller, faster, less reliable)
- `qwen3:8b` (good tool support)

```powershell
# Pull a recommended model
ollama pull gpt-oss:20b (Context Length: 131072)
```

### Permission Denied in Safe Mode

```
⚠ Tool 'create_file' is blocked in safe-only mode
```

**Solution:**
This is expected! Safe mode blocks modifying operations. Use interactive or auto mode:
```powershell
wolf "create file"  # Interactive mode
wolf --auto "create file"  # Auto mode
```


---

## 📁 Project Structure

```
wolf-cli/
├── wolf/                      # Main package
│   ├── cli_wrapper.py         # CLI entry point
│   ├── config_manager.py      # Configuration system
│   ├── permission_manager.py  # Safety & permissions
│   ├── tool_registry.py       # Tool schema registry
│   ├── tool_executor.py       # Tool execution engine
│   ├── orchestrator.py        # LLM orchestration loop
│   ├── llm/                   # LLM adapters
│   │   └── ollama.py          # Ollama integration
│   ├── providers/             # Tool implementations
│   │   ├── file_ops.py        # File operations
│   │   └── ps_client.py       # PowerShell executor
│   └── utils/                 # Utilities
│       ├── logging_utils.py   # Logging
│       ├── validation.py      # Validation
│       └── paths.py           # Path handling
├── docs/                      # Documentation
│   ├── TASK_SUMMARY.md        # Project details
│   └── TEST_GUIDE.md          # Testing guide
├── tests/                     # Test suite
├── .gitignore                 # Git ignore rules
├── README.md                  # User documentation
├── requirements.txt           # Python dependencies
├── setup.py                   # Package installation
```

---

## 📦 Dependencies

Wolf CLI automatically installs all required dependencies when you run `pip install -e .`. Key dependencies include:

**Core Framework:**
- `click` - CLI framework
- `rich` - Beautiful terminal output
- `prompt-toolkit` - Interactive prompts

**System & File Operations:**
- `psutil` - Cross-platform system information
- `send2trash` - Safe file deletion (cross-platform recycle bin)
- `pillow` - Image handling for vision features

**HTTP & API:**
- `requests` - HTTP client
- `httpx` - Async HTTP client
- `aiohttp` - Async HTTP framework

**Data Processing:**
- `pyyaml` - YAML parsing
- `jsonschema` - JSON validation
- `python-dateutil` - Date/time utilities

**Optional:**
- `duckduckgo-search` - Web search (Phase 2)
- `pyperclip` - Clipboard operations (Phase 2)

See `requirements.txt` for the complete list with version constraints.

---

## 🔧 Development

### Running Tests

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Follow test scenarios in TEST_GUIDE.md
```

### Adding Custom Tools

Tools are defined in `wolf/tool_registry.py`. To add a new tool:

1. Define the schema in the registry
2. Implement the handler in `wolf/providers/`
3. Register it with the appropriate risk level

---

## 🗺️ Roadmap

### ✅ Phase 1: MVP (Current)
- [x] Core tool system
- [x] File operations
- [x] Permission management
- [x] Ollama integration
- [x] Safety controls

### 📋 Phase 2: Extended Tools
- [ ] Web search (DuckDuckGo)
- [ ] HTTP request tool
- [ ] Data format conversions
- [ ] Git integration
- [ ] Clipboard operations

### 🚀 Phase 3: Advanced Features
- [ ] OpenRouter provider
- [ ] Conversation history
- [ ] Custom tool plugins
- [ ] Batch/script mode
- [ ] Tool usage analytics

---

## 📄 License

TBD

---

## 🙏 Acknowledgments

- **[shell_gpt](https://github.com/TheR1D/shell_gpt)** by TheR1D - The original project this fork is based on
- **Ollama** - Local LLM runtime
- **Rich** - Beautiful terminal formatting
- **Click** - CLI framework

---

## 📞 Support

For issues, questions, or contributions:
- Check `TEST_GUIDE.md` for testing scenarios
- Review `TASK_SUMMARY.md` for project details
- See troubleshooting section above

---

**Built with 🐺 by Wolf**

*Last Updated: 2025-11-10*
