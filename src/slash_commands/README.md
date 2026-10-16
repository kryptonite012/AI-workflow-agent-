# 📝 Slash Commands Package

**Extensible Command System for AI-Agent-Workflow**

> A clean, registry-based slash command architecture that allows users to interact with the chatbot using Discord-style `/` commands.

---

## 📋 **Table of Contents**

1. [Why We Need This Package](#why-we-need-this-package)
2. [Architecture Overview](#architecture-overview)
3. [How Slash Commands Work (Step-by-Step)](#how-slash-commands-work-step-by-step)
4. [Components Explained](#components-explained)
5. [Quick Start Guide](#quick-start-guide)
6. [Creating Custom Commands](#creating-custom-commands)
7. [Available Commands](#available-commands)
8. [Troubleshooting](#troubleshooting)
9. [API Reference](#api-reference)

---

## 🎯 **Why We Need This Package**

### **The Problem We Solved**

Users need a simple way to interact with the chatbot beyond normal conversations:
- ❌ Hard to invoke specific features (agent mode, tools, etc.)
- ❌ No structured way to pass parameters
- ❌ Difficult to discover available features
- ❌ No help system for users

### **What This Package Provides**

A **Discord-style slash command system** that users love:
- ✅ **Simple syntax**: `/agent --high analyze market trends`
- ✅ **Discoverable**: `/help` shows all commands
- ✅ **Extensible**: Add new commands easily
- ✅ **Type-safe**: Validates commands before execution
- ✅ **Options support**: Flags and arguments (`--name`, `--tags`)

**Examples:**
```bash
/help                      # Show all commands
/help --command agent     # Show help for specific command
/agent --high analyze this # Invoke agent with high complexity
/clear                     # Clear chat history
/exit                      # Exit the application
```

---

## 🏗️ **Architecture Overview**

This package follows **Clean Architecture** with **Separation of Concerns**:

```
┌──────────────────────────────────────────────────────────────┐
│                  SLASH COMMAND SYSTEM FLOW                    │
│                  (Clean Registry Pattern)                     │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  👤 User Input                                                │
│      ↓                                                        │
│  "/agent --high analyze market trends"                       │
│      ↓                                                        │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ 1. Parser (parser.py)                                   │ │
│  │    Validates syntax: Must start with '/'                │ │
│  │    Extracts: command="agent", options=[--high, ...]     │ │
│  │    Creates: SlashCommand object                         │ │
│  └────────────────────┬────────────────────────────────────┘ │
│                       ↓                                      │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ 2. Executionar (executionar.py)                         │ │
│  │    Gets command handler from registry                   │ │
│  │    Calls: handler(slash_command, options)               │ │
│  └────────────────────┬────────────────────────────────────┘ │
│                       ↓                                      │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ 3. Registry (on_run_time_register.py)                   │ │
│  │    Singleton registry of all commands                   │ │
│  │    Returns: SlashCommand with handler function          │ │
│  └────────────────────┬────────────────────────────────────┘ │
│                       ↓                                      │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ 4. Handler (commands/core_slashs/agent.py)              │ │
│  │    Executes the command logic                           │ │
│  │    Returns: CommandResult(success, message, data)       │ │
│  └─────────────────────────────────────────────────────────┘ │
│                       ↓                                      │
│  ✅ Result: "Agent invoked successfully"                     │
└──────────────────────────────────────────────────────────────┘
```

---

## 📊 **How Slash Commands Work (Step-by-Step)**

Let me walk you through **exactly** what happens when you type a slash command:

### **Step 1: User Types Command**

```bash
/agent --high analyze the market trends
```

**What happens:**
- You type this in the chat
- The application detects it starts with `/`
- Sends it to the Parser

---

### **Step 2: Parser Validates and Parses**

**File:** `slash_commands/parser.py`

```python
# Input string
input_str = "/agent --high analyze the market trends"

# Parser extracts:
command = "agent"              # The command name
option_name = "high"           # The flag name
option_value = ["analyze", "the", "market", "trends"]  # The arguments
```

**Validation:**
1. ✅ Must start with `/`
2. ✅ Command name must be valid (alphanumeric, no spaces)
3. ✅ Options follow `--name value` format

**Output:**
```python
SlashCommand(
    command="agent",
    options=[
        CommandOption(
            name="high",
            type=SlashOptionValueType.STRING,
            value=["analyze the market trends"]  # Joined into single string
        )
    ],
    handler=None  # Will be filled by registry
)
```

---

### **Step 3: Executionar Looks Up Handler**

**File:** `slash_commands/executionar.py`

```python
def execute(self, slash_com: SlashCommand):
    # 1. Get command from registry
    registered_command = self.registry.get("agent")
    
    # 2. Call the handler
    result = registered_command.handler(slash_com, slash_com.options[0])
    
    return result
```

**What happens:**
- Executionar asks registry: "Do you have a command called 'agent'?"
- Registry returns the full SlashCommand with handler function
- Executionar calls the handler with the parsed options

---

### **Step 4: Registry Returns Handler**

**File:** `slash_commands/on_run_time_register.py`

```python
# Registry is a Singleton - only one instance exists
registry = OnRunTimeRegistry()

# Has a list of registered commands
_registered_commands = [
    SlashCommand(command="agent", handler=agent_handler),
    SlashCommand(command="help", handler=help_handler),
    SlashCommand(command="clear", handler=clear_handler),
    ...
]

# Finds the command
slash_command = next(cmd for cmd in _registered_commands if cmd.command == "agent")
# Returns: SlashCommand(command="agent", handler=agent_handler)
```

**Why Singleton:**
- Only **ONE** registry exists in the entire application
- All parts of the app share the same command list
- Thread-safe (uses locks)

---

### **Step 5: Handler Executes Logic**

**File:** `slash_commands/commands/core_slashs/agent.py`

```python
def agent_handler(command: SlashCommand, options: CommandOption | None):
    # User wants high complexity agent
    # Option name: "high"
    # Option value: ["analyze the market trends"]
    
    # Execute agent logic here
    # (Currently routes to agent node)
    
    return CommandResult(
        success=True,
        message="Agent invoked successfully",
        data={"message_type": "agent"}
    )
```

**What happens:**
- Handler receives the command and options
- Processes the request
- Returns a `CommandResult` with success/failure info

---

### **Step 6: Result Returned to User**

```python
CommandResult(
    success=True,
    message="Agent invoked successfully",
    data={"message_type": "agent"},
    error=None
)
```

**User sees:**
```
✅ Agent invoked successfully
```

---

## 🧩 **Components Explained**

### **1. Protocol (`protocol.py`)**

**What it does:** Defines all data structures for the command system.

**Contains:**

#### **SlashOptionValueType**
```python
class SlashOptionValueType(Enum):
    STRING = "string"      # Multi-word value: --name John Smith
    CHARACTER = "character" # Comma-separated: --tags a,b,c
```

**Examples:**
```bash
# STRING type (joins all words)
/greet --name John Smith
# Result: CommandOption(name="name", value=["John Smith"])

# CHARACTER type (splits by comma)
/read --files a.txt,b.txt,c.txt
# Result: CommandOption(name="files", value=["a.txt", "b.txt", "c.txt"])
```

#### **CommandOption**
```python
@dataclass
class CommandOption:
    name: str              # Option name (e.g., "high", "name")
    type: SlashOptionValueType
    value: list[Any]       # Option values
    description: str       # Help text
    required: bool         # Is it mandatory?
    default: Any           # Default value if not provided
```

#### **SlashCommand**
```python
@dataclass
class SlashCommand:
    command: str           # Command name (e.g., "agent")
    options: list[CommandOption]
    requirements: list     # Permissions (future use)
    description: str       # Help text
    handler: Callable      # Function to execute
```

#### **CommandResult**
```python
@dataclass
class CommandResult:
    success: bool          # Did command succeed?
    message: str           # Result message
    data: Any              # Additional data
    additional_warnings: list[str]  # Non-critical warnings
    error: dict            # Error details if failed
```

**Why we need it:**
- **Single source of truth** for command data structures
- **Type safety** - Can't create invalid commands
- **Clear contracts** - Everyone knows what a command looks like

---

### **2. Parser (`parser.py`)**

**What it does:** Validates and parses user input into SlashCommand objects.

**Methods:**

#### **ParseCommand.get_command()**
```python
input_str = "/agent --high analyze this"

# Returns:
SlashCommand(
    command="agent",
    options=[CommandOption(name="high", value=["analyze this"])],
    handler=None
)
```

#### **Validation Rules:**
1. ✅ Must start with `/`
2. ✅ Command name must be alphanumeric
3. ✅ Options follow `--name value` format
4. ❌ Raises `ValueError` if invalid

**Error examples:**
```python
ParseCommand.get_command("agent")  # ❌ No '/' prefix
# ValueError: Command must start with '/'

ParseCommand.get_command("/123agent")  # ❌ Invalid name
# ValueError: Invalid command name: '123agent'

ParseCommand.get_command("/agent --")  # ❌ Option without value
# ValueError: Invalid option format: '' after --
```

**Why we need it:**
- **Early validation** - Catches errors before execution
- **Normalizes input** - Consistent format for handlers
- **Type conversion** - Converts strings to proper types

---

### **3. Executionar (`executionar.py`)**

**What it does:** Executes registered slash commands.

```python
class ExecutionAr:
    def execute(self, slash_com: SlashCommand) -> CommandResult:
        # 1. Get command from registry
        registered_command = self.registry.get(slash_com.command)
        
        # 2. Call handler
        return registered_command.handler(slash_com, options)
```

**Error Handling:**
```python
# Command not found
CommandResult(
    success=False,
    message="Command 'xyz' not found",
    error={"error": "Command not found"}
)

# Execution error
CommandResult(
    success=False,
    message="Failed to execute command",
    error={"error": str(exception)}
)
```

**Why we need it:**
- **Orchestration** - Coordinates registry and handlers
- **Error handling** - Catches and reports errors gracefully
- **Abstraction** - Handlers don't know about registry

---

### **4. Registry (`registry.py` + `on_run_time_register.py`)**

**What it does:** Manages all registered commands (Singleton pattern).

#### **Abstract Base: Registry**
Defines the interface all registries must implement:
```python
class Registry(ABC):
    @abstractmethod
    def register(command: SlashCommand): ...
    @abstractmethod
    def unregister(command: SlashCommand): ...
    @abstractmethod
    def get(command: str) -> SlashCommand: ...
```

#### **Concrete Implementation: OnRunTimeRegistry**
Singleton that holds all commands:
```python
class OnRunTimeRegistry(Registry):
    _registered_commands: list[SlashCommand] = []
    instance = None  # Singleton instance
    
    def register(self, slash_command):
        # Check if already registered
        if slash_command in self._registered_commands:
            raise CommandAlreadyRegisteredError
        
        self._registered_commands.append(slash_command)
    
    def get(self, command: str):
        # Find command by name
        cmd = next(c for c in self._registered_commands if c.command == command)
        if not cmd:
            raise CommandNotFoundError
        return cmd
```

**Singleton Pattern:**
```python
def __new__(cls):
    if cls.instance is None:
        cls.instance = super().__new__(cls)
        cls.instance._registered_commands = []
    return cls.instance

# Always returns the same instance
registry1 = OnRunTimeRegistry()
registry2 = OnRunTimeRegistry()
# registry1 is registry2  # True!
```

**Why Singleton:**
- **One source of truth** - All code sees same commands
- **Thread-safe** - Uses locks for concurrent access
- **Memory efficient** - Only one list exists

**Why we need it:**
- **Central registry** - One place to find all commands
- **Dependency injection** - Executionar doesn't create it
- **Testability** - Can swap registries for testing

---

### **5. Commands (`commands/`)**

**What it does:** Individual command implementations.

**Structure:**
```
commands/
├── help.py           # /help command
├── clear.py          # /clear command
├── exit.py           # /exit command
└── core_slashs/      # Core slash commands
    ├── agent.py      # /agent command
    ├── chat_llm.py   # /chat command
    └── use_tool.py   # /tool command
```

#### **Example: Help Command**

**File:** `commands/help.py`

```python
# 1. Register function
def register_help_command():
    help_command = SlashCommand(
        command="help",
        options=[CommandOption(name="command")],
        description="Show available commands",
        handler=help_handler  # ← Handler function
    )
    registry = OnRunTimeRegistry()
    registry.register(help_command)

# 2. Handler function
def help_handler(command, options) -> CommandResult:
    if options and options.value:
        # Show help for specific command
        return get_specific_command_help(options.value[0])
    else:
        # Show all commands
        help_message = "Available Commands:\n"
        for cmd in registry:
            help_message += f"/{cmd.command}: {cmd.description}\n"
        return CommandResult(success=True, message=help_message)
```

**Usage:**
```bash
/help
# Shows all commands

/help --command agent
# Shows detailed help for /agent command
```

#### **Example: Agent Command**

**File:** `commands/core_slashs/agent.py`

```python
def register_agent_command():
    agent_command = SlashCommand(
        command="agent",
        options=[
            CommandOption(name="low", description="Simple tasks"),
            CommandOption(name="medium", description="Moderate tasks"),
            CommandOption(name="high", description="Complex tasks"),
        ],
        description="Invoke agent with complexity level",
        handler=agent_handler
    )
    registry.register(agent_command)

def agent_handler(command, options) -> CommandResult:
    # Route to agent node based on complexity
    return CommandResult(
        success=True,
        message="Agent invoked successfully",
        data={"message_type": "agent"}
    )
```

**Usage:**
```bash
/agent --low tell me a joke
/agent --medium summarize this text
/agent --high analyze market trends
```

---

## 🚀 **Quick Start Guide**

### **For Users (Just Want to Use Commands)**

```bash
# Show all available commands
/help

# Show help for specific command
/help --command agent

# Use a command
/agent --high analyze the stock market

# Clear chat history
/clear

# Exit application
/exit
```

**That's it!** Just type `/` and the command name.

---

### **For Developers (Want to Add Commands)**

#### **Step 1: Create Command Handler**

Create a new file in `commands/` (e.g., `commands/my_command.py`):

```python
from ..protocol import SlashCommand, CommandOption, CommandResult
from ..on_run_time_register import OnRunTimeRegistry

def register_my_command():
    """Register the /my_command command."""
    my_command = SlashCommand(
        command="my_command",
        options=[
            CommandOption(
                name="option1",
                description="Description of option1",
                required=False
            )
        ],
        description="What my command does",
        handler=my_command_handler
    )
    
    registry = OnRunTimeRegistry()
    try:
        registry.register(my_command)
    except registry.CommandAlreadyRegisteredError:
        pass  # Already registered

def my_command_handler(command: SlashCommand, options: CommandOption | None) -> CommandResult:
    """Handle /my_command execution."""
    try:
        # Your command logic here
        result = "Did something!"
        
        return CommandResult(
            success=True,
            message=result,
            data={"custom_data": "value"}
        )
    except Exception as e:
        return CommandResult(
            success=False,
            message="Command failed",
            error={"error": str(e)}
        )
```

#### **Step 2: Register Command at Startup**

**File:** `src/core/chat_initializer.py` (or wherever commands are registered)

```python
from src.slash_commands.commands.my_command import register_my_command

# In initialization function
register_my_command()
```

#### **Step 3: Use Your Command**

```bash
/my_command --option1 some value
```

**That's it!** Your command is now available.

---

## 📚 **Available Commands**

### **Core Commands**

| Command | Description | Options | Example |
|---------|-------------|---------|---------|
| `/help` | Show available commands | `--command <name>` | `/help --command agent` |
| `/agent` | Invoke agent with complexity | `--low`, `--medium`, `--high` | `/agent --high analyze this` |
| `/chat` | Normal chat mode | None | `/chat` |
| `/tool` | Use specific tool | `--name <tool_name>` | `/tool --name google_search` |
| `/clear` | Clear chat history | None | `/clear` |
| `/exit` | Exit application | None | `/exit` |

### **Command Details**

#### **`/help`**
**Purpose:** Display help information

**Options:**
- `--command <name>` - Show help for specific command

**Examples:**
```bash
/help                    # List all commands
/help --command agent   # Show agent command help
```

---

#### **`/agent`**
**Purpose:** Invoke AI agent with complexity level

**Options:**
- `--low` - Simple tasks (jokes, quotes, basic info)
- `--medium` - Moderate tasks (summarization, basic analysis)
- `--high` - Complex tasks (market analysis, strategic planning)

**Examples:**
```bash
/agent --low tell me a joke
/agent --medium summarize the following text: [text]
/agent --high analyze market trends for next week
```

**How it works:**
1. Parser extracts complexity level (low/medium/high)
2. Handler routes to agent node
3. Agent processes with appropriate complexity

---

#### **`/clear`**
**Purpose:** Clear chat history

**Options:** None

**Example:**
```bash
/clear
```

---

#### **`/exit`**
**Purpose:** Exit the application

**Options:** None

**Example:**
```bash
/exit
```

---

## 🛠️ **Creating Custom Commands**

### **Example: Create `/quote` Command**

Let's create a command that returns random quotes with different categories.

#### **Step 1: Create Handler File**

**File:** `commands/quote.py`

```python
from ..protocol import SlashCommand, CommandOption, CommandResult
from ..on_run_time_register import OnRunTimeRegistry
import random

# Sample quotes database
QUOTES = {
    "motivation": [
        "The only way to do great work is to love what you do. - Steve Jobs",
        "Believe you can and you're halfway there. - Theodore Roosevelt",
    ],
    "funny": [
        "I'm not lazy, I'm on energy saving mode.",
        "I'm not arguing, I'm just explaining why I'm right.",
    ],
    "wisdom": [
        "The only true wisdom is in knowing you know nothing. - Socrates",
        "In the middle of difficulty lies opportunity. - Albert Einstein",
    ]
}

def register_quote_command():
    """Register the /quote command."""
    quote_command = SlashCommand(
        command="quote",
        options=[
            CommandOption(
                name="category",
                description="Quote category: motivation, funny, wisdom",
                required=False
            )
        ],
        description="Get a random quote",
        handler=quote_handler
    )
    
    registry = OnRunTimeRegistry()
    try:
        registry.register(quote_command)
    except registry.CommandAlreadyRegisteredError:
        pass

def quote_handler(command: SlashCommand, options: CommandOption | None) -> CommandResult:
    """Handle /quote command."""
    try:
        # Determine category
        if options and options.value:
            category = options.value[0].lower()
            if category not in QUOTES:
                return CommandResult(
                    success=False,
                    message=f"Unknown category '{category}'. Use: motivation, funny, wisdom",
                    error={"error": "Invalid category"}
                )
        else:
            # Random category
            category = random.choice(list(QUOTES.keys()))
        
        # Get random quote from category
        quote = random.choice(QUOTES[category])
        
        return CommandResult(
            success=True,
            message=f"📜 {category.capitalize()} Quote:\n{quote}",
            data={"category": category, "quote": quote}
        )
    except Exception as e:
        return CommandResult(
            success=False,
            message="Failed to get quote",
            error={"error": str(e)}
        )
```

#### **Step 2: Register Command**

**File:** `src/core/chat_initializer.py`

```python
from src.slash_commands.commands.quote import register_quote_command

# In initialization
register_quote_command()
```

#### **Step 3: Use Command**

```bash
/quote
# 📜 Motivation Quote:
# The only way to do great work is to love what you do. - Steve Jobs

/quote --category funny
# 📜 Funny Quote:
# I'm not lazy, I'm on energy saving mode.

/quote --category xyz
# ❌ Unknown category 'xyz'. Use: motivation, funny, wisdom
```

---

## 🐛 **Troubleshooting**

### **Problem: Command Not Found**

**Error:**
```
Command 'xyz' not found
```

**Causes:**
1. Command not registered
2. Typo in command name
3. Registration failed silently

**Fix:**
```python
# Check if command is registered
registry = OnRunTimeRegistry()
print(len(registry))  # Number of registered commands
for cmd in registry:
    print(cmd.command)  # List all command names
```

---

### **Problem: Invalid Syntax**

**Error:**
```
ValueError: Command must start with '/'
```

**Cause:** Forgot the `/` prefix

**Fix:**
```bash
# ❌ Wrong
agent --high analyze this

# ✅ Correct
/agent --high analyze this
```

---

### **Problem: Option Not Found**

**Error:**
```
CommandResult(success=False, error={"error": "..."})
```

**Cause:** Using undefined option

**Fix:**
```bash
# Check available options
/help --command agent

# Use correct option
/agent --high analyze this  # ✅
/agent --ultra analyze this # ❌ (ultra not defined)
```

---

### **Problem: Command Already Registered**

**Error:**
```
CommandAlreadyRegisteredError: Slash command 'agent' already registered
```

**Cause:** Registering same command twice

**Fix:**
```python
# Wrap in try-except
try:
    registry.register(my_command)
except registry.CommandAlreadyRegisteredError:
    pass  # Ignore if already registered
```

---

## 📚 **API Reference**

### **Parser**

#### **ParseCommand.get_command()**
```python
@classmethod
def get_command(cls, input_str: str) -> SlashCommand:
    """
    Parse and validate a slash command string.
    
    Args:
        input_str: Command string (e.g., "/agent --high text")
        
    Returns:
        SlashCommand object with parsed data
        
    Raises:
        ValueError: If command syntax is invalid
    """
```

**Example:**
```python
cmd = ParseCommand.get_command("/agent --high analyze this")
# SlashCommand(command="agent", options=[...])
```

---

### **Executionar**

#### **ExecutionAr.execute()**
```python
def execute(self, slash_com: SlashCommand) -> CommandResult:
    """
    Execute a registered slash command.
    
    Args:
        slash_com: Parsed SlashCommand object
        
    Returns:
        CommandResult with execution outcome
    """
```

**Example:**
```python
executor = ExecutionAr()
result = executor.execute(slash_command)
if result.success:
    print(result.message)
else:
    print(result.error)
```

---

### **Registry**

#### **OnRunTimeRegistry.register()**
```python
def register(self, slash_command: SlashCommand) -> None:
    """
    Register a command handler.
    
    Args:
        slash_command: SlashCommand with handler
        
    Raises:
        CommandAlreadyRegisteredError: If already registered
    """
```

#### **OnRunTimeRegistry.get()**
```python
def get(self, command: str) -> SlashCommand:
    """
    Get registered command by name.
    
    Args:
        command: Command name (without '/')
        
    Returns:
        SlashCommand with handler
        
    Raises:
        CommandNotFoundError: If not found
    """
```

#### **OnRunTimeRegistry.__len__()**
```python
def __len__(self) -> int:
    """Return number of registered commands."""
```

#### **OnRunTimeRegistry.__contains__()**
```python
def __contains__(self, slash_command: SlashCommand) -> bool:
    """Check if command is registered."""
```

**Example:**
```python
registry = OnRunTimeRegistry()

# Register
registry.register(my_command)

# Get
cmd = registry.get("agent")

# Check
if len(registry) > 0:
    print(f"{len(registry)} commands registered")

# Contains
if my_command in registry:
    print("Command registered")
```

---

## 🎓 **Design Patterns Used**

### **1. Command Pattern**
Each slash command encapsulates a request as an object:
- **Command Object:** `SlashCommand`
- **Receiver:** Command handler function
- **Invoker:** `ExecutionAr`
- **Registry:** `OnRunTimeRegistry`

### **2. Singleton Pattern**
`OnRunTimeRegistry` ensures only one instance exists:
```python
registry1 = OnRunTimeRegistry()
registry2 = OnRunTimeRegistry()
# registry1 is registry2  # True!
```

### **3. Registry Pattern**
Central place to register and retrieve commands:
- Commands register themselves at startup
- Executionar looks up commands from registry
- Decouples command creation from execution

### **4. Strategy Pattern**
Different handlers for different commands:
- Each command has its own handler function
- Handlers implement same signature
- Easy to swap or add handlers

---

## 🤝 **Contributing**

### **Adding New Commands**

1. Create handler file in `commands/`
2. Define `register_*_command()` function
3. Define `*_handler()` function
4. Register at startup
5. Test with `/help` and actual usage

### **Modifying Existing Commands**

1. Find handler in `commands/`
2. Modify handler logic
3. Update options if needed
4. Test thoroughly

---

## 📝 **Changelog**

### **Version 1.0 (Current)**
- ✅ Core slash command system
- ✅ Parser with validation
- ✅ Registry pattern (Singleton)
- ✅ Help, Agent, Clear, Exit commands
- ✅ Option support (STRING, CHARACTER types)
- ✅ Error handling

### **Future Enhancements**
- ⏳ Command aliases (`/h` for `/help`)
- ⏳ Auto-completion
- ⏳ Command history
- ⏳ Permissions system
- ⏳ Required options validation

---

## 🆘 **Support**

**Questions?** Check:
1. This README
2. Code comments (all files are well-documented)
3. `/help` command in the application

**Found a bug?** Create an issue with:
- Command you tried
- Expected behavior
- Actual behavior
- Error messages

---

**Status:** ✅ **Production-Ready**

**Completion:** 100% (Core system complete)

**Maintainer:** AI-Agent-Workflow Team

**Last Updated:** December 24, 2025

