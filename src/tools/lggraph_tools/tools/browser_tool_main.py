"""
This module provides a robust, process-managed wrapper for the browser-use tool.
It uses Python's multiprocessing to run the browser automation in an isolated process,
providing timeout handling, process ID (PID) tracking, and clean termination.

UPDATE (Feb 2026): Added Runner-based event-driven execution as alternative to subprocess.
"""
import asyncio
import datetime
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import List

# Ensure project root is on sys.path for correct module resolution in the subprocess
if __package__ is None:
    p = Path(__file__).resolve()
    project_root = next((parent for parent in p.parents if (parent / 'src').is_dir()),
                        p.parents[4] if len(p.parents) > 4 else p.parent)
    sys.path.insert(0, str(project_root))

# browser dependencies - only import what's needed for BrowserUseCompatibleLLM in parent process

from src.config import settings
from src.ui.diagnostics.debug_helpers import debug_info

# Import Runner and config for event-driven execution
from src.tools.lggraph_tools.tools.browser_tool.runner import Runner
from src.tools.lggraph_tools.tools.browser_tool.config import BrowserRequiredConfig


class BrowserHandler:
    """
    Handles the execution of the browser_use_tool in a separate, manageable subprocess.
    Uses subprocess.Popen for true process isolation with OS-level stdout/stderr redirection.

    UPDATE (Feb 2026): Now supports Runner-based event-driven execution via use_runner flag.
    """
    time_out: int = settings.BROWSER_USE_TIMEOUT
    enabled: bool = settings.BROWSER_USE_ENABLED
    running_processes: List[subprocess.Popen] = []

    # Flag to switch between legacy subprocess and new Runner-based execution

    def __init__(self, query: str, head_less_mode: bool = False, log: bool = True, keep_alive: bool = True):
        if not self.enabled:
            raise RuntimeError("Browser use tool is disabled in the settings.")
        self.query = query
        self.head_less_mode = head_less_mode
        self.keep_alive = keep_alive
        self.process_id = None
        self.process: subprocess.Popen | None = None
        self.log = log
        self.result_file = None
        self.log_file_handle = None
        self.result = self._run_with_process_management()

    def _run_with_process_management(self) -> str:
        """
        Manages the subprocess using subprocess.Popen and returns the result or error message.
        """
        # # Create unique result file for this execution
        # result_file_name = f"browser_result_{uuid.uuid4().hex}.json"
        # self.result_file = settings.BASE_DIR / "basic_logs" / result_file_name
        # self.result_file.parent.mkdir(parents=True, exist_ok=True)
        self.result_file = Path(settings.BROWSER_USE_LOG_FILE).resolve()

        # Prepare arguments for subprocess
        args_dict = {
            'query': self.query,
            'headless': self.head_less_mode,
            'keep_alive': self.keep_alive,
            'result_file': str(self.result_file)
        }

        # Get path to the subprocess runner script
        runner_script = Path(__file__).parent/ "browser_tool" / "browser_subprocess_runner.py"

        # Build command
        cmd = [sys.executable, str(runner_script), json.dumps(args_dict)]

        result_str = None

        try:
            # Setup stdout/stderr redirection
            if self.log:
                log_path = settings.BASE_DIR / "basic_logs" / "browser.txt"
                log_path.parent.mkdir(parents=True, exist_ok=True)

                # Open log file for subprocess output
                self.log_file_handle = open(log_path, 'w', encoding='utf-8', buffering=1)

                # Write header
                self.log_file_handle.write(f"\n{'='*80}\n")
                self.log_file_handle.write(f"BROWSER SUBPROCESS STARTED - TIME: {datetime.datetime.now()}\n")
                self.log_file_handle.write(f"Query: {self.query}\n")
                self.log_file_handle.write(f"Headless: {self.head_less_mode}, Keep Alive: {self.keep_alive}\n")
                self.log_file_handle.write(f"Result file: {self.result_file}\n")
                self.log_file_handle.write(f"{'='*80}\n")
                self.log_file_handle.flush()

                stdout_target = self.log_file_handle
                stderr_target = self.log_file_handle
            else:
                stdout_target = subprocess.DEVNULL
                stderr_target = subprocess.DEVNULL

            # Create subprocess with OS-level stdout/stderr redirection
            # On Windows, use CREATE_NO_WINDOW to prevent console popup
            creation_flags = 0
            if sys.platform == 'win32':
                creation_flags = subprocess.CREATE_NO_WINDOW

            # Prepare environment with UTF-8 encoding to handle emojis in browser_use logs
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'  # Force UTF-8 for subprocess I/O (fixes emoji system_logging)

            self.process = subprocess.Popen(
                cmd,
                stdout=stdout_target,
                stderr=stderr_target,
                creationflags=creation_flags,
                env=env  # Use modified environment with UTF-8 encoding
            )

            self.process_id = self.process.pid
            self.running_processes.append(self.process)

            debug_info(
                "BROWSER SUBPROCESS",
                f"Started browser subprocess with PID: {self.process_id}",
                metadata={
                    "pid": self.process_id,
                    "query": self.query,
                    "result_file": str(self.result_file),
                    "log_enabled": self.log
                }
            )

            # Wait for process to complete with timeout
            try:
                exit_code = self.process.wait(timeout=self.time_out)

                if exit_code != 0:
                    result_str = f"Browser subprocess exited with non-zero exit code: {exit_code}. Check browser.txt for details."
                else:
                    # Read result from file
                    if self.result_file.exists():
                        try:
                            with open(self.result_file, 'r', encoding='utf-8') as f:
                                result_data = json.load(f)

                            if result_data.get('status') == 'success':
                                result_str = result_data.get('result', 'No result in file')
                            else:
                                error = result_data.get('error', 'Unknown error')
                                traceback_info = result_data.get('traceback', '')
                                result_str = f"Browser subprocess error: {error}\n\n{traceback_info}"
                        except json.JSONDecodeError as e:
                            result_str = f"Failed to parse result file: {e}. Check browser.txt for details."
                    else:
                        result_str = "Browser subprocess completed but no result file was created. Check browser.txt for details."

            except subprocess.TimeoutExpired:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait()
                result_str = f"Tool execution timed out after {self.time_out} seconds and was terminated."

        except Exception as e:
            result_str = f"An error occurred while managing the browser tool process: {e}"
            if self.process:
                try:
                    if self.process.poll() is None:  # Process is still running
                        self.process.terminate()
                        try:
                            self.process.wait(timeout=3)
                        except subprocess.TimeoutExpired:
                            self.process.kill()
                            self.process.wait()
                except:
                    pass
            self.process_id = None

        finally:
            # Cleanup
            if self.log_file_handle:
                try:
                    self.log_file_handle.close()
                except:
                    pass

            # Delete result file
            if self.result_file and self.result_file.exists():
                try:
                    self.result_file.unlink()
                except:
                    pass

        return result_str

    @staticmethod
    def _clean_up(process: subprocess.Popen):
        """
        Ensures the process is terminated if still running.
        """
        if process is None:
            return
            
        try:
            if process.poll() is None:  # Process is still running
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()

            debug_info(
                "BROWSER TOOL CLEAN UP",
                f"BrowserHandler: Cleaned up process with PID {process.pid}",
                metadata={
                    "process_id": process.pid,
                    "is_alive": process.poll() is None,
                    "returncode": process.returncode
                }
            )
            if process in BrowserHandler.running_processes:
                BrowserHandler.running_processes.remove(process)
        except ProcessLookupError:
            pass
        except OSError:
            pass

    @staticmethod
    def clear_all_processes():
        """
        close all the running subprocesses if any
        :return:
        """
        if hasattr(BrowserHandler, 'running_processes') and BrowserHandler.running_processes:
            # Create a copy of the list to avoid modification during iteration
            processes_to_clean = BrowserHandler.running_processes.copy()
            for proc in processes_to_clean:
                BrowserHandler._clean_up(proc)


