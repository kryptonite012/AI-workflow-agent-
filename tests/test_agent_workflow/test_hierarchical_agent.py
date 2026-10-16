"""
Comprehensive test suite for the hierarchical agent workflow system.
Tests for AgentGraphCore, TASK models, and workflow execution.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import os
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add the project root to Python path
# (Already added above; keep this as a no-op for historical reasons.)

try:
    # Import the modules we need to test
    from src.agents.agentic_orchestrator.AgentGraphCore import (
        AgentGraphCore,
        TASK,
        REQUIRED_CONTEXT,
        EXECUTION_CONTEXT,
        FAILURE_CONTEXT,
        subAgent_CONTEXT,
        MAIN_STATE,
        AgentState,
        AgentCoreHelpers,
        WorkflowStateModel,
        Spawn_subAgent,
    )
    from src.models.state import State

    MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Import error: {e}")
    MODULES_AVAILABLE = False


class TestTaskModels(unittest.TestCase):
    """Test cases for the TASK and related Pydantic models."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        if not MODULES_AVAILABLE:
            self.skipTest("Required modules not available")

    def test_task_creation_basic(self):
        """Test basic TASK model creation."""
        required_context = REQUIRED_CONTEXT(source_node="test_node")
        task = TASK(
            task_id="1",
            description="Test task description",
            tool_name="test_tool",
            required_context=required_context
        )
        
        self.assertEqual(task.task_id, "1")
        self.assertEqual(task.description, "Test task description")
        self.assertEqual(task.tool_name, "test_tool")
        self.assertEqual(task.status, "pending")  # Default status
        self.assertEqual(task.max_retries, 1)  # Default retries
        self.assertIsNone(task.execution_context)
        self.assertIsNone(task.failure_context)

    def test_task_creation_with_execution_context(self):
        """Test TASK creation with execution context."""
        required_context = REQUIRED_CONTEXT(source_node="test_node")
        execution_context = EXECUTION_CONTEXT(
            tool_name="test_tool",
            parameters={"param1": "value1"}
        )
        
        task = TASK(
            task_id="2",
            description="Test task with execution context",
            tool_name="test_tool",
            required_context=required_context,
            execution_context=execution_context
        )
        
        self.assertIsNotNone(task.execution_context)
        self.assertEqual(task.execution_context.tool_name, "test_tool")
        self.assertEqual(task.execution_context.parameters, {"param1": "value1"})

    def test_task_creation_with_failure_context(self):
        """Test TASK creation with failure context."""
        required_context = REQUIRED_CONTEXT(source_node="test_node")
        failure_context = FAILURE_CONTEXT(
            error_message="Test error",
            fail_count=2,
            error_type="TestError"
        )
        
        task = TASK(
            task_id="3",
            description="Test task with failure",
            tool_name="test_tool",
            required_context=required_context,
            failure_context=failure_context
        )
        
        self.assertIsNotNone(task.failure_context)
        self.assertEqual(task.failure_context.error_message, "Test error")
        self.assertEqual(task.failure_context.fail_count, 2)
        self.assertEqual(task.failure_context.error_type, "TestError")

    def test_recovery_actions_assignment(self):
        """Test that recovery_actions can be assigned as a dictionary."""
        required_context = REQUIRED_CONTEXT(source_node="test_node")
        failure_context = FAILURE_CONTEXT(
            error_message="Test error",
            fail_count=1,
            error_type="TestError"
        )
        
        # Test direct assignment of recovery actions as dict
        recovery_dict = {
            "require_spawn_new_agent": True,
            "updated_parameters": {"new_param": "new_value"},
            "alternative_tool": "alternative_tool_name"
        }
        
        failure_context.recovery_actions = recovery_dict
        
        self.assertEqual(failure_context.recovery_actions["require_spawn_new_agent"], True)
        self.assertEqual(failure_context.recovery_actions["updated_parameters"]["new_param"], "new_value")
        self.assertEqual(failure_context.recovery_actions["alternative_tool"], "alternative_tool_name")


