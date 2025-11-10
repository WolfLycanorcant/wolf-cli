# 🐺 Wolf CLI - Testing Guide

## ✅ Setup Complete!

Your Wolf CLI is ready! Here's how to install and test it:

## 🚀 Quick Installation

### Windows (PowerShell)
```powershell
git clone https://github.com/yourusername/wolf-cli.git
cd wolf-cli
pip install -e .
wolf --list-tools
```


## 📋 Prerequisites

Make sure Ollama is running:

```bash
# Start Ollama (if not already running)
ollama serve

# In another terminal, pull the recommended models
ollama pull gpt-oss:20b  # Recommended (Context Length: 131072, best reliability)
ollama pull qwen3-vl:8b  # Recommended
```

## 🧪 Test Scenarios

### 1. Basic Tool Listing (✅ Working!)
```powershell
wolf --list-tools
```
**Expected**: Rich table showing 10 tools (file ops, system info, execute command)

---

### 2. Simple Read-Only Query (Safe Mode)
```powershell
wolf --safe "what files are in the current directory?"
```
**Expected**: 
- LLM calls `list_directory` tool
- Shows directory listing
- No confirmation needed (safe operation)

---

### 3. File Creation (Interactive Mode - Default)
```powershell
wolf "create a file named hello.txt with the content 'Hello Wolf!'"
```
**Expected**:
- LLM requests `create_file` tool
- Prompts you: "Proceed? (Y/n)"
- Press `y` or Enter
- File created successfully

---

### 4. System Information
```powershell
wolf "show me system information"
```
**Expected**:
- Calls `get_system_info` tool
- Displays CPU, memory, disk info
- No confirmation (safe operation)

---

### 5. Multiple Tool Calls (Chain)
```powershell
wolf "create a file named test.txt with 'hello', then read it back to me"
```
**Expected**:
- First calls `create_file` (requires confirmation)
- Then calls `read_file` (no confirmation)
- Shows the content

---

### 6. Auto Mode (No Confirmations)
```powershell
wolf --auto "create a file named auto-test.txt with 'testing auto mode'"
```
**Expected**:
- Executes `create_file` automatically
- No confirmation prompt
- File created

---

### 7. Destructive Operation (Requires YES)
```powershell
wolf "delete the file test.txt"
```
**Expected**:
- Prompts: "Type YES to confirm"
- Requires typing "YES" (not just y)
- Moves file to recycle bin

---

### 8. PowerShell Command Execution
```powershell
wolf "run the command 'Get-Process' and show me the top 5 processes"
```
**Expected**:
- Calls `execute_command` with PowerShell
- May require confirmation (modifying risk level)
- Shows process list

---

### 9. Verbose Logging
```powershell
wolf -v "list files in current directory"
```
**Expected**:
- Shows detailed logging
- Tool execution progress
- LLM iteration info

---

### 10. Vision Test (If you have an image)
```powershell
# Replace with actual image path
wolf --image "C:\path\to\image.png" "describe what you see in this image"
```
**Expected**:
- Encodes image to base64
- Sends to Ollama with vision model
- Returns description

---

### 11. Web Search Test (wolfw)
```powershell
# Search for current technology information
wolfw "artificial intelligence trends 2025"

# Compare technologies
wolfw "best Python web frameworks comparison"

# Find tutorials and guides
wolfw "machine learning for beginners"
```
**Expected**:
- Shows "🔍 Searching the web..." message
- Calls `search_web` tool with DuckDuckGo
- Returns up to 10 search results
- LLM synthesizes results into organized summary
- Includes source URLs and key takeaways
- No confirmation needed (safe operation)

---

## 🔍 Troubleshooting

### Error: "Ollama API error: Connection refused"
```powershell
# Start Ollama server
ollama serve
```

### Error: "Model doesn't support tools" or "400 Bad Request"
```powershell
# Pull a recommended model that supports function calling
ollama pull gpt-oss:20b  # Best option (Context Length: 131072)

# Then update your config to use it:
# Edit: C:\Users\Administrator\wolf\AI\WORKBENCH\.wolf-cli-config.json
# Set "ollama_model": "gpt-oss:20b"
```

### Permission denied in safe mode
- This is expected! Safe mode blocks modifying operations
- Try with `--auto` or without `--safe`

### Max iterations reached
- The task is too complex or requires too many steps
- Simplify the prompt or increase iterations in config

---

## 📋 What to Check

✅ **Tool Registry Integration**
- All 11 tools listed (including search_web)
- Correct risk levels (safe/modifying/destructive)

✅ **Permission System**
- Safe mode blocks modifying operations
- Interactive mode prompts for confirmation
- Auto mode executes without prompts
- Destructive operations require "YES"

✅ **Tool Execution**
- File operations work (create, read, write, delete)
- PowerShell commands execute
- System info returns correctly

✅ **Orchestrator Loop**
- LLM makes tool calls
- Tool results fed back to LLM
- Final response generated
- Max iterations enforced (configurable via --max-iterations)

✅ **Error Handling**
- Invalid tool names handled gracefully
- Bad parameters caught by validation
- Permission denials reported clearly

---

## 🎯 Success Criteria

If you can complete tests 1-11 successfully, your Wolf CLI is **fully functional**!

- ✅ Tools are registered and callable (11 tools total)
- ✅ Permission system works
- ✅ LLM orchestration loop works
- ✅ File operations execute
- ✅ User confirmations work
- ✅ Web search with wolfw works (DuckDuckGo)
- ✅ Vision mode with wolfv works (screenshot capture)

---

## 📏 Notes

1. **Config file**:
   - Windows: `%APPDATA%\wolf-cli\config.json`
2. **Log file**: `wolf-cli.log` (in current directory)
3. **Model**: Defaults to `gpt-oss:20b` (v0.2.0+)
4. **Ollama URL**: `http://localhost:11434` (configurable)
5. **System Prompt**: Intelligent prompt prevents unnecessary tool calls for greetings

---



---

## 🚀 Next Steps (Phase 2)

After MVP testing passes:
1. Implement OpenRouter provider #future-use
2. ✅ Add web search (DuckDuckGo) - COMPLETED in v0.3.1 via `wolfw`
3. Add HTTP request tool
4. Add Git integration
5. Add conversation history
6. Custom tool plugins

---

*Last Updated: 2025-11-10*
