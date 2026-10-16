"""Node Factory: Creates LangGraph-compatible node functions with dependency injection
"""

from src.agents.chat_llm import generate_llm_response
from src.agents.classify_agent import classify_message_type
from src.agents.router import route_message
from src.agents.tool_selector import tool_selection_agent


class NodeFactory:
    """Factory class for creating dependency-injected LangGraph nodes"""

    def __init__(self, state_accessor, tools, console):
        self.state_accessor = state_accessor
        self.tools = tools
        self.console = console

    def create_classifier_node(self):
        """Creates classifier node with injected dependencies"""

        def classifier_wrapper(state):
            return classify_message_type(state, self.state_accessor)

        return classifier_wrapper

    def create_router_node(self):
        """Creates router node with injected dependencies"""

        def router_wrapper(state):
            return route_message(state)

        return router_wrapper

    def create_llm_node(self):
        """Creates LLM node with injected dependencies"""

        def llm_wrapper(state):
            return generate_llm_response(state, self.state_accessor, self.tools)

        return llm_wrapper

    def create_tool_node(self):
        """Creates tool selection node with injected dependencies"""

        def tool_wrapper(state):
            return tool_selection_agent(
                state, self.state_accessor, self.console, self.tools,
            )

        return tool_wrapper


# Alternative: Functional approach using closures
def create_classifier_node(state_accessor, console):
    """Closure that captures dependencies for the classifier"""

    def classifier_wrapper(state):
        return classify_message_type(state, state_accessor)

    return classifier_wrapper


def create_llm_node(state_accessor, tools, console):
    """Closure that captures dependencies for LLM response generation"""

    def llm_wrapper(state):
        return generate_llm_response(state, state_accessor, tools)

    return llm_wrapper


def create_tool_node(state_accessor, console, tools):
    """Closure that captures dependencies for tool selection"""

    def tool_wrapper(state):
        return tool_selection_agent(state, state_accessor, console, tools)

    return tool_wrapper


def create_router_node(console, state_accessor):
    """Router with injected dependencies"""

    def router_wrapper(state):
        return route_message(state)

    return router_wrapper
