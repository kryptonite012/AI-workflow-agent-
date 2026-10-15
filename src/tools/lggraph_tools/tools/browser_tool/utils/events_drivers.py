"""
Event driver implementations for browser tool lifecycle.

Each driver class:
- Inherits from Handler
- Has enum_value class attribute
- Has __init__(self, runner_instance)
- Has async methods that execute_method will find and run

Mapping from browser_subprocess_runner.py:
- PreRequirementsCustomEvent: Check internet, RAM, browser_use installed
- SetupDriver: Create LLM, Browser, Agent instances + monkey patch
- OnStartDriver: Load custom sessions, wait for browser ready
- OnRunningDriver: Run agent.run(), start monitoring thread
- OnCompleteDriver: Save sessions, extract result, write to file
- OnExceptionDriver: Log errors, write error to file
- TeardownDriver: Close agent, handle keep_alive, cleanup
"""
from __future__ import annotations

import asyncio
import json
import queue
import sys
import traceback
from pathlib import Path
from threading import Thread, RLock
from typing import TYPE_CHECKING

import psutil

if TYPE_CHECKING:
    from ..runner import Runner

from ..Handler import Handler, HandlerEnums


# =============================================================================
# PRE-REQUIREMENTS DRIVER (Critical - huge_error=True)
# =============================================================================

class PreRequirementsCustomEvent(Handler):
    """Check pre-requirements before starting browser tool.

    🎯 What this does (like I'm 10):
    Before we play with the browser robot, we check:
    1. Is the internet working? (Can we connect?)
    2. Do we have enough memory? (RAM)
    3. Is the browser_use toy installed?
    """

    enum_value = HandlerEnums.ON_PRE_REQUIREMENTS
    huge_error = True  # If ANY check fails, STOP everything!

    def __init__(self, runner_instance: 'Runner'):
        """Initialize with runner instance for accessing config."""
        self.runner = runner_instance

    def check_internet(self):
        """Check internet connectivity."""
        import socket
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            print("✅ Internet connected")
            return {"internet": "connected"}
        except OSError:
            raise ConnectionError("Active internet connection required!")

    def check_ram(self):
        """Check minimum RAM."""
        import os
        import psutil

        if os.name != 'nt':
            print("⚠️  RAM check skipped (Windows only)")
            return {"ram_check": "skipped"}

        min_ram_gb = 4
        total_ram = psutil.virtual_memory().total / (1024 ** 3)

        if total_ram < min_ram_gb:
            print(f"⚠️  Warning: RAM ({total_ram:.2f} GB) below {min_ram_gb} GB")
        else:
            print(f"✅ RAM: {total_ram:.2f} GB")

        return {"ram_gb": total_ram}

    def check_browser_use(self):
        """Check if browser_use is installed."""
        import importlib.util

        if importlib.util.find_spec("browser_use") is None:
            raise ImportError("browser_use package not installed!")

        print("✅ browser_use installed", flush=True)
        return {"browser_use": "installed"}


# =============================================================================
# SETUP DRIVER (Critical - huge_error=True)
# =============================================================================

