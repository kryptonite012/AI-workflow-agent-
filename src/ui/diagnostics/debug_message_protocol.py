"""
Debug Message Protocol for AI-Agent-Workflow Project

This is a robust version that handles enum/string conversion safely
without being affected by IDE auto-formatting.

Features:
- Structured JSON message format
- Support for both string and pickle object transmission
- Rich metadata for enhanced debugging
- Type-safe message handling
- Extensible message types
- Robust enum handling

Usage:
    from src.utils.debug_message_protocol import DebugMessageSender, MessageType

    # Send structured debug message
    sender = DebugMessageSender()
    sender.send_debug_message(
        heading="AGENT_MODE • TOOL_EVALUATION",
        body="Tool execution failed",
        level="WARNING",
        metadata={"tool_name": "google_search"}
    )

    # Send Rich Panel object
    sender.send_rich_panel(panel_object)
"""

import base64
import json
import pickle
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, Union

from rich.console import RenderableType

# Import centralized timestamp utility
from src.utils.timestamp_util import get_formatted_timestamp


# Helper: robust JSON serializer to handle datetimes, Enums, dataclasses, and other objects
def _default_json_serializer(obj):
    """Return a JSON-serializable representation for objects that json.dumps can't handle.

    - datetime -> ISO string
    - Enum -> value
    - dataclass instances -> asdict()
    - objects with __dict__ -> their dict
    - fallback -> str(obj)
    """
    try:
        # datetimes
        if isinstance(obj, datetime):
            return obj.isoformat()

        # Enums
        if isinstance(obj, Enum):
            return getattr(obj, "value", str(obj))

        # dataclass instances
        from dataclasses import is_dataclass

        if is_dataclass(obj):
            return asdict(obj)

        # objects with __dict__ (simple fallback)
        if hasattr(obj, "__dict__"):
            return obj.__dict__

    except Exception:
        pass

    # Last resort: stringify
    return str(obj)


class ObjectType(Enum):
    """Types of objects that can be transmitted"""

    STRING = "str"
    PICKLE = "pickle"


class DataType(Enum):
    """Types of data structures supported"""

    PLAIN_TEXT = "PlainText"
    DEBUG_MESSAGE = "DebugMessage"
    ERROR_LOG = "ErrorLog"
    RICH_PANEL = "Panel"
    PERFORMANCE_WARNING = "PerformanceWarning"
    TOOL_RESPONSE = "ToolResponse"
    API_CALL = "ApiCall"


