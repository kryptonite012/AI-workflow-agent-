import asyncio
from enum import Enum
from pathlib import Path
import sys
from browser_use import BrowserSession
from browser_use.browser.events import BaseEvent

import json
import aiofiles

class SessionManagerEnums(Enum):
    # all the session manager functions must be private methods
    SAVE_SESSION = "__save_custom_sessions"
    LOAD_SESSION = "__load_custom_sessions"

    def get_callable(self, instance):
        """
        Retrieves the bound method from the SessionManager instance.
        Handles Python's name mangling for private methods automatically! 🧩
        """
        method_name = f"_{instance.__class__.__name__}{self.value}"
        return getattr(instance, method_name)

class SessionManager:
    """
    Manages user sessions for the browser tool.

    **Architecture: Attach from Here**
    Use the `attach` method to hook this manager into the browser's lifecycle events.
    This keeps the 'Runner' code decoupled from specific session saving/loading implementation details.

    Current implementation supports:
    (
        - current url
        - cookies
        - scroll position
        - time stamps
    )
    """


    def attach(self, session_event:SessionManagerEnums, browser_event : BaseEvent | None = None):
        """
        Attaches session management functions to browser events or **OUR CUSTOM EVENTS**.
        :param session_event: The session management event to attach (SAVE_SESSION or LOAD_SESSION).
        :param browser_event: The browser event to attach to. If None, attaches to custom events.
        # todo the custom event thing is not implemented yet so that's why we used none as type
        """
        if browser_event is not None:
            # Attach to a specific browser event
            # We must CALL () the method and pass the browser from the event 'e'
            try:
                browser_event.event_bus.on(browser_event, lambda e: session_event.get_callable(self)(e.browser_session))
            except Exception as ex:
                print(f"[SUBPROCESS] Failed to attach session manager to browser event: {ex}")
        elif browser_event is  None:
            # Attach to custom events (placeholders for now)
            raise NotImplementedError("Custom event attachment not implemented yet.")



    def __init__(self, profile_dir : Path = None):
        self._profile_dir = profile_dir if profile_dir else Path("./browser_profiles/main_profile")


    async def __save_custom_sessions(self, browser: BrowserSession):
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




    async def __load_custom_sessions(self, browser: BrowserSession):
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
                raise RuntimeError(
                    f"Browser did not become ready in time. CDP client is still None. wated for {waited} seconds.")

        await wait_until_browser_ready()
        from src.config import settings
        session_data = {}
        session_file_path = Path(settings.BROWSER_USE_USER_PROFILE_PATH) / "custom_sessions.json"
        if not session_file_path.exists():
            print("[SUBPROCESS] No custom session file found, starting fresh.")
            return
        async with aiofiles.open(session_file_path, 'r', encoding='utf-8') as f:
            content = await f.read()
            session_data = json.loads(content)

        current_url = session_data.get('current_url', None)
        form_data: dict = session_data.get('form_data', {})
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

            print(
                f"[SUBPROCESS] Restored {restore_result.get('result', {}).get('value', 0)} out of {len(form_data)} form fields.")

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