class SetupDriver(Handler):
    """Setup phase: Create browser, agent, LLM.

    🎯 What this does (like I'm 10):
    Now we build our robot:
    1. Apply a special trick (monkey patch) so browser doesn't close
    2. Create the brain (LLM - Language Model)
    3. Create the browser window
    4. Create the robot agent that controls the browser

    Maps to browser_subprocess_runner.py lines:
    - BrowserUseCompatibleLLM class (lines 70-160)
    - Browser creation (lines 174-180)
    - Agent creation (lines 185-193)
    - Monkey patch (lines 419-430)
    """

    enum_value = HandlerEnums.SET_UP
    huge_error = True  # Setup failure is critical!

    def __init__(self, runner_instance: 'Runner'):
        self.runner = runner_instance

    def apply_monkey_patch_on_watch_dog(self):
        """Apply monkey patch to watchdog to prevent browser from closing if keep_alive is True."""
        from browser_use.browser.events import BrowserStopEvent, BrowserKillEvent
        from browser_use.browser.watchdogs.local_browser_watchdog import LocalBrowserWatchdog

        async def on_BrowserStopEvent(instance, event: BrowserStopEvent) -> None:
            """Monkey patched stop watchdog to prevent browser from closing if keep_alive is True."""
            force_kill = getattr(event, 'force', False)
            browser_profile = getattr(instance.browser_session, 'browser_profile', None)
            keep_alive = getattr(browser_profile, 'keep_alive', False)
            if instance._subprocess and instance.browser_session.is_local:
                if keep_alive and not force_kill:
                    print("[DRIVER] Keep alive is True, skipping browser stop.")
                    sys.stdout.flush()
                    return
            instance.event_bus.dispatch(BrowserKillEvent())

        LocalBrowserWatchdog.on_BrowserStopEvent = on_BrowserStopEvent
        print("✅ Applied monkey patch on watchdog", flush=True)
        return {"monkey_patch": "applied"}

    async def create_browser_compatible_llm(self):
        """Create BrowserUseCompatibleLLM adapter.

        This wraps ModelManager to be compatible with browser_use's expected LLM interface.
        From browser_subprocess_runner.py lines 70-160.
        """
        from src.config import settings
        from src.utils.model_manager import ModelManager
        from browser_use.llm.messages import BaseMessage, UserMessage, SystemMessage, AssistantMessage
        from browser_use.llm.views import ChatInvokeCompletion
        from pydantic import BaseModel
        from typing import List, Optional, TypeVar, overload

        T = TypeVar('T', bound=BaseModel)

        class BrowserUseCompatibleLLM:
            """Adapter to make ModelManager compatible with browser_use's BaseChatModel protocol"""

            def __init__(self, model_manager: ModelManager):
                self._model_manager = model_manager
                self.model = ModelManager.current_model or 'default'
                self._verified_api_keys = getattr(model_manager, '_verified_api_keys', False)

            @property
            def provider(self) -> str:
                model_name = getattr(self, 'model', 'default').lower()
                if 'gpt' in model_name: return 'openai'
                if 'claude' in model_name: return 'anthropic'
                if 'llama' in model_name or 'mistral' in model_name: return 'ollama'
                return 'unknown'

            @property
            def name(self) -> str:
                return getattr(self, 'model', 'default_model')

            @property
            def model_name(self) -> str:
                return getattr(self, 'model', 'default')

            @overload
            async def ainvoke(self, messages: List[BaseMessage], output_format: None = None) -> ChatInvokeCompletion[
                str]:
                ...

            @overload
            async def ainvoke(self, messages: List[BaseMessage], output_format: type[T]) -> ChatInvokeCompletion[T]:
                ...

            async def ainvoke(
                    self,
                    messages: List[BaseMessage],
                    output_format: Optional[type[T]] = None,
                    **kwargs
            ) -> ChatInvokeCompletion[T] | ChatInvokeCompletion[str]:
                """Convert browser_use messages to LangChain format and invoke the model"""
                langchain_messages = []
                for msg in messages:
                    if isinstance(msg, UserMessage):
                        from langchain_core.messages import HumanMessage
                        content = msg.text if hasattr(msg, 'text') else str(msg.content)
                        langchain_messages.append(HumanMessage(content=content))
                    elif isinstance(msg, SystemMessage):
                        from langchain_core.messages import SystemMessage as LCSystemMessage
                        content = msg.text if hasattr(msg, 'text') else str(msg.content)
                        langchain_messages.append(LCSystemMessage(content=content))
                    elif isinstance(msg, AssistantMessage):
                        from langchain_core.messages import AIMessage
                        content = msg.text if hasattr(msg, 'text') else str(msg.content)
                        langchain_messages.append(AIMessage(content=content or ''))
                    else:
                        from langchain_core.messages import HumanMessage
                        langchain_messages.append(HumanMessage(content=str(msg)))

                try:
                    response = await asyncio.get_running_loop().run_in_executor(
                        None, self._model_manager.invoke, langchain_messages
                    )
                    usage = None
                    if hasattr(response, 'response_metadata'):
                        metadata = response.response_metadata
                        prompt_tokens = metadata.get('prompt_eval_count', 0) or metadata.get('prompt_tokens', 0)
                        completion_tokens = metadata.get('eval_count', 0) or metadata.get('completion_tokens', 0)
                        total_tokens = prompt_tokens + completion_tokens
                        if prompt_tokens > 0 or completion_tokens > 0:
                            from browser_use.llm.views import ChatInvokeUsage
                            usage = ChatInvokeUsage(
                                prompt_tokens=prompt_tokens,
                                completion_tokens=completion_tokens,
                                total_tokens=total_tokens
                            )

                    if output_format is None:
                        completion = response.content if hasattr(response, 'content') else str(response)
                        return ChatInvokeCompletion[str](completion=completion, usage=usage)
                    else:
                        try:
                            if hasattr(response, 'content') and isinstance(response.content, str):
                                try:
                                    json_content = json.loads(response.content)
                                    completion = output_format.model_validate(json_content)
                                    return ChatInvokeCompletion[T](completion=completion, usage=usage)
                                except (json.JSONDecodeError, Exception):
                                    completion = output_format.model_validate(response.content)
                                    return ChatInvokeCompletion[T](completion=completion, usage=usage)
                            else:
                                completion = output_format.model_validate(response.content)
                                return ChatInvokeCompletion[T](completion=completion, usage=usage)
                        except Exception:
                            completion = response.content if hasattr(response, 'content') else str(response)
                            return ChatInvokeCompletion[str](completion=completion, usage=usage)
                except Exception as e:
                    raise e

        # Initialize settings for LangChain messages
        if settings.AIMessage is None and settings.HumanMessage is None:
            from langchain_core.messages import AIMessage as LangChainAIMessage
            from langchain_core.messages import HumanMessage as LangChainHumanMessage
            settings.AIMessage = LangChainAIMessage
            settings.HumanMessage = LangChainHumanMessage

        print("[DRIVER] Initializing ModelManager and BrowserUseCompatibleLLM...", flush=True)
        model_manager = ModelManager()
        browser_use_llm = BrowserUseCompatibleLLM(model_manager)

        # Store on runner for later use
        self.runner.llm = browser_use_llm

        print("✅ BrowserUseCompatibleLLM created", flush=True)
        return {"llm": "created", "model": browser_use_llm.model}

    async def create_browser_instance(self):
        """Create Browser instance.

        From browser_subprocess_runner.py lines 174-180.
        """
        from browser_use import Browser
        from src.config import settings

        config = self.runner.config

        print("[DRIVER] Starting Browser instance...", flush=True)
        browser = Browser(
            headless=config.headless,
            keep_alive=config.keep_alive,
            record_video_dir=config.video_dir if config.record_video else None,
            user_data_dir=config.user_data_dir or settings.BROWSER_USE_USER_PROFILE_PATH,
        )

        # Store on runner for later use
        self.runner.browser = browser
        await browser.start()

        print("✅ Browser instance created", flush=True)
        return {"browser": "created", "headless": config.headless}

    async def create_agent_instance(self):
        """Create Agent instance.

        From browser_subprocess_runner.py lines 185-193.
        """
        from browser_use import Agent

        config = self.runner.config
        llm = self.runner.llm
        browser = self.runner.browser

        print("[DRIVER] Creating Agent...")
        agent = Agent(
            task=config.query,
            llm=llm,
            browser=browser,
            max_failures=config.max_failures,
            max_steps=config.max_steps,
            vision_detail_level=config.vision_detail_level
        )

        # Store on runner for later use
        self.runner.agent = agent

        print("✅ Agent created", flush=True)
        return {"agent": "created", "task": config.query[:50] + "..." if len(config.query) > 50 else config.query}


