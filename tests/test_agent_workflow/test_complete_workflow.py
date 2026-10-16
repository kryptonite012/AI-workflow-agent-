"""
End-to-end tests for the hierarchical agent workflow.

The compiled LangGraph is run for real; only the LLM (ModelManager) and the
tool layer are replaced with deterministic fakes, so no Ollama, API key or
network access is needed.
"""

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.agents.agentic_orchestrator import AgentGraphCore as core_module
from src.agents.agentic_orchestrator.AgentGraphCore import AgentGraphCore
from src.utils.model_manager import ModelManager


def make_fake_model(replies):
    """Build a ModelManager stand-in that answers by matching the system prompt.

    `replies` maps a substring of the system prompt to the reply (a JSON-able
    object, or a str returned verbatim). Unmatched prompts get "{}".
    """
    prompts = []

    class FakeModel:
        convert_to_json = staticmethod(ModelManager.convert_to_json)

        def __init__(self, *args, **kwargs):
            pass

        def invoke(self, messages):
            system_prompt = messages[0]["content"]
            prompts.append(system_prompt)
            for marker, reply in replies.items():
                if marker in system_prompt:
                    content = reply if isinstance(reply, str) else json.dumps(reply)
                    return Mock(content=content)
            return Mock(content="{}")

    return FakeModel, prompts


def make_tool(name):
    tool = Mock()
    tool.name = name
    tool.description = f"{name} tool"
    return tool


class TestCompleteWorkflow(unittest.TestCase):
    GOAL = "Search the web for python tutorials and save a summary to notes.md"

    def run_workflow(self, replies, tools, tool_results, recursion_limit=80):
        fake_model, prompts = make_fake_model(replies)
        executed = []

        def execute_tool(tool_name, parameters, timeout=60):
            executed.append((tool_name, parameters))
            return tool_results(tool_name, parameters)

        with patch.object(core_module, "ModelManager", fake_model), \
                patch.object(core_module, "AgentStatusUpdater"), \
                patch.object(core_module.ToolAssign, "get_tools_list", return_value=tools), \
                patch.object(core_module.AgentCoreHelpers.ToolExecutionHelpers, "exeCuteTool",
                             side_effect=execute_tool):
            graph = AgentGraphCore.build_graph()
            final_state = graph.invoke(
                {"tasks": [], "current_task_id": "0", "executed_nodes": [], "original_goal": self.GOAL},
                {"recursion_limit": recursion_limit},
            )
        return final_state, executed, prompts

    def test_multi_step_plan_runs_to_completion(self):
        """A two-task plan executes each tool in order with generated parameters."""
        replies = {
            "tool recommendation expert": ["google_search", "write_file"],
            "JSON ARRAY OF TASKS": [
                {"description": "Search for python tutorials", "tool_name": "google_search"},
                {"description": "Write the summary to notes.md", "tool_name": "write_file"},
            ],
            "PARAMETER GENERATOR": {"query": "python tutorials", "path": "notes.md", "content": "summary"},
            "COMPLEXITY ANALYZER": {"requires_decomposition": False, "reasoning": "single tool call"},
            "expert analysis AI": "The tool call succeeded.",
            "VALIDATING IMMEDIATE TOOL EXECUTION": {"goal_achieved": True, "reasoning": "tool output is valid"},
            "EXACTLY ONE JSON OBJECT": {"user_response": {"message": "Saved the tutorial summary."}},
        }
        tools = [make_tool("google_search"), make_tool("write_file")]

        final_state, executed, _ = self.run_workflow(replies, tools, lambda name, params: (True, f"{name} ok"))

        self.assertEqual(final_state["workflow_status"], "COMPLETED")
        self.assertEqual([name for name, _ in executed], ["google_search", "write_file"])
        self.assertEqual([t.status for t in final_state["tasks"]], ["completed", "completed"])
        self.assertEqual(final_state["final_response"]["user_response"]["message"], "Saved the tutorial summary.")
        self.assertEqual(final_state["executed_nodes"][0], "subAGENT_initial_planner")
        self.assertEqual(final_state["executed_nodes"][-1], "subAGENT_finalizer")

    def test_unrecoverable_task_terminates_instead_of_looping(self):
        """When the LLM never produces usable output, the workflow still finishes.

        Regression test: error fallback used to leave the task 'failed' without
        progress, so classifier <-> error_fallback looped until the recursion limit.
        """
        tools = [make_tool("list_directory")]

        final_state, _, prompts = self.run_workflow({}, tools, lambda name, params: (True, "listing"))

        self.assertIn("subAGENT_finalizer", final_state["executed_nodes"])
        task = final_state["tasks"][0]
        self.assertEqual(task.status, "skip")
        self.assertIn("abandoned after failed recovery", task.execution_context.analysis)
        recovery_prompts = [p for p in prompts if "error recovery strategist" in p]
        self.assertLessEqual(len(recovery_prompts), AgentGraphCore.MAX_RECOVERY_ATTEMPTS)

    def test_invalid_recovery_strategy_defaults_to_parameter_repair(self):
        """decide_recovery_strategy returns the validated strategy, not just the raw LLM dict."""
        fake_model, _ = make_fake_model({"error recovery strategist": {"recovery_strategy": "MADE_UP"}})
        task = core_module.TASK(
            task_id="1",
            description="Read config",
            tool_name="read_file",
            status="failed",
            required_context=core_module.REQUIRED_CONTEXT(source_node="test"),
            failure_context=core_module.FAILURE_CONTEXT(error_message="boom"),
        )
        state = core_module.WorkflowStateModel(
            tasks=[task], current_task_id="1", executed_nodes=[], original_goal=self.GOAL
        )

        with patch.object(core_module, "ModelManager", fake_model), \
                patch.object(core_module.ToolAssign, "get_tools_list", return_value=[make_tool("read_file")]):
            decision = core_module.AgentCoreHelpers.EnhancedErrorFallbackHelpers.decide_recovery_strategy(task, state)

        self.assertEqual(decision["recovery_strategy"], "PARAMETER_REPAIR")


if __name__ == "__main__":
    unittest.main()
