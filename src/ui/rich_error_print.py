"""
Enhanced Rich Error Print for AI-Agent-Workflow Project

This module handles the new JSON-based debug message protocol and provides
beautiful, contextual display of debug information in the debug console.

Features:
- JSON message protocol parsing
- Context-aware panel styling
- Rich object deserialization
- Enhanced visual organization
- Metadata display for debugging

Usage:
    This is used automatically by the debug console process (error_transfer.py)
"""

import base64
import json
import pickle
from datetime import datetime
from typing import Dict, Any

from rich.align import Align
from rich.box import ROUNDED, DOUBLE, HEAVY
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text

from src.ui.diagnostics.debug_message_protocol import DebugMessage, ObjectType, DataType


class RichErrorPrint:
    """Enhanced debug message display with JSON protocol support"""

    def __init__(self, debug_console: Console = None):
        if debug_console is None:
            # Enhanced console configuration for debug process
            self.console = Console(
                force_terminal=True,
                color_system="windows",
                width=150,  # Even wider for better structured display
                legacy_windows=False,
                safe_box=True,
                highlight=True,
                emoji=True,
                markup=True,
                log_time=False,  # We handle timestamps in messages
                log_path=False,
            )
        else:
            self.console = debug_console
            self.console.force_terminal = True
            self.console.safe_box = True

        # Initialize Rich Traceback for debug process
        from src.ui.diagnostics.rich_traceback_manager import RichTracebackManager

        RichTracebackManager.initialize_debug_process(
            debug_console=self.console,
            show_locals=False,
            max_frames=10,
            theme="monokai",
            extra_lines=1,
            suppress_modules=[
                "click",
                "rich",
                "__main__",
                "runpy",
                "threading",
                "socket",
                "pickle",
            ],
        )

    def print_rich(self, message: str):
        """
        Main entry point for processing debug messages.
        Handles both new JSON protocol and legacy string messages.
        Can handle multiple concatenated JSON messages in one transmission.
        """
        try:
            # Check if this might be multiple concatenated JSON messages
            if self._is_multiple_json_messages(message):
                self._handle_multiple_json_messages(message)
            elif self._is_json_message(message):
                self._handle_json_message(message)
            else:
                # Fallback to legacy string handling
                self._handle_legacy_message(message)

        except Exception as e:
            # Ultimate fallback for any parsing errors
            self._handle_parse_error(message, str(e))

    def _is_json_message(self, message: str) -> bool:
        """Check if message is a valid JSON debug message"""
        try:
            data = json.loads(message)
            return isinstance(data, dict) and "obj_type" in data and "data_type" in data
        except (json.JSONDecodeError, TypeError):
            return False

    def _is_multiple_json_messages(self, message: str) -> bool:
        """Check if message contains multiple concatenated JSON objects"""
        try:
            # Quick check: if it starts with { and has }{ pattern, it's likely multiple JSON
            if message.startswith("{") and "}{" in message:
                return True
            return False
        except Exception:
            return False

    def _handle_multiple_json_messages(self, message: str):
        """Handle multiple concatenated JSON messages"""
        try:
            # Split the message into individual JSON objects
            json_messages = self._split_json_messages(message)

            # Process each JSON message individually
            for json_msg in json_messages:
                if json_msg.strip():  # Skip empty messages
                    self._handle_json_message(json_msg)

        except Exception as e:
            self._handle_parse_error(message, f"Multiple JSON parsing error: {e}")

    def _split_json_messages(self, message: str) -> list:
        """Split concatenated JSON messages into individual JSON strings"""
        json_messages = []
        current_message = ""
        brace_count = 0
        in_string = False
        escape_next = False

        for char in message:
            current_message += char

            if escape_next:
                escape_next = False
                continue

            if char == "\\":
                escape_next = True
                continue

            if char == '"' and not escape_next:
                in_string = not in_string
                continue

            if not in_string:
                if char == "{":
                    brace_count += 1
                elif char == "}":
                    brace_count -= 1

                    # When brace_count reaches 0, we have a complete JSON object
                    if brace_count == 0:
                        json_messages.append(current_message.strip())
                        current_message = ""

        # Add any remaining message
        if current_message.strip():
            json_messages.append(current_message.strip())

        return json_messages

    def _handle_json_message(self, message: str):
        """Handle new JSON protocol messages"""
        try:
            debug_msg = DebugMessage.from_json(message)

            if debug_msg.obj_type == ObjectType.STRING.value:
                self._handle_string_message(debug_msg)
            elif debug_msg.obj_type == ObjectType.PICKLE.value:
                self._handle_pickle_message(debug_msg)
            else:
                self._handle_unknown_message(debug_msg)

        except Exception as e:
            self._handle_parse_error(message, f"JSON parsing error: {e}")

    def _handle_string_message(self, debug_msg: DebugMessage):
        """Handle string-based structured messages"""
        data_type = debug_msg.data_type
        timestamp = self._format_timestamp(debug_msg.timestamp)

        if data_type == DataType.PLAIN_TEXT.value:
            self._display_plain_text(debug_msg.data, timestamp)

        elif data_type == DataType.DEBUG_MESSAGE.value:
            self._display_debug_message(debug_msg.data, timestamp)

        elif data_type == DataType.ERROR_LOG.value:
            self._display_error_log(debug_msg.data, timestamp)

        elif data_type == DataType.PERFORMANCE_WARNING.value:
            self._display_performance_warning(debug_msg.data, timestamp)

        elif data_type == DataType.TOOL_RESPONSE.value:
            self._display_tool_response(debug_msg.data, timestamp)

        elif data_type == DataType.API_CALL.value:
            self._display_api_call(debug_msg.data, timestamp)

        else:
            self._display_unknown_data_type(debug_msg.data, data_type, timestamp)

    def _handle_pickle_message(self, debug_msg: DebugMessage):
        """Handle pickled object messages"""
        data_type = debug_msg.data_type
        timestamp = self._format_timestamp(debug_msg.timestamp)

        if data_type == DataType.RICH_PANEL.value:
            self._display_rich_panel(debug_msg.data, timestamp)
        else:
            self._display_unknown_pickle(debug_msg.data, data_type, timestamp)

    def _display_plain_text(self, data: str, timestamp: str):
        """Display simple plain text message"""
        title = Text("💬 MESSAGE", style="bold bright_cyan")
        title.append(f" • {timestamp}", style="dim cyan")

        panel = Panel(
            Align.left(data),
            title=title,
            border_style="bright_cyan",
            box=ROUNDED,
            padding=(0, 1),
            width=148,
        )
        self.console.print(panel)

    def _display_debug_message(self, data: Dict[str, Any], timestamp: str):
        """Display structured debug message with enhanced formatting"""
        heading = data.get("heading", "DEBUG")
        body = data.get("body", "")
        level = data.get("level", "INFO")
        metadata = data.get("metadata", {})

        # Choose styling based on level
        level_styles = {
            "DEBUG": ("🔍", "bright_blue", "blue"),
            "INFO": ("ℹ️", "bright_green", "green"),
            "WARNING": ("⚠️", "bright_yellow", "yellow"),
            "ERROR": ("🚨", "bright_red", "red"),
            "CRITICAL": ("💥", "bright_white", "red"),
        }

        icon, title_style, border_style = level_styles.get(
            level, ("📝", "bright_white", "white")
        )

        # Create title with context
        title = Text(f"{icon} {heading}", style=f"bold {title_style}")
        title.append(f" • {timestamp}", style=f"dim {title_style}")

        # Create content with metadata if present
        content_parts = [body]

        if metadata:
            content_parts.append("")  # Empty line
            content_parts.append("📋 Metadata:")
            for key, value in metadata.items():
                content_parts.append(f"   • {key}: {value}")

        content = "\n".join(content_parts)

        panel = Panel(
            Align.left(content),
            title=title,
            border_style=border_style,
            box=HEAVY if level in ["ERROR", "CRITICAL"] else ROUNDED,
            padding=(0, 1),
            width=148,
        )

        # Add separator for errors and critical messages
        if level in ["ERROR", "CRITICAL"]:
            self.console.print(Rule(style=border_style))

        self.console.print(panel)

        if level in ["ERROR", "CRITICAL"]:
            self.console.print(Rule(style=border_style))

    def _display_error_log(self, data: Dict[str, Any], timestamp: str):
        """Display structured error log"""
        error_type = data.get("error_type", "Unknown")
        error_message = data.get("error_message", "")
        context = data.get("context", "")
        traceback_summary = data.get("traceback_summary", "")
        metadata = data.get("metadata", {})

        title = Text(f"🚨 ERROR LOG • {error_type}", style="bold bright_red")
        title.append(f" • {timestamp}", style="dim red")

        content_parts = [f"📍 Context: {context}", f"💬 Message: {error_message}"]

        if traceback_summary:
            content_parts.extend(["", "📚 Traceback:", traceback_summary])

        if metadata:
            content_parts.extend(["", "📋 Metadata:"])
            for key, value in metadata.items():
                content_parts.append(f"   • {key}: {value}")

        content = "\n".join(content_parts)

        self.console.print(Rule("🚨 ERROR LOG", style="bold red"))
        panel = Panel(
            Align.left(content),
            title=title,
            border_style="bright_red",
            box=HEAVY,
            padding=(1, 1),
            width=148,
        )
        self.console.print(panel)
        self.console.print(Rule(style="red"))

    def _display_performance_warning(self, data: Dict[str, Any], timestamp: str):
        """Display performance warning with timing details"""
        operation = data.get("operation", "Unknown")
        duration = data.get("duration", 0.0)
        threshold = data.get("threshold", 0.0)
        context = data.get("context", "")
        metadata = data.get("metadata", {})

        title = Text(f"🐌 PERFORMANCE • {operation}", style="bold bright_yellow")
        title.append(f" • {timestamp}", style="dim yellow")

        content_parts = [
            f"⏱️  Duration: {duration:.2f}s (threshold: {threshold:.2f}s)",
            f"📍 Context: {context}",
            f"⚡ Exceeded by: {duration - threshold:.2f}s",
        ]

        if metadata:
            content_parts.extend(["", "📋 Metadata:"])
            for key, value in metadata.items():
                content_parts.append(f"   • {key}: {value}")

        content = "\n".join(content_parts)

        panel = Panel(
            Align.left(content),
            title=title,
            border_style="bright_yellow",
            box=ROUNDED,
            padding=(0, 1),
            width=148,
        )
        self.console.print(panel)

    def _display_tool_response(self, data: Dict[str, Any], timestamp: str):
        """Display tool response information"""
        tool_name = data.get("tool_name", "Unknown")
        status = data.get("status", "unknown")
        response_summary = data.get("response_summary", "")
        execution_time = data.get("execution_time", 0.0)
        metadata = data.get("metadata", {})

        # Choose styling based on status
        status_styles = {
            "success": ("✅", "bright_green", "green"),
            "failed": ("❌", "bright_red", "red"),
            "warning": ("⚠️", "bright_yellow", "yellow"),
        }

        icon, title_style, border_style = status_styles.get(
            status, ("🔧", "bright_cyan", "cyan")
        )

        title = Text(f"{icon} TOOL • {tool_name}", style=f"bold {title_style}")
        title.append(f" • {timestamp}", style=f"dim {title_style}")

        content_parts = [
            f"📊 Status: {status.upper()}",
            f"📝 Response: {response_summary}",
        ]

        if execution_time > 0:
            content_parts.append(f"⏱️  Execution Time: {execution_time:.2f}s")

        if metadata:
            content_parts.extend(["", "📋 Metadata:"])
            for key, value in metadata.items():
                content_parts.append(f"   • {key}: {value}")

        content = "\n".join(content_parts)

        panel = Panel(
            Align.left(content),
            title=title,
            border_style=border_style,
            box=ROUNDED,
            padding=(0, 1),
            width=148,
        )
        self.console.print(panel)

    def _display_api_call(self, data: Dict[str, Any], timestamp: str):
        """Display API call information"""
        api_name = data.get("api_name", "Unknown")
        operation = data.get("operation", "")
        status = data.get("status", "unknown")
        duration = data.get("duration", 0.0)
        metadata = data.get("metadata", {})

        # Choose styling based on status
        status_styles = {
            "started": ("🚀", "bright_blue", "blue"),
            "completed": ("✅", "bright_green", "green"),
            "failed": ("❌", "bright_red", "red"),
        }

        icon, title_style, border_style = status_styles.get(
            status, ("🌐", "bright_cyan", "cyan")
        )

        title = Text(
            f"{icon} API • {api_name} • {operation}", style=f"bold {title_style}"
        )
        title.append(f" • {timestamp}", style=f"dim {title_style}")

        content_parts = [f"📊 Status: {status.upper()}"]

        if duration > 0:
            content_parts.append(f"⏱️  Duration: {duration:.2f}s")

        if metadata:
            content_parts.extend(["", "📋 Metadata:"])
            for key, value in metadata.items():
                content_parts.append(f"   • {key}: {value}")

        content = "\n".join(content_parts)

        panel = Panel(
            Align.left(content),
            title=title,
            border_style=border_style,
            box=ROUNDED,
            padding=(0, 1),
            width=148,
        )
        self.console.print(panel)

    def _display_rich_panel(self, data: str, timestamp: str):
        """Display deserialized Rich Panel object"""
        try:
            # Deserialize the panel
            panel_bytes = base64.b64decode(data)
            panel_object = pickle.loads(panel_bytes)

            # Add visual separator for Rich panels
            self.console.print()
            self.console.print(
                Rule(f"🎨 RICH PANEL • {timestamp}", style="bold magenta")
            )

            # Display the panel
            self.console.print(panel_object)

            # Add closing separator
            self.console.print(Rule(style="magenta"))
            self.console.print()

        except Exception as e:
            self._display_deserialization_error(data, str(e), timestamp)

    def _display_deserialization_error(self, data: str, error: str, timestamp: str):
        """Display error when panel deserialization fails"""
        title = Text("❌ DESERIALIZATION ERROR", style="bold bright_red")
        title.append(f" • {timestamp}", style="dim red")

        content = f"Failed to deserialize Rich Panel: {error}\nData length: {len(data)} characters"

        panel = Panel(
            Align.left(content),
            title=title,
            border_style="bright_red",
            box=HEAVY,
            padding=(0, 1),
            width=148,
        )
        self.console.print(panel)

    def _handle_legacy_message(self, message: str):
        """Handle legacy string messages (backward compatibility)"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Check for legacy prefixes
        if "[debug]" in message.lower():
            self._display_plain_text(message.replace("[debug]", "").strip(), timestamp)
        elif "[info]" in message.lower():
            self._display_plain_text(message.replace("[info]", "").strip(), timestamp)
        elif "[warning]" in message.lower():
            self._display_plain_text(
                message.replace("[warning]", "").strip(), timestamp
            )
        elif "[error]" in message.lower():
            self._display_plain_text(message.replace("[error]", "").strip(), timestamp)
        elif "critical" in message.lower():
            self._display_plain_text(message.replace("critical", "").strip(), timestamp)
        else:
            self._display_plain_text(message, timestamp)

    def _handle_parse_error(self, message: str, error: str):
        """Handle message parsing errors"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        title = Text("⚠️ PARSE ERROR", style="bold bright_yellow")
        title.append(f" • {timestamp}", style="dim yellow")

        content = f"Failed to parse message: {error}\n\nRaw message:\n{message}{'...' if len(message) > 200 else ''}"

        panel = Panel(
            Align.left(content),
            title=title,
            border_style="bright_yellow",
            box=ROUNDED,
            padding=(0, 1),
            width=148,
        )
        self.console.print(panel)

    def _format_timestamp(self, timestamp_str: str) -> str:
        """Format timestamp for display"""
        try:
            # Parse ISO format timestamp
            dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            return dt.strftime("%H:%M:%S")
        except (ValueError, AttributeError):
            # Fallback to current time
            return datetime.now().strftime("%H:%M:%S")

    def _display_unknown_data_type(self, data: Any, data_type: str, timestamp: str):
        """Display unknown data type"""
        title = Text(f"❓ UNKNOWN TYPE • {data_type}", style="bold bright_magenta")
        title.append(f" • {timestamp}", style="dim magenta")

        content = f"Unknown data type: {data_type}\nData: {str(data)[:200]}{'...' if len(str(data)) > 200 else ''}"

        panel = Panel(
            Align.left(content),
            title=title,
            border_style="bright_magenta",
            box=ROUNDED,
            padding=(0, 1),
            width=148,
        )
        self.console.print(panel)

    def _display_unknown_pickle(self, data: str, data_type: str, timestamp: str):
        """Display unknown pickle type"""
        title = Text(f"❓ UNKNOWN PICKLE • {data_type}", style="bold bright_magenta")
        title.append(f" • {timestamp}", style="dim magenta")

        content = (
            f"Unknown pickle type: {data_type}\nData length: {len(data)} characters"
        )

        panel = Panel(
            Align.left(content),
            title=title,
            border_style="bright_magenta",
            box=ROUNDED,
            padding=(0, 1),
            width=148,
        )
        self.console.print(panel)

    def print_startup_banner(self):
        """Print enhanced startup banner"""
        banner_text = Text(
            "🚀 AI-AGENT DEBUG CONSOLE v2.0", style="bold bright_magenta"
        )
        subtitle_text = Text(
            "Enhanced JSON Protocol • Structured Debugging", style="dim bright_magenta"
        )

        banner_panel = Panel(
            Align.center(f"{banner_text}\n{subtitle_text}"),
            box=DOUBLE,
            border_style="bright_magenta",
            padding=(1, 2),
            width=148,
        )

        self.console.print(Rule("🎯 DEBUG SESSION STARTED", style="bright_magenta"))
        self.console.print(banner_panel)
        self.console.print(Rule(style="bright_magenta"))
        self.console.print()

    def print_separator(self, text: str = "", style: str = "dim white"):
        """Print visual separator"""
        self.console.print(Rule(text, style=style))

    def print_section_header(self, title: str, style: str = "bold bright_white"):
        """Print section header"""
        header_text = Text(f"📋 {title.upper()}", style=style)
        self.console.print()
        self.console.print(Rule(style="dim"))
        self.console.print(Align.center(header_text))
        self.console.print(Rule(style="dim"))

    def _handle_unknown_message(self, debug_msg: DebugMessage):
        """Handle unknown message types"""
        timestamp = self._format_timestamp(debug_msg.timestamp)

        title = Text("❓ UNKNOWN MESSAGE TYPE", style="bold bright_magenta")
        title.append(f" • {timestamp}", style="dim magenta")

        content = f"Unknown object type: {debug_msg.obj_type}\nData type: {debug_msg.data_type}\nData: {str(debug_msg.data)[:200]}{'...' if len(str(debug_msg.data)) > 200 else ''}"

        panel = Panel(
            Align.left(content),
            title=title,
            border_style="bright_magenta",
            box=ROUNDED,
            padding=(0, 1),
            width=148,
        )
        self.console.print(panel)