# =============================================================================
# ON_START DRIVER (Non-critical - can continue on failure)
# =============================================================================

class OnStartDriver(Handler):
    """Start phase: Load custom sessions, prepare browser.

    🎯 What this does (like I'm 10):
    Before the robot starts working:
    1. Wait for browser to be ready (connected)
    2. Load saved data from last time (form data, scroll position)

    Maps to browser_subprocess_runner.py:
    - load_custom_sessions() function (lines 285-375)
    - wait_until_browser_ready() (lines 287-298)
    """

    enum_value = HandlerEnums.ON_START

    # No huge_error - session loading failure is not critical

    def __init__(self, runner_instance: 'Runner'):
        self.runner = runner_instance

    async def wait_for_browser_ready(self):
        """Wait until browser CDP client is ready.

        From browser_subprocess_runner.py lines 287-298.
        """
        browser = self.runner.browser
        config = self.runner.config

        max_wait = config.browser_ready_timeout or 30
        waited = 0

        while browser._cdp_client_root is None and waited < max_wait:
            print(f"[DRIVER] Waiting for browser to be ready... {waited}s/{max_wait}s")
            await asyncio.sleep(1)
            waited += 1

        if browser._cdp_client_root is None:
            raise RuntimeError(f"Browser did not become ready in {waited} seconds. CDP client is still None.")

        print("✅ Browser is ready (CDP connected)", flush=True)
        return {"browser_ready": True, "wait_time": waited}

    async def load_custom_sessions(self):
        """Load custom browser sessions if available.

        Restores: URL, form data, scroll position.
        From browser_subprocess_runner.py lines 299-375.
        """
        import aiofiles
        from src.config import settings

        browser = self.runner.browser
        config = self.runner.config

        session_file_path = Path(
            config.user_data_dir or settings.BROWSER_USE_USER_PROFILE_PATH) / "custom_sessions.json"

        if not session_file_path.exists():
            print("[DRIVER] No custom session file found, starting fresh.")
            return {"session_loaded": False, "reason": "no_file"}

        async with aiofiles.open(session_file_path, 'r', encoding='utf-8') as f:
            content = await f.read()
            session_data = json.loads(content)

        current_url = session_data.get('current_url', None)
        form_data: dict = session_data.get('form_data', {})
        scroll_pos = session_data.get('scroll_position', {'x': 0, 'y': 0})

        if not current_url:
            print("[DRIVER] No URL found in session data.", flush=True)
            return {"session_loaded": False, "reason": "no_url"}

        # Navigate to saved URL
        from browser_use.browser.events import NavigateToUrlEvent
        await browser.event_bus.dispatch(NavigateToUrlEvent(url=current_url))
        await asyncio.sleep(3)

        # Restore form data
        cdp_session = await browser.get_or_create_cdp_session()
        form_data_string = json.dumps(form_data)

        restore_form_script = f"""
        (function() {{
            const formData = {form_data_string};
            let restoredCount = 0;
            for (const [key, value] of Object.entries(formData)) {{
                let input = document.querySelector(`input[name="${{key}}"]`) ||
                           document.querySelector(`textarea[name="${{key}}"]`) ||
                           document.querySelector(`select[name="${{key}}"]`) ||
                           document.querySelector(`#${{key}}`) ||
                           document.querySelector(`input[aria-label="${{key}}"]`);
                if (input) {{
                    input.value = value;
                    input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    restoredCount++;
                }}
            }}
            return restoredCount;
        }})();
        """

        restore_result = await cdp_session.cdp_client.send.Runtime.evaluate(
            params={'expression': restore_form_script, 'returnByValue': True},
            session_id=cdp_session.session_id
        )
        restored_count = restore_result.get('result', {}).get('value', 0)
        print(f"[DRIVER] Restored {restored_count}/{len(form_data)} form fields.", flush=True)

        # Restore scroll position
        scroll_script = f"""
        (function() {{
            window.scrollTo({scroll_pos['x']}, {scroll_pos['y']});
            return true;
        }})();
        """
        await cdp_session.cdp_client.send.Runtime.evaluate(
            params={'expression': scroll_script, 'returnByValue': True},
            session_id=cdp_session.session_id
        )

        print(f"✅ Session restored: {current_url}", flush=True)
        return {"session_loaded": True, "url": current_url, "form_fields": restored_count}


