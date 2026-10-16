"""
Configuration settings for AI LLM project.
"""
from __future__ import annotations

import os
# Load environment variables from .env file
from pathlib import Path
from typing import TypedDict, TYPE_CHECKING

import dotenv

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from src.utils.listeners.rich_status_listen import RichStatusListener
    from src.utils.listeners.exit_listener import ExitListener

dotenv.load_dotenv(
    Path(__file__).resolve().parent.parent.parent / ".env", override=True
)

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent  # src directory

# Server configuration
SOCKET_HOST = os.getenv("SOCKET_HOST", "localhost")
SOCKET_PORT = int(os.getenv("SOCKET_PORT", 5390))

# Model configuration
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "llava-llama3:latest")
CYPHER_MODEL = os.getenv("CYPHER_MODEL", "deepseek-r1:8b")
CLASSIFIER_MODEL = os.getenv("CLASSIFIER_MODEL", "llama3.1:8b")
GPT_MODEL = os.getenv("GPT_MODEL", "openai/gpt-oss-120b")
KIMI_MODEL = os.getenv("KIMI_MODEL", "moonshotai/kimi-k2-instruct-0905")
API_DEFAULT_API_MODEL = KIMI_MODEL
OPEN_AI_API_KEY = os.getenv("OPENAI_API_KEY", "your_openai_api_key_here")

# API endpoints
TRANSLATION_API_URL = os.getenv(
    "TRANSLATION_API_URL", "http://localhost:5560/translate"
)

# Default paths
DEFAULT_RAG_EXAMPLE_FILE_PATH = BASE_DIR / "RAG" / "RAG_FILES" / "kafka.pdf"
DEFAULT_RAG_FILES_HASH_TXT_PATH = (
        BASE_DIR / "RAG" / "RAG_FILES" / "processed_hash_chunks.txt"
)
DEFAULT_RAG_FILES_PROCESSED_TRIPLES_PATH = (
        BASE_DIR / "RAG" / "RAG_FILES" / "processed_triple.json"
)

# Task management configuration
SKIP_THRESHOLD = int(os.getenv("SKIP_THRESHOLD", 70))  # Skip tasks with skip_probability >= this value

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Feature flags
ENABLE_SOCKET_LOGGING = os.getenv("ENABLE_SOCKET_LOGGING", "true").lower() == "true"
ENABLE_SOUND_NOTIFICATIONS = (
        os.getenv("ENABLE_SOUND_NOTIFICATIONS", "true").lower() == "true"
)

# Log display mode options:
# 'separate_window' - Opens log server in separate console window (recommended)
# 'background' - Runs log server in background (logs not visible)
# 'file' - Logs to file (socket_server.log)
# 'console' - Shows logs in same console (can be messy)
LOG_DISPLAY_MODE = os.getenv("LOG_DISPLAY_MODE", "separate_window")
LOG_TEXT_HANDLER_ROTATION_SIZE_LIMIT_MB = int(
    os.getenv("LOG_TEXT_HANDLER_ROTATION_SIZE_LIMIT_MB", 5 * 1024 * 1024)
)  # 5 MB
LOG_TEXT_HANDLER_ROTATION_TIME_LIMIT_HOURS = int(
    os.getenv("LOG_TEXT_HANDLER_ROTATION_TIME_LIMIT_HOURS", 24 * 60 * 60)
)  # 24 hours
LOG_ROTATION_ALWAYS_ON = os.getenv("LOG_ROTATION_ALWAYS_ON", "true").lower() == "true" ##### set to true for debugging only

# Development/Production mode
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# API Timeout settings (in seconds)
OPENAI_TIMEOUT = int(os.getenv("OPENAI_TIMEOUT", 60))  # Default 60 seconds
OPENAI_CONNECT_TIMEOUT = int(
    os.getenv("OPENAI_CONNECT_TIMEOUT", 10)
)  # Default 10 seconds

# NEO4J settings
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "your_password_here")
neo4j_driver = (
    None  # Placeholder for Neo4j driver, to be initialized in main_orchestrator.py
)

# SEMAPHORE SETTINGS
SEMAPHORE_CLI = int(os.getenv("SEMAPHORE_LIMIT_CLI", 15))
SEMAPHORE_API = int(os.getenv("SEMAPHORE_LIMIT_API", 5))
SEMAPHORE_OPENAI = int(os.getenv("SEMAPHORE_LIMIT_OPENAI", 15))

# PNG FILE PATH
PNG_FILE_PATH = BASE_DIR.parent / "basic_logs" / "graph.png"

console = (
    None  # Placeholder for console object, to be initialized in main_orchestrator.py
)
debug_console = (
    None  # Placeholder for debug console object, to be initialized in error_transfer.py
)

# Message class placeholders - to be initialized in chat_initializer.py
HumanMessage = None  # Placeholder for HumanMessage class
AIMessage = None  # Placeholder for AIMessage class
BaseMessage = None  # Placeholder for BaseMessage class
socket_con = (
    None  # Placeholder for socket connection, to be initialized in main_orchestrator.py
)

# listeners

class ListenersDict(TypedDict):
    eval: 'RichStatusListener | None'
    exit: 'ExitListener | None'

listeners: ListenersDict = {
    "eval": None,
    "exit": None
}

#exit flag to close the application smoothly
exit_flag = False

# recursion limits
recursion_limit = int(os.getenv("RECURSION_LIMIT", 500))  ## recursion limit for the agent graph core

# browser use
BROWSER_USE_ENABLED = os.getenv("BROWSER_USE_ENABLED", "true").lower() == "true"
BROWSER_USE_TIMEOUT = int(os.getenv("BROWSER_USE_TIMEOUT", 1300))  # Timeout in seconds (default 1300s = 20min)
BROWSER_USE_LOG_FILE = "browser.txt"
BROWSER_USE_USER_PROFILE_PATH = os.getenv("BROWSER_USE_USER_PROFILE_PATH", str(BASE_DIR.parent.parent / "./profiles/main_profile"))


# mcp.md configs
MCP_CONFIG = {
    "MCP_ENABLED": os.getenv("MCP_ENABLED", "true").lower() == "true",
    "MCP_HOST": os.getenv("MCP_HOST", "localhost"),
    "MCP_PORT": int(os.getenv("MCP_PORT", 5000)),
    "MCP_API_KEY": os.getenv("MCP_API_KEY", "your_api_key_here"),
    "MCP_TIMEOUT": int(os.getenv("MCP_TIMEOUT", 30)),  # Timeout in seconds
    "MCP_CONFIG_PATH": BASE_DIR.parent / ".mcp.json",  # Path to MCP configuration file
}

if __name__ == "__main__":
    # true
    print(
        Path(Path().resolve().parent / "RAG" / "RAG_FILES" / "kafka.pdf")
        .resolve()
        .exists()
    )
    # print(MCP_CONFIG.get('MCP_CONFIG_PATH').exists()) # true
