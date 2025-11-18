# 🐺 Wolf CLI - Task Summary & Implementation Roadmap

## Project Overview

**Wolf CLI** is a production-ready, comprehensive command-line AI assistant that combines LLM capabilities with tool-calling, vision support, and a robust safety system. This is a fork of [shell_gpt](https://github.com/TheR1D/shell_gpt) by TheR1D, extended with comprehensive tool-calling capabilities, enhanced safety controls, and Windows PowerShell integration.

---

## Core Requirements

### 1. **Architecture**
- **Base Integration**: Standalone CLI tool (not a wrapper - independent implementation)
- **Primary LLM**: Ollama with `granite3.1-moe:3b` (local, 3B parameter model with excellent tool support)
- **Alternative LLM**: OpenRouter API (planned for Phase 2) #future-use
- **Platform**: Windows 11 (PowerShell 7.5.4) - ✅ Fully tested
- **Project Location**: `C:\Users\Administrator\wolf\AI\WORKBENCH\wolf-cli`

### 2. **Comprehensive Tool Suite**

#### **File & Directory Operations** ✅ MVP Complete
- ✅ Create, read, write files
- ✅ Delete files (with recycle bin support)
- ✅ Move, rename, copy files
- ✅ List directories (recursive option)
- ✅ Get file info (size, dates, metadata)
- ⏳ Compress/extract archives (Phase 2)
- ⏳ Search files by pattern (Phase 2)

#### **Shell & System Integration** ✅ MVP Complete
- ✅ Execute PowerShell commands (with safety filters)
- ✅ Get system information (CPU, memory, disk)
- ✅ PowerShell-specific denylist/allowlist filtering
- ⏳ List processes (Phase 2)
- ⏳ Get command help (Phase 2)

#### **Web & Network Tools** ✅ Web Search Complete
- ✅ Web search (DuckDuckGo) - via `wolfw` command
- ⏳ HTTP requests (GET/POST) - Phase 2
- ⏳ Download files - Phase 2
- ⏳ Network diagnostics (ping, traceroute) - Phase 2
- ⏳ Get IP information - Phase 2
- ⏳ API calls (weather, cryptocurrency prices, etc.) - Phase 2

#### **Data Processing**
- Parse/convert JSON, CSV, YAML, XML
- Math calculations (safe eval)
- Unit conversions
- Date/time operations (timezone conversion, formatting)

#### **Vision & Image Processing** ✅ MVP Complete (Basic)
- ✅ Analyze images (via Ollama vision API)
- ✅ Image input support via --image flag
- ⏳ Extract text from images (OCR - Phase 2)
- ⏳ Get image metadata (EXIF, dimensions - Phase 2)

#### **Code Intelligence**
- Explain code snippets
- Refactor code
- Debug code
- Generate code from descriptions

#### **Version Control**
- Git status, diff, log (safe/read-only)
- Git commit, push (requires confirmation)
- Branch operations

#### **Context & Automation**
- Memory/note storage (persistent JSON)
- Clipboard read/write
- Script generation (.ps1)
- Task scheduling (schtasks wrapper)
- Batch command execution

---

## 3. **Safety & Permission System**

### Three-Tier Trust Levels

| Trust Level | Behavior | Use Case |
|------------|----------|----------|
| **safe-only** | Only executes read-only tools; blocks modifying/destructive | Paranoid mode, untrusted environments |
| **interactive** (default) | Confirms before modifying/destructive actions | Daily terminal use, balanced safety |
| **auto** | Executes automatically with full logging | Automation scripts, trusted scenarios |

### Risk-Based Confirmation

| Risk Level | Tools | Confirmation Required |
|-----------|-------|---------------------|
| **Safe** | read_file, list_directory, web_search, get_system_info | None (auto-execute) |
| **Modifying** | create_file, write_file, execute_command, move_file | `[Y/n]` prompt |
| **Destructive** | delete_file, git_push, format operations | Explicit `YES` required |

### Command Filtering (PowerShell-Specific)

**Default Denylist** (always requires explicit YES):
- `Remove-Item -Recurse`
- `del /s`, `rd /s`
- `Format-Volume`, `diskpart`, `bcdedit`
- `Invoke-Expression`, `iex`
- Piped web downloads: `curl | iex`
- Registry deletions: `reg delete`

**Default Allowlist** (auto-execute if safe):
- `Get-Process`, `Get-Service`, `Get-Help`
- `Get-ChildItem`, `dir`, `ls`
- `Get-Content`, `cat`, `type`
- `Select-String`, `findstr`

---

## 4. **User Experience & Transparency**

### Execution Flow
```
User: wolf "create a file named dog.txt"

Assistant (LLM): I can create C:\path\dog.txt. Proceed? (Y/n)
User: y
[Tool: create_file] Creating C:\path\dog.txt...
[Tool: create_file] Done. bytes_written=0
```

### Logging & Output
- **Console**: Structured, color-coded output with Rich library
  - `[Info]` - General information
  - `[Tool: name]` - Tool execution progress
  - `[Warn]` - Warnings
  - `[Error]` - Errors
  - `[Success]` - Successful completion

- **File**: Rotating log file (`wolf-cli.log`, 10MB max, 3 backups)
  - Timestamp, level, component, message
  - Full exception traces for debugging

### CLI Flags
```bash
wolf "<prompt>"                  # Standard interactive mode
wolf --safe "<prompt>"           # Safe-only mode (no modifications)
wolf --auto "<prompt>"           # Auto mode (no confirmations)
wolf --image path.png "<prompt>" # Include image for vision
wolfv "<prompt>"                 # Vision mode (auto screenshot)
wolfw "<search query>"           # Web search mode (DuckDuckGo)
wolf --provider openrouter       # Use OpenRouter instead of Ollama
wolf --model <model_name>        # Override default model
wolf --verbose                   # Increase logging verbosity
wolf --list-tools                # Show all available tools
```

---

## 5. **Technical Implementation**

### Project Structure
```
wolf-cli/
├── wolf/
│   ├── __init__.py
│   ├── cli_wrapper.py           # Main CLI entry point (Click/Typer)
│   ├── config_manager.py        # Configuration loader
│   ├── permission_manager.py    # Safety & confirmation system
│   ├── tool_registry.py         # Central tool schema registry
│   ├── tool_executor.py         # Tool execution engine
│   ├── orchestrator.py          # LLM tool-call loop
│   ├── utils/
│   │   ├── logging_utils.py     # Console & file logging
│   │   ├── validation.py        # Parameter validation
│   │   └── paths.py             # Safe path handling
│   ├── llm/
│   │   ├── ollama.py            # Ollama adapter (tools + vision)
│   │   └── openrouter_adapter.py # OpenRouter API client #future-use
│   ├── providers/
│   │   ├── file_ops.py          # File operation handlers
│   │   ├── ps_client.py         # PowerShell executor
│   │   ├── web_search.py        # Web & HTTP tools
│   │   ├── vision.py            # Vision tool wrappers
│   │   └── git_client.py        # Git operations
│   └── memory/
│       └── store.py             # Persistent context storage
├── tests/
├── requirements.txt
├── setup.py
├── .wolf-cli-config.json        # User configuration (auto-generated)
└── README.md
```

### Configuration System
**Location**:
- **Windows**: `%APPDATA%\wolf-cli\config.json`

**Load Order**: `Defaults → .env File → config.json → Environment Variables → CLI Flags`

**Priority**: Environment variables from `.env` file override `config.json` values. This ensures `.env` file always takes precedence.

**Default Config**:
```json
{
  "model_provider": "ollama",
  "ollama_model": "granite3.1-moe:3b",
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
  "system_prompt": "<intelligent prompt that prevents unnecessary tool calls>"
}
```

### Environment Variables
- `WOLF_MODEL_PROVIDER` - Override model provider
- `WOLF_OLLAMA_MODEL` - Override Ollama model (default: `granite3.1-moe:3b`)
- `WOLF_VISION_MODEL` - Override vision model (default: `qwen3-vl:8b`)
- `WOLF_OLLAMA_BASE_URL` - Ollama API endpoint
- `WOLF_CURSOR_API_URL` - Cursor API endpoint (default: `http://localhost:5005`)
- `WOLF_OPENROUTER_API_KEY` - OpenRouter API key #future-use
- `WOLF_TRUST_LEVEL` - Default trust level
- `WOLF_TIMEOUT` - Command timeout in seconds

**Note**: Environment variables can be set via `.env` file (recommended) or system environment variables. `.env` file values always override `config.json`.

---

## 6. **LLM Integration**

### Ollama Adapter
**Endpoint**: `POST http://localhost:11434/api/chat`

**Payload Structure**:
```json
{
  "model": "granite3.1-moe:3b",
  "messages": [
    {"role": "system", "content": "<system_prompt from config>"},
    {"role": "user", "content": "create dog.txt", "images": ["<base64>"]}
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "create_file",
        "description": "Create a new file...",
        "parameters": {"type": "object", "properties": {...}}
      }
    }
  ],
  "stream": false
}
```

**Response Handling**:
- `message.tool_calls` → Execute tools, append results, continue loop
- `message.content` → Display to user, end loop

### OpenRouter Adapter #future-use
**Endpoint**: `POST https://openrouter.ai/api/v1/chat/completions` #future-use

**Headers**: #future-use
- `Authorization: Bearer <api_key>` #future-use
- `HTTP-Referer: https://github.com/wolf/wolf-cli` #future-use
- `X-Title: Wolf CLI` #future-use

**Payload**: OpenAI-compatible format #future-use
- Tools: Same schema as Ollama #future-use
- Images: Via `content` array with `image_url` type #future-use

### Orchestrator Loop (Pseudo-code)
```python
messages = [system_msg, user_msg_with_images]
tools = registry.export_openai_tools()

for i in range(max_tool_iterations):
    response = provider.chat(messages, tools)
    
    if response.type == "content":
        print(response.text)
        break
    
    if response.type == "tool_calls":
        for call in response.calls:
            # Parse arguments (handle stringified JSON)
            args = safe_json_parse(call.arguments)
            
            # Execute with permission check
            result = executor.execute(call.name, args)
            
            # Append tool result to conversation
            messages.append({
                "role": "tool",
                "name": call.name,
                "content": json.dumps(result)
            })
```

---

## 7. **MVP Scope (Phase 1)**

### Included in MVP
✅ **Core Infrastructure**
- Configuration management
- Permission & safety system
- Tool registry & executor
- Logging utilities

✅ **File Operations** (8 tools)
- create_file, read_file, write_file, delete_file
- list_directory, get_file_info, move_file, copy_file

✅ **Shell & System** (2 tools)
- execute_command (PowerShell)
- get_system_info

✅ **LLM Integration**
- Ollama adapter (tools + vision)
- Tool-call orchestration loop with multi-turn support
- Configurable system prompt for intelligent tool usage
- ⏳ OpenRouter adapter (Phase 2) #future-use

✅ **CLI Wrapper**
- Main entry point with Click framework
- Comprehensive flag parsing (--safe, --auto, --image, --verbose, --list-tools)
- Rich console output with color-coding

✅ **Web & Network** (1 tool)
- search_web (DuckDuckGo) - via `wolfw` command

✅ **Cursor Editor API** (7 tools) - v0.3.3
- cursor_get_editor_state - Get current editor state
- cursor_get_file_content - Read files via Cursor
- cursor_write_file - Write files via Cursor
- cursor_list_files - List project files
- cursor_search_files - Search code with context
- cursor_run_code - Execute code snippets
- cursor_describe_codebase - Analyze project structure

### Deferred to Phase 2+
⏳ Additional Web & Network tools (HTTP requests, downloads, diagnostics)
⏳ Data processing tools
⏳ Git operations
⏳ Advanced vision tools
⏳ Code intelligence
⏳ Memory/context storage
⏳ Clipboard operations
⏳ Task automation

---

## 8. **Dependencies**

```txt
# Core CLI
click>=8.1.7
rich>=13.7.0
prompt-toolkit>=3.0.43

# HTTP & APIs
requests>=2.31.0
httpx>=0.27.0
aiohttp>=3.9.3

# Data & Validation
pyyaml>=6.0.1
jsonschema>=4.21.1
python-dateutil>=2.8.2

# Utilities
psutil>=5.9.8          # System info
send2trash>=1.8.2      # Safe file deletion
pillow>=10.2.0         # Image handling
ddgs>=3.1.0            # DuckDuckGo search (wolfw command)

# Optional (Phase 2+)
pyperclip>=1.8.2
tqdm>=4.66.2
xmltodict>=0.13.0
```

---

## 9. **Installation & Setup**

### Prerequisites
1. **Python 3.11+**
2. **PowerShell 7+** (`pwsh`)
3. **Ollama** (installed and running)
   ```bash
   ollama serve  # Start Ollama server
   ollama pull granite3.1-moe:3b  # Recommended model
   ```

### Installation Steps
```bash
# 1. Navigate to project
cd C:\Users\Administrator\wolf\AI\WORKBENCH\wolf-cli

# 2. Create virtual environment
python -m venv venv

# 3. Activate venv
.\venv\Scripts\Activate.ps1

# 4. Install dependencies
pip install -r requirements.txt

# 5. Install Wolf CLI in development mode
pip install -e .

# 6. Initialize configuration
wolf --help  # Auto-creates .wolf-cli-config.json

# 7. Test basic functionality
wolf --list-tools
wolf "what's in my current directory?"
```

---

## 10. **Testing Strategy**

### Unit Tests
- Permission manager confirmation logic
- Tool parameter validation
- Path normalization & safety checks
- Command allowlist/denylist matching

### Integration Tests
- File operations (create, read, write, delete)
- PowerShell execution with timeout
- Ollama API communication
- Tool-call orchestration loop

### Live Tests (Manual)
1. **Single Tool Call**
   ```bash
   wolf "create a file named test.txt with content 'hello'"
   ```

2. **Multi-Tool Chain**
   ```bash
   wolf "list all .txt files, then create a summary"
   ```

3. **Vision Test**
   ```bash
   wolf --image screenshot.png "what's in this image?"
   ```

4. **Web Search Test** (wolfw command)
   ```bash
   wolfw "artificial intelligence trends 2025"
   wolfw "best Python web frameworks"
   wolfw "machine learning for beginners"
   ```

5. **Safety Test**
   ```bash
   wolf "delete everything in this folder"  # Should require YES
   ```

6. **OpenRouter Test** #future-use
   ```bash
   wolf --provider openrouter "explain this code: ..."
   ```

---

## 11. **Success Criteria**

✅ **Functional Requirements**
1. Can execute file operations with confirmation
2. PowerShell commands run with safety checks
3. Ollama model calls tools correctly
4. Vision input works (image analysis)
5. Multi-step tool chains complete successfully
6. Permission system blocks/confirms appropriately

✅ **Safety Requirements**
1. Destructive commands require explicit YES
2. Denylist patterns correctly block dangerous commands
3. --safe mode blocks all modifying operations
4. --auto mode logs all actions

✅ **UX Requirements**
1. Clear, color-coded console output
2. Transparent progress logging
3. Helpful error messages
4. Configuration persists between sessions

---

## 12. **Current Progress**

### ✅ Completed (v0.3.1 - Windows Only)
- [x] Project structure created
- [x] Configuration manager with .env support
- [x] Permission manager (3-tier trust, allowlist/denylist)
- [x] Logging utilities (Rich + file logging)
- [x] Path utilities (safe resolution)
- [x] Tool registry (10 core tools)
- [x] File operations (8 handlers)
- [x] PowerShell client with safety filtering
- [x] Tool executor (validation + execution)
- [x] Ollama adapter (tool + vision support)
- [x] Orchestrator (multi-turn tool-call loop)
- [x] **Intelligent System Prompt** (prevents unnecessary tool calls)
- [x] CLI wrapper (main entry point)
- [x] setup.py for pip installation
- [x] README documentation
- [x] CHANGELOG with version history
- [x] Comprehensive testing and validation
- [x] Switched to `granite3.1-moe:3b` for excellent tool support
- [x] Simple 'wolf' command installation
- [x] Web search tool (DuckDuckGo) with `wolfw` command
- [x] Vision mode with `wolfv` command
- [x] Environment-based configuration (`.env` file support)
- [x] Cursor Editor API integration (7 new tools)
- [x] Standalone installer/uninstaller executables

### 📋 Installation
```bash
# Simple 3-step installation
git clone https://github.com/yourusername/wolf-cli.git
cd wolf-cli
pip install -e .

# Start using immediately
wolf --list-tools
wolf "your prompt here"
```

### 🎯 Next Phase: Extended Tools
1. Implement OpenRouter provider #future-use
2. Add web search (DuckDuckGo)
3. Add HTTP request tool
4. Add data format conversions
5. Add Git integration
6. Add clipboard operations
7. Implement conversation history

---

## 13. **Future Enhancements (Post-MVP)**

### Phase 2: Extended Tools
- Web search (DuckDuckGo API)
- HTTP request tool
- Data format conversions
- Git integration
- Clipboard operations

### Phase 3: Advanced Features
- Conversation history/context
- Tool usage analytics
- Custom tool plugins
- Batch/script mode
- Web UI dashboard

### Phase 4: Enterprise Features
- Multi-user support
- Audit logging
- Role-based permissions
- Integration with CI/CD
- Cloud deployment options

---

## 14. **Troubleshooting Guide**

### Common Issues

**1. "Ollama API error: Connection refused"**
- Start Ollama: `ollama serve`
- Check endpoint: `http://localhost:11434`
- Verify model: `ollama list`

**2. "Model doesn't support tools" or "400 Bad Request"**
- Not all Ollama models support function calling
- **Recommended models**:
  - `granite3.1-moe:3b` (default, excellent tool support)
  - `gpt-oss:20b` (larger, Context Length: 131072, best instruction-following)
  - `llama3.2:latest` (smaller, faster, less reliable)
  - `qwen3:8b` (good tool support)
- **Avoid**: llava, codellama (vision/code-focused, poor tool support)
- Pull recommended model: `ollama pull granite3.1-moe:3b`

**3. "Permission denied errors"**
- Check trust level: `--auto` or `--safe`
- Review allowlist/denylist in config
- Use `--verbose` to see permission checks

**4. "Image not loading"**
- Verify image path is correct
- Check file format (PNG, JPG supported)
- Ensure file size is reasonable (<10MB)

---

## 15. **Contact & Support**

- **Project**: Wolf CLI
- **Author**: Wolf
- **Version**: 0.3.1 (Windows Only)
- **License**: TBD
- **Repository**: TBD


---

*Last Updated: 2025-11-18*
