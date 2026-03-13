"""
Standalone subprocess runner for browser_use tool.
This script is executed as a separate process via subprocess.Popen.

It receives arguments via command line (JSON), executes the browser agent,
and writes the result to a specified output file.

All stdout/stderr is redirected by the parent process via Popen, so Playwright
and Chromium can function normally without os.dup2() interference.
"""
import asyncio
import json
import queue
import sys
import traceback
from pathlib import Path
from threading import Thread

import psutil
from browser_use import Agent, Browser
from browser_use.browser.events import BrowserStopEvent, BrowserKillEvent
from browser_use.browser.watchdogs.local_browser_watchdog import LocalBrowserWatchdog


def main():
    """Main entry point for the subprocess runner."""
    args_dict = {}  # Initialize to avoid reference errors

    # keep_alive monitoring queue (set when keep_alive=True inside the async runner)
    monitor_queue: queue.Queue | None = None

    if len(sys.argv) < 2:
        error_result = {
            "status": "error",
            "error": "No arguments provided to subprocess runner",
            "traceback": ""
        }
        print(json.dumps(error_result), file=sys.stderr)
        sys.exit(1)

    try:
        # Parse arguments from command line
        args_json = sys.argv[1]
        args_dict = json.loads(args_json)

        query = args_dict['query']
        headless = args_dict['headless']
        keep_alive = args_dict['keep_alive']
        result_file = args_dict['result_file']

        print(f"[SUBPROCESS] Starting browser agent with query: {query}")
        print(f"[SUBPROCESS] Headless: {headless}, Keep Alive: {keep_alive}")
        print(f"[SUBPROCESS] Result file: {result_file}")
        sys.stdout.flush()

        # Import browser_use and dependencies (after stdout is already redirected by parent)

        # Import project dependencies
        # Add project root to path
        project_root = Path(__file__).resolve().parents[4]
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))

        from src.config import settings
        from src.utils.model_manager import ModelManager

        # Import the BrowserUseCompatibleLLM from the parent module
        # We need to be careful here - let's inline it to avoid import issues
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
            async def ainvoke(self, messages: List[BaseMessage], output_format: None = None) -> ChatInvokeCompletion[str]:
                ...

            @overload
            async def ainvoke(self, messages: List[BaseMessage], output_format: type[T]) -> ChatInvokeCompletion[T]:
                ...

            async def ainvoke(
                    self,
                    messages: List[BaseMessage],
                    output_format: Optional[type[T]] = None
            ) -> ChatInvokeCompletion[T] | ChatInvokeCompletion[str]:
                """Convert browser_use messages to LangChain format and invoke the model"""
                langchain_messages = []
                for msg in messages:
                    if isinstance(msg, UserMessage):
                        from langchain_core.messages import HumanMessage
                        content = msg.text if hasattr(msg, 'text') else str(msg.content)
                        langchain_messages.append(HumanMessage(content=content))
                    elif isinstance(msg, SystemMessage):
                        from langchain_core.messages import SystemMessage as LangChainSystemMessage
                        content = msg.text if hasattr(msg, 'text') else str(msg.content)
                        langchain_messages.append(LangChainSystemMessage(content=content))
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
                                import json as json_module
                                try:
                                    json_content = json_module.loads(response.content)
                                    completion = output_format.model_validate(json_content)
                                    return ChatInvokeCompletion[T](completion=completion, usage=usage)
                                except (json_module.JSONDecodeError, Exception):
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

        # Run the browser agent
        async def run_browser_agent_v2():
            ## run the browser agent using new packages
            from .browser_tool.runner import Runner, BrowserRequiredConfig
            runner = Runner(BrowserRequiredConfig(
                query=query,
                headless=headless,
                keep_alive=keep_alive
            ))

        async def run_browser_agent():
            """Execute the browser agent and return the result."""
            if settings.AIMessage is None and settings.HumanMessage is None:
                from langchain_core.messages import AIMessage as LangChainAIMessage
                from langchain_core.messages import HumanMessage as LangChainHumanMessage
                settings.AIMessage = LangChainAIMessage
                settings.HumanMessage = LangChainHumanMessage

            print("[SUBPROCESS] Initializing ModelManager and BrowserUseCompatibleLLM...")
            sys.stdout.flush()

            model_manager = ModelManager()
            browser_use_llm = BrowserUseCompatibleLLM(model_manager)

            print("[SUBPROCESS] Starting Browser instance...")
            sys.stdout.flush()

            browser = Browser(
                headless=headless,
                keep_alive=keep_alive,
                record_video_dir=settings.BASE_DIR / "basic_logs" / "browser_videos" if result_file else None,
                user_data_dir=settings.BROWSER_USE_USER_PROFILE_PATH if result_file else None,
            )

            print("[SUBPROCESS] Creating Agent...")
            sys.stdout.flush()

            agent = Agent(
                task=query,
                llm=browser_use_llm,
                browser=browser,
                max_failures=5,
                max_steps=500,
                vision_detail_level='high'
            )

            print("[SUBPROCESS] Starting agent execution...")
            sys.stdout.flush()

            try:
                ### we have to apply the monkey patch here for the keep_alive bug
                LocalBrowserWatchdog.on_BrowserStopEvent = on_BrowserStopEvent
                running_agent_task = asyncio.create_task(agent.run())

                # Keep-alive mode: start monitoring immediately (before awaiting agent.run())
                nonlocal monitor_queue
                if keep_alive and monitor_queue is None:
                    monitor_queue = queue.Queue()
                    monitering_browser_process(monitor_queue)

                await asyncio.create_task(load_custom_sessions(browser))  # this doesn't break
                result = await running_agent_task

                print("[SUBPROCESS] Agent execution completed!")
                sys.stdout.flush()
            except Exception as agent_error:
                print(f"[SUBPROCESS] CRITICAL: agent.run() failed: {agent_error}")
                print(traceback.format_exc())
                sys.stdout.flush()
                sys.exit(1)

            print("[SUBPROCESS] Closing agent and browser...")
            sys.stdout.flush()

            await agent.close()
            # await browser.stop() # this would kill the browser even if keep_alive is True
            ## delete the session data

            print("[SUBPROCESS] Cleanup completed!")
            sys.stdout.flush()

            final_result = str(result.final_result())
            print(f"[SUBPROCESS] Final result: {final_result}..." if len(final_result) > 200 else f"[SUBPROCESS] Final result: {final_result}")
            sys.stdout.flush()

            return final_result

        # Execute the agent
        try:
            result_str = asyncio.run(run_browser_agent())
        except Exception as asyncio_error:
            print(f"[SUBPROCESS] Asyncio execution failed: {asyncio_error}")
            sys.stdout.flush()
            raise

        # Write success result to file
        result_data = {
            "status": "success",
            "result": result_str
        }

        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)

        print(f"[SUBPROCESS] Result written to {result_file}")
        sys.stdout.flush()

        # IMPORTANT: In keep_alive mode, DO NOT exit immediately.
        # We must wait until monitoring detects the browser is closed.
        if not keep_alive:
            print("[SUBPROCESS] Exiting subprocess.")
            sys.stdout.flush()
            sys.exit(0)

        print("[SUBPROCESS] keep_alive=True -> waiting for browser to close...")
        sys.stdout.flush()

        if monitor_queue is not None:
            try:
                ok = monitor_queue.get(timeout=60 * 60 * 24)  # effectively 'wait forever'
                print(f"[SUBPROCESS] Keep-alive monitoring completed (ok={ok}), exiting subprocess.")
                sys.stdout.flush()
                sys.exit(0)
            except Exception as e:
                print(f"[SUBPROCESS] Keep-alive monitoring wait failed: {e}")
                print(traceback.format_exc())
                sys.stdout.flush()
                sys.exit(0)

        print("[SUBPROCESS] keep_alive=True but monitoring queue not found; exiting to avoid zombie subprocess.")
        sys.stdout.flush()
        sys.exit(0)
    except Exception as e:
        # Write error result to file
        error_result = {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }

        print(f"[SUBPROCESS] ERROR: {e}")
        print(traceback.format_exc())
        sys.stderr.flush()

        try:
            # Try to write error to result file
            result_file = args_dict.get('result_file') if args_dict else None
            if result_file:
                with open(result_file, 'w', encoding='utf-8') as f:
                    json.dump(error_result, f, ensure_ascii=False, indent=2)
        except:
            pass  # If we can't write to file, error is already printed to stderr

        sys.exit(1)


