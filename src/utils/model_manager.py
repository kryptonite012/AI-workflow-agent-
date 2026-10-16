import json
import os
import subprocess
import time
from typing import ClassVar, Optional, Any, Iterator, Union

from langchain_core.language_models import LanguageModelInput
from langchain_core.messages import BaseMessageChunk, BaseMessage, AIMessageChunk
from langchain_core.runnables import RunnableConfig
from langchain_ollama import ChatOllama

from src.config import settings
from src.utils.open_ai_integration import OpenAIIntegration
from src.ui.diagnostics.debug_helpers import debug_info, debug_warning, debug_error

# 🎨 Rich Traceback Integration (updated path after refactor)
try:  # Lazy-resilient import in case path shifts
    from src.ui.diagnostics.rich_traceback_manager import (
        RichTracebackManager,
        rich_exception_handler,
        safe_execute,
    )
except ImportError:  # Fallback (older path compatibility)
    from src.ui.diagnostics import rich_traceback_manager as _rtm  # type: ignore

    RichTracebackManager = _rtm.RichTracebackManager  # type: ignore
    rich_exception_handler = _rtm.rich_exception_handler  # type: ignore
    safe_execute = getattr(_rtm, "safe_execute", lambda f, *a, **k: f(*a, **k))  # type: ignore

# 🔧 COMPLETELY ISOLATED DEBUG LOGGING - NO IMPORTS, NO DEPENDENCIES
# (Replaced by debug_helpers unified system_logging)


