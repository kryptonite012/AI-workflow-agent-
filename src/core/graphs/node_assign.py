from langgraph.graph import StateGraph, START, END

from src.agents.chat_llm import generate_llm_response
from src.agents.classify_agent import classify_message_type
from src.agents.router import route_message
from src.agents.tool_selector import tool_selection_agent
from src.agents.agent_mode_node import agent_node


class GraphBuilder:
    """
    here we build the graph for the chat application.
    It initializes the graph with the given state and provides methods to add nodes and edges.
    The graph is built using the StateGraph class from langgraph.
    """

    def __init__(self, state):
        self.state = state
        self.graph = StateGraph(state)

    def _assigning_nodes(self):
        self.graph.add_node("classifier", classify_message_type)
        self.graph.add_node("router", route_message)
        self.graph.add_node("chatBot", generate_llm_response)
        self.graph.add_node("tool_agent", tool_selection_agent)
        self.graph.add_node("agent_node", agent_node)
        return self

    def _assign_edges(self):
        self.graph.add_edge(START, "classifier")
        self.graph.add_edge("classifier", "router")

        def route_by_message_type(state):
            return state["message_type"]

        self.graph.add_conditional_edges(
            "router",
            route_by_message_type,
            {"llm": "chatBot", "tool": "tool_agent", "agent": "agent_node"},
        )
        self.graph.add_edge("chatBot", END)
        self.graph.add_edge("tool_agent", END)
        self.graph.add_edge("agent_node", END)
        return self

    def compile_graph(self):
        """
        Compile the graph after adding all nodes and edges.
        :return: Compiled graph
        """
        self._assigning_nodes()
        self._assign_edges()
        return self.graph.compile()
