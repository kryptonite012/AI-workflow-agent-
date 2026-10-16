from typing import Literal

from pydantic import BaseModel, Field


class ToolSelection(BaseModel):
    tool_name: str = Field(
        description="The name of the tool to use, or 'none' if no tool is needed.",
    )
    reasoning: str = Field(description="Reasoning for selecting this tool.")
    parameters: dict = Field(description="The parameters to pass to the tool.")


class message_classifier(BaseModel):
    message_type: Literal["llm", "tool"] = Field(
        description="classify the message as Type of message: 'llm' for LLM response, 'tool' for tool response.",
    )
