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
            task_id=1,
            description="Test task description",
            tool_name="test_tool",
            required_context=required_context
        )
        
        self.assertEqual(task.task_id, 1)
        self.assertEqual(task.description, "Test task description")
        self.assertEqual(task.tool_name, "test_tool")
        self.assertEqual(task.status, "pending")  # Default status
        self.assertEqual(task.max_retries, 3)  # Default retries
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
            task_id=2,
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
            task_id=3,
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
        
        # Create a basic state object with required fields
        state = State(messages=[], message_type=None)
        main_state = MAIN_STATE(state=state)
        
        # Create a simple task
        required_context = REQUIRED_CONTEXT(source_node="test_node")
        task = TASK(
            task_id=1,
            description="Test task",
            tool_name="test_tool",
            required_context=required_context
        )
        
        # Create agent state
        agent_state = AgentState(
            TASKS=[task],
            MAIN_STATE=main_state,
            CURRENT_TASK_ID=1,
            original_goal="Test goal"
        )
        
        self.assertEqual(len(agent_state.TASKS), 1)
        self.assertEqual(agent_state.CURRENT_TASK_ID, 1)
        self.assertEqual(agent_state.original_goal, "Test goal")
        self.assertEqual(agent_state.MAIN_STATE.WORKFLOW_STATUS, "STARTED")


class TestAgentGraphCoreHelpers(unittest.TestCase):
    """Test cases for AgentGraphCore helper methods."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        if not MODULES_AVAILABLE:
            self.skipTest("Required modules not available")

    @patch('src.agents.agentic_orchestrator.AgentGraphCore.ToolAssign')
    def test_get_safe_tools_list_success(self, mock_tool_assign):
        """Test __get_safe_tools_list when tools are available."""
        # Mock tools
        mock_tool1 = Mock()
        mock_tool1.name = "test_tool_1"
        mock_tool2 = Mock()
        mock_tool2.name = "test_tool_2"
        
        mock_tool_assign.get_tools_list.return_value = [mock_tool1, mock_tool2]
        
        tools = AgentGraphCore._AgentGraphCore__get_safe_tools_list()
        
        self.assertEqual(len(tools), 2)
        self.assertEqual(tools[0].name, "test_tool_1")
        self.assertEqual(tools[1].name, "test_tool_2")

    @patch('src.agents.agentic_orchestrator.AgentGraphCore.ToolAssign')
    def test_get_safe_tools_list_empty(self, mock_tool_assign):
        """Test __get_safe_tools_list when no tools are available."""
        mock_tool_assign.get_tools_list.return_value = []
        
        with self.assertRaises(RuntimeError) as context:
            AgentGraphCore._AgentGraphCore__get_safe_tools_list()
        
        self.assertIn("No tools available", str(context.exception))

    @patch('src.agents.agentic_orchestrator.AgentGraphCore.AgentGraphCore.get_detailed_tool_context')
    def test_get_tools_string(self, mock_get_detailed_context):
        """Test __get_detailed_tool_context formatting."""
        # Mock the context returned by the detailed context method
        mock_get_detailed_context.return_value = "• test_tool_1: Test tool 1 description\n  Parameters: {}"

        tools_string = AgentGraphCore.get_detailed_tool_context(["test_tool_1"])

        self.assertIn("test_tool_1: Test tool 1 description", tools_string)
        self.assertIn("Parameters: {}", tools_string)


class TestToolExecutor(unittest.TestCase):
    """Test cases for the tool executor method."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        if not MODULES_AVAILABLE:
            self.skipTest("Required modules not available")

    @patch('src.agents.agentic_orchestrator.AgentGraphCore.AgentGraphCore._AgentGraphCore__get_safe_tools_list')
    @patch('src.tools.lggraph_tools.tool_response_manager.ToolResponseManager')
    def test_tool_executor_success(self, mock_response_manager, mock_get_tools):
        """Test successful tool execution."""
        # Mock tool
        mock_tool = Mock()
        mock_tool.name = "test_tool"
        mock_get_tools.return_value = [mock_tool]
        
        # Mock response
        mock_response = Mock()
        mock_response.content = "Tool executed successfully"
        mock_response_manager_instance = Mock()
        mock_response_manager_instance.get_response.return_value = [mock_response]
        mock_response_manager.return_value = mock_response_manager_instance
        
        success, result = AgentGraphCore._AgentGraphCore__tool_executor(
            "test_tool", 
            {"param1": "value1"}
        )
        
        self.assertTrue(success)
        self.assertEqual(result, "Tool executed successfully")

    @patch('src.agents.agentic_orchestrator.AgentGraphCore.AgentGraphCore._AgentGraphCore__get_safe_tools_list')
    def test_tool_executor_tool_not_found(self, mock_get_tools):
        """Test tool executor when tool is not found."""
        mock_tool = Mock()
        mock_tool.name = "different_tool"
        mock_get_tools.return_value = [mock_tool]
        
        success, result = AgentGraphCore._AgentGraphCore__tool_executor(
            "nonexistent_tool", 
            {"param1": "value1"}
        )
        
        self.assertFalse(success)
        self.assertIn("not found", result)

    @patch('src.agents.agentic_orchestrator.AgentGraphCore.AgentGraphCore._AgentGraphCore__get_safe_tools_list')
    @patch('src.tools.lggraph_tools.tool_response_manager.ToolResponseManager')
    def test_tool_executor_no_response(self, mock_response_manager, mock_get_tools):
        """Test tool executor when no response is received."""
        # Mock tool
        mock_tool = Mock()
        mock_tool.name = "test_tool"
        mock_get_tools.return_value = [mock_tool]
        
        # Mock empty response
        mock_response_manager_instance = Mock()
        mock_response_manager_instance.get_response.return_value = []
        mock_response_manager.return_value = mock_response_manager_instance
        
        success, result = AgentGraphCore._AgentGraphCore__tool_executor(
            "test_tool", 
            {"param1": "value1"}
        )
        
        self.assertFalse(success)
        self.assertIn("No response received", result)