def browser_use_tool(query: str, head_less_mode: bool = True, log: bool = True, keep_alive:bool = False) -> str:
    """
    Main entry point for the browser_agent tool.
    Creates an instance of BrowserHandler and returns the result.
    
    Args:
        query: The task/query to be executed by the browser agent
        head_less_mode: Whether to run the browser in headless mode
        log: Whether to enable system_logging to browser.txt
        keep_alive: Whether to keep the browser alive after execution
        
    Returns:
        str: The result of the browser agent execution or error message
    """
    try:
        handler = BrowserHandler(query=query, head_less_mode=head_less_mode, log=log, keep_alive=keep_alive)
        return handler.result
    except Exception as e:
        error_msg = f"browser_use_tool failed with exception: {e}"
        # Try to log the error if system_logging is enabled
        if log:
            try:
                log_path = settings.BASE_DIR / "basic_logs" / "browser.txt"
                log_path.parent.mkdir(parents=True, exist_ok=True)
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(f"\n[ERROR] {error_msg}\n")
            except:
                pass  # Ignore system_logging errors
        return error_msg


if __name__ == '__main__':
    # test_query = "/agent you have to open browser in which open nvidia nim api website where you have to get knowledge about the models it offers for developers those model are text-to-text generation capabilities you have to then provide me best model for agentic and bigger context window !! to accomplish best among them you have to keep comparing with each others into ai benchmark websites !! after which you have to just provide me one model name !! who is best agentic model and long context model !! https://build.nvidia.com/explore/discover this is the website url !!"
    test_query = "/agent Navigate to YouTube, search the night we met, identify the official music video, play it, and keep alive, log to the true."
    print(f"Invoking browser_use_tool for query: '{test_query}'")

    # Run the tool and get the result directly
    final_response = browser_use_tool(query=test_query, head_less_mode=False, log=True, keep_alive=True)

    print(f"\n--- Standalone Execution Result ---")
    print(final_response)
    print("------------------------------------")