class LogLevel(Enum):
    """Log levels for debug messages"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class DebugMessageData:
    """Structured data for debug messages"""

    heading: str
    body: str
    level: str
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ErrorLogData:
    """Structured data for error logs"""

    error_type: str
    error_message: str
    context: str
    traceback_summary: str = ""
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class PerformanceWarningData:
    """Structured data for performance warnings"""

    operation: str
    duration: float
    threshold: float
    context: str
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ToolResponseData:
    """Structured data for tool responses"""

    tool_name: str
    status: str  # "success", "failed", "warning"
    response_summary: str
    execution_time: float = 0.0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ApiCallData:
    """Structured data for API calls"""

    api_name: str  # "OpenAI", "Ollama", "Google", etc.
    operation: str  # "chat_completion", "embedding", "search"
    status: str  # "started", "completed", "failed"
    duration: float = 0.0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class DebugMessage:
    """Main message container for JSON communication"""

    def __init__(
        self,
        obj_type,  # Can be enum or string
        data_type,  # Can be enum or string
        data: Union[str, Dict[str, Any], bytes],
        timestamp: Optional[str] = None,
    ):
        # ROBUST enum/string handling that won't be affected by IDE formatting
        self.obj_type = self._safe_enum_to_string(obj_type)
        self.data_type = self._safe_enum_to_string(data_type)
        self.data = data
        self.timestamp = timestamp or get_formatted_timestamp()

    def _safe_enum_to_string(self, value):
        """Safely convert enum to string without IDE interference"""
        if value is None:
            return ""

        # If it's already a string, return it
        if isinstance(value, str):
            return value

        # Try to get the value attribute safely
        value_attr = getattr(value, "value", None)
        if value_attr is not None:
            return value_attr

        # Fallback to string conversion
        return str(value)

    def to_json(self) -> str:
        """Convert message to JSON string for transmission"""
        message_dict = {
            "obj_type": self.obj_type,
            "data_type": self.data_type,
            "timestamp": self.timestamp,
            "data": self.data,
        }
        # Use a default serializer to handle datetimes and other non-JSON-native types.
        return json.dumps(message_dict, ensure_ascii=False, default=_default_json_serializer)

    @classmethod
    def from_json(cls, json_str: str) -> "DebugMessage":
        """Create DebugMessage from JSON string"""
        try:
            data = json.loads(json_str)
            return cls(
                obj_type=data["obj_type"],  # Already strings from JSON
                data_type=data["data_type"],  # Already strings from JSON
                data=data["data"],
                timestamp=data.get("timestamp"),
            )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise ValueError(f"Invalid debug message JSON: {e}")


class DebugMessageSender:
    """High-level interface for sending debug messages (backward compatible name)"""

    def __init__(self, socket_connection=None):
        self.socket_connection = socket_connection

    def _send_message(self, message: DebugMessage):
        """Send message through socket connection"""
        if self.socket_connection and hasattr(self.socket_connection, "send_error"):
            try:
                json_str = message.to_json()
                self.socket_connection.send_error(json_str)
            except Exception as e:
                # Fallback to simple string message - CHECK FOR None FIRST!
                if self.socket_connection and hasattr(
                    self.socket_connection, "send_error"
                ):
                    fallback_msg = f"[ERROR] Failed to send structured message: {e}"
                    self.socket_connection.send_error(fallback_msg)
                else:
                    # Ultimate fallback - suppress console output to prevent user window spam
                    # Debug messages should only go to debug window, never to user console
                    pass
        else:
            # No socket connection - suppress console output to prevent user window spam
            # print(f"[DEBUG] No socket connection available to send message: {message.to_json()}")
            # Debug messages should only go to debug window, never to user console
            pass

    def send_plain_text(self, text: str):
        """Send simple plain text message"""
        message = DebugMessage(
            obj_type=ObjectType.STRING, data_type=DataType.PLAIN_TEXT, data=text
        )
        self._send_message(message)

    def send_debug_message(
        self,
        heading: str,
        body: str,
        level: Union[LogLevel, str] = LogLevel.INFO,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Send structured debug message"""
        if isinstance(level, LogLevel):
            level = level.value

        debug_data = DebugMessageData(
            heading=heading, body=body, level=level, metadata=metadata or {}
        )

        message = DebugMessage(
            obj_type=ObjectType.STRING,
            data_type=DataType.DEBUG_MESSAGE,
            data=asdict(debug_data),
        )
        self._send_message(message)

    def send_error_log(
        self,
        error_type: str,
        error_message: str,
        context: str,
        traceback_summary: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Send structured error log"""
        error_data = ErrorLogData(
            error_type=error_type,
            error_message=error_message,
            context=context,
            traceback_summary=traceback_summary,
            metadata=metadata or {},
        )

        message = DebugMessage(
            obj_type=ObjectType.STRING,
            data_type=DataType.ERROR_LOG,
            data=asdict(error_data),
        )
        self._send_message(message)

    def send_performance_warning(
        self,
        operation: str,
        duration: float,
        threshold: float,
        context: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Send performance warning"""
        perf_data = PerformanceWarningData(
            operation=operation,
            duration=duration,
            threshold=threshold,
            context=context,
            metadata=metadata or {},
        )

        message = DebugMessage(
            obj_type=ObjectType.STRING,
            data_type=DataType.PERFORMANCE_WARNING,
            data=asdict(perf_data),
        )
        self._send_message(message)

    def send_tool_response(
        self,
        tool_name: str,
        status: str,
        response_summary: str,
        execution_time: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Send tool response information"""
        tool_data = ToolResponseData(
            tool_name=tool_name,
            status=status,
            response_summary=response_summary,
            execution_time=execution_time,
            metadata=metadata or {},
        )

        message = DebugMessage(
            obj_type=ObjectType.STRING,
            data_type=DataType.TOOL_RESPONSE,
            data=asdict(tool_data),
        )
        self._send_message(message)

    def send_api_call(
        self,
        api_name: str,
        operation: str,
        status: str,
        duration: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Send API call information"""
        api_data = ApiCallData(
            api_name=api_name,
            operation=operation,
            status=status,
            duration=duration,
            metadata=metadata or {},
        )

        message = DebugMessage(
            obj_type=ObjectType.STRING,
            data_type=DataType.API_CALL,
            data=asdict(api_data),
        )
        self._send_message(message)

    def send_rich_panel(self, panel: RenderableType):
        """Send Rich Panel object via pickle serialization"""
        try:
            # Serialize the Rich object to bytes
            panel_bytes = pickle.dumps(panel)
            # Encode as base64 for JSON transmission
            panel_b64 = base64.b64encode(panel_bytes).decode("utf-8")

            message = DebugMessage(
                obj_type=ObjectType.PICKLE,
                data_type=DataType.RICH_PANEL,
                data=panel_b64,
            )
            self._send_message(message)

        except Exception:
            # Fallback to string representation
            fallback_text = f"[RICH_PANEL] {str(panel)}"
            self.send_plain_text(fallback_text)


# Convenience functions for backward compatibility
def send_debug_message(
    socket_connection,
    heading: str,
    body: str,
    level: str = "INFO",
    metadata: Dict[str, Any] = None,
):
    """Convenience function for sending debug messages"""
    sender = DebugMessageSender(socket_connection)
    sender.send_debug_message(heading, body, level, metadata)


def send_rich_panel(socket_connection, panel: RenderableType):
    """Convenience function for sending Rich panels"""
    sender = DebugMessageSender(socket_connection)
    sender.send_rich_panel(panel)
