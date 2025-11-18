# Wolf CLI v0.3.3 - Environment Configuration & Cursor API Integration

## Release Date

2025-11-18

## Summary

Version 0.3.3 introduces environment-based configuration management and Cursor editor API integration. This release adds `.env` file support for model configuration, integrates with Cursor's API for code-aware operations, and provides standalone installer/uninstaller executables for easy deployment.

---

## What's New

### ✨ Environment-Based Configuration (`.env` File)

**Problem Solved**: Model names were hardcoded in the codebase, making it difficult to change default models without modifying source code.

**Solution**: Implemented `.env` file support with proper configuration priority that ensures environment variables override saved config files.

#### Features:
- 📝 `.env` file support for model configuration
- 🔄 Environment variables override `config.json` automatically
- 🎯 Separate configuration for default model and vision model
- 📦 `.env.example` template included for easy setup
- 🔒 `.env` file excluded from git (sensitive config)

#### Configuration Variables:
```env
# Default model for regular chat operations
WOLF_OLLAMA_MODEL=granite3.1-moe:3b

# Vision model for vision operations (wolfv command)
WOLF_VISION_MODEL=qwen3-vl:8b

# Cursor API integration
WOLF_CURSOR_API_URL=http://localhost:5005
```

#### Configuration Priority (Highest to Lowest):
1. CLI flags (`--model`)
2. Environment variables from `.env` file
3. `config.json` file (only for values not in `.env`)
4. Defaults (hardcoded fallbacks)

---

### 🎯 Cursor Editor API Integration

**Problem Solved**: Users wanted to interact with their Cursor editor directly from Wolf CLI, enabling code-aware operations.

**Solution**: Full integration with Cursor API (port 5005) providing 7 new tools for editor interaction.

#### Features:
- 📁 Get current editor state (file, cursor position, open tabs)
- 📖 Read files through Cursor API
- ✏️ Write files through Cursor API
- 📋 List project files
- 🔍 Search in files with line numbers
- 🏃 Run code snippets
- 📝 Describe codebase structure

#### New Tools:
1. `cursor_get_editor_state` - Get current editor state
2. `cursor_get_file_content` - Read files via Cursor
3. `cursor_write_file` - Write files via Cursor
4. `cursor_list_files` - List project files
5. `cursor_search_files` - Search code with context
6. `cursor_run_code` - Execute code snippets
7. `cursor_describe_codebase` - Analyze project structure

#### Usage Examples:
```bash
# Get current file and editor state
wolf "what file am I currently editing in Cursor?"

# Read a file through Cursor
wolf "read the current file in Cursor"

# Search for TODO comments
wolf "search for 'TODO' in my Cursor project"

# List Python files
wolf "list all Python files in my project"

# Describe codebase
wolf "describe my codebase structure"
```

---

### 📦 Standalone Installer & Uninstaller

**Problem Solved**: Users needed an easy way to install and uninstall Wolf CLI without manual Python setup.

**Solution**: Created PyInstaller-based installer and uninstaller executables that handle the complete installation process.

#### Features:
- 🚀 `install.exe` - Standalone installer executable
- 🗑️ `uninstall.exe` - Complete uninstaller (preserves Ollama)
- 📦 Bundles all required files (requirements.txt, setup.py, wolf/, .env)
- 🔧 Automatic virtual environment creation
- 📝 Automatic package installation
- ✅ Verification of required files

#### Installer Capabilities:
- Extracts bundled files to installation directory
- Creates virtual environment (`.venv`)
- Installs all dependencies from `requirements.txt`
- Installs wolf-cli package via `setup.py`
- Sets up `wolf` command for use

