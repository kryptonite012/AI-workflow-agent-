import duckduckgo_search.exceptions
import langchain_core.exceptions
from langchain.agents import initialize_agent, AgentType
from langchain.prompts import PromptTemplate
from langchain_ollama import OllamaLLM

import tools

# Initialize the language model
llm = OllamaLLM(
    model="llava-llama3:latest",
    temperature=0.1,
)

# Define tools
tools_llm = [tools.search_tool]

# Create a simplified ReAct prompt template
react_prompt = PromptTemplate.from_template(
    """You are a helpful AI assistant that can search for information on the web using the DuckDuckGoSearch tool.
    
When I ask you a question, first decide if you need to search for information.
If you need to search, use the DuckDuckGoSearch tool.
If you already know the answer or it doesn't require factual information, just respond directly.

Use the following format:
Question: the input question
Thought: your thought process about what to do
Action: the action to take, should be one of [DuckDuckGoSearch, Final Answer]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat multiple times)
Thought: I now know the final answer
Action: Final Answer
Action Input: your final answer to the original input question

Begin!

Question: {input}
{agent_scratchpad}
"""
)

# Initialize agent
agent_llm = initialize_agent(
    tools=tools_llm,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    max_iterations=3,
    handle_parsing_errors=True,
    early_stopping_method="generate",
)

try:
    user_query = input("enter your query: ")
    result = agent_llm.invoke({"input": user_query.strip()})

    # Print the final answer nicely
    print("\nFinal Answer:")
    if "output" in result:
        print(result["output"])
    else:
        print("No clear answer was found, but here's what I know:")
        print(result)

    # Print intermediate steps if available
    if "intermediate_steps" in result and result["intermediate_steps"]:
        print("\nSearch Steps:")
        for step in result["intermediate_steps"]:
            print(f"Search Query: {step[0].tool_input}")
            print(f"Result: {step[1][:200]}...")  # Only print first 200 chars
            print("---")

except Exception as e:
    # Handle specific exceptions for better debugging
    if isinstance(e, duckduckgo_search.exceptions.DuckDuckGoSearchError):
        print(f"DuckDuckGo Search Error: {e}")
    elif isinstance(e, langchain_core.exceptions.LangChainError):
        print(f"LangChain Error: {e}")
    else:
        print(f"An unexpected error occurred: {e}")
        print(type(e).__name__)