# =============================================================================
# ON_RUNNING DRIVER (Critical during execution)
# =============================================================================

class OnRunningDriver(Handler):
    """Running phase: Execute agent task.

    🎯 What this does (like I'm 10):
    Now the robot actually does the work:
    1. Start a helper that watches if browser is still alive
    2. Tell the robot to do the task (agent.run())
    3. Wait for the robot to finish

    Maps to browser_subprocess_runner.py:
    - agent.run() (lines 215-218)
    - monitering_browser_process() (lines 211-213, 560-590)
    """

    enum_value = HandlerEnums.ON_RUNNING
    huge_error = True  # Agent execution failure is critical

    def __init__(self, runner_instance: 'Runner'):
        self.runner = runner_instance
        # FIX: Use queue.Queue (sync) not asyncio.Queue (async) for threading
        self.runner.monitor_queue = queue.Queue()

        self.lock = RLock()

        # FIX: Move these from class variables to instance variables
        self.killer_flag = {'started': False, 'got_run': False, 'should_kill': False}
        self.browser_pid = None
        self.ghost_pid = None

    def __get_info_browser_pid(self):
        """Get the browser subprocess PID."""
        for process in psutil.process_iter(['pid', 'name', 'cmdline', 'ppid']):
            try:
                name = (process.info.get('name') or '').lower()
                if 'chrome' in name or 'chromium' in name:
                    cmdline = ' '.join(process.info.get('cmdline') or []).lower()
                    if '--remote-debugging-port' in cmdline:
                        self.browser_pid = process.info['pid']
                        self.ghost_pid = process.info['ppid']
                        browser_actual_parent_runner_pid = None
                        try:
                            if psutil.pid_exists(self.ghost_pid):
                                parent_process = psutil.Process(self.ghost_pid)
                                browser_actual_parent_runner_pid = parent_process.ppid()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            browser_actual_parent_runner_pid = None

                        print(
                            f"[SUBPROCESS] Detected browser process PID: {self.browser_pid}, Parent (ghost) PID: {self.ghost_pid}, Grand-parent PID: {browser_actual_parent_runner_pid}",
                            flush=True)
                        sys.stdout.flush()
                        return
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
                print(f"[SUBPROCESS] Process iteration error: {e}", flush=True)
                continue

        # Reset if not found
        self.browser_pid = None
        self.ghost_pid = None

    async def __watch_process_alive(self):
        """Monitor browser process lifecycle with proper state transitions."""
        while not self.killer_flag['should_kill']:
            self.__get_info_browser_pid()

            # State machine logic
            if self.browser_pid and not self.killer_flag['started']:
                # Browser started
                self.killer_flag['started'] = True
                print(f"[DRIVER] Browser started - PID: {self.browser_pid}", flush=True)
                sys.stdout.flush()

            elif self.browser_pid and self.killer_flag['started'] and not self.killer_flag['got_run']:
                # Agent began execution
                self.killer_flag['got_run'] = True
                print("[DRIVER] Agent execution started", flush=True)
                sys.stdout.flush()

            elif not self.browser_pid and self.killer_flag['started']:
                # Browser died - emit kill event regardless of got_run state
                self.killer_flag['should_kill'] = True
                print("[DRIVER] Browser closed - emitting kill event", flush=True)
                sys.stdout.flush()

                # Ensure kill event gets queued
                try:
                    self.runner.monitor_queue.put_nowait(True)
                    print("[DRIVER] Kill signal queued successfully", flush=True)
                except queue.Full:
                    print("[DRIVER] Queue full - kill signal may be delayed", flush=True)

            print(f"[DRIVER] Monitor state: {self.killer_flag}", flush=True)
            sys.stdout.flush()
            await asyncio.sleep(3)

            # Only queue if state changed (don't flood queue)
            if self.killer_flag['should_kill']:
                try:
                    self.runner.monitor_queue.put_nowait(self.killer_flag['should_kill'])
                except queue.Full:
                    pass

    async def start_browser_monitoring(self):
        """Start monitoring thread to watch if browser is still alive.

        From browser_subprocess_runner.py lines 560-590.
        """

        def _runner(q: queue.Queue):
            loop = asyncio.new_event_loop()
            try:
                asyncio.set_event_loop(loop)
                q.put(loop.run_until_complete(self.__watch_process_alive()))
            except Exception as e:
                print(f"[DRIVER] Monitoring thread crashed: {e}")
                q.put(True)
            finally:
                try:
                    loop.close()
                except Exception:
                    pass

        self.runner.monitor_thread = Thread(target=_runner, daemon=True, args=(self.runner.monitor_queue,))
        self.runner.monitor_thread.start()

        print("✅ Browser monitoring started")
        return {"monitoring": "started"}

    async def run_agent(self):
        """Execute the agent task.

        From browser_subprocess_runner.py lines 215-218.
        """
        agent = self.runner.agent

        print("[DRIVER] Starting agent execution...")
        sys.stdout.flush()

        try:
            result = await agent.run()

            # Store result on runner
            self.runner.agent_result = result

            print("[DRIVER] Agent execution completed!")
            return {"agent_run": "completed"}
        except Exception as e:
            print(f"[DRIVER] CRITICAL: agent.run() failed: {e}")
            raise


