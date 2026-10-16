from src.config import settings
from src.tools.lggraph_tools.tool_response_manager import ToolResponseManager
from src.tools.lggraph_tools.tools.browser_tool import browser_use_tool


class BrowserUseWrapper:
    def __init__(self, **kwargs):

        self.query = kwargs.get("query", "")
        self.head_less_mode = kwargs.get("head_less_mode", False)
        self.log = kwargs.get("log", True)
        self.keep_alive = kwargs.get("keep_alive", True)
        self._run_browser_use()

    def _run_browser_use(self):
        try:
            response = browser_use_tool(self.query, self.head_less_mode, self.log, self.keep_alive)
            if response is not None:
                ToolResponseManager().set_response(
                    [settings.AIMessage(content=response)]
                )
            else:
                ToolResponseManager().set_response(
                    [settings.AIMessage(content="No response from browser use tool.")]
                )
        except Exception as e:
            error_message = f"BrowserAgent failed with an exception: {e}"
            ToolResponseManager().set_response(
                [settings.AIMessage(content=error_message)]
            )
