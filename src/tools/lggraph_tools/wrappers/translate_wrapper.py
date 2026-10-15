from src.config import settings
from src.tools.lggraph_tools.tool_response_manager import ToolResponseManager


class TranslateToolWrapper:
    """
    Wrapper for the Translate Tool.
    This class is used to manage the response from the Translate Tool.
    """

    def __init__(self, message: str, target_language: str):
        from src.tools.lggraph_tools.tools.translate_tool import translate_text

        """
        Initialize the TranslateToolWrapper with a message and target language.

        :param message: The message to translate.
        :param target_language: The language to translate the message into.
        """
        self.message = message
        self.target_language = target_language

        # Call the translate_text function with the message and target language
        result = translate_text(self.message, self.target_language)
        if result is not None:
            ToolResponseManager().set_response([settings.AIMessage(content=result)])