async def load_custom_sessions(browser: Browser):
    """Load custom browser sessions if needed

    This function waits for the browser to be ready (up to 30 seconds) before attempting to load session data.
    It restores the current URL, form data, and scroll position from a saved session file if available.
    """
    ### we have to wait until the browser is not connected
    async def wait_until_browser_ready():
        max_wait = 30  # seconds
        waited = 0
        while browser._cdp_client_root is None and waited < max_wait:
            print(f"[SUBPROCESS] Waited for browser to be ready... {waited}seconds upto {max_wait}seconds")
            await asyncio.sleep(1)
            waited += 1

        if browser._cdp_client_root is None:
            raise RuntimeError(f"Browser did not become ready in time. CDP client is still None. wated for {waited} seconds.")


    await wait_until_browser_ready()
    import json
    import aiofiles
    from src.config import settings
    from pathlib import Path
    session_data = {}
    session_file_path = Path(settings.BROWSER_USE_USER_PROFILE_PATH) / "custom_sessions.json"
    if not session_file_path.exists():
        print("[SUBPROCESS] No custom session file found, starting fresh.")
        return
    async with aiofiles.open(session_file_path, 'r', encoding='utf-8') as f:
        content = await f.read()
        session_data = json.loads(content)

    current_url = session_data.get('current_url', None)
    form_data:dict = session_data.get('form_data', {})
    scroll_pos = session_data.get('scroll_position', {'x': 0, 'y': 0})

    if current_url:
        from browser_use.browser.events import NavigateToUrlEvent
        await browser.event_bus.dispatch(NavigateToUrlEvent(url=current_url))
        await asyncio.sleep(3)

        # fill form data
        cdp_session = await browser.get_or_create_cdp_session()
        form_data_string = json.dumps(form_data)

        restore_form_script = f"""
        (function() {{
                const formData = {form_data_string};
                let restoredCount = 0;
                
                for (const [key, value] of Object.entries(formData)) {{
                    // Try to find input by name, id, or aria-label
                    let input = document.querySelector(`input[name="${{key}}"]`) ||
                               document.querySelector(`textarea[name="${{key}}"]`) ||
                               document.querySelector(`select[name="${{key}}"]`) ||
                               document.querySelector(`#${{key}}`) ||
                               document.querySelector(`input[aria-label="${{key}}"]`);
                    
                    if (input) {{
                        input.value = value;
                        // Trigger input event so React/Vue/Angular detect the change
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

        print(f"[SUBPROCESS] Restored {restore_result.get('result', {}).get('value', 0)} out of {len(form_data)} form fields.")


        # scroll to position
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

        print("[SUBPROCESS] Restored scroll position.")
    else:
        ## no session to restore
        print("[SUBPROCESS] No URL found in custom session data to restore.")
        pass

    print(f"[SUBPROCESS] Loaded custom session data: {session_data}")
    sys.stdout.flush()
    return


async def save_custom_sessions(browser: Browser):
    """Save custom browser sessions if needed (placeholder)."""
    if browser._cdp_client_root is None and not hasattr(browser, '_cdp_client_root'):
        print("[SUBPROCESS] Browser CDP client not ready, skipping session save.")
        return
    current_url = await browser.get_current_page_url()
    cdp_session = await browser.get_or_create_cdp_session()

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

    # Extract scroll position via JavaScript
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


    ## now save them into the local storage
    ## todo this needs to be secure but in future this is currently in development
    from src.utils.timestamp_util import get_formatted_timestamp
    timestamp = get_formatted_timestamp()
    session_data = {
        'current_url': current_url,  # ← Fixed key name
        'form_data': form_data,
        'scroll_position': scroll_pos,
        'timestamp': timestamp
    }

    import json
    import aiofiles
    from src.config import settings
    from pathlib import Path
    session_file_path = Path(settings.BROWSER_USE_USER_PROFILE_PATH) / 'custom_sessions.json'
    async with aiofiles.open(session_file_path, 'w', encoding='utf-8') as f:
        content = json.dumps(session_data, indent=2)
        await f.write(content)

    print(f"[SUBPROCESS] Custom session saved to {session_file_path}")
    sys.stdout.flush()


async def on_BrowserStopEvent(self, event: BrowserStopEvent) -> None:
    """Monkey patched stop watchdog to prevent browser from closing if keep_alive is True."""
    force_kill = getattr(event, 'force', False)  # ✅ Corrected: use 'force' not 'force_close'
    browser_profile = getattr(self.browser_session, 'browser_profile', None)
    keep_alive = getattr(browser_profile, 'keep_alive', False)
    if self._subprocess and self.browser_session.is_local:
        if keep_alive and not force_kill:
            print("[SUBPROCESS] Keep alive is True, skipping browser stop. applying monkey patch.")
            sys.stdout.flush()
            return
    # ✅ Corrected: use self.event_bus.dispatch() (synchronous, no await)
    self.event_bus.dispatch(BrowserKillEvent())



async def watch_process_alive() -> bool:
    """
    Monitor the ghost process (browser's parent) and exit when it dies.

    The ghost process is created by browser-use/Playwright and owns Chrome.
    When user closes browser, Chrome dies → ghost detects it → ghost exits.
    We detect ghost's death and exit gracefully.
    """
    #     this would watch the process of chrome and the ghost process of sub runner to calculate that does user closed the browser or not if keep alive is true
    #     if the processes are running sleep for 5 seconds then again wait till the browser process didn't close
    browser_pid = None
    browser_actual_parent_runner_pid = None
    browser_ghost_parent_runner_pid = None
    killer_flag = -1

    def get_browser_process_info():
        nonlocal browser_pid, browser_actual_parent_runner_pid, browser_ghost_parent_runner_pid, killer_flag
        try:
            if killer_flag <= 0:
                for process in psutil.process_iter(['pid', 'name', 'cmdline', 'ppid']):
                            try:
                                name = (process.info.get('name') or '').lower()
                                if 'chrome' in name or 'chromium' in name:
                                    cmdline = ' '.join(process.info.get('cmdline') or []).lower()
                                    if '--remote-debugging-port' in cmdline:
                                        browser_pid = process.info['pid']
                                        browser_ghost_parent_runner_pid = process.info['ppid']
                                        browser_actual_parent_runner_pid = None
                                        try:
                                            if psutil.pid_exists(browser_ghost_parent_runner_pid):
                                                parent_process = psutil.Process(browser_ghost_parent_runner_pid)
                                                browser_actual_parent_runner_pid = parent_process.ppid()
                                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                                            browser_actual_parent_runner_pid = None

                                        print(
                                            f"[SUBPROCESS] Detected browser process PID: {browser_pid}, Parent (ghost) PID: {browser_ghost_parent_runner_pid}, Grand-parent PID: {browser_actual_parent_runner_pid}")
                                        sys.stdout.flush()
                                        break
                            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                                continue

            if killer_flag == -1: # that means this is executing first time
                if browser_pid:
                    # that means we found the process
                    killer_flag += 1
                    # resetting the variables for next check
                    browser_pid = None
                    browser_ghost_parent_runner_pid = None
                    browser_actual_parent_runner_pid = None
            elif killer_flag == 0:  # that means we did found the process earlier
                # and if the browser process is still not none means browser is still running after getting found
                if browser_pid:
                    # erase it now !! 
                    browser_pid = None
                    browser_ghost_parent_runner_pid = None
                    browser_actual_parent_runner_pid = None
                    pass
                else:
                    # that means we found the browser process earlier but now its gone
                    print(f"[SUBPROCESS] Detected browser process has exited.")
                    killer_flag += 1
                pass
                # now check that does it gone away or not
        except Exception as e:
            print(f"[SUBPROCESS] Failed to get browser process info: {e}")
            sys.stdout.flush()

    while killer_flag <= 0:
        await asyncio.sleep(3)
        if get_browser_process_info():
            break
    return True


def monitering_browser_process(result_que: queue.Queue) -> Thread:
    """Start a daemon thread that runs an asyncio loop to monitor browser closure.

    It will put True into result_que once the browser is closed.
    """

    def _runner(q: queue.Queue):
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            q.put(loop.run_until_complete(watch_process_alive()))
        except Exception as e:
            print(f"[SUBPROCESS][MONITOR] Monitoring thread crashed: {e}")
            print(traceback.format_exc())
            sys.stdout.flush()
            q.put(True)  # fail-open so parent can unblock
        finally:
            try:
                loop.close()
            except Exception:
                pass

    t = Thread(target=_runner, daemon=True, args=(result_que,))
    t.start()
    return t



if __name__ == '__main__':
    main()