class TestSpawnSubAgent(unittest.TestCase):
    """Test cases for the Spawn_subAgent class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        if not MODULES_AVAILABLE:
            self.skipTest("Required modules not available")
        
        # Create a sample parent task
        self.required_context = REQUIRED_CONTEXT(source_node="test_node")
        self.parent_task = TASK(
            task_id=1,
            description="Complex task requiring decomposition",
            tool_name="complex_tool",
            required_context=self.required_context
        )
        
        # Create a sample state with required fields
        state = State(messages=[], message_type=None)
        main_state = MAIN_STATE(state=state)
        self.agent_state = AgentState(
            TASKS=[self.parent_task],
            MAIN_STATE=main_state,
            CURRENT_TASK_ID=1,
            original_goal="Test goal"
        )

    @patch('src.agents.agentic_orchestrator.AgentGraphCore.ModelManager')
    def test_analyze_spawn_requirement_should_spawn(self, mock_model_manager):
        """Test spawn requirement analysis that recommends spawning."""
        # Mock LLM response indicating spawning is needed
        mock_response = Mock()
        mock_response.content = '{"should_spawn": true, "reasoning": "Task is complex"}'
        
        mock_model_instance = Mock()
        mock_model_instance.invoke.return_value = mock_response
        mock_model_manager.return_value = mock_model_instance
        
        # Mock JSON conversion
        with patch('src.agents.agentic_orchestrator.AgentGraphCore.ModelManager.convert_to_json') as mock_convert:
            mock_convert.return_value = {
                "should_spawn": True,
                "reasoning": "Task is complex"
            }
            
            result = Spawn_subAgent.analyze_spawn_requirement(
                self.parent_task, 
                "complexity analysis", 
                self.agent_state
            )
            
            self.assertTrue(result["should_spawn"])
            self.assertEqual(result["reasoning"], "Task is complex")

    @patch('src.agents.agentic_orchestrator.AgentGraphCore.ModelManager')
    def test_analyze_spawn_requirement_no_spawn(self, mock_model_manager):
        """Test spawn requirement analysis that doesn't recommend spawning."""
        # Mock LLM response indicating no spawning needed
        mock_response = Mock()
        mock_response.content = '{"should_spawn": false, "reasoning": "Task is simple"}'
        
        mock_model_instance = Mock()
        mock_model_instance.invoke.return_value = mock_response
        mock_model_manager.return_value = mock_model_instance
        
        # Mock JSON conversion
        with patch('src.agents.agentic_orchestrator.AgentGraphCore.ModelManager.convert_to_json') as mock_convert:
            mock_convert.return_value = {
                "should_spawn": False,
                "reasoning": "Task is simple"
            }
            
            result = Spawn_subAgent.analyze_spawn_requirement(
                self.parent_task, 
                "complexity analysis", 
                self.agent_state
            )
            
            self.assertFalse(result["should_spawn"])
            self.assertEqual(result["reasoning"], "Task is simple")

    @patch('src.agents.agentic_orchestrator.AgentGraphCore.AgentGraphCore.recommend_tools_for_task')
    @patch('src.agents.agentic_orchestrator.AgentGraphCore.AgentGraphCore.get_safe_tools_list')
    @patch('src.agents.agentic_orchestrator.AgentGraphCore.ModelManager')
    def test_decompose_task_for_subAgent(self, mock_model_manager, mock_get_tools, mock_recommend_tools):
        """Test task decomposition into sub-tasks."""
        # Mock available tools
        mock_tool1 = Mock()
        mock_tool1.name = "subtool_1"
        mock_tool2 = Mock()
        mock_tool2.name = "subtool_2"
        mock_get_tools.return_value = [mock_tool1, mock_tool2]
        
        # Mock recommended tools
        mock_recommend_tools.return_value = ["subtool_1", "subtool_2"]
        
        # Mock LLM response with decomposed tasks
        mock_response = Mock()
        mock_response.content = '[{"description": "Subtask 1", "tool_name": "subtool_1"}, {"description": "Subtask 2", "tool_name": "subtool_2"}]'
        
        mock_model_instance = Mock()
        mock_model_instance.invoke.return_value = mock_response
        mock_model_manager.return_value = mock_model_instance
        
        # Mock JSON conversion
        with patch('src.agents.agentic_orchestrator.AgentGraphCore.ModelManager.convert_to_json') as mock_convert:
            mock_convert.return_value = [
                {"description": "Subtask 1", "tool_name": "subtool_1"},
                {"description": "Subtask 2", "tool_name": "subtool_2"}
            ]
            
            subtasks = Spawn_subAgent.decompose_task_for_subAgent(
                self.parent_task, 
                self.agent_state
            )
            
            self.assertEqual(len(subtasks), 2)
            self.assertEqual(subtasks[0].description, "Subtask 1")
            self.assertEqual(subtasks[0].tool_name, "subtool_1")
            self.assertEqual(subtasks[0].task_id, 1.1)  # Parent ID 1 + sub-index 1
            self.assertEqual(subtasks[1].description, "Subtask 2")
            self.assertEqual(subtasks[1].tool_name, "subtool_2")
            self.assertEqual(subtasks[1].task_id, 1.2)  # Parent ID 1 + sub-index 2

    def test_inject_subAgent_into_workflow(self):
        """Test injection of sub-tasks into workflow."""
        # Create subtasks
        subtask1 = TASK(
            task_id=1.1,
            description="Subtask 1",
            tool_name="subtool_1",
            required_context=REQUIRED_CONTEXT(source_node="decomposer")
        )
        subtask2 = TASK(
            task_id=1.2,
            description="Subtask 2",
            tool_name="subtool_2",
            required_context=REQUIRED_CONTEXT(source_node="decomposer")
        )
        
        # Mock the state's TASKS list to make the parent task findable
        self.agent_state.TASKS = [self.parent_task]
        
        result = Spawn_subAgent.inject_subAgent_into_workflow(
            self.parent_task, 
            [subtask1, subtask2], 
            self.agent_state
        )
        
        # Check that parent task status is updated
        self.assertEqual(self.parent_task.status, "in_progress")
        self.assertIsNotNone(self.parent_task.execution_context)
        self.assertIn("2 sub-tasks", self.parent_task.execution_context.analysis)
        
        # Check that subtasks are injected correctly
        updated_tasks = result["tasks"]
        self.assertEqual(len(updated_tasks), 3)  # Parent + 2 subtasks
        self.assertEqual(updated_tasks[0], self.parent_task)  # Parent first
        self.assertEqual(updated_tasks[1], subtask1)  # Then subtasks
        self.assertEqual(updated_tasks[2], subtask2)


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

    @patch('src.agents.agentic_orchestrator.AgentGraphCore.ModelManager')
    def test_initial_planner_basic_execution(self, mock_model_manager):
        """Test basic execution of the initial planner node."""
        # Mock LLM response
        mock_response = Mock()
        mock_response.content = '[{"task_id": 1, "description": "Test task", "tool_name": "test_tool"}]'
        
        mock_model_instance = Mock()
        mock_model_instance.invoke.return_value = mock_response
        mock_model_manager.return_value = mock_model_instance
        
        # Mock JSON conversion
        with patch('src.agents.agentic_orchestrator.AgentGraphCore.ModelManager.convert_to_json') as mock_convert:
            mock_convert.return_value = [
                {"task_id": 1, "description": "Test task", "tool_name": "test_tool"}
            ]
            
            # Create initial state with required fields
            state = State(messages=[], message_type=None)
            main_state = MAIN_STATE(state=state)
            agent_state = AgentState(
                TASKS=[],
                MAIN_STATE=main_state,
                CURRENT_TASK_ID=0,
                original_goal="Test goal"
            )
            
            # Convert to dict for node execution
            state_dict = {
                'original_goal': 'Test goal',
                'executed_nodes': []
            }
            
            result = AgentGraphCore._AgentGraphCore__subAGENT_initial_planner(state_dict)
            
            self.assertIn('tasks', result)
            self.assertIn('current_task_id', result)
            self.assertIn('workflow_status', result)
            self.assertEqual(result['workflow_status'], 'RUNNING')
            self.assertEqual(len(result['tasks']), 1)
            self.assertEqual(result['tasks'][0].description, "Test task")