class TestAgentState(unittest.TestCase):
    """Test cases for AgentState model."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        if not MODULES_AVAILABLE:
            self.skipTest("Required modules not available")

    def test_agent_state_creation(self):
        task = TASK(
            task_id="1",
            description="Test task",
            tool_name="test_tool",
            required_context=REQUIRED_CONTEXT(source_node="test_node"),
        )

        agent_state = AgentState(TASKS=[task], CURRENT_TASK_ID=1, original_goal="Test goal")

        self.assertEqual(len(agent_state.TASKS), 1)
        self.assertEqual(agent_state.CURRENT_TASK_ID, 1)
        self.assertEqual(agent_state.original_goal, "Test goal")
        self.assertIsNone(agent_state.persona)

    def test_main_state_defaults(self):
        main_state = MAIN_STATE()

        self.assertEqual(main_state.WORKFLOW_STATUS, "STARTED")
        self.assertEqual(main_state.EXECUTED_NODES, [])


class TestAgentGraphCoreHelpers(unittest.TestCase):
    """Test cases for AgentCoreHelpers tool helpers."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        if not MODULES_AVAILABLE:
            self.skipTest("Required modules not available")

    @patch('src.agents.agentic_orchestrator.AgentGraphCore.ToolAssign')
    def test_get_safe_tools_list_success(self, mock_tool_assign):
        """get_safe_tools_list returns the registered tools."""
        mock_tool1 = Mock()
        mock_tool1.name = "test_tool_1"
        mock_tool2 = Mock()
        mock_tool2.name = "test_tool_2"
        mock_tool_assign.get_tools_list.return_value = [mock_tool1, mock_tool2]

        tools = AgentCoreHelpers.get_safe_tools_list()

        self.assertEqual(len(tools), 2)
        self.assertEqual(tools[0].name, "test_tool_1")
        self.assertEqual(tools[1].name, "test_tool_2")

    @patch('src.agents.agentic_orchestrator.AgentGraphCore.ToolAssign')
    def test_get_safe_tools_list_empty(self, mock_tool_assign):
        """get_safe_tools_list raises when no tools are registered."""
        mock_tool_assign.get_tools_list.return_value = []

        with self.assertRaises(RuntimeError) as context:
            AgentCoreHelpers.get_safe_tools_list()

        self.assertIn("No tools available", str(context.exception))

    @patch('src.agents.agentic_orchestrator.AgentGraphCore.get_tool_argument_schema')
    @patch('src.agents.agentic_orchestrator.AgentGraphCore.ToolAssign')
    def test_get_tools_string(self, mock_tool_assign, mock_schema):
        """get_detailed_tool_context formats only the recommended tools."""
        wanted = Mock()
        wanted.name = "test_tool_1"
        wanted.description = "Test tool 1 description"
        other = Mock()
        other.name = "other_tool"
        other.description = "Should not appear"
        mock_tool_assign.get_tools_list.return_value = [wanted, other]
        mock_schema.return_value = {}

        tools_string = AgentCoreHelpers.get_detailed_tool_context(["test_tool_1"])

        self.assertIn("test_tool_1: Test tool 1 description", tools_string)
        self.assertIn("Parameters: {}", tools_string)
        self.assertNotIn("other_tool", tools_string)

    @patch('src.agents.agentic_orchestrator.AgentGraphCore.ToolAssign')
    def test_get_tools_string_includes_virtual_synthesis_tool(self, mock_tool_assign):
        """The virtual perform_synthesis tool is injected when recommended."""
        mock_tool_assign.get_tools_list.return_value = [Mock()]

        tools_string = AgentCoreHelpers.get_detailed_tool_context(["perform_synthesis"])

        self.assertIn("perform_synthesis", tools_string)


