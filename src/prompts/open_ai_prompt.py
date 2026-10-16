"""
open_ai_prompt.py

This module contains the prompt used directly by the OpenAI API.
It is intended for scenarios where no content is found using the standard approach,
and only a reasoning-based response is available.

Created: 2023-10-01
Enhanced: 2025-01-15 - Simple JSON extraction from reasoning content
"""


class Prompt:
    """
    Simple OpenAI prompt for extracting valid JSON from reasoning-based responses.
    Used only when NVIDIA API returns reasoning_content instead of regular content.
    """

    def get_json_extraction_prompts(self) -> tuple[str, str]:
        """
        Returns system and user prompts for extracting JSON from reasoning content.

        Returns:
            tuple[str, str]: (system_prompt, user_prompt_template)
        """

        SYSTEM_PROMPT = (
            "You are a JSON extraction specialist. Your only job is to find and extract valid JSON from reasoning content. "
            "\n\n"
            "RULES:\n"
            "1. Extract ONLY valid JSON dictionaries (objects with {}) from the content\n"
            "2. Do NOT modify, invent, or add any information not present\n"
            "3. If multiple JSON objects exist, select the most complete one\n"
            "4. Preserve all original key-value pairs exactly as found\n"
            "5. Return ONLY the JSON - no explanations, no markdown, no extra text\n"
            "6. If no valid JSON found, return: {}\n"
            "\n"
            "EXAMPLES:\n"
            'Input: \'Let me think... {"tool_name": "search", "params": {"q": "test"}} ...done\'\n'
            'Output: {"tool_name": "search", "params": {"q": "test"}}\n'
            "\n"
            "Input: 'Analysis shows no structured data here'\n"
            "Output: {}"
        )

        USER_PROMPT = (
            "Extract the JSON from this reasoning content:\n\n{reasoning_content}"
        )

        return SYSTEM_PROMPT, USER_PROMPT


# Legacy compatibility
def get_extracted_json_prompt() -> str:
    """
    Legacy function for backward compatibility.

    Returns:
        str: Standard JSON extraction prompt
    """
    system_prompt, _ = Prompt().get_json_extraction_prompts()
    return system_prompt
