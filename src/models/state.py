from typing import TypedDict, List, Annotated

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import add_messages


class State(TypedDict):
    messages: Annotated[List[HumanMessage | AIMessage], add_messages]
    message_type: str | None


class StateAccessor:
    _instance = None
    _current_state: State | None = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StateAccessor, cls).__new__(cls)
        return cls._instance

    def get_state(self) -> State:
        """
        Get the current state.
        :return: The current state.
        """
        if self._current_state is None:
            self._current_state = State(messages=[], message_type=None)
        return self._current_state

    # we have to explicitly update the state

    def _update_state(self, new_state: State) -> None:
        """
        Update the current state with a new state.
        :param new_state: The new state to set.
        """
        self._current_state = new_state.copy()

    def sync_with_langgraph(self, langgraph_state: State) -> None:
        """
        Explicitly sync with LangGraph state.
        Use this in your nodes to keep singleton in sync.
        :param langgraph_state: The current LangGraph state
        """
        self._update_state(langgraph_state)

    def get_messages(self) -> List[HumanMessage | AIMessage]:
        """
        Convenience method to get current messages.
        :return: Current messages list
        """
        current_state = self.get_state()
        return current_state["messages"]

    def get_message_type(self) -> str | None:
        """
        Convenience method to get current message type.
        :return: Current message type
        """
        current_state = self.get_state()
        return current_state["message_type"]

    def get_last_message(self):
        """
        Get the last message from the current state.
        :return: The last message or None if no messages exist.
        """
        messages = self.get_messages()
        return messages[-1] if messages else None

    def get_last_human_message(self) -> HumanMessage | None:
        """
        Get the last human message from the current state.
        :return: The last human message or None if no human messages exist.
        """
        messages = self.get_messages()
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                return msg
        return None

    def clear_state(self) -> None:
        """
        Clear the current state.
        """
        self._current_state = State(messages=[], message_type=None)