# =============================================================================
# ON_COMPLETE DRIVER (Non-critical for saving)
# =============================================================================

class OnCompleteDriver(Handler):
    """Complete phase: Extract result, save session.

    🎯 What this does (like I'm 10):
    The robot finished! Now we:
    1. Get what the robot found (the result)
    2. Save where we were (so we can continue later)
    3. Write the answer to a file

    Maps to browser_subprocess_runner.py:
    - result.final_result() (lines 227-228)
    - save_custom_sessions() (lines 378-416)
    - Write result to file (lines 233-238)
    """

    enum_value = HandlerEnums.ON_COMPLETE

    # No huge_error - saving failure shouldn't crash

    def __init__(self, runner_instance: 'Runner'):
        self.runner = runner_instance

    async def extract_final_result(self):
        """Extract final result from agent.

        From browser_subprocess_runner.py lines 227-228.
        """
        agent_result = getattr(self.runner, 'agent_result', None)

        if agent_result is None:
            print("[DRIVER] No agent result found!")
            return {"final_result": None}

        final_result = str(agent_result.final_result())

        # Store for later use
        self.runner.final_result = final_result

        result_preview = final_result[:200] + "..." if len(final_result) > 200 else final_result
        print(f"[DRIVER] Final result: {result_preview}")
        return {"final_result": final_result}

    async def save_custom_sessions(self):
        """Save current browser session state.

        From browser_subprocess_runner.py lines 378-416.
        """
        import aiofiles
        from src.config import settings
        from src.utils.timestamp_util import get_formatted_timestamp

        browser = self.runner.browser
        config = self.runner.config

        # Check if browser connection is still valid
        if browser._cdp_client_root is None:
            print("[DRIVER] Browser CDP client not ready, skipping session save.")
            return {"session_saved": False, "reason": "cdp_not_ready"}

        # Additional health check - try to create a session
        try:
            test_session = await browser.get_or_create_cdp_session()
            # Quick health check
            await test_session.cdp_client.send.Runtime.evaluate(
                params={'expression': '1', 'returnByValue': True},
                session_id=test_session.session_id
            )
        except Exception as e:
            print(f"[DRIVER] Browser connection health check failed: {e}, skipping session save.")
            return {"session_saved": False, "reason": "connection_unhealthy", "error": str(e)}

        try:
            current_url = await browser.get_current_page_url()
            cdp_session = await browser.get_or_create_cdp_session()

            # Extract form data
            form_data_script = """
            (function() {
                const formData = {};
                const inputs = document.querySelectorAll('input, textarea, select');
                inputs.forEach(input => {
                    const key = input.name || input.id || input.getAttribute('aria-label');
                    if (key && input.value) {
                        formData[key] = input.value;
                    }
                });
                return formData;
            })();
            """
            form_result = await cdp_session.cdp_client.send.Runtime.evaluate(
                params={'expression': form_data_script, 'returnByValue': True},
                session_id=cdp_session.session_id
            )
            form_data = form_result.get('result', {}).get('value', {})

            # Extract scroll position
            scroll_script = """
            (function() {
                return {
                    x: window.scrollX || window.pageXOffset || 0,
                    y: window.scrollY || window.pageYOffset || 0
                };
            })();
            """
            scroll_result = await cdp_session.cdp_client.send.Runtime.evaluate(
                params={'expression': scroll_script, 'returnByValue': True},
                session_id=cdp_session.session_id
            )
            scroll_pos = scroll_result.get('result', {}).get('value', {'x': 0, 'y': 0})

            # Build session data
            session_data = {
                'current_url': current_url,
                'form_data': form_data,
                'scroll_position': scroll_pos,
                'timestamp': get_formatted_timestamp()
            }

            # Save to file
            session_file_path = Path(
                config.user_data_dir or settings.BROWSER_USE_USER_PROFILE_PATH) / 'custom_sessions.json'
            async with aiofiles.open(session_file_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(session_data, indent=2))

            print(f"✅ Session saved to {session_file_path}", flush=True)
            return {"session_saved": True, "url": current_url}
        except Exception as e:
            print(f"[DRIVER] Failed to save session: {e}", flush=True)
            return {"session_saved": False, "error": str(e)}

    async def write_result_to_file(self):
        """Write final result to output file.

        From browser_subprocess_runner.py lines 233-238.
        """
        config = self.runner.config
        final_result = getattr(self.runner, 'final_result', None)

        if config.file_path is None:
            print("[DRIVER] No result file path configured, skipping file write.", flush=True)
            return {"file_written": False, "reason": "no_path"}

        result_data = {
            "status": "success",
            "result": final_result
        }

        with open(config.file_path, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)

        print(f"✅ Result written to {config.file_path}", flush=True)
        return {"file_written": True, "path": str(config.file_path)}


