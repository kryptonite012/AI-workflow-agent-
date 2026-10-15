import os
import sys
import pathlib

# Add project root to Python path
project_root = pathlib.Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 🎨 Initialize Rich Traceback for MAIN PROCESS (display happens in debug console)
from src.ui.diagnostics.rich_traceback_manager import (
    RichTracebackManager,
    rich_exception_handler,
)

# ✅ Handle Sentry encoding issues without disabling error monitoring
try:
    import sentry_sdk  # type: ignore
    from sentry_sdk.integrations.threading import ThreadingIntegration  # type: ignore

    sentry_sdk.init()
except ImportError:  # Sentry optional; suppress noise
    sentry_sdk = None  # type: ignore
except Exception:
    # Silently ignore other Sentry initialization failures
    sentry_sdk = None  # type: ignore

RichTracebackManager.initialize(
    show_locals=False,  # Disabled for main process - display in debug console
    max_frames=10,
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

from src.core.chat_destructor import ChatDestructor
from src.utils.socket_manager import SocketManager

import gc
from rich.align import Align

from src.core.chat_initializer import ChatInitializer
from src.config import settings
from src.core.graphs.node_assign import GraphBuilder
from src.models.state import State
from src.ui.print_banner import print_banner
from src.utils.model_manager import ModelManager
from src.mcp.manager import MCP_Manager
from src.utils.argument_schema_util import get_tool_argument_schema
from src.tools.lggraph_tools.tools.browser_tool import BrowserHandler


@rich_exception_handler("Main Chat Application")
def run_chat(destructor: ChatDestructor):
    """Run the chat application."""
    try:
        chat = ChatInitializer()
        graph = GraphBuilder(State).compile_graph()
        chat.set_graph(graph).tools_register().set_exit(
            destructor.call_all_cleanup_functions
        )
        settings.chat = chat  # Set global chat reference

        os.system("cls" if os.name == "nt" else "clear")  # Clear console
        print_banner()
        console = settings.console or __import__("rich").console.Console()
        settings.console = console

        console.print(
            Align.center("[bold blue]Welcome to the LangGraph Chatbot![/bold blue]")
        )
        console.print(
            Align.center("Type '[bold red]exit[/bold red]' to end the conversation.\n")
        )

        from rich.table import Table

        table = Table(title="Registered Tools", border_style="blue", show_lines=True)
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Description", style="magenta")
        table.add_column("Arguments", style="green")

        for tool in chat.tools or []:
            try:
                name = getattr(tool, "name", "N/A")
                desc = getattr(tool, "description", "N/A")
                args = get_tool_argument_schema(tool)
                table.add_row(str(name), str(desc), str(args))
            except Exception as tool_error:
                RichTracebackManager.handle_exception(
                    tool_error,
                    context=f"Tool Registration Display - {getattr(tool, 'name', 'Unknown Tool')}",
                )
                table.add_row("ERROR", "Failed to load tool", "N/A")

        console.print(table)

        try:
            while not chat.break_loop:
                try:
                    chat.run_chat()
                    gc.collect()
                except Exception as chat_error:
                    RichTracebackManager.handle_exception(
                        chat_error,
                        context="Chat Loop Execution",
                        extra_context={"break_loop": chat.break_loop},
                    )
                    if isinstance(chat_error, (KeyboardInterrupt, SystemExit)):
                        raise
        except (KeyboardInterrupt, SystemExit):
            console.print("[bold red]Chat ended. Goodbye![/bold red]")
        finally:
            console.print("[dim]Exiting chat application...[/dim]")
    except Exception as init_error:
        RichTracebackManager.handle_exception(
            init_error,
            context="Chat Application Initialization",
            extra_context={"phase": "startup"},
        )
        raise


if __name__ == "__main__":
    try:
        destructor = ChatDestructor()
        destructor.add_destroyer_function(SocketManager.cleanup)
        destructor.add_destroyer_function(ModelManager.cleanup_all_models)
        destructor.add_destroyer_function(MCP_Manager.cleanup)
        destructor.add_destroyer_function(BrowserHandler.clear_all_processes)

        destructor.register_cleanup_handlers()
        run_chat(destructor)
    except Exception as e:  # pragma: no cover
        console = settings.console
        if console:
            console.print(f"[bold red]Unexpected error: {e}[/bold red]")
        else:
            print(f"Unexpected error: {e}")
    finally:
        gc.collect()
