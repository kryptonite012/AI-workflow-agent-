from langchain_core.messages import AIMessage, HumanMessage

from src.config import settings
from src.tools.lggraph_tools.tool_assign import ToolAssign
from src.ui.print_message_style import print_message
from src.utils.model_manager import ModelManager


def generate_llm_response(state) -> dict:
    """Generates a response using the LLM based on the conversation history and the latest user message.
    Shows a spinner while generating the response.
    """
    console = settings.console
    console.print("\t\t----[bold][green]Node is chatBot[/bold][/green]")
    # Access state directly from LangGraph parameter
    messages = state.get("messages", [])
    history = "\n".join(f"{msg.type}: {msg.content}" for msg in messages[:-1])
    latest_message_content = messages[-1].content if messages else ""

    tools = ToolAssign.get_tools_list()

    tools_context = (
        "\n\n".join(
            [f"Tool: {tool.name}\nDescription: {tool.description}" for tool in tools],
        )
        if tools
        else "No tools available."
    )

    system_prompt = (
        "You are an intelligent AI assistant with deep reasoning capabilities and full conversation awareness.\n\n"
        "**Your Core Abilities:**\n"
        "- Understand context from the entire conversation, not just the latest message\n"
        "- Reason about relationships between different parts of our discussion\n"
        "- Explain complex topics in simple, clear language\n"
        "- Reference and build upon previous exchanges naturally\n"
        "- Provide thoughtful analysis and insights\n\n"
        "**Context Analysis:**\n"
        "- When users refer to 'that', 'it', 'the previous result', or 'what we discussed', understand what they mean\n"
        "- Connect current questions to earlier topics in our conversation\n"
        "- Explain how different pieces of information relate to each other\n"
        "- Clarify and expand on previous responses when asked\n\n"
        "**Available Capabilities:**\n"
        f"I have access to these tools when needed: {tools_context}\n"
        "But right now, you're asking me to think and reason, not to use external tools.\n\n"
        "**Our Conversation So Far:**\n"
        f"{history}\n\n"
        "**Your Current Question/Request:**\n"
        f"{latest_message_content}\n\n"
        "**Instructions:**\n"
        "- Respond naturally and conversationally\n"
        "- Reference our conversation history when relevant\n"
        "- Explain your reasoning clearly\n"
        "- If you're unsure about something from our conversation, ask for clarification\n"
        '- Always return a valid JSON object: {{"response": "Your thoughtful response here"}}\n\n'
        "Think about what the user really wants to know, considering everything we've discussed together."
    )
    messages_with_system_prompt = [HumanMessage(content=system_prompt)]
    llm = ModelManager(temperature=0.7, format="json")

    with console.status("[bold green]Thinking...[/bold green]", spinner="dots"):
        stream = llm.stream(messages_with_system_prompt)
        content = ""
        for part in stream:
            chunk = part.content if part.content is not None else ""
            content += chunk
    # Print AI message in modern style
    # now we will not print raw json now we will extract the response from the content
    json_content = llm.convert_to_json(content)
    if json_content and "response" in json_content:
        content = json_content["response"]
    else:
        # If the response is not in the expected format, print the raw content
        pass
    print_message(content.strip(), sender="ai")
    return {"messages": [AIMessage(content=content.strip())]}