# =============================================================================
# ON_EXCEPTION DRIVER
# =============================================================================

class OnExceptionDriver(Handler):
    """Exception phase: Handle and log errors.

    🎯 What this does (like I'm 10):
    Something went wrong! We need to:
    1. Write down what went wrong (log it)
    2. Save the error to a file so we know what happened
    """

    enum_value = HandlerEnums.ON_EXCEPTION

    def __init__(self, runner_instance: 'Runner'):
        self.runner = runner_instance
        self.exception = None  # Will be set by runner

    async def log_exception(self):
        """Log the exception details."""
        exception = getattr(self.runner, 'last_exception', None)

        if exception is None:
            print("[DRIVER] No exception to log.")
            return {"exception_logged": False}

        print(f"❌ Exception occurred: {type(exception).__name__}: {exception}", flush=True)
        traceback_str = traceback.format_exc()
        print(traceback_str, flush=True)

        return {"exception_logged": True, "type": type(exception).__name__, "message": str(exception)}

    async def write_error_to_file(self):
        """Write error to result file.

        From browser_subprocess_runner.py lines 267-277.
        """
        config = self.runner.config
        exception = getattr(self.runner, 'last_exception', None)

        if config.file_path is None:
            return {"error_written": False, "reason": "no_path"}

        error_result = {
            "status": "error",
            "error": str(exception) if exception else "Unknown error",
            "traceback": traceback.format_exc()
        }

        try:
            with open(config.file_path, 'w', encoding='utf-8') as f:
                json.dump(error_result, f, ensure_ascii=False, indent=2)
            print(f"❌ Error written to {config.file_path}", flush=True)
            return {"error_written": True, "path": str(config.file_path)}
        except Exception as e:
            print(f"[DRIVER] Failed to write error file: {e}", flush=True)
            return {"error_written": False, "error": str(e)}