class TestToolExecutor(unittest.TestCase):
    """Test cases for AgentCoreHelpers.ToolExecutionHelpers._tool_executor."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        if not MODULES_AVAILABLE:
            self.skipTest("Required modules not available")
        self.executor = AgentCoreHelpers.ToolExecutionHelpers._tool_executor

    @patch('src.agents.agentic_orchestrator.AgentGraphCore.AgentCoreHelpers.get_safe_tools_list')
    @patch('src.tools.lggraph_tools.tool_response_manager.ToolResponseManager')
    def test_tool_executor_success(self, mock_response_manager, mock_get_tools):
        """Successful tool execution returns the last response content."""
        mock_tool = Mock()
        mock_tool.name = "test_tool"
        mock_get_tools.return_value = [mock_tool]

        mock_response = Mock()
        mock_response.content = "Tool executed successfully"
        mock_response_manager.return_value.get_response.return_value = [mock_response]

        success, result = self.executor("test_tool", {"param1": "value1"})

        self.assertTrue(success)
        self.assertIn("Tool executed successfully", result)
        mock_tool.invoke.assert_called_once_with({"param1": "value1", "tool_name": "test_tool"})

    @patch('src.agents.agentic_orchestrator.AgentGraphCore.AgentCoreHelpers.get_safe_tools_list')
    def test_tool_executor_tool_not_found(self, mock_get_tools):
        """Unknown tool names fail without invoking anything."""
        mock_tool = Mock()
        mock_tool.name = "different_tool"
        mock_get_tools.return_value = [mock_tool]

        success, result = self.executor("nonexistent_tool", {"param1": "value1"})

        self.assertFalse(success)
        self.assertIn("not found", result)
        mock_tool.invoke.assert_not_called()

    @patch('src.agents.agentic_orchestrator.AgentGraphCore.AgentCoreHelpers.get_safe_tools_list')
    @patch('src.tools.lggraph_tools.tool_response_manager.ToolResponseManager')
    def test_tool_executor_no_response(self, mock_response_manager, mock_get_tools):
        """A tool that produces no response is reported as a failure."""
        mock_tool = Mock()
        mock_tool.name = "test_tool"
        mock_get_tools.return_value = [mock_tool]
        mock_response_manager.return_value.get_response.return_value = []

        success, result = self.executor("test_tool", {"param1": "value1"})

        self.assertFalse(success)
        self.assertIn("No response received", result)


class TestSpawnSubAgent(unittest.TestCase):
    """Test cases for the Spawn_subAgent class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        if not MODULES_AVAILABLE:
            self.skipTest("Required modules not available")

        self.parent_task = TASK(
            task_id="1",
            description="Complex task requiring decomposition",
            tool_name="complex_tool",
            required_context=REQUIRED_CONTEXT(source_node="test_node"),
        )
        self.state = WorkflowStateModel(
            tasks=[self.parent_task],
            current_task_id="1",
            executed_nodes=[],
            original_goal="Test goal",
        )

    def _run_analysis(self, llm_json):
        with patch('src.agents.agentic_orchestrator.AgentGraphCore.ModelManager') as mock_model_manager, \
                patch('src.agents.agentic_orchestrator.AgentGraphCore.AgentGraphCore.get_tool_schema',
                      return_value={}):
            mock_model_manager.convert_to_json.return_value = llm_json
            return Spawn_subAgent.analyze_spawn_requirement(
                self.parent_task, "complexity analysis", self.state
            )

    def test_analyze_spawn_requirement_should_spawn(self):
        """requires_decomposition=True from the LLM maps to should_spawn=True."""
        result = self._run_analysis({"requires_decomposition": True, "reasoning": "Task is complex"})

        self.assertTrue(result["should_spawn"])
        self.assertEqual(result["reasoning"], "Task is complex")

    def test_analyze_spawn_requirement_no_spawn(self):
        """requires_decomposition=False from the LLM maps to should_spawn=False."""
        result = self._run_analysis({"requires_decomposition": False, "reasoning": "Task is simple"})

        self.assertFalse(result["should_spawn"])
        self.assertEqual(result["reasoning"], "Task is simple")

    def test_analyze_spawn_requirement_invalid_llm_response(self):
        """An invalid LLM response falls back to not spawning."""
        result = self._run_analysis("not json")

        self.assertFalse(result["should_spawn"])

    @patch('src.agents.agentic_orchestrator.AgentGraphCore.AgentCoreHelpers.get_detailed_tool_context',
           return_value="tools")
    @patch('src.agents.agentic_orchestrator.AgentGraphCore.AgentCoreHelpers.recommend_tools_for_task')
    @patch('src.agents.agentic_orchestrator.AgentGraphCore.ModelManager')
    def test_decompose_task_for_subAgent(self, mock_model_manager, mock_recommend_tools, _mock_context):
        """Decomposition creates depth+1 sub-tasks and drops tools outside the recommended set."""
        mock_recommend_tools.return_value = ["subtool_1", "subtool_2"]
        mock_model_manager.convert_to_json.return_value = [
            {"description": "Subtask 1", "tool_name": "subtool_1"},
            {"description": "Subtask 2", "tool_name": "subtool_2"},
            {"description": "Hallucinated", "tool_name": "unknown_tool"},
        ]

        subtasks = Spawn_subAgent.decompose_task_for_subAgent(
            self.parent_task, self.state, parent_context=None
        )

        self.assertEqual(len(subtasks), 2)
        self.assertEqual(subtasks[0].description, "Subtask 1")
        self.assertEqual(subtasks[0].tool_name, "subtool_1")
        self.assertTrue(subtasks[0].task_id.startswith("1.1-"))
        self.assertEqual(subtasks[1].tool_name, "subtool_2")
        self.assertTrue(subtasks[1].task_id.startswith("1.2-"))
        for subtask in subtasks:
            self.assertEqual(subtask.depth, 1)
            self.assertEqual(subtask.required_context.triggering_task_id, "1")

    def test_inject_subAgent_into_workflow(self):
        """Sub-tasks are inserted right after their parent."""
        later_task = TASK(
            task_id="2",
            description="Later task",
            tool_name="other_tool",
            required_context=REQUIRED_CONTEXT(source_node="test_node"),
        )
        self.state.tasks = [self.parent_task, later_task]
        subtask1 = TASK(
            task_id="1.1",
            description="Subtask 1",
            tool_name="subtool_1",
            required_context=REQUIRED_CONTEXT(source_node="decomposer"),
        )
        subtask2 = TASK(
            task_id="1.2",
            description="Subtask 2",
            tool_name="subtool_2",
            required_context=REQUIRED_CONTEXT(source_node="decomposer"),
        )

        result = Spawn_subAgent.inject_subAgent_into_workflow(
            self.parent_task, [subtask1, subtask2], self.state
        )

        self.assertEqual(self.parent_task.status, "in_progress")
        self.assertIn("2 sub-tasks", self.parent_task.execution_context.analysis)
        self.assertEqual(
            [t.task_id for t in result["tasks"]], ["1", "1.1", "1.2", "2"]
        )

    def test_inject_skips_subtasks_matching_completed_work(self):
        """Sub-tasks equivalent to an already completed task are not injected again."""
        done = TASK(
            task_id="0",
            description="Subtask 1",
            tool_name="subtool_1",
            status="completed",
            required_context=REQUIRED_CONTEXT(source_node="test_node"),
        )
        self.state.tasks = [done, self.parent_task]
        duplicate = TASK(
            task_id="1.1",
            description="subtask 1",
            tool_name="SUBTOOL_1",
            required_context=REQUIRED_CONTEXT(source_node="decomposer"),
        )

        result = Spawn_subAgent.inject_subAgent_into_workflow(self.parent_task, [duplicate], self.state)

        self.assertEqual([t.task_id for t in result["tasks"]], ["0", "1"])


