"""Agent Node for LangGraph Workflow

This module defines the agent_node function which implements the core agent node logic for the LangGraph workflow system
using the new hierarchical AgentGraphCore system.

Features:
    - Complete integration with AgentGraphCore for all agent operations
    - Robust error handling and debug system_logging
    - Full support for complex task decomposition and execution
    - Designed for extensibility and integration with LangGraph

Usage:
    # To use the agent node in a workflow:
    from src.agents.agent_mode_node import agent_node
    result = agent_node(state)
"""

import re
import sys
import unicodedata

# 🔄 HIERARCHICAL AGENT INTEGRATION: Import AgentGraphCore for complex workflows
from src.agents.agentic_orchestrator.AgentGraphCore import (
    AgentGraphCore,
)
from src.config import settings
# 🚀 Debug System
from src.ui.diagnostics.debug_helpers import (
    debug_critical,
    debug_info, debug_error,
)
# 🎨 Rich Traceback Integration
from src.ui.diagnostics.rich_traceback_manager import (
    RichTracebackManager,
    rich_exception_handler,
)


def normalize_utf8_text(text: str) -> str:
    """Normalize UTF-8 text to fix encoding issues and mojibake.
    
    Args:
        text (str): Text that may have encoding issues
        
    Returns:
        str: Properly encoded UTF-8 text
    """
    if not isinstance(text, str):
        text = str(text)
    
    try:
        # Normalize Unicode to fix composition issues
        text = unicodedata.normalize("NFKC", text)
        
        # Ensure proper UTF-8 encoding
        text = text.encode("utf-8", "replace").decode("utf-8")
        
        return text
    except Exception as e:
        debug_info("UTF8_NORMALIZATION", f"Failed to normalize text: {e}", metadata={
            "original_length": len(text),
            "error_type": type(e).__name__
        })
        return text


def formated_final_response(create_display_response: str) -> str:
    """Formats the final response string for display, handling Windows paths and Unicode decoding issues.

    Args:
        create_display_response (str): The response string to format.

    Returns:
        str: The formatted response string.

    """
    # Normalize UTF-8 first to fix encoding issues
    create_display_response = normalize_utf8_text(create_display_response)
    
    # Escape Windows paths
    if re.search(r"[A-Za-z]:\\", create_display_response):
        create_display_response = create_display_response.replace("\\", "\\\\")
    # If actual escape sequences are present, decode them
    if re.search(r"\\u[0-9a-fA-F]{4}|\\n|\\t|\\r", create_display_response):
        try:
            create_display_response = bytes(create_display_response, "utf-8").decode(
                "unicode_escape",
            )
        except Exception:
            pass  # Fallback: show as-is
    # Return the formatted string
    return create_display_response