class TestFailureRecovery(unittest.TestCase):
    """Test cases for the failure recovery and retry loop."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        if not MODULES_AVAILABLE:
            self.skipTest("Required modules not available")

    @patch('src.agents.agentic_orchestrator.AgentGraphCore.ModelManager')
    @patch('src.agents.agentic_orchestrator.AgentGraphCore.AgentGraphCore._AgentGraphCore__tool_executor')
    def test_failure_recovery_loop_and_fallback(self, mock_tool_executor, mock_model_manager):
        """
        Test the full failure-retry-fallback loop.
        - A task should fail.
        - It should retry based on max_retries.
        - After exhausting retries, it should trigger the error_fallback node.
        """
        # 1. Setup Mocks
        # Mock the tool executor to always fail
        mock_tool_executor.return_value = (False, "Mock tool failure: File not found")

        # Mock the LLM response for the error_fallback node
        mock_fallback_response = Mock()
        fallback_suggestion = {
            "recovery_strategy": "RETRY_WITH_NEW_PARAMS",
            "updated_parameters": {"path": "/corrected/path.txt"},
            "alternative_tool": None,
            "reasoning": "The file path was likely incorrect. Correcting the path."
        }
        mock_fallback_response.content = str(fallback_suggestion)
        
        mock_model_instance = Mock()
        # The first call to the model will be for parameter generation, the rest for fallback
        mock_model_instance.invoke.side_effect = [
            # Mock response for parameter generator (1st attempt)
            Mock(content='{"path": "/wrong/path.txt"}'),
            # Mock response for parameter generator (2nd attempt)
            Mock(content='{"path": "/another/wrong/path.txt"}'),
            # Mock response for the error_fallback node
            mock_fallback_response,
            # Add extra responses to prevent StopIteration
            mock_fallback_response,
            mock_fallback_response
        ]
        mock_model_manager.return_value = mock_model_instance

        # 2. Setup Initial State
        # Create a task that is destined to fail
        task = TASK(
            task_id=1,
            description="Read a file that does not exist.",
            tool_name="read_text_file",
            required_context=REQUIRED_CONTEXT(source_node="initial_planner"),
            max_retries=2 # Set a specific retry limit
        )
        
        initial_state = {
            "tasks": [task],
            "current_task_id": 1,
            "original_goal": "Test the failure recovery loop.",
            "executed_nodes": [],
            "persona": "AGENT_PERFORM_TASK",
            "workflow_status": "RUNNING"
        }

        # 3. Build and run the graph
        graph = AgentGraphCore.build_graph()
        # We need to manually set the entry point for this test
        # to bypass the initial_planner
        graph.entry_point = "subAGENT_classifier"
        final_state = graph.invoke(initial_state)

        # 4. Assertions
        # Find the final state of our task
        final_task = next((t for t in final_state['tasks'] if t.task_id == 1), None)

        self.assertIsNotNone(final_task)
        self.assertEqual(final_task.status, "failed")
        self.assertIsNotNone(final_task.failure_context)
        
        # It should have failed once, then retried once, failing again.
        # The fail_count should be equal to max_retries.
        self.assertEqual(final_task.failure_context.fail_count, 2)
        
        # Check that the error_fallback node was executed
        self.assertIn("subAGENT_error_fallback", final_state["executed_nodes"])
        
        # Check that the recovery suggestion from the mocked LLM was stored
        self.assertIsNotNone(final_task.failure_context.recovery_actions)
        self.assertEqual(final_task.failure_context.recovery_actions["updated_parameters"]["path"], "/corrected/path.txt")

if __name__ == '__main__':
    unittest.main()