#### Uninstaller Capabilities:
- Removes Python package from system
- Removes virtual environment
- Removes configuration files (`%APPDATA%\wolf-cli\`)
- Removes log files
- Optionally removes installation files
- **Preserves Ollama** - Does not touch Ollama installation or models

---

## Technical Changes

### Files Created

1. **`wolf/providers/cursor_client.py`**
   - `CursorAPI` class for Cursor editor integration
   - Methods: `get_editor_state()`, `get_file_content()`, `write_file()`, `list_files()`, `search_in_files()`, `run_code()`, `describe_codebase()`
   - Graceful handling when Cursor API is unavailable
   - Configurable base URL (default: `http://localhost:5005`)

2. **`install.py`**
   - Standalone installer script
   - Extracts bundled files from PyInstaller executable
   - Creates virtual environment
   - Installs dependencies and package
   - Cross-platform support (Windows/Linux/macOS)

3. **`install.spec`**
   - PyInstaller specification for `install.exe`
   - Bundles: `requirements.txt`, `setup.py`, `README.md`, `wolf/`, `cursor_api/`, `.env`

4. **`uninstall.py`**
   - Standalone uninstaller script
   - Removes package, venv, config files, logs
   - Preserves Ollama installation
   - Interactive prompts for file removal

5. **`uninstall.spec`**
   - PyInstaller specification for `uninstall.exe`

6. **`.env.example`**
   - Template file for environment configuration
   - Includes default model, vision model, and Cursor API URL
   - Safe to commit to git (no sensitive data)

7. **`docs/RELEASE_NOTES_v0.3.3.md`** - This file

### Files Modified

1. **`wolf/config_manager.py`**
   - Added `.env` file loading with `load_dotenv()`
   - Checks multiple locations for `.env` file:
     - Current working directory
     - Project root (if running from source)
     - User home directory (`~/.wolf-cli/.env`)
     - Config directory (`%APPDATA%\wolf-cli\.env`)
   - Added `cursor_api_url` to `DEFAULT_CONFIG`
   - Added `WOLF_CURSOR_API_URL` environment variable mapping
   - Updated `save()` method to exclude environment-set values from `config.json`
   - Ensures `.env` values always override `config.json`

2. **`wolf/tool_registry.py`**
   - Registered 7 new Cursor API tools
   - Added "Cursor Editor" category
   - All tools properly categorized and documented

3. **`wolf/tool_executor.py`**
   - Imported Cursor API functions
   - Bound all 7 Cursor tool handlers
   - Integrated with existing permission system

4. **`wolf/cli_wrapper.py`**
   - Updated `main_vision()` to use `config.get("vision_model")` instead of hardcoded value
   - Updated `main_camera()` to use `config.get("vision_model")` instead of hardcoded value
   - Removed hardcoded model references

5. **`.gitignore`**
   - Added `.env` to ignore list (but keep `.env.example`)
   - Changed `wolf.spec` to `*.spec` to ignore all spec files
   - Added `*.exe` to ignore list (but allow `test_install/*.exe`)
   - Added `test_install/build/`, `test_install/dist/`, `test_install/*.egg-info/` to ignore

---

## Tool Registry Updates

### New Tools

| Tool Name | Description | Risk Level | Category |
|-----------|-------------|------------|----------|
| `cursor_get_editor_state` | Get current editor state (file, cursor position, open tabs) | Safe | Cursor Editor |
| `cursor_get_file_content` | Read file content through Cursor API | Safe | Cursor Editor |
| `cursor_write_file` | Write file content through Cursor API | Modifying | Cursor Editor |
| `cursor_list_files` | List files in the project | Safe | Cursor Editor |
| `cursor_search_files` | Search for text in files with line numbers | Safe | Cursor Editor |
| `cursor_run_code` | Execute code snippets through Cursor | Modifying | Cursor Editor |
| `cursor_describe_codebase` | Analyze and describe codebase structure | Safe | Cursor Editor |

### Tool Count: 18 (was 11 in v0.3.2)

---

## Configuration Changes

### New Configuration Options

The following environment variables can now be set in `.env` file:

- `WOLF_OLLAMA_MODEL` - Default model for regular chat operations
- `WOLF_VISION_MODEL` - Vision model for vision operations (wolfv command)
- `WOLF_CURSOR_API_URL` - Cursor API base URL (default: `http://localhost:5005`)

### Configuration Priority (Highest to Lowest):

1. CLI flags (`--model`)
2. Environment variables from `.env` file
3. `config.json` file (only for values not in `.env`)
4. Defaults (hardcoded fallbacks)

**Important**: Values from `.env` file are **never saved** to `config.json`, ensuring `.env` always takes precedence on subsequent runs.

---

## Dependencies

**No new dependencies added**. Existing dependencies are sufficient:
- `python-dotenv>=1.0.0` (already in requirements.txt)
- `requests>=2.31.0` (already in requirements.txt)

---

## Breaking Changes

**None** - This is a purely additive release. All existing functionality remains unchanged:
- All existing `wolf` functionality preserved
- All existing `wolfv` functionality preserved
- All existing `wolfw` functionality preserved
- Existing `config.json` files continue to work
- `.env` file is optional (defaults still work)

---

## Testing & Validation

### ✅ Tested Features

- `.env` file loading from multiple locations verified
- Environment variable override of `config.json` confirmed
- Cursor API integration tested with all 7 tools
- Graceful degradation when Cursor API unavailable
- Tool registry shows 18 tools (11 existing + 7 new)
- Installer executable builds and runs successfully
- Uninstaller removes all components correctly
- Ollama preservation during uninstall verified
- Configuration priority system working as expected

### Confidence Level: 95%

---

## Known Issues

1. **Windows Only**: Currently tested and supported on Windows only
   - Linux/macOS support designed but requires validation
   - Cross-platform features implemented but not production-tested

2. **Cursor API Required**: Cursor tools require Cursor editor with API enabled
   - Tools gracefully handle unavailable API
   - Other Wolf CLI functionality continues to work

3. **.env File Location**: Must be in one of the checked locations
   - Current working directory
   - Project root (if running from source)
   - User home directory (`~/.wolf-cli/.env`)
   - Config directory (`%APPDATA%\wolf-cli\.env`)

4. **Python Required for Installer**: Installer requires system Python to create venv
   - Installer cannot create venv without Python installed
   - Future versions may bundle Python runtime

---

## Upgrade Instructions

### From Source (Development)

```powershell
# Navigate to wolf-cli directory
cd C:\Users\YourUsername\wolf\AI\WORKBENCH\wolf-cli

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Pull latest changes
git pull origin main

# Install/upgrade dependencies
pip install -r requirements.txt

# Reinstall in editable mode
pip install -e .

# Optional: Create .env file
copy .env.example .env
# Edit .env with your preferred models

# Test new features
wolf --list-tools  # Should show 18 tools
wolf "what file am I editing in Cursor?"
```

### Using Installer Executable

```powershell
# Download or build install.exe
# Build installer (requires PyInstaller)
python -m PyInstaller --clean --noconfirm .\install.spec

# Run installer
.\dist\install.exe

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Test installation
wolf --list-tools
```

### Building Executables (Optional)

```powershell
# Install PyInstaller if not already installed
pip install --upgrade pyinstaller

# Clean previous builds
Remove-Item -Path ".\build\*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path ".\dist\*" -Recurse -Force -ErrorAction SilentlyContinue

# Build installer
python -m PyInstaller --clean --noconfirm .\install.spec

# Build uninstaller
python -m PyInstaller --clean --noconfirm .\uninstall.spec

# Test the executables
.\dist\install.exe
.\dist\uninstall.exe
```

---

## What's Next?

### Planned for v0.4.0

- **Conversation History**: Persistent conversation context across sessions
- **Custom Tool Plugins**: User-defined tool registration system
- **HTTP Request Tool**: Make REST API calls from the CLI
- **Git Integration**: Git operations (status, commit, push, etc.)
- **Data Format Conversions**: JSON ↔ YAML ↔ CSV ↔ XML conversions
- **Email Integration**: Send emails via SMTP (email provider already created)

### Future Enhancements

- **OpenRouter Provider**: Support for cloud-hosted models
- **Batch/Script Mode**: Non-interactive execution for automation
- **Tool Usage Analytics**: Track and visualize tool usage patterns
- **Multi-platform Testing**: Validate Linux/macOS support
- **Additional Cursor API Features**: Git integration, terminal access via Cursor
- **Configuration UI**: Wizard for initial setup

---

## Contributors

- **Wolf** - Initial release, environment configuration, Cursor API integration, installer/uninstaller

---

## Support & Feedback

- **Issues**: Report bugs or request features on GitHub Issues
- **Documentation**: See `README.md`, `TEST_GUIDE.md`, and `docs/`
- **Testing**: Follow scenarios in `TEST_GUIDE.md`

---

**Built with 🐺 by Wolf**

*Release Date: 2025-11-18*