class ModelManager(ChatOllama):
    """
    Singleton class for managing Ollama model loading and switching.

    Inherits from ChatOllama and provides methods to load, stop, and invoke models.
    Ensures only one model is active at a time and manages the current model state.
    """

    instance: ClassVar[Optional["ModelManager"]] = None
    current_model: ClassVar[Optional[str]] = None
    _openai_integration: ClassVar[Optional[OpenAIIntegration]] = None
    _is_openai_mode: ClassVar[bool] = False

    model_list: ClassVar[list[str]] = [
        settings.DEFAULT_MODEL,
        settings.CYPHER_MODEL,
        settings.CLASSIFIER_MODEL,
    ]
    api_model_list: ClassVar[list[str]] = [settings.GPT_MODEL, settings.KIMI_MODEL]

    def __new__(cls, *args: Any, **kwargs: Any) -> "ModelManager":
        """
        Ensures only one instance of ModelManager exists (Singleton pattern).
        """
        if cls.instance is None:
            cls.instance = super(ModelManager, cls).__new__(cls)
        return cls.instance

    @rich_exception_handler("ModelManager Initialization")
    def __init__(self, *args, **kwargs):
        """
        Initializes the ModelManager and loads the specified model.

        Args:
            model (str): The model to load (default is config.DEFAULT_MODEL).
            Other keyword arguments are passed to the parent ChatOllama class.
        """
        try:
            if getattr(self, "_initialized", False):
                # If instance already exists, skip re-initialization
                return

            self._initialized = True

            # Check if this should use OpenAI integration
            if len(kwargs) == 0 or "model" not in kwargs:
                kwargs["model"] = settings.API_DEFAULT_API_MODEL
            if kwargs.get("model") in ModelManager.api_model_list:
                try:
                    # For OpenAI models, create integration and mark as OpenAI mode
                    ModelManager._openai_integration = OpenAIIntegration(
                        api_key=kwargs.get("api_key", settings.OPEN_AI_API_KEY),
                        model=kwargs.get("model", settings.API_DEFAULT_API_MODEL),
                    )
                    ModelManager._is_openai_mode = True
                    # Still initialize ChatOllama with a default model to avoid issues
                    super().__init__(
                        model=settings.DEFAULT_MODEL,
                        **{k: v for k, v in kwargs.items() if k != "model"},
                    )
                except Exception as openai_error:
                    RichTracebackManager.handle_exception(
                        openai_error,
                        context="OpenAI Integration Setup",
                        extra_context={
                            "model": kwargs.get("model", "Unknown"),
                            "api_key_available": bool(
                                kwargs.get("api_key", settings.OPEN_AI_API_KEY)
                            ),
                        },
                    )
                    raise
            else:
                try:
                    # Initialize as regular ChatOllama instance
                    ModelManager._openai_integration = None
                    ModelManager._is_openai_mode = False
                    super().__init__(*args, **kwargs)
                    ModelManager.load_model(kwargs.get("model", settings.DEFAULT_MODEL))
                except Exception as ollama_error:
                    RichTracebackManager.handle_exception(
                        ollama_error,
                        context="Ollama Model Setup",
                        extra_context={
                            "model": kwargs.get("model", settings.DEFAULT_MODEL),
                            "args": str(args)[:100],
                            "kwargs": str(
                                {k: v for k, v in kwargs.items() if k != "api_key"}
                            )[:100],
                        },
                    )
                    raise
        except Exception as e:
            RichTracebackManager.handle_exception(
                e,
                context="ModelManager Initialization",
                extra_context={
                    "initialization_phase": "main_init",
                    "model_requested": kwargs.get("model", "Unknown"),
                },
            )
            raise

    @property
    def openai_chat(self) -> Optional[OpenAIIntegration]:
        """Property to access the OpenAI integration."""
        return ModelManager._openai_integration

    @classmethod
    @rich_exception_handler("Model Cleanup")
    def cleanup_all_models(cls):
        """
        Public method to explicitly clean up all models.
        Can be called manually or by signal handlers.
        """
        # OpenAI Integration Cleanup
        if cls._openai_integration is not None:
            try:
                debug_info(
                    "MODEL_MANAGER • CLEANUP",
                    "Cleaning up OpenAI integration",
                    {"cleanup_type": "openai_integration"},
                )
                OpenAIIntegration.cleanup()
                cls._openai_integration = None
                cls._is_openai_mode = False
                debug_info(
                    "MODEL_MANAGER • CLEANUP_SUCCESS",
                    "OpenAI integration cleanup completed",
                    {"cleanup_type": "openai_integration", "status": "completed"},
                )
            except Exception as openai_cleanup_error:
                RichTracebackManager.handle_exception(
                    openai_cleanup_error,
                    context="OpenAI Integration Cleanup",
                    extra_context={"integration_status": "cleanup_failed"},
                )
                debug_error(
                    "MODEL_MANAGER • CLEANUP_ERROR",
                    f"Error during OpenAI integration cleanup: {openai_cleanup_error}",
                    {
                        "cleanup_type": "openai_integration",
                        "error_type": type(openai_cleanup_error).__name__,
                    },
                )
        # Ollama Model Cleanup
        if cls.current_model:
            try:
                debug_info(
                    "MODEL_MANAGER • MODEL_CLEANUP",
                    f"Cleaning up model: {cls.current_model}",
                    {"cleanup_type": "model", "model_name": cls.current_model},
                )
                cls._stop_model()
                cls.current_model = None
                debug_info(
                    "MODEL_MANAGER • MODEL_CLEANUP_SUCCESS",
                    "Model cleanup completed",
                    {"cleanup_type": "model", "status": "completed"},
                )
            except Exception as model_cleanup_error:
                RichTracebackManager.handle_exception(
                    model_cleanup_error,
                    context="Ollama Model Cleanup",
                    extra_context={"current_model": cls.current_model},
                )
                debug_error(
                    "MODEL_MANAGER • MODEL_CLEANUP_ERROR",
                    f"Error during model cleanup: {model_cleanup_error}",
                    {
                        "cleanup_type": "model",
                        "error_type": type(model_cleanup_error).__name__,
                    },
                )

    @staticmethod
    def load_model(model_name: str):
        """
        Loads the specified model if available and manages switching between models.

        Args:
            model_name (str): The name of the model to load.

        Raises:
            ValueError: If the model_name is not in the list of available models.
        """
        running_one = subprocess.Popen(
            "ollama ps", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        r_read = running_one.stdout.read().decode("utf-8")

        for i in ModelManager.model_list:
            if r_read.__contains__(i):
                ModelManager.current_model = i
        if model_name not in ModelManager.model_list:
            raise ValueError(
                f"Model {model_name} is not available. Available models: {ModelManager.model_list}"
            )
        debug_info(
            "MODEL_MANAGER • MODEL_LOADING",
            f"Loading model {model_name}",
            {
                "current_model": ModelManager.current_model,
                "target_model": model_name,
                "action": "model_loading",
            },
        )
        if ModelManager.current_model is not None:
            if ModelManager.current_model == model_name:
                debug_info(
                    "MODEL_MANAGER • MODEL_ALREADY_LOADED",
                    f"Model {model_name} is already loaded",
                    {"model": model_name, "status": "already_loaded"},
                )
            else:
                ModelManager._stop_model()
                ModelManager.current_model = model_name
                debug_info(
                    "MODEL_MANAGER • MODEL_SWITCHED",
                    f"Switched to model {model_name}",
                    {"model": model_name, "status": "switched"},
                )
        else:
            ModelManager.current_model = model_name
            debug_info(
                "MODEL_MANAGER • MODEL_LOADED",
                f"Model {model_name} loaded successfully",
                {"model": model_name, "status": "loaded"},
            )

    @classmethod
    def _stop_model(cls):
        """
        Stops the currently running model using the Ollama CLI.
        """
        if cls.current_model:
            debug_info(
                "MODEL_MANAGER • MODEL_STOPPING",
                f"Stopping model: {cls.current_model}",
                {"model": cls.current_model, "action": "stopping"},
            )
            os.system(f"ollama stop {cls.current_model}")

    def invoke(
        self,
        input: LanguageModelInput,
        config: Optional[RunnableConfig] = None,
        *,
        stop: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> BaseMessage | Any:
        """
        Invokes the loaded model with the given input.

        Args:
            input (LanguageModelInput): The input message(s) for the model.
            config (Optional[RunnableConfig]): Optional configuration for the run.
            stop (Optional[list[str]]): Optional stop sequences.
            **kwargs: Additional keyword arguments.

        Returns:
            BaseMessage: The response from the model.
        """
        if (
            ModelManager._is_openai_mode
            and ModelManager._openai_integration is not None
        ):
            # If using OpenAIIntegration, delegate to it
            # if input is a list, treat the first element as system message then the rest as user messages
            if isinstance(input, list) and len(input) > 0:
                system_message = (
                    input[0].content if hasattr(input[0], "content") else str(input[0])
                )
                user_messages = [
                    msg.content if hasattr(msg, "content") else str(msg)
                    for msg in input[1:]
                ]
                messages = [{"role": "system", "content": system_message}] + [
                    {"role": "user", "content": msg} for msg in user_messages
                ]
                open_ai_response = ModelManager._openai_integration.generate_text(
                    messages=messages
                )
            else:
                # If input is not a list, treat it as a single user message
                open_ai_response = ModelManager._openai_integration.generate_text(
                    prompt=getattr(input, "content", str(input))
                )
            return settings.AIMessage(content=str(open_ai_response))
        else:
            return super().invoke(input=input, config=config, stop=stop, **kwargs)

    def stream(
        self,
        input: LanguageModelInput,
        config: Optional[RunnableConfig] = None,
        *,
        stop: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> Iterator[BaseMessageChunk]:
        """
        Streams the response from the model for the given input.

        Args:
            input (LanguageModelInput): The input message(s) for the model.
            config (Optional[RunnableConfig]): Optional configuration for the run.
            stop (Optional[list[str]]): Optional stop sequences.
            **kwargs: Additional keyword arguments.

        Returns:
            Iterator[BaseMessageChunk]: An iterator yielding message chunks.
        """
        if (
            ModelManager._is_openai_mode
            and ModelManager._openai_integration is not None
        ):
            # If using OpenAIIntegration, delegate to it
            open_ai_response = ModelManager._openai_integration.generate_text(
                prompt=getattr(input[0], "content")
                if isinstance(input, list) and not isinstance(input[0], dict)
                else input.content,
                stream=True,
            )
            return self._normalize_streaming_response(open_ai_response)
        return super().stream(input=input, config=config, stop=stop, **kwargs)

    @classmethod
    def _normalize_streaming_response(
        cls, response_to_parse: Iterator[str]
    ) -> Iterator[AIMessageChunk]:
        """
        Normalizes the streaming response from OpenAIIntegration to AIMessageChunk format.

        Args:
            response_to_parse (Iterator[str]): The streaming response generator (yields content strings).

        Returns:
            Iterator[AIMessageChunk]: An iterator yielding AIMessageChunk objects with content only.
        """
        last_time = time.time()
        buffer = ""
        for chunk in response_to_parse:
            buffer += chunk
            current_time = time.time()
            if current_time - last_time >= 0.1:  # Yield every 100 milliseconds
                if buffer:
                    yield AIMessageChunk(content=buffer)
                    buffer = ""
                last_time = current_time
        if buffer:
            yield AIMessageChunk(content=buffer)

    @classmethod
    def convert_to_json(
        cls, response: Union[str, dict, list, BaseMessage]
    ) -> Union[dict, list]:
        """
        🔧 ENHANCED v4.0: JSON extraction with COMPLETELY ISOLATED system_logging (no recursion possible)

        Args:
            response: Response to convert (can be string, dict, list, or BaseMessage)

        Returns:
            dict or list: The extracted JSON object or fallback structure
        """
        # Handle already parsed objects (most common case for async responses)
        if isinstance(response, (dict, list)):
            debug_info(
                "MODEL_MANAGER • JSON_CONVERSION",
                "Response already parsed as JSON",
                {
                    "response_type": type(response).__name__,
                    "conversion_method": "direct_passthrough",
                },
            )
            return response

        # Handle BaseMessage objects with priority-based content extraction
        if isinstance(response, BaseMessage):
            content = response.content
        else:
            content = str(response)

        # Handle empty or None responses
        if not content or content.strip() == "":
            debug_warning(
                "MODEL_MANAGER • JSON_CONVERSION_EMPTY",
                "Empty response detected, returning fallback",
                {
                    "response_type": type(response).__name__,
                    "fallback_action": "empty_response_wrapper",
                },
            )
            return {"content": "empty_response"}

        # Try 1: Direct JSON parsing (highest priority)
        try:
            parsed = json.loads(content)
            debug_info(
                "MODEL_MANAGER • JSON_CONVERSION_DIRECT",
                "Direct JSON parsing successful",
                {
                    "response_type": type(parsed).__name__,
                    "conversion_method": "direct_parsing",
                },
            )
            return parsed
        except (json.JSONDecodeError, TypeError):
            pass

        # Try 2: Extract from markdown code blocks
        import re

        markdown_pattern = r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```"
        markdown_match = re.search(markdown_pattern, content, re.DOTALL)
        if markdown_match:
            try:
                parsed = json.loads(markdown_match.group(1))
                debug_info(
                    "MODEL_MANAGER • JSON_CONVERSION_MARKDOWN",
                    "JSON extracted from markdown code block",
                    {
                        "response_type": type(parsed).__name__,
                        "conversion_method": "markdown_extraction",
                    },
                )
                return parsed
            except json.JSONDecodeError:
                pass

        # Try 3: Find JSON objects with proper brace matching (prioritize objects for agent_mode)
        json_objects = []

        # Look for JSON objects first (priority for agent mode compliance)
        brace_count = 0
        start_pos = -1
        for i, char in enumerate(content):
            if char == "{":
                if brace_count == 0:
                    start_pos = i
                brace_count += 1
            elif char == "}":
                brace_count -= 1
                if brace_count == 0 and start_pos != -1:
                    try:
                        json_str = content[start_pos : i + 1]
                        parsed = json.loads(json_str)
                        json_objects.append(("object", parsed))
                    except json.JSONDecodeError:
                        pass
                    start_pos = -1

        # Then look for JSON arrays
        bracket_count = 0
        start_pos = -1
        for i, char in enumerate(content):
            if char == "[":
                if bracket_count == 0:
                    start_pos = i
                bracket_count += 1
            elif char == "]":
                bracket_count -= 1
                if bracket_count == 0 and start_pos != -1:
                    try:
                        json_str = content[start_pos : i + 1]
                        parsed = json.loads(json_str)
                        json_objects.append(("array", parsed))
                    except json.JSONDecodeError:
                        pass
                    start_pos = -1

        # Return first valid JSON object found (prefer objects over arrays for agent compliance)
        if json_objects:
            # Sort to prioritize objects over arrays
            json_objects.sort(key=lambda x: 0 if x[0] == "object" else 1)
            json_type, parsed_json = json_objects[0]

            debug_info(
                "MODEL_MANAGER • JSON_CONVERSION_EXTRACTED",
                f"JSON {json_type} extracted via pattern matching",
                {
                    "response_type": type(parsed_json).__name__,
                    "conversion_method": f"pattern_matching_{json_type}",
                    "objects_found": len([x for x in json_objects if x[0] == "object"]),
                    "arrays_found": len([x for x in json_objects if x[0] == "array"]),
                },
            )
            return parsed_json

        # Fallback: wrap content with enhanced error information
        debug_warning(
            "MODEL_MANAGER • JSON_CONVERSION_FAILED",
            "All JSON parsing methods failed, returning content fallback",
            {
                "content_preview": str(content)[:100] if content else "",
                "content_length": len(content) if content else 0,
                "fallback_action": "wrap_as_content",
                "conversion_method": "fallback_wrapper",
            },
        )

        # Enhanced fallback with attempt to preserve useful information
        return {
            "content": str(content),
            "parsing_error": "Failed to extract valid JSON",
            "original_response_type": type(response).__name__,
        }
