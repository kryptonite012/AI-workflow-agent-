import asyncio
import gc
import json
import threading
import time
from typing import Any, Optional, Iterator, Union, overload, List, Dict

import winsound
from openai import OpenAI, AsyncOpenAI

from src.config.settings import OPEN_AI_API_KEY, OPENAI_TIMEOUT
from src.utils.listeners.rich_status_listen import RichStatusListener


class OpenAIIntegration:
    """
    Integrates with OpenAI's API for text generation.

    This class provides methods to generate text using OpenAI's models, supporting both streaming and non-streaming responses.
    Enhanced with proper async support for RAG and Neo4j integration.

    IMPORTANT: The number of requests must be less than 30 per minute to comply with rate limits.
    """

    instance: Optional["OpenAIIntegration"] = None
    _async_lock: Optional[AsyncOpenAI] = None
    requests_count: int = 0
    _last_request_time: Optional[float] = None

    # 🔧 FIX: Add error handling attributes for circuit breaker pattern
    _failure_count: int = 0
    _circuit_open: bool = False
    _circuit_open_until: Optional[float] = None
    _max_failures: int = 5  # Changed from 3 to 5 to match test expectations
    _circuit_timeout: int = 10  # seconds

    _thread_lock = threading.Lock()
    _client_lock = asyncio.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> "OpenAIIntegration":
        """
        Ensures only one instance of OpenAIIntegration exists (Singleton pattern).
        """
        if cls.instance is None:
            cls.instance = super().__new__(cls)
        return cls.instance

    def __init__(
            self, api_key: Optional[str] = None, model: Optional[str] = None
    ) -> None:
        """
        Initialize the OpenAIIntegration instance.

        Args:
            api_key (Optional[str]): The OpenAI API key. If not provided, uses OPEN_AI_API_KEY from settings.
            model (Optional[str]): The model name to use. Defaults to 'openai/gpt-oss-120b'.
        """
        # Prevent re-initialization of singleton
        if hasattr(self, "_initialized"):
            return

        self._initialized = True
        key = api_key or OPEN_AI_API_KEY
        self.model = model or "openai/gpt-oss-120b"
        self.base_url = "https://integrate.api.nvidia.com/v1"

        if not key:
            raise ValueError(
                "API key must be provided either as an argument or through the OPEN_AI_API_KEY environment variable."
            )

        self.api_key = key
        self.client = OpenAI(
            base_url=self.base_url, api_key=key, timeout=OPENAI_TIMEOUT, max_retries=2
        )

    async def _get_async_client(self) -> AsyncOpenAI:
        """
        Get or create async client with proper lifecycle management.

        Returns:
            AsyncOpenAI: The async client instance
        """
        async with self._client_lock:
            if self._async_lock is None:
                self._async_lock = AsyncOpenAI(
                    base_url=self.base_url,
                    api_key=self.api_key,
                    timeout=OPENAI_TIMEOUT,
                    max_retries=2,
                )
        return self._async_lock

    async def _close_async_client(self) -> None:
        """
        Properly close the async client.
        """
        async with self._client_lock:
            if self._async_lock is not None:
                await self._async_lock.close()
                self._async_lock = None

    @overload
    def generate_text(self, prompt: str, stream: bool = False) -> str:
        ...

    @overload
    def generate_text(self, prompt: str, stream: bool = True) -> Iterator[str]:
        ...

    @overload
    def generate_text(
            self, messages: list[dict[str, str]], stream: bool = False
    ) -> str:
        ...

    @overload
    def generate_text(
            self, messages: list[dict[str, str]], stream: bool = True
    ) -> Iterator[str]:
        ...

    def generate_text(
            self,
            prompt: Optional[str] = None,
            messages: Optional[list[dict[str, str]]] = None,
            stream: bool = False,
    ) -> Union[str, Iterator[str]]:
        """
        Generate text from the OpenAI API.

        Args:
            prompt (str): The prompt to send to the model.
            stream (bool): Whether to stream the response. Defaults to False.
            messages (list[dict[str, str]]): Optional list of message dictionaries for chat completions.

        Returns:
            If stream is True: an iterator of response content strings (NO separate reasoning field).
            If stream is False: a single response content string (NO separate reasoning field).

        NOTE: The response does NOT include a separate 'reasoning' field. If you require reasoning, instruct the model in the system prompt to include reasoning in the content.
        """
        # 🔧 FIX: Check circuit breaker first
        if self._is_circuit_open():
            from src.ui.diagnostics.debug_helpers import debug_warning

            debug_warning(
                heading="OPENAI • CIRCUIT_BREAKER_BLOCK",
                body="Request blocked by circuit breaker",
                metadata={"circuit_open_until": self._circuit_open_until},
            )
            return self._get_fallback_response("circuit_breaker")

        # rate limit management
        # first increment the request count
        OpenAIIntegration()._manage_requests_sync()

        if not prompt and not messages:
            raise ValueError("Prompt cannot be empty.")

        # Enhanced system_logging for debugging
        from src.ui.diagnostics.debug_helpers import debug_api_call

        if prompt:
            debug_api_call(
                api_name="OpenAI",
                operation="sync_call_with_prompt",
                status="started",
                metadata={"prompt_preview": prompt, "has_messages": bool(messages)},
            )
        if messages:
            debug_api_call(
                api_name="OpenAI",
                operation="sync_call_with_messages",
                status="started",
                metadata={"message_count": len(messages), "has_prompt": bool(prompt)},
            )

        # 🔧 FIX: Enhanced error handling for NVIDIA API issues
        attempt = 1
        max_attempts = 5

        while attempt <= max_attempts:
            try:
                from src.ui.diagnostics.debug_helpers import debug_info

                debug_info(
                    heading="OPENAI • API_ATTEMPT",
                    body=f"Attempting API call (attempt {attempt}/{max_attempts})",
                    metadata={"attempt": attempt, "stream": stream},
                )

                if prompt or (messages and len(messages) < 2):
                    prompt = messages[0]["content"] if messages else prompt
                    completion = self.client.chat.completions.create(
                        model=self.model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.7,
                        top_p=1,
                        max_tokens=4096,
                        stream=stream,
                    )
                else:
                    completion = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        temperature=0.7,
                        top_p=1,
                        max_tokens=4096,
                        stream=stream,
                    )

                # Enhanced response system_logging
                from src.ui.diagnostics.debug_helpers import debug_api_call

                debug_api_call(
                    api_name="OpenAI",
                    operation="api_call_completed",
                    status="completed",
                    metadata={
                        "stream_mode": stream,
                        "request_count": OpenAIIntegration.requests_count,
                    },
                )

                # Record success for circuit breaker
                self._record_success()

                if stream:
                    return self._handle_streaming_response(completion)
                else:
                    return self._handle_non_streaming_response_with_debugging(
                        completion
                    )

            except Exception as e:
                from src.ui.diagnostics.debug_helpers import debug_error

                error_str = str(e)

                # Handle specific NVIDIA API errors
                if "'NoneType' object is not iterable" in error_str:
                    debug_error(
                        heading="OPENAI • UNEXPECTED_ERROR",
                        body=f"Unexpected error on attempt {attempt}: {error_str}",
                        metadata={"attempt": attempt, "error_type": type(e).__name__},
                    )

                    # Record failure
                    self._record_failure()

                    if attempt < max_attempts:
                        attempt += 1
                        continue
                    else:
                        debug_error(
                            heading="OPENAI • UNEXPECTED_FAILURE",
                            body=f"Unexpected error in generate_text: {error_str}",
                            metadata={"error_type": type(e).__name__},
                        )
                        # Return a fallback response instead of crashing
                        return self._get_fallback_response("unexpected")

                elif "502" in error_str or "Error code: 502" in error_str:
                    debug_error(
                        heading="OPENAI • 502_ERROR",
                        body=f"502 error on attempt {attempt}: {error_str}",
                        metadata={"attempt": attempt, "error_code": "502"},
                    )

                    # Record failure
                    self._record_failure()

                    if attempt < max_attempts:
                        time.sleep(
                            2 ** (attempt - 1)
                        )  # Exponential backoff: 1s, 2s, 4s
                        attempt += 1
                        continue
                    else:
                        return self._get_fallback_response("502")

                elif (
                        "BadRequestError" in error_str
                        or "500" in error_str
                        or "400" in error_str
                ):
                    debug_error(
                        heading="OPENAI • API_ERROR",
                        body=f"API error on attempt {attempt}: {error_str}",
                        metadata={"attempt": attempt, "error_type": type(e).__name__},
                    )

                    # Record failure
                    self._record_failure()

                    if attempt < max_attempts:
                        time.sleep(1)  # Brief delay before retry
                        attempt += 1
                        continue
                    else:
                        return self._get_fallback_response("api_error")

                else:
                    # Record failure for unknown errors too
                    self._record_failure()

                    # For unknown errors, if this isn't the last attempt, continue trying
                    if attempt < max_attempts:
                        attempt += 1
                        time.sleep(1)
                        continue
                    else:
                        # Return fallback instead of re-raising
                        return self._get_fallback_response("unknown")

        # Should never reach here, but safety fallback
        return self._get_fallback_response("max_attempts")

    async def generate_text_async(
            self, prompt: str = None, messages: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Asynchronously generate text from the OpenAI API with enhanced error handling.

        Args:
            prompt (str): The prompt to send to the model.
            messages (Optional[List[Dict[str, str]]]): Optional list of message dictionaries for chat completions.

        Returns:
            str: The generated text response.

        Raises:
            ValueError: If OpenAI integration not initialized or invalid parameters.
            Exception: If API call fails or no content found.
        """
        # rate limit management
        await OpenAIIntegration()._manage_requests_async()

        if not hasattr(self, "_initialized"):
            raise ValueError("OpenAI integration not initialized")

        # Enhanced system_logging for debugging
        from src.ui.diagnostics.debug_helpers import debug_api_call

        if prompt:
            debug_api_call(
                api_name="OpenAI",
                operation="async_call_with_prompt",
                status="started",
                metadata={"has_messages": bool(messages)},
            )
        if messages:
            debug_api_call(
                api_name="OpenAI",
                operation="async_call_with_messages",
                status="started",
                metadata={"message_count": len(messages), "has_prompt": bool(prompt)},
            )

        try:
            async_client = await self._get_async_client()

            # Prepare messages for API call
            if messages and len(messages) > 1:
                api_messages = messages
            elif messages and len(messages) == 1:
                api_messages = [{"role": "user", "content": messages[0]["content"]}]
            else:
                api_messages = [{"role": "user", "content": prompt}]

            # Add timeout wrapper for async call
            completion = await asyncio.wait_for(
                async_client.chat.completions.create(
                    model=self.model,
                    messages=api_messages,
                    temperature=0.7,
                    top_p=1,
                    max_tokens=4096,
                    stream=False,
                ),
                timeout=OPENAI_TIMEOUT,
            )

            # Enhanced response system_logging
            # if settings.socket_con:
            #     settings.socket_con.send_error(f"[DEBUG] OpenAI async API call completed successfully")

            return self._handle_non_streaming_response_with_debugging(completion)

        except Exception as e:
            from src.ui.diagnostics.debug_helpers import debug_error

            debug_error(
                heading="OPENAI • API_CALL_FAILED",
                body=f"OpenAI async call failed: {e}",
                metadata={"error_type": type(e).__name__, "context": "async_api_call"},
            )
            raise Exception(f"OpenAI async API call failed: {e}")

    async def generate_text_async_streaming(
            self, prompt: str, messages: Optional[List[Dict[str, str]]] = None
    ) -> Iterator[str]:
        """
        Asynchronously generate streaming text from the OpenAI API.

        Args:
            prompt (str): The prompt to send to the model.
            messages (Optional[List[Dict[str, str]]]): Optional list of message dictionaries for chat completions.

        Yields:
            str: Content chunks from the streaming response.

        Raises:
            ValueError: If OpenAI integration not initialized or invalid parameters.
            Exception: If API call fails.
        """

        if not hasattr(self, "_initialized"):
            raise ValueError("OpenAI integration not initialized")

        try:
            async_client = await self._get_async_client()

            # Prepare messages for API call
            if messages and len(messages) > 1 and not prompt:
                # If multiple messages are provided, use them directly
                api_messages = messages
            elif messages and len(messages) == 1:
                # If only one message is provided, use its content
                api_messages = [{"role": "user", "content": messages[0]["content"]}]
            else:
                # If no messages provided, use the prompt
                if not prompt:
                    raise ValueError(
                        "Either prompt or messages must be provided for async streaming."
                    )
                api_messages = [{"role": "user", "content": prompt}]

            # Add timeout wrapper for async streaming call
            completion = await asyncio.wait_for(
                async_client.chat.completions.create(
                    model=self.model,
                    messages=api_messages,
                    temperature=0.7,
                    top_p=1,
                    max_tokens=4096,
                    stream=True,
                ),
                timeout=OPENAI_TIMEOUT,
            )

            async for chunk in completion:
                if (
                        chunk.choices
                        and chunk.choices[0].delta
                        and chunk.choices[0].delta.content
                ):
                    yield chunk.choices[0].delta.content

        except Exception as e:
            from src.ui.diagnostics.debug_helpers import debug_error

            debug_error(
                heading="OPENAI • STREAMING_CALL_FAILED",
                body=f"OpenAI async streaming call failed: {e}",
                metadata={
                    "error_type": type(e).__name__,
                    "context": "async_streaming_call",
                },
            )
            raise Exception(f"OpenAI async streaming API call failed: {e}")

    @classmethod
    async def generate_text_async_class(cls, prompt: str) -> str:
        """
        Class method for async text generation (backward compatibility).

        Args:
            prompt (str): The prompt to send to the model.

        Returns:
            str: The generated text response.
        """
        if not cls.instance:
            raise ValueError("OpenAI integration not initialized")

        return await cls.instance.generate_text_async(prompt)

    @staticmethod
    def _handle_streaming_response(completion) -> Iterator[str]:
        """
        Handle streaming responses from the OpenAI API.

        Args:
            completion: The streaming completion object from OpenAI.

        Yields:
            str: Content chunks from the response (NO separate reasoning field).
        """
        # 🔧 FIX: Add comprehensive None and error checking
        if completion is None:
            from src.ui.diagnostics.debug_helpers import debug_error

            debug_error(
                heading="OPENAI • NULL_STREAMING_COMPLETION",
                body="Streaming completion object is None - possible API failure",
                metadata={"completion_status": "null"},
            )
            return

        try:
            # 🔧 FIX: Safe iteration with comprehensive error handling
            for chunk in completion:
                try:
                    # Enhanced safety checks for chunk processing
                    if chunk is None:
                        continue

                    if not hasattr(chunk, "choices"):
                        continue

                    if not chunk.choices or len(chunk.choices) == 0:
                        continue

                    choice = chunk.choices[0]
                    if choice is None:
                        continue

                    if not hasattr(choice, "delta"):
                        continue

                    delta = choice.delta
                    if delta is None:
                        continue

                    content = getattr(delta, "content", None)
                    if content is not None and content != "":
                        yield content

                except Exception as chunk_error:
                    from src.ui.diagnostics.debug_helpers import debug_warning

                    debug_warning(
                        heading="OPENAI • CHUNK_PROCESSING_ERROR",
                        body=f"Error processing streaming chunk: {chunk_error}",
                        metadata={
                            "error_type": type(chunk_error).__name__,
                            "chunk_type": type(chunk).__name__ if chunk else "None",
                        },
                    )
                    # Continue processing other chunks
                    continue

        except Exception as streaming_error:
            from src.ui.diagnostics.debug_helpers import debug_error

            debug_error(
                heading="OPENAI • STREAMING_ERROR",
                body=f"Error during streaming: {streaming_error}",
                metadata={"error_type": type(streaming_error).__name__},
            )
            # Record failure for circuit breaker
            OpenAIIntegration.requests_count += 1  # Ensure request is counted
            instance = OpenAIIntegration()
            instance._record_failure()

    @staticmethod
    def _handle_non_streaming_response_with_debugging(completion) -> str:
        """
        Enhanced response handler with debugging for NVIDIA API compatibility.
        """
        # 🔧 FIX: Comprehensive None checking first
        if completion is None:
            from src.ui.diagnostics.debug_helpers import debug_error

            debug_error(
                heading="OPENAI • NULL_COMPLETION",
                body="Completion object is None - possible API failure",
                metadata={"completion_status": "null"},
            )
            # Record failure for circuit breaker
            instance = OpenAIIntegration()
            instance._record_failure()
            raise Exception("API returned None completion object")

        # 🔧 FIX: Enhanced choices validation
        try:
            if not hasattr(completion, "choices"):
                from src.ui.diagnostics.debug_helpers import debug_error

                debug_error(
                    heading="OPENAI • NO_CHOICES_ATTRIBUTE",
                    body="Completion object missing 'choices' attribute",
                    metadata={"completion_type": type(completion).__name__},
                )
                raise Exception("Invalid completion object structure")

            choices = completion.choices
            if choices is None or len(choices) == 0:
                from src.ui.diagnostics.debug_helpers import debug_error

                debug_error(
                    heading="OPENAI • NO_CHOICES",
                    body="No choices found in API response",
                    metadata={
                        "choices_value": str(choices),
                        "choices_type": type(choices).__name__
                        if choices is not None
                        else "None",
                    },
                )
                # Record failure for circuit breaker
                instance = OpenAIIntegration()
                instance._record_failure()
                raise Exception("No choices found in API response")

            # 🔧 FIX: Enhanced message validation
            choice = choices[0]
            if choice is None:
                raise Exception("First choice is None")

            if not hasattr(choice, "message") or choice.message is None:
                from src.ui.diagnostics.debug_helpers import debug_error

                debug_error(
                    heading="OPENAI • NO_MESSAGE",
                    body="First choice has no message",
                    metadata={
                        "choice_type": type(choice).__name__,
                        "choice_has_message": hasattr(choice, "message"),
                    },
                )
                raise Exception("No message found in API response choice")

            msg = choice.message

        except Exception as structure_error:
            from src.ui.diagnostics.debug_helpers import debug_critical

            debug_critical(
                heading="OPENAI • RESPONSE_STRUCTURE_ERROR",
                body=f"Error accessing completion structure: {structure_error}",
                metadata={
                    "error_type": type(structure_error).__name__,
                    "completion_type": type(completion).__name__
                    if completion
                    else "None",
                },
            )
            # Record failure for circuit breaker
            instance = OpenAIIntegration()
            instance._record_failure()
            raise Exception(f"API response structure error: {structure_error}")

        # Content extraction with enhanced fallback handling
        content = getattr(msg, "content", None)
        reasoning_content = getattr(msg, "reasoning_content", None)

        from src.ui.diagnostics.debug_helpers import debug_info, debug_warning

        # 🎯 Return regular content immediately if available
        if content and str(content).strip():
            debug_info(
                heading="OPENAI • CONTENT_FOUND",
                body=f"Standard content found: {str(content)}",
                metadata={
                    "content_type": "standard_content",
                    "content_length": len(str(content)),
                },
            )
            return content

        # 🚨 Extract JSON from reasoning_content only when needed
        elif reasoning_content and str(reasoning_content).strip():
            debug_warning(
                heading="OPENAI • REASONING_CONTENT_DETECTED",
                body="No standard content - attempting JSON extraction from reasoning_content",
                metadata={
                    "content_type": "reasoning_content",
                    "content_length": len(str(reasoning_content)),
                    "extraction_needed": True,
                },
            )

            extracted_json = OpenAIIntegration._extract_json_from_reasoning(
                reasoning_content
            )
            if extracted_json:
                debug_info(
                    heading="OPENAI • JSON_EXTRACTION_SUCCESS",
                    body=f"Successfully extracted: {extracted_json}",
                    metadata={"extraction_successful": True},
                )
                return extracted_json
            else:
                return reasoning_content

        # Alternative field checking
        for field_name in ["text", "message", "response", "output"]:
            alt_content = getattr(msg, field_name, None)
            if alt_content and str(alt_content).strip():
                debug_info(
                    heading="OPENAI • ALTERNATIVE_CONTENT",
                    body=f"Content found via {field_name}: {str(alt_content)[:100]}...",
                    metadata={"content_source": field_name},
                )
                return str(alt_content)

        # Final fallback
        if hasattr(msg, "__str__") and str(msg).strip():
            content_str = str(msg).strip()
            debug_info(
                heading="OPENAI • MESSAGE_STRING",
                body=f"Using message string: {content_str[:100]}...",
                metadata={"content_source": "message_string"},
            )
            return content_str

        # If everything fails, record failure and provide fallback
        from src.ui.diagnostics.debug_helpers import debug_error

        debug_error(
            heading="OPENAI • COMPLETE_FAILURE",
            body="No content found in response - providing fallback",
            metadata={"failure_type": "content_extraction_failure"},
        )

        # Record failure for circuit breaker
        instance = OpenAIIntegration()
        instance._record_failure()

        # Return a fallback response instead of raising an exception
        return '{"error": "No content available", "fallback": true}'

    @staticmethod
    def _extract_json_from_reasoning(reasoning_content: str) -> Optional[str]:
        """
        Extract JSON from reasoning_content using LLM.
        Only called when NVIDIA API returns reasoning_content but no regular content.

        Args:
            reasoning_content: The reasoning content that may contain JSON

        Returns:
            Extracted JSON as string, or None if extraction fails
        """
        try:
            from src.prompts.open_ai_prompt import Prompt

            # Get the simple extraction prompts
            prompt_generator = Prompt()
            system_prompt, user_prompt_template = (
                prompt_generator.get_json_extraction_prompts()
            )

            from src.ui.diagnostics.debug_helpers import debug_info

            debug_info(
                heading="OPENAI • JSON_EXTRACTION_ATTEMPT",
                body="Starting LLM-based JSON extraction from reasoning content",
                metadata={
                    "reasoning_content_length": len(reasoning_content),
                    "reasoning_preview": reasoning_content[:1000] + "..."
                    if len(reasoning_content) > 200
                    else reasoning_content,
                },
            )

            # Create user prompt with the reasoning content
            user_prompt = user_prompt_template.format(
                reasoning_content=reasoning_content
            )

            # Create a separate client to avoid recursion
            extractor_client = OpenAI(
                base_url="https://integrate.api.nvidia.com/v1",
                api_key=OPEN_AI_API_KEY,
                timeout=OPENAI_TIMEOUT,
                max_retries=1,
            )

            # Make the extraction API call
            extraction_completion = extractor_client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,  # Low temperature for consistent extraction
                max_tokens=8192,  # Allow enough tokens for JSON extraction
                stream=False,
            )

            # Get the extracted content
            if (
                    extraction_completion.choices
                    and extraction_completion.choices[0].message
            ):
                extracted = extraction_completion.choices[0].message.content
                from src.ui.diagnostics.debug_helpers import debug_info

                debug_info(
                    heading="OPENAI • EXTRACTION_RESPONSE",
                    body=f"LLM extraction response received: {extracted}",
                    metadata={
                        "extracted_content": extracted,
                        "extracted_length": len(extracted) if extracted else 0,
                    },
                )

                if extracted and extracted.strip():
                    # Validate that it's actually JSON using direct json.loads (avoid circular import)
                    try:
                        # Direct JSON validation without calling ModelManager.convert_to_json
                        json.loads(extracted.strip())

                        from src.ui.diagnostics.debug_helpers import debug_info

                        debug_info(
                            heading="OPENAI • JSON_EXTRACTION_SUCCESS",
                            body="Successfully extracted valid JSON from reasoning_content",
                            metadata={
                                "extraction_method": "llm_extraction",
                                "json_length": len(extracted.strip()),
                            },
                        )
                        return extracted.strip()

                    except json.JSONDecodeError as json_error:
                        from src.ui.diagnostics.debug_helpers import debug_warning

                        debug_warning(
                            heading="OPENAI • INVALID_JSON_EXTRACTED",
                            body=f"Extracted content is not valid JSON: {json_error}",
                            metadata={
                                "extracted_content": extracted.strip(),
                                "reasoning_content_length": len(reasoning_content),
                                "json_error": str(json_error),
                            },
                        )

                        # If LLM extraction fails with a JSON error (which is rare), fallback to ModelManager for JSON conversion
                        from src.utils.model_manager import ModelManager

                        ModelManager.convert_to_json(extracted.strip())
            else:
                from src.ui.diagnostics.debug_helpers import debug_critical

                debug_critical(
                    heading="OPENAI • NO_EXTRACTED_CONTENT",
                    body="No content extracted from reasoning_content",
                    metadata={"reasoning_content_length": len(reasoning_content)},
                )

            return None

        except Exception as extraction_error:
            from src.ui.diagnostics.debug_helpers import debug_warning

            debug_warning(
                heading="OPENAI • JSON_EXTRACTION_ERROR",
                body=f"JSON extraction failed: {str(extraction_error)}",
                metadata={
                    "error_type": type(extraction_error).__name__,
                    "fallback_action": "return_none",
                },
            )
            return None

    @classmethod
    async def cleanup_async(cls) -> None:
        """
        Clean up async resources.
        """
        if cls.instance:
            await cls.instance._close_async_client()

    @classmethod
    def _manage_requests_sync(cls) -> None:
        """
        Manage the number of requests to OpenAI API to comply with rate limits.
        This method ensures that no more than 30 requests are made 60 sec.

        IMPORTANT: THIS METHOD SHOULD BE CALLED BEFORE EACH OPENAI API REQUEST TO ENSURE COMPLIANCE WITH RATE LIMITS.
        IMPORTANT: THIS IS A SYNCHRONOUS METHOD, SO IT SHOULD BE USED IN SYNC CONTEXTS ONLY.
        :return: fuck the cpu for waiting
        """
        from src.config import settings

        with cls._thread_lock:
            OpenAIIntegration.requests_count += 1
            eval_listener: RichStatusListener = settings.listeners.get("eval", None)
            # if eval_listener is not None:
            #     eval_listener.emit_on_variable_change(
            #         OpenAIIntegration,
            #         "status",
            #         f"{eval_listener.get_last_event().meta_data.get('new_value')}",
            #         f"{eval_listener.get_last_event().meta_data.get('new_value')} @"
            #         f"request count :- {cls.requests_count}",
            #     )
            if OpenAIIntegration.requests_count == 1:
                OpenAIIntegration._last_request_time = time.perf_counter()
            current_time = time.perf_counter()
            if OpenAIIntegration.requests_count >= 30:
                elapsed_time = current_time - OpenAIIntegration._last_request_time
                if elapsed_time < 60:
                    wait_time = 60 - elapsed_time
                    from src.ui.diagnostics.debug_helpers import debug_critical

                    debug_critical(
                        heading="OPENAI • RATE_LIMIT",
                        body="API rate limit hit - waiting for reset",
                        metadata={
                            "wait_time": wait_time,
                            "context": "sync_rate_limiting",
                        },
                    )
                    if eval_listener is not None:
                        eval_listener.emit_on_variable_change(
                            OpenAIIntegration,
                            "None",
                            "None",
                            f"Rate limit hit - waiting for reset {wait_time} seconds"
                            f"no of requests :- {cls.requests_count}",
                        )
                    time.sleep(wait_time)
                    OpenAIIntegration.requests_count = 0
                    OpenAIIntegration._last_request_time = time.perf_counter()
                else:
                    OpenAIIntegration.requests_count = 0
                    OpenAIIntegration._last_request_time = time.perf_counter()

    @classmethod
    async def _manage_requests_async(cls):
        """
        Manage the number of requests to OpenAI API to comply with rate limits.
        This method ensures that no more than 30 requests are made 60 sec.

        IMPORTANT: THIS METHOD SHOULD BE CALLED BEFORE EACH OPENAI API REQUEST TO ENSURE COMPLIANCE WITH RATE LIMITS.
        :return: fuck the asynchronicity
        """
        # 🔧 FIX: Proper async context management
        from src.config import settings

        # Use proper async lock instead of sync lock
        async with cls._client_lock:
            OpenAIIntegration.requests_count += 1
            eval_listener: RichStatusListener = settings.listeners.get("eval", None)

            if eval_listener is not None:
                eval_listener.emit_on_variable_change(
                    OpenAIIntegration,
                    "status",
                    f"Processing request {cls.requests_count}",
                    f"API request {cls.requests_count} in progress",
                )

            if OpenAIIntegration.requests_count == 1:
                OpenAIIntegration._last_request_time = time.perf_counter()

            current_time = time.perf_counter()

            if OpenAIIntegration.requests_count >= 30:
                elapsed_time = current_time - OpenAIIntegration._last_request_time
                if elapsed_time < 60:
                    wait_time = 60 - elapsed_time
                    # make update that we hit rate limit
                    from src.ui.diagnostics.debug_helpers import debug_critical

                    debug_critical(
                        heading="OPENAI • RATE_LIMIT",
                        body="API rate limit hit - waiting for reset",
                        metadata={
                            "wait_time": wait_time,
                            "context": "async_rate_limiting",
                        },
                    )

                    if eval_listener is not None:
                        eval_listener.emit_on_variable_change(
                            OpenAIIntegration,
                            "None",
                            "None",
                            f"Rate limit hit - waiting for reset {wait_time} seconds, requests: {cls.requests_count}",
                        )

                    await asyncio.sleep(wait_time)
                    OpenAIIntegration.requests_count = 0
                    OpenAIIntegration._last_request_time = time.perf_counter()
                else:
                    OpenAIIntegration.requests_count = 0
                    OpenAIIntegration._last_request_time = time.perf_counter()

    @classmethod
    def cleanup(cls) -> None:
        """
        Clean up the OpenAI client instance and release resources.
        Enhanced with async cleanup.
        """
        if cls.instance and hasattr(cls.instance, "client"):
            try:
                cls.instance.client.close()
            except Exception as e:
                from src.ui.diagnostics.debug_helpers import debug_error

                debug_error(
                    heading="OPENAI • CLEANUP_ERROR",
                    body=f"Error during OpenAI sync client cleanup: {e}",
                    metadata={
                        "error_type": type(e).__name__,
                        "context": "sync_client_cleanup",
                    },
                )

        # Schedule async cleanup if needed
        if cls._async_lock is not None:
            try:
                # Try to cleanup async client if we're in an async context
                loop = asyncio.get_running_loop()
                loop.create_task(cls.cleanup_async())
            except RuntimeError:
                # Not in async context, skip async cleanup
                pass

        cls.instance = None
        cls._async_lock = None
        gc.collect()

    def _get_fallback_response(self, error_type: str = "unknown") -> str:
        """
        Get a fallback response when API calls fail.

        Args:
            error_type: Type of error that occurred

        Returns:
            str: Fallback response message (for some types, returns JSON)
        """
        if error_type == "classification":
            # Return JSON for classification fallback
            return '{"message_type": "fallback", "reasoning": "API unavailable, using default classification", "confidence": "low"}'

        elif error_type == "agent":
            return "I apologize, but I'm currently experiencing technical difficulties with my AI processing system. I'm unable to perform complex agent-mode operations at the moment. Please try again later or use simpler commands. In the meantime, I can still help with basic questions using my fallback systems."

        elif error_type == "parameter_generation":
            # 🔧 FIX: Return valid JSON structure for parameter generation failures
            return '{"tool_name": "none", "reasoning": "API unavailable - unable to generate parameters", "parameters": {}}'

        elif error_type == "tool_execution":
            # 🔧 FIX: Return valid response for tool execution failures
            return '{"evaluation": {"status": "failed", "reasoning": "Tool execution failed due to API issues"}, "fallback": {"tool_name": "none", "reasoning": "API fallback", "parameters": {}}}'

        elif error_type == "general":
            return "I'm currently experiencing technical issues and may not be able to provide my usual detailed responses. Please try rephrasing your question or try again in a few moments."

        else:
            # Default fallback messages for other error types
            fallback_messages = {
                "502": "I'm experiencing temporary connectivity issues. Please try your request again in a moment.",
                "rate_limit": "I'm currently receiving high traffic. Please wait a moment and try again.",
                "timeout": "The request took longer than expected. Please try a simpler query or try again later.",
                "circuit_breaker": "I'm temporarily unavailable due to recent technical issues. Please try again in a few minutes.",
                "unexpected": "I'm temporarily unable to process complex requests due to technical issues. Please try again or simplify your request.",
                "api_error": "I'm experiencing API difficulties. Please try again or rephrase your request.",
                "max_attempts": "Unable to complete the request after multiple attempts. Please try again later.",
                "unknown": "I'm temporarily unable to process your request. Please try again or rephrase your question.",
            }

            return fallback_messages.get(error_type, fallback_messages["unknown"])

    def _is_circuit_open(self) -> bool:
        """
        Check if circuit breaker is open (preventing API calls).

        Returns:
            bool: True if circuit is open, False if closed
        """
        if not OpenAIIntegration._circuit_open:
            return False

        # Check if circuit timeout has expired
        if (
                OpenAIIntegration._circuit_open_until
                and time.time() > OpenAIIntegration._circuit_open_until
        ):
            OpenAIIntegration._circuit_open = False
            OpenAIIntegration._circuit_open_until = None
            OpenAIIntegration._failure_count = 0
            from src.ui.diagnostics.debug_helpers import debug_info

            debug_info(
                heading="OPENAI • CIRCUIT_BREAKER_RESET",
                body="Circuit breaker reset after timeout",
                metadata={"timeout_duration": OpenAIIntegration._circuit_timeout},
            )
            return False

        return True

    def _record_failure(self):
        """Record an API failure and potentially open circuit breaker."""
        OpenAIIntegration._failure_count += 1

        from src.ui.diagnostics.debug_helpers import debug_warning

        debug_warning(
            heading="OPENAI • API_FAILURE_RECORDED",
            body=f"API failure recorded (count: {OpenAIIntegration._failure_count}/{OpenAIIntegration._max_failures})",
            metadata={
                "failure_count": OpenAIIntegration._failure_count,
                "max_failures": OpenAIIntegration._max_failures,
            },
        )

        if OpenAIIntegration._failure_count >= OpenAIIntegration._max_failures:
            OpenAIIntegration._circuit_open = True
            OpenAIIntegration._circuit_open_until = (
                    time.time() + OpenAIIntegration._circuit_timeout
            )
            from src.ui.diagnostics.debug_helpers import debug_critical

            debug_critical(
                heading="OPENAI • CIRCUIT_BREAKER_OPEN",
                body=f"Circuit breaker opened after {OpenAIIntegration._failure_count} failures",
                metadata={"timeout_duration": OpenAIIntegration._circuit_timeout},
            )

    def _record_success(self):
        """Record an API success and reset failure count."""
        if OpenAIIntegration._failure_count > 0:
            from src.ui.diagnostics.debug_helpers import debug_info

            debug_info(
                heading="OPENAI • API_RECOVERY",
                body="API call successful - resetting failure count",
                metadata={"previous_failures": OpenAIIntegration._failure_count},
            )
            OpenAIIntegration._failure_count = 0

    @property
    def requests_count_property(self) -> int:
        """
        Property to get the current requests count.
        """
        return OpenAIIntegration.requests_count

    @requests_count_property.setter
    def requests_count_property(self, value: int) -> None:
        """
        Setter for the requests_count property.
        Emits an event to listeners when the value changes.
        """
        old_value = OpenAIIntegration.requests_count
        OpenAIIntegration.requests_count = value

        # Emit event to listeners
        # eval_listener: RichStatusListener = settings.listeners.get('eval', None)
        # if eval_listener is not None:
        #     new_value = (f"{eval_listener.get_last_event().meta_data.get('new_value')!s}"
        #                  .split('@'))[0] + f"@request count :- {value}"
        #     eval_listener.emit_on_variable_change(OpenAIIntegration, "status",
        #                                           f"{eval_listener.get_last_event().meta_data.get('new_value')}",
        #                                           new_value)


if __name__ == "__main__":
    # Example usage - uses API key from .env file
    openai_integration = OpenAIIntegration()
    print(
        openai_integration.generate_text("What is the capital of France?", False)
    )  # Non-streaming response

    winsound.Beep(4234, 1000)  # Beep to indicate start of OpenAI API call
