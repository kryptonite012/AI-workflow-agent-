"""
Module: run_shell_command_tool

This module provides functionality to run shell commands from a tool agent or agentic node.
It is intended to be used as part of the lggraph_tools package.

Typical usage:
    - Execute shell commands programmatically.
    - Capture output and errors from shell commands.
    - Integrate shell command execution into agent workflows.

Dependencies:
    - Python standard library (e.g., subprocess)

Author: PIRATE-E
"""

### progress --- schema is not created, yet we are writing the code first of some basic functionality of run shell command tool


def run_shell_command(command: str, creation_flag=False) -> str:
    """
    Run a shell command and return its output.

    Args:
        command (str): The shell command to run.
        creation_flag (bool): If True, the command will be run in a new console window.
                              If False, it will run in the current console.

    Returns:
        str: The output of the command.
    """
    import subprocess

    try:
        # Run the command using subprocess.Popen with proper encoding handling
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",  # ✅ Explicit UTF-8 encoding
            errors="replace",  # ✅ Replace problematic characters instead of failing
            creationflags=subprocess.CREATE_NEW_CONSOLE if creation_flag else 0,
        )
        stdout, stderr = process.communicate()

        # ✅ Safe handling of None values
        if process.returncode == 0:
            return (stdout or "").strip() or "Command executed successfully (no output)"
        else:
            error_msg = (stderr or "").strip() or "Unknown error occurred"
            return f"Error (code {process.returncode}): {error_msg}"

    except subprocess.CalledProcessError as e:
        # ✅ Safe handling of stderr
        error_msg = getattr(e, "stderr", None)
        if error_msg:
            return f"CalledProcessError: {error_msg.strip()}"
        else:
            return f"CalledProcessError: Command failed with return code {e.returncode}"
    except Exception as e:
        # ✅ Catch any other subprocess errors
        return f"Subprocess Error: {str(e)}"
