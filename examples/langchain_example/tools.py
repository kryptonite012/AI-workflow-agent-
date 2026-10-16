# from browser_use import Agent # Removed as it's no longer used
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import Tool

search_duckduck = DuckDuckGoSearchRun()
search_tool = Tool(
    name="DuckDuckGoSearch",
    description="For general web searches (recent info, facts, news).",  # Simplified description
    func=search_duckduck,
    return_direct=False,
)

# Removed browser_task function

# Removed browser_tool definition
