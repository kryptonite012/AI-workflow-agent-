"""
Debug Helper Functions for AI-Agent-Workflow Project

This module provides convenient, structured debug system_logging and message sending utilities for the AI-Agent-Workflow project.
It provides a clean, structured debug system_logging system for diagnostics, analytics, and debugging.

Features:
    - Unified debug message sending (info, warning, error, critical) with metadata support
    - Tool and API call reporting for analytics
    - Performance and error system_logging with context
    - Direct debug message printing for UI diagnostics
    - Clean debug message routing and error handling

Usage:
    # Send an info message:
    debug_info("AGENT_MODE • TOOL_EVALUATION", "Tool executed successfully", {"tool_name": "google_search"})

    # Send a warning:
    debug_warning("AGENT_MODE • TOOL_EVALUATION", "Tool failed", {"tool_name": "google_search"})

    # Print debug content directly:
    debug_rich_panel("Error content here", "Error Title")

    # Send plain text messages:
    debug_plain_text("Simple debug message")

All debug messages are routed through DebugMessageSender for clean, structured output.
"""

from __future__ import annotations

import threading
from typing import Any, Dict, Optional

from rich.console import Console

from src.config import settings
from src.ui.diagnostics.debug_message_protocol import DebugMessageSender, LogLevel

_console = Console(stderr=True, highlight=False)
_lock = threading.RLock()


def _get_debug_sender() -> DebugMessageSender:
    """Get debug message sender - always returns a sender (with or without socket)"""
    socket_con = None
    if hasattr(settings, "socket_con") and settings.socket_con:
        socket_con = settings.socket_con
    return DebugMessageSender(socket_con)


# Removed _safe_emit and _guard_key functions - they were part of panel sending system


def debug_info(heading: str, body: str, metadata: Optional[Dict[str, Any]] = None):
    """Send INFO level debug message"""
    sender = _get_debug_sender()
    sender.send_debug_message(heading, body, LogLevel.INFO, metadata)


def debug_warning(heading: str, body: str, metadata: Optional[Dict[str, Any]] = None):
    """Send WARNING level debug message"""
    sender = _get_debug_sender()
    sender.send_debug_message(heading, body, LogLevel.WARNING, metadata)


def debug_error(heading: str, body: str, metadata: Optional[Dict[str, Any]] = None):
    """Send ERROR level debug message"""
    sender = _get_debug_sender()
    sender.send_debug_message(heading, body, LogLevel.ERROR, metadata)


def debug_critical(heading: str, body: str, metadata: Optional[Dict[str, Any]] = None):
    """Send CRITICAL level debug message"""
    sender = _get_debug_sender()
    sender.send_debug_message(heading, body, LogLevel.CRITICAL, metadata)


def debug_tool_response(
    tool_name: str,
    status: str,
    response_summary: str,
    execution_time: float = 0.0,
    metadata: Optional[Dict[str, Any]] = None,
):
    """Send tool response information"""
    sender = _get_debug_sender()
    sender.send_tool_response(
        tool_name, status, response_summary, execution_time, metadata
    )


def debug_api_call(
    api_name: str,
    operation: str,
    status: str,
    duration: float = 0.0,
    metadata: Optional[Dict[str, Any]] = None,
):
    """Send API call information"""
    sender = _get_debug_sender()
    sender.send_api_call(api_name, operation, status, duration, metadata)


def debug_performance_warning(
    operation: str,
    duration: float,
    threshold: float,
    context: str,
    metadata: Optional[Dict[str, Any]] = None,
):
    """Send performance warning"""
    sender = _get_debug_sender()
    sender.send_performance_warning(operation, duration, threshold, context, metadata)


def debug_error_log(
    error_type: str,
    error_message: str,
    context: str,
    traceback_summary: str = "",
    metadata: Optional[Dict[str, Any]] = None,
):
    """Send structured error log"""
    sender = _get_debug_sender()
    sender.send_error_log(
        error_type, error_message, context, traceback_summary, metadata
    )


def debug_rich_panel(panel_content: str, title: str = "Debug Panel"):
    """
    REMOVED: Panel sending functionality. Now prints error content directly.

    Args:
        panel_content: The content that would have been in the panel
        title: The title for the debug message
    """
    print(f"[DEBUG {title}] {panel_content}")


def send_object_over_socket(obj: Any, obj_type: str = "object"):
    """
    REMOVED: Object sending functionality. Now prints content directly.

    Args:
        obj: The object content to print
        obj_type: Type identifier for the debug message
    """
    if isinstance(obj, dict):
        heading = obj.get("heading", "OBJECT")
        body = obj.get("body", str(obj))
        print(f"[DEBUG {obj_type}] {heading}: {body}")
    elif isinstance(obj, str):
        print(f"[DEBUG {obj_type}] {obj}")
    else:
        print(f"[DEBUG {obj_type}] {str(obj)}")


# Removed safe_socket_send - legacy support eliminated


def debug_plain_text(text: str):
    """Send plain text message (for simple cases)"""
    sender = _get_debug_sender()
    sender.send_plain_text(text)


# Removed safe_send_error - legacy support eliminated


# Removed send_debug_message_legacy - legacy support eliminated


# Removed SafeSocketConnection class and ensure_safe_socket_con - legacy support eliminated
