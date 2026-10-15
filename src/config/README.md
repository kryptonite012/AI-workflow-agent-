# ⚙️ Config Package

**Centralized Configuration Management for AI-Agent-Workflow**

> Single source of truth for all application settings, environment variables, and runtime configurations.

---

## 📋 **Table of Contents**

1. [Why We Need This Package](#why-we-need-this-package)
2. [Architecture Overview](#architecture-overview)
3. [Configuration Categories](#configuration-categories)
4. [Quick Start Guide](#quick-start-guide)
5. [Environment Variables](#environment-variables)
6. [Runtime Configuration](#runtime-configuration)
7. [Troubleshooting](#troubleshooting)

---

## 🎯 **Why We Need This Package**

### **The Problem We Solved**

Without centralized configuration:
- ❌ Settings scattered across multiple files
- ❌ Hardcoded values difficult to change
- ❌ No environment-specific configs
- ❌ Magic numbers everywhere

### **What This Package Provides**

A **single configuration hub** that:
- ✅ **Environment Variables** - Load from `.env` file
- ✅ **Type Safety** - Proper typing for all settings
- ✅ **Defaults** - Sensible fallback values
- ✅ **Runtime Objects** - Shared global objects (console, socket, etc.)
- ✅ **Easy Access** - Import once, use everywhere

---

## 🏗️ **Architecture Overview**

```
┌──────────────────────────────────────────────────────────┐
│              CONFIG PACKAGE ARCHITECTURE                  │
│          (Centralized Configuration Hub)                  │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  📁 .env (Project Root)                                   │
│      ↓ Loaded by python-dotenv                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ settings.py                                         │ │
│  │  • Loads environment variables                      │ │
│  │  • Defines constants with defaults                  │ │
│  │  • Creates runtime placeholders                     │ │
│  └─────────────────────────────────────────────────────┘ │
│                       ↓                                   │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ Application Uses Config                             │ │
│  │                                                     │ │
│  │  from src.config import settings                    │ │
│  │  print(settings.DEFAULT_MODEL)                      │ │
│  │  settings.console.print("Hello")                    │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

---

## 📊 **Configuration Categories**

### **1. Base Paths**

```python
BASE_DIR = Path(__file__).resolve().parent.parent  # src directory
```

**Why:** Reference point for all file paths.

**Usage:**
```python
from src.config import settings
log_file = settings.BASE_DIR / "basic_logs" / "error_log.txt"
```

---

### **2. Server Configuration**

```python
SOCKET_HOST = "localhost"
SOCKET_PORT = 5390
```

**What:** Debug log server TCP settings.

**Environment Variables:**
- `SOCKET_HOST` - Host for socket server (default: `localhost`)
- `SOCKET_PORT` - Port for socket server (default: `5390`)

---

### **3. Model Configuration**

```python
# Ollama Models
DEFAULT_MODEL = "llava-llama3:latest"
CYPHER_MODEL = "deepseek-r1:8b"
CLASSIFIER_MODEL = "llama3.1:8b"

# API Models
GPT_MODEL = "openai/gpt-oss-120b"
KIMI_MODEL = "moonshotai/kimi-k2-instruct"
OPEN_AI_API_KEY = "your_openai_api_key_here"
```

**Purpose:**
- `DEFAULT_MODEL` - Main chat model (Ollama)
- `CYPHER_MODEL` - Neo4j Cypher query generation
- `CLASSIFIER_MODEL` - Message classification
- `GPT_MODEL` - OpenAI model (via NVIDIA API)
- `KIMI_MODEL` - Moonshot AI model

**Environment Variables:**
```bash
DEFAULT_MODEL=qwen2.5:32b-instruct
CLASSIFIER_MODEL=llama3.1:8b
OPENAI_API_KEY=your_actual_key
```

---

### **4. API Configuration**

```python
TRANSLATION_API_URL = "http://localhost:5560/translate"
OPENAI_TIMEOUT = 60  # seconds
OPENAI_CONNECT_TIMEOUT = 10  # seconds
```

**Purpose:** External API endpoints and timeouts.

---

### **5. RAG Configuration**

```python
DEFAULT_RAG_EXAMPLE_FILE_PATH = BASE_DIR / "RAG" / "RAG_FILES" / "kafka.pdf"
DEFAULT_RAG_FILES_HASH_TXT_PATH = BASE_DIR / "RAG" / "RAG_FILES" / "processed_hash_chunks.txt"
DEFAULT_RAG_FILES_PROCESSED_TRIPLES_PATH = BASE_DIR / "RAG" / "RAG_FILES" / "processed_triple.json"
```

**Purpose:** Paths for RAG (Retrieval Augmented Generation) files.

---

### **6. Neo4j Configuration**

```python
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "your_password_here"
neo4j_driver = None  # Runtime placeholder
```

**Environment Variables:**
```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_actual_password
```

**Runtime Initialization:**
```python
from src.config import settings
# Initialized in main_orchestrator.py
settings.neo4j_driver = GraphDatabase.driver(
    settings.NEO4J_URI,
    auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
)
```

---

### **7. Feature Flags**

```python
ENABLE_SOCKET_LOGGING = True
ENABLE_SOUND_NOTIFICATIONS = True
DEBUG = False
BROWSER_USE_ENABLED = True
MCP_ENABLED = True
```

**Environment Variables:**
```bash
ENABLE_SOCKET_LOGGING=true
ENABLE_SOUND_NOTIFICATIONS=false
DEBUG=true
```

**Purpose:** Toggle features on/off without code changes.

---

### **8. Logging Configuration**

```python
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DISPLAY_MODE = "separate_window"
```

**Log Display Modes:**
- `separate_window` - New console window (recommended)
- `background` - Hidden process
- `file` - Output to file
- `console` - Same console (messy)

**Environment Variable:**
```bash
LOG_DISPLAY_MODE=separate_window
```

---

### **9. Semaphore Limits**

```python
SEMAPHORE_CLI = 15  # Max concurrent CLI operations
SEMAPHORE_API = 5   # Max concurrent API calls
SEMAPHORE_OPENAI = 15  # Max concurrent OpenAI calls
```

**Purpose:** Control concurrency to prevent resource exhaustion.

---

### **10. Runtime Objects (Placeholders)**

```python
console = None  # Rich console (initialized in main_orchestrator.py)
debug_console = None  # Debug console (initialized in error_transfer.py)
socket_con = None  # Socket connection (initialized in main_orchestrator.py)
neo4j_driver = None  # Neo4j driver (initialized in main_orchestrator.py)

# Message classes (initialized in chat_initializer.py)
HumanMessage = None
AIMessage = None
BaseMessage = None

# Listeners (initialized at runtime)
listeners = {
    "eval": None,  # RichStatusListener
    "exit": None   # ExitListener
}
```

**Why Placeholders:**
- Avoid circular imports
- Lazy initialization
- Shared global access

**Initialization Example:**
```python
from rich.console import Console
from src.config import settings

# Initialize console
settings.console = Console()

# Now available everywhere
from src.config import settings
settings.console.print("Hello, World!")
```

---

### **11. MCP Configuration**

```python
MCP_CONFIG = {
    "MCP_ENABLED": True,
    "MCP_HOST": "localhost",
    "MCP_PORT": 5000,
    "MCP_API_KEY": "your_api_key_here",
    "MCP_TIMEOUT": 30,
    "MCP_CONFIG_PATH": BASE_DIR.parent / ".mcp.json"
}
```

**Environment Variables:**
```bash
MCP_ENABLED=true
MCP_HOST=localhost
MCP_PORT=5000
```

---

## 🚀 **Quick Start Guide**

### **Step 1: Create `.env` File**

Create `.env` in project root:

```bash
# Model Configuration
DEFAULT_MODEL=qwen2.5:32b-instruct
CLASSIFIER_MODEL=llama3.1:8b
OPENAI_API_KEY=your_api_key_here

# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password

# Feature Flags
ENABLE_SOCKET_LOGGING=true
DEBUG=false
```

### **Step 2: Import Settings**

```python
from src.config import settings

# Access configuration
print(settings.DEFAULT_MODEL)
print(settings.SOCKET_PORT)
```

### **Step 3: Use Runtime Objects**

```python
from src.config import settings

# After initialization in main_orchestrator.py
settings.console.print("[green]Hello, World!")
```

---

## 📚 **Environment Variables**

### **Complete List**

| Variable | Default | Description |
|----------|---------|-------------|
| `SOCKET_HOST` | `localhost` | Debug server host |
| `SOCKET_PORT` | `5390` | Debug server port |
| `DEFAULT_MODEL` | `llava-llama3:latest` | Main chat model |
| `CYPHER_MODEL` | `deepseek-r1:8b` | Neo4j query model |
| `CLASSIFIER_MODEL` | `llama3.1:8b` | Classification model |
| `GPT_MODEL` | `openai/gpt-oss-120b` | OpenAI model |
| `OPENAI_API_KEY` | `your_openai_api_key_here` | OpenAI API key |
| `NEO4J_URI` | `bolt://localhost:7687` | Neo4j connection URI |
| `NEO4J_USERNAME` | `neo4j` | Neo4j username |
| `NEO4J_PASSWORD` | `your_password_here` | Neo4j password |
| `ENABLE_SOCKET_LOGGING` | `true` | Enable socket logging |
| `ENABLE_SOUND_NOTIFICATIONS` | `true` | Enable sound beeps |
| `DEBUG` | `false` | Debug mode |
| `LOG_DISPLAY_MODE` | `separate_window` | Log display mode |
| `OPENAI_TIMEOUT` | `60` | OpenAI timeout (seconds) |
| `SEMAPHORE_LIMIT_CLI` | `15` | Max CLI concurrency |
| `SEMAPHORE_LIMIT_API` | `5` | Max API concurrency |
| `RECURSION_LIMIT` | `500` | Agent recursion limit |
| `BROWSER_USE_ENABLED` | `true` | Enable browser tool |
| `MCP_ENABLED` | `true` | Enable MCP servers |

---

## 🔧 **Runtime Configuration**

### **Console Initialization**

```python
from rich.console import Console
from src.config import settings

# In main_orchestrator.py
settings.console = Console(
    force_terminal=True,
    color_system="auto",
    width=120
)
```

### **Socket Connection**

```python
from src.utils.socket_manager import socket_manager
from src.config import settings

# Initialize socket connection
settings.socket_con = socket_manager.get_socket_connection()
```

### **Message Classes**

```python
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from src.config import settings

# In chat_initializer.py
settings.HumanMessage = HumanMessage
settings.AIMessage = AIMessage
settings.BaseMessage = BaseMessage
```

### **Listeners**

```python
from src.utils.listeners.rich_status_listen import RichStatusListener
from src.config import settings

# Initialize status listener
settings.listeners["eval"] = RichStatusListener(settings.console)
```

---

## 🐛 **Troubleshooting**

### **Problem: Environment Variables Not Loading**

**Cause:** `.env` file not found or wrong location

**Fix:**
```python
# Check if .env exists
from pathlib import Path
env_file = Path(".env")
print(f".env exists: {env_file.exists()}")

# Check load path
import dotenv
dotenv.load_dotenv(verbose=True)  # Shows loading details
```

---

### **Problem: Import Errors**

**Error:**
```
ImportError: cannot import name 'settings' from 'src.config'
```

**Fix:**
```python
# Correct import
from src.config import settings

# NOT this
from src.config.settings import settings  # Wrong!
```

---

### **Problem: Runtime Object is None**

**Error:**
```
AttributeError: 'NoneType' object has no attribute 'print'
```

**Cause:** Runtime object not initialized yet

**Fix:**
```python
from src.config import settings

# Check before use
if settings.console is None:
    print("Console not initialized yet!")
else:
    settings.console.print("Hello!")
```

---

## 📝 **Best Practices**

### **1. Use Type Hints**

```python
from src.config import settings
from rich.console import Console

def my_function(console: Console = None):
    console = console or settings.console
    console.print("Hello!")
```

### **2. Centralize Defaults**

```python
# ❌ Bad - Magic number
timeout = 60

# ✅ Good - Use setting
from src.config import settings
timeout = settings.OPENAI_TIMEOUT
```

### **3. Check Runtime Objects**

```python
from src.config import settings

# Safe access
if settings.socket_con:
    settings.socket_con.send_error("Message")
```

---

## 🆘 **Support**

**Questions?** Check:
1. This README
2. `.env.example` file
3. Code comments in `settings.py`

**Found a bug?** Create an issue with:
- Configuration causing issue
- Expected behavior
- Actual behavior

---

**Status:** ✅ **Production-Ready**

**Maintainer:** AI-Agent-Workflow Team

**Last Updated:** December 24, 2025

