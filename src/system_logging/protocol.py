"""
system_logging system protocol definitions for structured log entries in a microservices architecture.
===================================================================

defined log levels and categories for consistent system_logging across services.
for custom log entry structure with metadata support.

"""




from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union
from enum import Enum


class LogLevel (Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogCategory (Enum):
    API_CALL = "API_CALL"
    TOOL_EXECUTION = "TOOL_EXECUTION"
    AGENT_WORKFLOW = "AGENT_WORKFLOW"
    MCP_SERVER = "MCP_SERVER"
    ERROR_TRACEBACK = "ERROR_TRACEBACK"
    OTHER = "OTHER"


@dataclass
class LogEntry:
    LOG_TYPE: LogCategory
    LOG_LEVEL: LogLevel
    TIME_STAMP: str
    MESSAGE: str # main message body
    METADATA: Optional[Dict[str, Any]] = None

    """
    LogLevel - DEBUG, INFO, WARNING, ERROR, CRITICAL
    LogType - API_CALL, TOOL_EXECUTION, AGENT_WORKFLOW, MCP_SERVER, ERROR_TRACEBACK
    """

#### todo make sure that the LogEntry matches the debug message protocol !!