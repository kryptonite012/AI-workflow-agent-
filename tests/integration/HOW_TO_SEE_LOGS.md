# 📊 How to See Logs in LangGraph Chatbot

Your LangGraph Chatbot now has automatic log management with multiple viewing options. Here's how to see your logs:

## 🚀 Quick Start - See Logs Immediately

### Option 1: Separate Console Window (Recommended)
```bash
# Just run your application - a separate console window will open automatically
python lggraph.py
```

**What happens:**
- ✅ Your main application runs in current terminal
- ✅ A **separate console window opens** showing all logs
- ✅ All error messages, debug info, and operations appear in the log window
- ✅ Clean separation between app interface and logs

### Option 2: Configure Different Log Display
```bash
# Run the configuration helper
python src/config/configure_logging.py
```

## 📋 Available Log Display Modes

| Mode | Description | Best For | Visibility |
|------|-------------|----------|------------|
| `separate_window` | Opens log server in separate console window | Development, debugging | ✅ Fully visible |
| `background` | Runs log server silently in background | Production, clean interface | ❌ Not visible |
| `file` | Logs to `socket_server.log` file | Production, log analysis | 📄 File-based |
| `console` | Shows logs in same console (mixed output) | Quick testing | ⚠️ Mixed with app output |

## 🔧 How to Change Log Display Mode

### Method 1: Edit config.py
```python
# In config.py, change this line:
LOG_DISPLAY_MODE = "separate_window"  # or "background", "file", "console"
```

### Method 2: Environment Variable
```bash
# Windows
set LOG_DISPLAY_MODE=separate_window
python lggraph.py

# Linux/Mac
export LOG_DISPLAY_MODE=separate_window
python lggraph.py
```

### Method 3: Use Configuration Helper
```bash
python configure_logging.py
```

## 👀 What You'll See in the Logs

When your LangGraph application runs, the log window will show:

```
Server is listening...
Connection from ('127.0.0.1', 54321)
[LGGRAPH] Loading Configuration: Configuration loaded successfully
[LGGRAPH] Initializing LLM: ChatOllama model initialized
[LGGRAPH] Building Graph: LangGraph workflow constructed
[LGGRAPH] User Input: User message received: 'Hello'
[LGGRAPH] Message Classification: Message classified as: llm
[LGGRAPH] LLM Response: Response generated successfully
[ERROR] Connection error: Could not connect to Ollama server
[WORKFLOW] Tool Selection: Selected tool: GoogleSearch
[RAG] Knowledge Graph Search: Cypher query generated
```

## 🧪 Testing Your Log Setup

### Test 1: Quick Test
```bash
python test_lggraph_integration.py
```
This will show you if logs are working and where they appear.

### Test 2: Interactive Demo
```bash
python log_viewer_demo.py
```
This lets you try different log modes and send test messages.

### Test 3: Configuration Test
```bash
python configure_logging.py
# Choose option 4: "Test current configuration"
```

## 🔍 Troubleshooting Log Visibility

### Problem: "I don't see any logs"

**Solution 1: Check if separate window opened**
- Look for a new console window titled "LangGraph Log Server"
- It might be behind other windows or minimized

**Solution 2: Check configuration**
```bash
python configure_logging.py
# Choose option 1: "Show current configuration"
```

**Solution 3: Force separate window mode**
```python
# In config.py, set:
LOG_DISPLAY_MODE = "separate_window"
ENABLE_SOCKET_LOGGING = True
```

### Problem: "Separate window closes immediately"

**Solution: Check for errors**
```bash
# Run error transfer manually to see what's wrong
python utils/error_transfer.py
```

### Problem: "Logs are mixed with my application"

**Solution: Use separate window mode**
```python
# In config.py:
LOG_DISPLAY_MODE = "separate_window"  # Not "console"
```

## 📄 File-Based Logging

If you prefer logs in a file:

```python
# In config.py:
LOG_DISPLAY_MODE = "file"
```

**Log file location:** `utils/socket_server.log`

**View logs:**
```bash
# Windows
type utils\socket_server.log

# Linux/Mac
cat utils/socket_server.log

# Or use any text editor
notepad utils\socket_server.log
```

## 🎯 Recommended Settings

### For Development
```python
LOG_DISPLAY_MODE = "separate_window"
ENABLE_SOCKET_LOGGING = True
```
**Why:** You can see all logs in real-time without cluttering your main interface.

### For Production
```python
LOG_DISPLAY_MODE = "file"
ENABLE_SOCKET_LOGGING = True
```
**Why:** Logs are saved for analysis but don't create extra windows.

### For Performance-Critical
```python
LOG_DISPLAY_MODE = "background"
ENABLE_SOCKET_LOGGING = True
```
**Why:** Minimal overhead, clean interface.

### For Debugging
```python
LOG_DISPLAY_MODE = "separate_window"
ENABLE_SOCKET_LOGGING = True
DEBUG = True
```
**Why:** Maximum visibility of what's happening.

## 🚀 Advanced Usage

### Custom Log Messages
```python
from utils.socket_manager import socket_manager

# In your code:
socket_con = socket_manager.get_socket_connection()
if socket_con:
    socket_con.send_error("Your custom log message")
```

### Multiple Log Levels
```python
# You can prefix messages for organization:
socket_con.send_error("[INFO] Application started")
socket_con.send_error("[WARNING] Large file detected")
socket_con.send_error("[ERROR] Connection failed")
socket_con.send_error("[DEBUG] Variable value: " + str(value))
```

### Log Server Management
```python
from utils.socket_manager import socket_manager

# Check if log server is running
if socket_manager.is_log_server_running():
    print("Log server is active")

# Manually restart log server
socket_manager.stop_log_server()
socket_manager.start_log_server()
```

## 📞 Still Having Issues?

1. **Run the diagnostic:**
   ```bash
   python configure_logging.py
   # Choose option 4: "Test current configuration"
   ```

2. **Check the test suite:**
   ```bash
   python tests/error_handling/test_subprocess_logging.py
   ```

3. **Manual verification:**
   ```bash
   # Terminal 1: Start log server manually
   python utils/error_transfer.py
   
   # Terminal 2: Run your app
   python lggraph.py
   ```

## 🎉 Summary

Your LangGraph Chatbot now automatically:
- ✅ **Starts its own log server** when needed
- ✅ **Opens a separate window** to show logs (by default)
- ✅ **Handles all logging** without manual setup
- ✅ **Cleans up** when application exits

**Just run `python lggraph.py` and look for the separate console window with your logs!**