class TestWorkflowIntegration(unittest.TestCase):
    """Integration tests for the complete workflow."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        if not MODULES_AVAILABLE:
            self.skipTest("Required modules not available")

    def test_graph_building(self):
        """Test that the LangGraph can be built successfully."""
        try:
            graph = AgentGraphCore.build_graph()
            self.assertIsNotNone(graph)
            # Graph should be compiled and ready to use
        except Exception as e:
            self.fail(f"Graph building failed: {e}")

    @patch('src.agents.agentic_orchestrator.AgentGraphCore.AgentStatusUpdater')
    @patch('src.agents.agentic_orchestrator.AgentGraphCore.AgentCoreHelpers.get_safe_tools_list')
    @patch('src.agents.agentic_orchestrator.AgentGraphCore.AgentCoreHelpers.get_detailed_tool_context',
           return_value="tools")
    @patch('src.agents.agentic_orchestrator.AgentGraphCore.AgentCoreHelpers.recommend_tools_for_task',
           return_value=["test_tool"])
    @patch('src.agents.agentic_orchestrator.AgentGraphCore.ModelManager')
    def test_initial_planner_basic_execution(self, mock_model_manager, _recommend, _context, mock_get_tools, _status):
        """The initial planner turns a valid LLM plan into pending TASKs."""
        tool = Mock()
        tool.name = "Test_Tool"
        mock_get_tools.return_value = [tool]
        mock_model_manager.convert_to_json.return_value = [
            {"description": "Test task", "tool_name": "test_tool"}
        ]
        state = WorkflowStateModel(tasks=[], current_task_id="0", executed_nodes=[], original_goal="Test goal")

        result = AgentGraphCore._AgentGraphCore__subAGENT_initial_planner(state)

        self.assertEqual(result['workflow_status'], 'RUNNING')
        self.assertEqual(result['current_task_id'], "1")
        self.assertEqual(result['executed_nodes'], ["subAGENT_initial_planner"])
        self.assertEqual(len(result['tasks']), 1)
        self.assertEqual(result['tasks'][0].description, "Test task")
        self.assertEqual(result['tasks'][0].tool_name, "Test_Tool")  # case corrected to the registered name
        self.assertEqual(result['tasks'][0].status, "pending")

    @patch('src.agents.agentic_orchestrator.AgentGraphCore.AgentStatusUpdater')
    @patch('src.agents.agentic_orchestrator.AgentGraphCore.AgentCoreHelpers.get_safe_tools_list')
    @patch('src.agents.agentic_orchestrator.AgentGraphCore.AgentCoreHelpers.get_detailed_tool_context',
           return_value="tools")
    @patch('src.agents.agentic_orchestrator.AgentGraphCore.AgentCoreHelpers.recommend_tools_for_task',
           return_value=["test_tool"])
    @patch('src.agents.agentic_orchestrator.AgentGraphCore.ModelManager')
    def test_initial_planner_falls_back_on_invalid_tools(self, mock_model_manager, _recommend, _context,
                                                          mock_get_tools, _status):
        """When every attempt names an unknown tool, the planner uses its fallback task."""
        tool = Mock()
        tool.name = "test_tool"
        mock_get_tools.return_value = [tool]
        mock_model_manager.convert_to_json.return_value = [
            {"description": "Bad task", "tool_name": "made_up_tool"}
        ]
        state = WorkflowStateModel(tasks=[], current_task_id="0", executed_nodes=[], original_goal="Test goal")

        result = AgentGraphCore._AgentGraphCore__subAGENT_initial_planner(state)

        self.assertEqual(len(result['tasks']), 1)
        self.assertEqual(result['tasks'][0].required_context.source_node, "initial_planner_fallback")


class TestFailureRecovery(unittest.TestCase):
    """The retry/fallback loop is wired through the graph routers."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        if not MODULES_AVAILABLE:
            self.skipTest("Required modules not available")

    @staticmethod
    def _state(*statuses, persona=None):
        tasks = [
            TASK(
                task_id=str(i + 1),
                description=f"Task {i + 1}",
                tool_name="test_tool",
                status=status,
                required_context=REQUIRED_CONTEXT(source_node="test"),
            )
            for i, status in enumerate(statuses)
        ]
        return WorkflowStateModel(
            tasks=tasks, current_task_id="1", executed_nodes=[], original_goal="Goal", persona=persona
        )

    def test_failed_task_routes_back_to_classifier(self):
        route = AgentGraphCore._AgentGraphCore__router_after_execution(self._state("failed", "pending"))
        self.assertEqual(route, "subAGENT_classifier")

    def test_completed_task_with_pending_work_routes_to_planner(self):
        route = AgentGraphCore._AgentGraphCore__router_after_execution(self._state("completed", "pending"))
        self.assertEqual(route, "subAGENT_task_planner")

    def test_all_done_routes_to_finalizer(self):
        route = AgentGraphCore._AgentGraphCore__router_after_execution(self._state("completed", "skip"))
        self.assertEqual(route, "subAGENT_finalizer")

    def test_classifier_routes_error_fallback_persona(self):
        route = AgentGraphCore._AgentGraphCore__router_classifier(
            self._state("failed", persona="AGENT_PERFORM_ERROR_FALLBACK")
        )
        self.assertEqual(route, "subAGENT_error_fallback")

    def test_classifier_routes_to_parameter_generator_by_default(self):
        route = AgentGraphCore._AgentGraphCore__router_classifier(self._state("pending"))
        self.assertEqual(route, "subAGENT_parameter_generator")

    def test_task_planner_finalizes_when_all_terminal(self):
        route = AgentGraphCore._AgentGraphCore__router_task_planner(self._state("completed", "failed", "skip"))
        self.assertEqual(route, "subAGENT_finalizer")


if __name__ == '__main__':
    unittest.main()
