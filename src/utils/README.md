# 🔧 Utils Package

**Utility Functions and Helper Classes for AI-Agent-Workflow**

> A collection of essential utility modules providing core functionality like socket-based logging, model management, API integration, and event listeners.

---

## 📋 **Table of Contents**

1. [Why We Need This Package](#why-we-need-this-package)
2. [Architecture Overview](#architecture-overview)
3. [Components Explained](#components-explained)
4. [Quick Start Guide](#quick-start-guide)
5. [Module Details](#module-details)
6. [Troubleshooting](#troubleshooting)
7. [API Reference](#api-reference)

---

## 🎯 **Why We Need This Package**

### **The Problem We Solved**

Every application needs utility functions, but they're often scattered:
- ❌ Logging code duplicated everywhere
- ❌ Model management tightly coupled to nodes
- ❌ API calls repeated with different error handling
- ❌ Socket connections managed inconsistently

### **What This Package Provides**

A **centralized utility library** that handles cross-cutting concerns:
- ✅ **Socket Manager** - TCP socket communication for debug logging
- ✅ **Model Manager** - Unified interface for Ollama & OpenAI models
- ✅ **OpenAI Integration** - API wrapper with rate limiting & error handling
- ✅ **Error Transfer** - Debug message server (subprocess)
- ✅ **Listeners** - Event-based communication (event listener, exit listener, status listener)

---

## 🏗️ **Architecture Overview**

```
┌──────────────────────────────────────────────────────────────┐
│                     UTILS PACKAGE OVERVIEW                    │
│                (Cross-Cutting Utility Modules)                │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ 1. Socket Manager (socket_manager.py)                   │ │
│  │    • Starts debug log server subprocess                 │ │
│  │    • Manages TCP socket connection                      │ │
│  │    • Provides send_error() legacy API                   │ │
│  │    • Bridges to DebugMessageSender protocol             │ │
│  └─────────────────────────────────────────────────────────┘ │
│                       ↓                                       │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ 2. Error Transfer (error_transfer.py)                   │ │
│  │    • TCP server listening on localhost:5390             │ │
│  │    • Receives debug messages via socket                 │ │
│  │    • Displays in Rich console (separate window)         │ │
│  │    • Routes to logging system (NEW)                     │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ 3. Model Manager (model_manager.py)                     │ │
│  │    • Singleton for Ollama model management              │ │
│  │    • OpenAI integration support                         │ │
│  │    • Dynamic model switching                            │ │
│  │    • JSON response normalization                        │ │
│  └─────────────────────────────────────────────────────────┘ │
│                       ↓                                       │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ 4. OpenAI Integration (open_ai_integration.py)          │ │
│  │    • NVIDIA API wrapper (OpenAI-compatible)             │ │
│  │    • Rate limiting (30 requests/min)                    │ │
│  │    • Circuit breaker pattern                            │ │
│  │    • Async & sync support                               │ │
│  │    • Streaming & non-streaming                          │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ 5. Listeners (listeners/)                               │ │
│  │    • event_listener.py - Event-driven communication     │ │
│  │    • exit_listener.py - Graceful shutdown handling      │ │
│  │    • rich_status_listen.py - Status updates             │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## 🧩 **Components Explained**

### **1. Socket Manager (`socket_manager.py`)**

**What it does:** Manages socket connections for debug logging.

**Key Responsibilities:**
- Start/stop debug log server subprocess
- Establish TCP connection to server
- Send debug messages over socket
- Health checking and reconnection

**Singleton Pattern:**
```python
socket_manager = SocketManager()  # Always returns same instance
```

**Key Methods:**

#### **start_log_server()**
Starts the debug log server as a subprocess:
```python
def start_log_server(self):
    # Starts error_transfer.py as subprocess
    # Creates separate console window (Windows)
    # Returns True if successful
```

**Log Display Modes:**
- `separate_window` - New console window (recommended)
- `background` - Hidden process
- `file` - Output to error_log.txt

Set in `settings.LOG_DISPLAY_MODE`.

#### **get_socket_connection()**
Gets or creates socket connection:
```python
connection = socket_manager.get_socket_connection()
# Returns SocketCon instance or None
```

**Health Checking:**
- Checks if existing connection is alive
- Automatically reconnects if dead
- Starts server if not running

#### **send_error(message)**
Legacy API for sending debug messages:
```python
socket_manager.send_error("[INFO] Server started")
```

**Modern Alternative (Structured):**
```python
from src.ui.diagnostics.debug_helpers import debug_info
debug_info("SERVER • STARTED", "Server listening on port 5000")
```

---

### **2. Error Transfer (`error_transfer.py`)**

**What it does:** TCP server that receives and displays debug messages.

**Architecture:**
- Runs as **subprocess** (separate Python process)
- Listens on `localhost:5390`
- Rich console for beautiful output
- Routes to `system_logging` package

**Main Loop:**
```python
while listening:
    client_socket, addr = server_socket.accept()
    while True:
        message = socket_con.receive_error()
        
        # 1. Display in Rich console
        print_error.print_rich(message)
        
        # 2. Write to legacy file
        write_to_file(message)
        
        # 3. Route to new logging system
        new_logger_write(message)
```

**Lock File:**
Prevents multiple instances from running:
```
src/basic_logs/server.lock
```

**Signal Handling:**
Graceful shutdown on SIGTERM, SIGINT, SIGBREAK.

---

### **3. Model Manager (`model_manager.py`)**

**What it does:** Unified interface for Ollama and OpenAI models.

**Singleton Pattern:**
```python
model = ModelManager(model="qwen2.5:32b-instruct")
# All subsequent calls return same instance
```

**Key Features:**

#### **Dynamic Model Switching**
```python
# Load Ollama model
model = ModelManager(model="qwen2.5:32b-instruct")

# Switch to OpenAI model
model = ModelManager(model="gpt-4o-mini", api_key="...")
# Automatically detects and uses OpenAI integration
```

#### **Invoke (Sync)**
```python
from langchain_core.messages import HumanMessage

response = model.invoke([HumanMessage(content="What is 2+2?")])
# Returns AIMessage with content
```

#### **Stream (Sync)**
```python
for chunk in model.stream([HumanMessage(content="Tell a story")]):
    print(chunk.content, end="", flush=True)
```

#### **JSON Conversion**
Extracts JSON from model responses:
```python
response = model.invoke([HumanMessage(content="Return JSON")])
json_obj = ModelManager.convert_to_json(response)
# Returns dict or list
```

**Extraction Methods:**
1. Direct JSON parsing
2. Markdown code block extraction
3. Brace/bracket matching
4. Fallback wrapper

#### **Cleanup**
```python
ModelManager.cleanup_all_models()
# Stops Ollama models
# Closes OpenAI clients
```

---

### **4. OpenAI Integration (`open_ai_integration.py`)**

**What it does:** Wrapper for OpenAI API (NVIDIA endpoints).

**Singleton Pattern:**
```python
openai = OpenAIIntegration(api_key="...", model="gpt-4o-mini")
# Only one instance exists
```

**Key Features:**

#### **Rate Limiting**
Automatically handles 30 requests/minute limit:
```python
# Blocks if limit exceeded
response = openai.generate_text("Hello")
# Waits if necessary before making request
```

#### **Circuit Breaker**
Prevents API calls during outages:
```python
# After 5 failures, circuit opens for 10 seconds
# Returns fallback responses instead of failing
```

**Circuit Breaker States:**
- **Closed**: Normal operation
- **Open**: Too many failures, block requests
- **Half-Open**: Timeout expired, try one request

#### **Sync API**
```python
# Non-streaming
response = openai.generate_text(
    prompt="What is 2+2?",
    stream=False
)
# Returns: "4"

# Streaming
for chunk in openai.generate_text(
    prompt="Tell a story",
    stream=True
):
    print(chunk, end="", flush=True)
```

#### **Async API**
```python
# Non-streaming
response = await openai.generate_text_async(
    prompt="What is 2+2?"
)

# Streaming
async for chunk in openai.generate_text_async_streaming(
    prompt="Tell a story"
):
    print(chunk, end="", flush=True)
```

#### **Messages API**
```python
messages = [
    {"role": "system", "content": "You are a helpful assistant"},
    {"role": "user", "content": "What is 2+2?"}
]

response = openai.generate_text(messages=messages)
```

#### **Error Handling**
Retries with exponential backoff:
```python
# Retries up to 5 times on:
# - 502 errors
# - 400/500 errors
# - Unexpected errors

# Returns fallback response after max attempts
```

#### **Fallback Responses**
```python
# Classification fallback
'{"message_type": "fallback", "reasoning": "API unavailable"}'

# Agent fallback
"I'm experiencing technical difficulties..."

# Parameter generation fallback
'{"tool_name": "none", "parameters": {}}'
```

---

### **5. Listeners (`listeners/`)**

Event-driven communication system.

#### **Event Listener (`event_listener.py`)**

**What it does:** Observer pattern for variable changes.

**Example:**
```python
from src.utils.listeners.event_listener import EventListener

listener = EventListener("my_listener")

# Register listener for variable changes
listener.on_variable_change(
    source=MyClass,
    variable_name="status",
    handler=lambda event: print(f"Status changed: {event.new_value}")
)

# Emit event
listener.emit_on_variable_change(
    source=MyClass,
    variable_name="status",
    old_value="idle",
    new_value="running"
)
```

#### **Exit Listener (`exit_listener.py`)**

**What it does:** Two-ticket exit system for graceful shutdown.

**Example:**
```python
from src.utils.listeners.exit_listener import TwoTicketExitListener

exit_listener = TwoTicketExitListener()

# Register listener
exit_listener.register_listener(
    listener_id=123,
    handler=lambda: print("Exit signal received")
)

# Emit exit signal (requires 2 tickets)
exit_listener.emit_exit()  # First ticket
exit_listener.emit_exit()  # Second ticket → triggers handlers
```

**Why Two Tickets:**
Prevents accidental exits - requires confirmation.

#### **Rich Status Listener (`rich_status_listen.py`)**

**What it does:** Status updates for Rich console.

**Example:**
```python
from src.utils.listeners.rich_status_listen import RichStatusListener

status_listener = RichStatusListener(console, spinner="dots")

# Update status
status_listener.emit_on_variable_change(
    source=MyClass,
    variable_name="status",
    old_value="idle",
    new_value="Processing request..."
)
```

---

## 🚀 **Quick Start Guide**

### **Using Socket Manager**

```python
from src.utils.socket_manager import socket_manager

# Socket manager is already initialized as singleton
connection = socket_manager.get_socket_connection()

# Send debug message (legacy API)
socket_manager.send_error("[INFO] Application started")

# Modern structured API
from src.ui.diagnostics.debug_helpers import debug_info
debug_info("APP • STARTED", "Application initialized successfully")
```

### **Using Model Manager**

```python
from src.utils.model_manager import ModelManager

# Initialize with Ollama model
model = ModelManager(model="qwen2.5:32b-instruct")

# Invoke
from langchain_core.messages import HumanMessage
response = model.invoke([HumanMessage(content="What is AI?")])
print(response.content)

# Stream
for chunk in model.stream([HumanMessage(content="Tell a joke")]):
    print(chunk.content, end="", flush=True)

# Convert response to JSON
json_obj = ModelManager.convert_to_json(response)
```

### **Using OpenAI Integration**

```python
from src.utils.open_ai_integration import OpenAIIntegration

# Initialize (Singleton)
openai = OpenAIIntegration(api_key="your-key", model="gpt-4o-mini")

# Generate text (sync)
response = openai.generate_text(prompt="What is 2+2?")
print(response)

# Generate text (async)
import asyncio
response = await openai.generate_text_async(prompt="What is 2+2?")
print(response)

# Streaming
for chunk in openai.generate_text(prompt="Tell a story", stream=True):
    print(chunk, end="", flush=True)
```

### **Using Listeners**

```python
from src.utils.listeners.event_listener import EventListener

listener = EventListener("my_listener")

# Listen for variable changes
listener.on_variable_change(
    source=MyClass,
    variable_name="status",
    handler=lambda event: print(f"Status: {event.new_value}")
)

# Emit change
listener.emit_on_variable_change(
    source=MyClass,
    variable_name="status",
    old_value="idle",
    new_value="running"
)
```

---

## 🐛 **Troubleshooting**

### **Problem: Socket Connection Failed**

**Error:**
```
❌ Failed to start log server
```

**Causes:**
1. Port 5390 already in use
2. Log server subprocess crashed
3. Lock file stale

**Fix:**
```python
# Check if server is running
if socket_manager.is_log_server_running():
    print("Server is running")
else:
    # Restart server
    socket_manager.start_log_server()

# Check for stale lock file
lock_file = Path("src/basic_logs/server.lock")
if lock_file.exists():
    # Check PID
    with lock_file.open() as f:
        pid = int(f.read())
    # Kill if needed
```

---

### **Problem: OpenAI Rate Limit Hit**

**Error:**
```
[OPENAI • RATE_LIMIT] API rate limit hit - waiting for reset
```

**Cause:** More than 30 requests in 60 seconds

**Fix:**
- **Automatic**: Code waits automatically
- **Manual**: Reduce request frequency
- **Monitor**: Check `OpenAIIntegration.requests_count`

---

### **Problem: Circuit Breaker Open**

**Error:**
```
[OPENAI • CIRCUIT_BREAKER_BLOCK] Request blocked by circuit breaker
```

**Cause:** Too many API failures (5+)

**Fix:**
- **Wait**: Circuit resets after 10 seconds
- **Check API**: Verify NVIDIA API is working
- **Manual Reset**: Restart application

---

## 📚 **API Reference**

### **Socket Manager**

#### **get_socket_connection()**
```python
def get_socket_connection(self) -> Optional[SocketCon]:
    """Get or create socket connection with health checking."""
```

#### **send_error(message)**
```python
def send_error(self, message: str):
    """Send debug message (legacy API)."""
```

#### **cleanup()**
```python
@classmethod
def cleanup(cls):
    """Clean up socket and kill subprocess."""
```

---

### **Model Manager**

#### **invoke()**
```python
def invoke(
    self,
    input: LanguageModelInput,
    config: Optional[RunnableConfig] = None,
    **kwargs
) -> BaseMessage:
    """Invoke model with input."""
```

#### **stream()**
```python
def stream(
    self,
    input: LanguageModelInput,
    **kwargs
) -> Iterator[BaseMessageChunk]:
    """Stream model response."""
```

#### **convert_to_json()**
```python
@classmethod
def convert_to_json(cls, response: Union[str, dict, BaseMessage]) -> Union[dict, list]:
    """Extract JSON from response."""
```

---

### **OpenAI Integration**

#### **generate_text()**
```python
def generate_text(
    self,
    prompt: Optional[str] = None,
    messages: Optional[list[dict]] = None,
    stream: bool = False
) -> Union[str, Iterator[str]]:
    """Generate text (sync)."""
```

#### **generate_text_async()**
```python
async def generate_text_async(
    self,
    prompt: str = None,
    messages: Optional[List[Dict]] = None
) -> str:
    """Generate text (async)."""
```

---

## 🎓 **Design Patterns Used**

### **1. Singleton Pattern**
All managers use singleton:
- `SocketManager`
- `ModelManager`
- `OpenAIIntegration`

**Why:** Only one instance should manage resources.

### **2. Observer Pattern**
`EventListener` implements observer:
- Subjects emit events
- Observers receive notifications

### **3. Circuit Breaker Pattern**
`OpenAIIntegration` implements circuit breaker:
- **Closed**: Normal operation
- **Open**: Block requests after failures
- **Half-Open**: Test recovery

### **4. Retry Pattern**
`OpenAIIntegration` retries with exponential backoff:
- Attempt 1: Immediate
- Attempt 2: 1 second delay
- Attempt 3: 2 seconds delay
- Attempt 4: 4 seconds delay
- Attempt 5: 8 seconds delay

---

## 🤝 **Contributing**

### **Adding New Utilities**

1. Create file in `utils/`
2. Follow singleton pattern if managing resources
3. Add to `__init__.py`
4. Document in this README

### **Testing**

```python
# Test socket manager
python -m src.utils.socket_manager

# Test OpenAI integration
python -m src.utils.open_ai_integration
```

---

## 📝 **Changelog**

### **Version 1.0 (Current)**
- ✅ Socket Manager with health checking
- ✅ Model Manager with Ollama & OpenAI support
- ✅ OpenAI Integration with rate limiting
- ✅ Error Transfer subprocess
- ✅ Event listeners (event, exit, status)

### **Recent Improvements**
- ✅ Circuit breaker pattern in OpenAI integration
- ✅ Async support for all API calls
- ✅ Better error handling with fallbacks
- ✅ Integrated with new `system_logging` package

---

## 🆘 **Support**

**Questions?** Check:
1. This README
2. Code comments (well-documented)
3. Related packages (`system_logging`, `ui/diagnostics`)

**Found a bug?** Create an issue with:
- Module name
- Expected behavior
- Actual behavior
- Error messages

---

**Status:** ✅ **Production-Ready**

**Completion:** 100% (Core utilities complete)

**Maintainer:** AI-Agent-Workflow Team

**Last Updated:** December 24, 2025