@rich_exception_handler("Agent Node Processing")
def agent_node(state):
    from src.ui.print_message_style import print_message

    """
    Agent node that handles messages requiring agent-like behavior using the new AgentGraphCore system.
    This node processes the latest message and determines which tools to invoke or if it should respond as an agent.
    """

    try:
        # Ensure UTF-8 encoding for stdout at startup
        try:
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass  # Ignore if reconfigure is not available

        console = settings.console
        console.print("\t\t----Node is agent_node")

        # Access state directly from LangGraph parameter (no sync needed)
        messages = state.get("messages", [])
        last_message = messages[-1].content if messages else "No messages available"

        debug_info(
            heading="AGENT_MODE • HIERARCHICAL_EXECUTION",
            body="Routing request to AgentGraphCore hierarchical system",
            metadata={
                "user_request_length": len(last_message),
                "conversation_length": len(messages),
                "execution_mode": "hierarchical",
                "context": "hierarchical_workflow_start",
            },
        )

        # Create initial state for AgentGraphCore workflow
        # This is a self-contained state that only includes what the AgentGraphCore needs
        initial_state = {
            "tasks": [],
            "current_task_id": 0,
            "executed_nodes": [],
            "original_goal": last_message,
            "persona": None,
            "workflow_status": "STARTED",
        }

        # Build and execute hierarchical graph
        debug_info(
            heading="AGENT_MODE • HIERARCHICAL_GRAPH_BUILD",
            body="Building AgentGraphCore workflow graph",
            metadata={
                "original_goal": last_message,
                "context": "hierarchical_graph_execution",
            },
        )
        from src.utils.listeners.rich_status_listen import RichStatusListener
        rich_evaluation_listener = RichStatusListener(settings.console)
        rich_evaluation_listener.start_status('Evaluating workflow quality with simplified structure...',
                                              spinner='dots')
        settings.listeners['eval'] = rich_evaluation_listener  # Register listener for evaluation status updates

        # Execute the AgentGraphCore workflow
        # Ensure these are defined so they are available even if graph invocation fails
        workflow_status = "UNKNOWN"
        final_response = None
        final_state = None

        try:
            graph = AgentGraphCore.build_graph()
            # Correct way to set recursion limit in LangGraph
            final_state = graph.invoke(initial_state, config={"recursion_limit": settings.recursion_limit})

            # Debug: Log the complete final_state structure
            debug_info(
                heading="AGENT_MODE • FINAL_STATE_DEBUG",
                body="Complete final_state structure received from graph",
                metadata={
                    "final_state_keys": list(final_state.keys()) if isinstance(final_state, dict) else "Not a dict",
                    "final_state_type": type(final_state).__name__,
                    "final_state_preview": str(final_state) if final_state else "None",
                    "context": "final_state_extraction"
                }
            )

            # Extract results with better error handling
            workflow_status = final_state.get("workflow_status", "UNKNOWN")
            final_response = final_state.get("final_response", None)

            # Use final_response from graph as-is. No local fallback extraction is performed.

            debug_info(
                heading="AGENT_MODE • HIERARCHICAL_COMPLETION",
                body=f"Hierarchical workflow completed with status: {workflow_status}",
                metadata={
                    "workflow_status": workflow_status,
                    "response_length": len(str(final_response)) if final_response is not None else 0,
                    "success": workflow_status == "COMPLETED",
                    "context": "hierarchical_workflow_completion",
                    "final_response_type": type(final_response).__name__ if final_response else "None"
                },
            )

        except Exception as workflow_error:
            debug_error(
                heading="AGENT_MODE • HIERARCHICAL_WORKFLOW_ERROR",
                body=f"AgentGraphCore workflow failed: {workflow_error!s}",
                metadata={
                    "error_type": type(workflow_error).__name__,
                    "context": "hierarchical_workflow_error",
                },
            )
            # Provide fallback response
            final_response = {
                "user_response": {
                    "message": f"I encountered an error while processing your complex request: {workflow_error!s}. Please try a simpler request or rephrase your question.",
                    "next_steps": "Try rephrasing your request or breaking it into smaller parts."
                },
                "analysis": {
                    "issues": f"Workflow error: {workflow_error!s}",
                    "reason": "Exception during graph execution"
                }
            }

        # Handle workflow failure: log critical info but do NOT overwrite the final_response provided by the LLM.
        if "workflow_status" in locals() and workflow_status != "COMPLETED":
            error_msg = f"Hierarchical workflow failed with status: {workflow_status}"
            debug_critical(
                heading="AGENT_MODE • HIERARCHICAL_ERROR",
                body=error_msg,
                metadata={
                    "workflow_status": workflow_status,
                    "context": "hierarchical_execution_error",
                },
            )
            # Do not synthesize or overwrite final_response here; rely on graph-provided final_response.

        # Try to extract a human-friendly message from structured final_response
        display_text = "No response generated from workflow."
        try:
            import json as _json
            response_data = final_response

            # If the response is a JSON string, parse it into a dictionary.
            if isinstance(response_data, str):
                try:
                    response_data = _json.loads(response_data)
                except _json.JSONDecodeError:
                    # It's just a raw string, not JSON. Use it directly.
                    display_text = response_data

            # If we have a dictionary, extract the message or pretty-print.
            if isinstance(response_data, dict):
                # Primary path: extract the specific user-facing message.
                message = response_data.get("user_response", {}).get("message")
                if message and isinstance(message, str) and message.strip():
                    display_text = message
                else:
                    # Show the LLM-provided dict as pretty JSON (do not replace with internal fallbacks).
                    display_text = _json.dumps(response_data, indent=2, ensure_ascii=False)

            # If LLM didn't provide anything, show a short explicit message rather than synthesizing task output.
            if not isinstance(display_text, str) or not display_text.strip():
                display_text = "No response generated from LLM."

        except Exception as e:
            debug_error("AGENT_MODE • FINAL_RESPONSE_EXTRACTION_ERROR", f"Error during response extraction: {e}", metadata={
                "raw_response": str(final_response),
                "response_type": type(final_response).__name__,
                "error_type": type(e).__name__
            })
            display_text = f"An error occurred while formatting the final response. Raw response: {final_response}"

        # Format the display text and print it
        try:
            display_text = formated_final_response(display_text or "No response generated from workflow.")
        except Exception as format_error:
            debug_info(
                heading="AGENT_MODE • RESPONSE_FORMATTING_ERROR",
                body=f"Failed to format display text: {format_error!s}",
                metadata={
                    "error_type": type(format_error).__name__,
                    "context": "response_formatting",
                },
            )

        # Log both the user-facing text and the raw normalized final_response for debugging
        debug_info("AGENT_MODE • FINAL_RESPONSE_DELIVER", f"Delivering final response to user", metadata={
            "function name": "agent_node",
            "display_preview": (display_text or "")[:400],
            "raw_preview": (str(final_response) or "")[:400],
        })

        print_message(display_text, "ai")
        # Stop the rich status listener
        if 'rich_evaluation_listener' in locals():
            rich_evaluation_listener.stop_status_display()
        # Return the user-facing message to the caller, but keep the raw final_response available if needed
        return {"messages": [settings.AIMessage(content=display_text)], "final_response_raw": final_response}

    except Exception as e:
        RichTracebackManager.handle_exception(
            e,
            context="Agent Node Processing",
            extra_context={
                "state_keys": list(state.keys()) if isinstance(state, dict) else "N/A",
                "messages_count": len(state.get("messages", []))
                if isinstance(state, dict)
                else "N/A",
            },
        )
        # Provide a fallback response in case of critical failure
        fallback_response = "I encountered an unexpected error while processing your request. Please try rephrasing or breaking down your request into smaller steps."
        print_message(fallback_response, "ai")
        return {"messages": [settings.AIMessage(content=fallback_response)]}