# =============================================================================
# TEARDOWN DRIVER (Always runs!)
# =============================================================================

class TeardownDriver(Handler):
    """Teardown phase: Cleanup resources.

    🎯 What this does (like I'm 10):
    Time to clean up our toys:
    1. Close the robot agent
    2. If keep_alive is True, wait for user to close browser
    3. Clean up any leftover mess

    Maps to browser_subprocess_runner.py:
    - agent.close() (line 223)
    - keep_alive wait logic (lines 240-261)
    """

    enum_value = HandlerEnums.TEAR_DOWN

    # No huge_error - cleanup should be best-effort

    def __init__(self, runner_instance: 'Runner'):
        from src.config.settings import BROWSER_USE_TIMEOUT
        self.runner = runner_instance
        print("[DRIVER] Starting teardown... waiting for monitor system to actually tell us its decision ", flush=True)
        self.runner.monitor_thread and self.runner.monitor_thread.join(timeout=BROWSER_USE_TIMEOUT)
        self.runner.monitor_thread.is_alive() and print("[DRIVER] Monitor thread is still alive after timeout, proceeding with teardown.", flush=True)

    async def __emit_kill_browser_event(self):
        """
        Emit the BrowserKillEvent to trigger browser shutdown.
        """
        try:
            if self.runner.browser:
                from browser_use.browser.events import BrowserKillEvent
                await self.runner.browser.event_bus.dispatch(BrowserKillEvent())
                print("[DRIVER] Emitted BrowserKillEvent to shut down browser.", flush=True)
            else:
                print("[DRIVER] No browser instance found to emit kill event.", flush=True)
        except Exception as e:
            print(f"[DRIVER] Failed to emit BrowserKillEvent: {e}", flush=True)

    async def handle_keep_alive(self):
        """Handle keep_alive mode - wait for browser to close.

        From browser_subprocess_runner.py lines 240-261.
        """
        config = self.runner.config
        monitor_queue = getattr(self.runner, 'monitor_queue', None)

        if not config.keep_alive:
            await self.__close_agent()
            await self.__close_browser()
            print("[DRIVER] keep_alive=False, no waiting needed.", flush=True)
            return {"keep_alive_wait": False}

        if monitor_queue is None:
            print("[DRIVER] No monitor queue, can't wait for browser close.", flush=True)
            return {"keep_alive_wait": False, "reason": "no_queue"}

        print("[DRIVER] keep_alive=True, waiting for browser to close...", flush=True)
        try:
            # Wait up to 24 hours (effectively forever)
            ok: bool = monitor_queue.get(timeout=60 * 60 * 24)
            print(f"[DRIVER] Browser closed (ok={ok})", flush=True)
            if ok:
                await self.__close_agent()
                await self.__close_browser()
                await self.__emit_kill_browser_event()
            return {"keep_alive_wait": True, "browser_closed": ok}
        except Exception as e:
            print(f"[DRIVER] Keep-alive wait failed: {e}, traceback: {traceback.format_exc()}", flush=True)
            return {"keep_alive_wait": False, "error": str(e)}

    async def __close_agent(self):
        """Close the agent.

        From browser_subprocess_runner.py line 223.
        """
        agent = getattr(self.runner, 'agent', None)

        if agent is None:
            print("[DRIVER] No agent to close.", flush=True)

        try:
            await agent.close()
            print("✅ Agent closed", flush=True)
        except Exception as e:
            print(f"[DRIVER] Failed to close agent: {e}", flush=True)


    async def __close_browser(self):
        """Force close browser bypassing monkey patch.

        CRITICAL: The monkey patch at line 131-143 blocks browser.stop() when keep_alive=True!
        We must use force=True to bypass it, otherwise CDP stays connected and tasks hang forever.
        """
        browser = getattr(self.runner, 'browser', None)
        if browser is None:
            print("[DRIVER] No browser to close.", flush=True)

        try:
            # CRITICAL: Use force=True to bypass monkey patch!
            from browser_use.browser.events import BrowserStopEvent

            print("[DRIVER] Force-closing browser (bypassing monkey patch)...", flush=True)

            # Dispatch with force=True to bypass the monkey patch at line 131-143
            await browser.event_bus.dispatch(BrowserStopEvent(force=True))

            # Wait a bit for cleanup to complete
            await asyncio.sleep(0.5)

            print("✅ Browser force-stopped successfully", flush=True)
        except Exception as e:
            print(f"[DRIVER] Failed to force-stop browser: {e}", flush=True)

            # Fallback: try direct CDP close
            try:
                print("[DRIVER] Attempting direct CDP connection close...", flush=True)
                if hasattr(browser, '_browser_session'):
                    session = browser._browser_session
                    if hasattr(session, '_cdp_client_root') and session._cdp_client_root:
                        await session._cdp_client_root.close()
                        print("✅ CDP connection closed directly", flush=True)
            except Exception as e2:
                print(f"[DRIVER] CDP direct close also failed: {e2}", flush=True)

    async def cleanup_resources(self):
        """Final cleanup of any remaining resources."""
        print("✅ Cleanup complete")
        return {"cleanup": "done"}
