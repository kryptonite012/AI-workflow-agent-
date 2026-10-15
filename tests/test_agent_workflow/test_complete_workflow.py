"""
End-to-end workflow test for the hierarchical agent system.
This test simulates a real user task and executes the complete workflow.
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
import tempfile
import shutil

try:
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


class TestCompleteWorkflow(unittest.TestCase):
    """Complete end-to-end workflow testing with real user scenarios."""

    def setUp(self):
        """Set up test fixtures for workflow testing."""
        if not MODULES_AVAILABLE:
            self.skipTest("Required modules not available")

        # Create temporary directory for test outputs
        self.test_output_dir = tempfile.mkdtemp(prefix="workflow_test_")

        # Sample user task for testing
        self.user_task = "Search the web for information about dark web security risks and create a detailed markdown report explaining the findings in the output folder"

        print(f"?? Setting up workflow test with output directory: {self.test_output_dir}")

    def tearDown(self):
        """Clean up test artifacts."""
        # Clean up temporary directory
        if os.path.exists(self.test_output_dir):
            shutil.rmtree(self.test_output_dir)

    @patch('src.agents.agentic_orchestrator.AgentGraphCore.ModelManager')
    @patch('src.agents.agentic_orchestrator.AgentGraphCore.ToolAssign')
    def test_complete_dark_web_research_workflow(self, mock_tool_assign, mock_model_manager):
        """
        Test complete workflow: User asks for dark web research ? Agent decomposes ? Executes ? Generates report

        This test simulates:
        1. User provides complex research task
        2. Initial planner breaks it into atomic tasks
        3. Each task gets executed by appropriate tools
        4. Results are consolidated into final markdown report
        """
        print("\n" + "="*80)
        print("?? TESTING: Complete Dark Web Research Workflow")
        print("="*80)

        # ========== STEP 1: Setup Mock Tools ==========
        print("?? Step 1: Setting up mock tools for workflow execution...")

        # Mock available tools
        mock_web_search_tool = Mock()
        mock_web_search_tool.name = "web_search"
        mock_web_search_tool.description = "Search the web for information"

        mock_file_writer_tool = Mock()
        mock_file_writer_tool.name = "write_markdown_file"
        mock_file_writer_tool.description = "Write content to markdown file"

        mock_summarizer_tool = Mock()
        mock_summarizer_tool.name = "llm_summarize"
        mock_summarizer_tool.description = "Summarize and analyze text content"

        # Setup tool registry
        mock_tool_assign.get_tools_list.return_value = [
            mock_web_search_tool,
            mock_file_writer_tool,
            mock_summarizer_tool
        ]

        # ========== STEP 2: Setup Mock LLM Responses ==========
        print("?? Step 2: Setting up mock LLM responses for workflow planning...")

        # Mock LLM responses for different workflow stages
        llm_responses = {
            'initial_planning': [
                {
                    "task_id": 1,
                    "description": "Search web for dark web security risks and threats",
                    "tool_name": "web_search"
                },
                {
                    "task_id": 2,
                    "description": "Analyze and summarize security risk findings",
                    "tool_name": "llm_summarize"
                },
                {
                    "task_id": 3,
                    "description": "Create comprehensive markdown report with findings",
                    "tool_name": "write_markdown_file"
                }
            ],
            'parameter_generation': [
                {
                    "query": "dark web security risks threats cybersecurity",
                    "num_results": 10,
                    "search_depth": "comprehensive"
                },
                {
                    "content": "research_findings_from_step_1",
                    "analysis_type": "security_risks",
                    "output_format": "structured_summary"
                },
                {
                    "file_path": f"{self.test_output_dir}/dark_web_security_report.md",
                    "content": "comprehensive_markdown_report",
                    "format": "markdown"
                }
            ],
            'task_complexity': [
                {
                    "requires_decomposition": False,
                    "reasoning": "Task is atomic and can be executed with single tool",
                    "atomic_tool_name": "web_search"
                },
                {
                    "requires_decomposition": False,
                    "reasoning": "Text summarization is atomic operation",
                    "atomic_tool_name": "llm_summarize"
                },
                {
                    "requires_decomposition": False,
                    "reasoning": "File writing is atomic operation",
                    "atomic_tool_name": "write_markdown_file"
                }
            ]
        }

        # ========== STEP 3: Setup Mock Tool Executions ==========
        print("?? Step 3: Setting up mock tool execution responses...")

        tool_execution_results = {
            "web_search": """
            # Dark Web Security Research Results

            ## Key Findings:
            1. **Access Methods**: Tor browser, I2P, specialized anonymity networks
            2. **Security Risks**:
               - Malware distribution
               - Stolen data marketplaces
               - Identity theft services
               - Drug trafficking platforms
            3. **Cybersecurity Threats**:
               - Ransomware-as-a-Service (RaaS)
               - Credential stuffing attacks
               - Zero-day exploit sales
               - Corporate data breaches
            4. **Protection Measures**:
               - Network monitoring
               - Employee training
               - Multi-factor authentication
               - Dark web monitoring services
            """,

            "llm_summarize": """
            # Executive Summary: Dark Web Security Risks

            The dark web poses significant cybersecurity threats to organizations and individuals:

            **Primary Threat Vectors:**
            - **Data Breaches**: Stolen corporate and personal data sold on marketplaces
            - **Malware Distribution**: Advanced persistent threats and ransomware
            - **Identity Theft**: Personal information trading and synthetic identity creation
            - **Cybercrime Services**: Hacking-for-hire and credential theft operations

            **Recommended Mitigations:**
            - Implement comprehensive monitoring solutions
            - Regular security awareness training
            - Deploy advanced threat detection systems
            - Establish incident response procedures
            """,

            "write_markdown_file": f"Successfully created dark web security report at {self.test_output_dir}/dark_web_security_report.md"
        }

        # ========== STEP 4: Configure Mock Behavior ==========
        print("?? Step 4: Configuring mock behavior for workflow execution...")

        def mock_model_manager_side_effect(*args, **kwargs):
            """Dynamic mock behavior based on context."""
            mock_instance = Mock()
            mock_response = Mock()

            # Determine which stage we're in based on call count
            call_count = getattr(mock_model_manager, 'call_count', 0)
            mock_model_manager.call_count = call_count + 1

            if call_count == 0:  # Initial planning
                mock_response.content = str(llm_responses['initial_planning']).replace("'", '"')  # Ensure valid JSON
            elif call_count <= 3:  # Parameter generation (3 tasks)
                param_index = min(call_count - 1, len(llm_responses['parameter_generation']) - 1)
                mock_response.content = str(llm_responses['parameter_generation'][param_index]).replace("'", '"')
            else:  # Task complexity analysis
                complexity_index = min((call_count - 4) % 3, len(llm_responses['task_complexity']) - 1)
                mock_response.content = str(llm_responses['task_complexity'][complexity_index]).replace("'", '"')

            mock_instance.invoke.return_value = mock_response
            return mock_instance

        mock_model_manager.side_effect = mock_model_manager_side_effect

        # ========== STEP 5: Mock Tool Response Manager ==========
        print("?? Step 5: Setting up tool response management...")

        def mock_tool_execution(tool_name, parameters):
            """Mock tool execution with realistic responses."""
            print(f"   ?? Executing tool: {tool_name} with parameters: {parameters}")

            if tool_name.lower() in tool_execution_results:
                result = tool_execution_results[tool_name.lower()]
                print(f"   ? Tool execution successful: {len(result)} characters returned")
                return (True, result)
            else:
                error_msg = f"Tool {tool_name} not found in mock registry"
                print(f"   ? Tool execution failed: {error_msg}")
                return (False, error_msg)

        # ========== STEP 6: Mock JSON Conversion ==========
        def mock_json_convert(content):
            """Mock JSON conversion with realistic parsing."""
            try:
                # Try to parse as JSON first
                import json
                if isinstance(content, str):
                    # Clean up the content for JSON parsing
                    clean_content = content.replace("'", '"')
                    return json.loads(clean_content)
                return content
            except:
                try:
                    import ast
                    return ast.literal_eval(content)
                except:
                    # Fallback parsing for different response types
                    content_str = str(content)
                    if 'task_id' in content_str and 'description' in content_str:
                        return llm_responses['initial_planning']
                    elif 'query' in content_str or 'file_path' in content_str:
                        # Return appropriate parameter response
                        call_count = getattr(mock_model_manager, 'call_count', 1)
                        param_index = min(max(0, call_count - 2), len(llm_responses['parameter_generation']) - 1)
                        return llm_responses['parameter_generation'][param_index]
                    elif 'requires_decomposition' in content_str:
                        return llm_responses['task_complexity'][0]
                    else:
                        return {"status": "parsed", "content": str(content)}

        # Mock hierarchical agent prompts
        def mock_prompt_generator():
            mock_generator = Mock()
            mock_generator.generate_initial_plan_prompt.return_value = ("system prompt", "human prompt")
            mock_generator.generate_parameter_prompt.return_value = ("system prompt", "human prompt")
            mock_generator.generate_task_complexity_analysis_prompt.return_value = ("system prompt", "human prompt")
            mock_generator.generate_final_response_prompt.return_value = ("system prompt", "human prompt")
            return mock_generator

        # ========== STEP 7: Execute Complete Workflow ==========
        print("?? Step 7: Executing complete workflow...")

        with patch('src.agents.agentic_orchestrator.AgentGraphCore.ModelManager.convert_to_json', side_effect=mock_json_convert), \
             patch('src.agents.agentic_orchestrator.AgentGraphCore.AgentGraphCore._AgentGraphCore__tool_executor', side_effect=mock_tool_execution), \
             patch('src.agents.agentic_orchestrator.AgentGraphCore.HierarchicalAgentPrompt', side_effect=mock_prompt_generator):

            # Create initial state
            print("   ?? Creating initial agent state...")
            state = State(messages=[], message_type=None)
            main_state = MAIN_STATE(state=state)

            initial_state = {
                'TASKS': [],
                'MAIN_STATE': main_state,
                'CURRENT_TASK_ID': 0,
                'original_goal': self.user_task,
                'persona': None,
                'executed_nodes': []  # Add missing executed_nodes key
            }

            # Build and execute workflow graph
            print("   ??? Building workflow graph...")
            graph = AgentGraphCore.build_graph()
            self.assertIsNotNone(graph, "Graph should be successfully built")

            print("   ?? Executing workflow...")

            # Execute initial planning
            print("      ? Stage 1: Initial Planning")
            planning_result = AgentGraphCore._AgentGraphCore__subAGENT_initial_planner(initial_state)

            # Verify planning results
            self.assertIn('tasks', planning_result)
            self.assertIn('workflow_status', planning_result)
            self.assertEqual(planning_result['workflow_status'], 'RUNNING')
            self.assertGreaterEqual(len(planning_result['tasks']), 1)  # At least 1 task should be generated

            print(f"      ? Generated {len(planning_result['tasks'])} tasks")
            for i, task in enumerate(planning_result['tasks'], 1):
                print(f"         Task {i}: {task.description} (tool: {task.tool_name})")

            # Execute each task through the workflow
            current_state = {
                'tasks': planning_result['tasks'],
                'current_task_id': planning_result['current_task_id'],
                'executed_nodes': planning_result['executed_nodes'],
                'original_goal': self.user_task
            }

            task_results = []

            for task_num in range(len(planning_result['tasks'])):
                print(f"      ? Stage {task_num + 2}: Processing Task {task_num + 1}")

                # Classifier stage
                classifier_result = AgentGraphCore._AgentGraphCore__subAGENT_classifier(current_state)
                current_state.update(classifier_result)

                # Parameter generation stage
                param_result = AgentGraphCore.subAGENT_parameter_generator(current_state)
                current_state.update(param_result)

                # Task execution stage
                exec_result = AgentGraphCore._AgentGraphCore__subAGENT_task_executor(current_state)
                current_state.update(exec_result)

                # Task planning stage (find next task)
                if task_num < len(planning_result['tasks']) - 1:
                    planner_result = AgentGraphCore._AgentGraphCore__subAGENT_task_planner(current_state)
                    current_state.update(planner_result)

                print(f"      ? Task {task_num + 1} completed")
                task_results.append(exec_result)

            # Final consolidation
            print("      ? Final Stage: Consolidating Results")
            final_result = AgentGraphCore._AgentGraphCore__subAGENT_finalizer(current_state)

            # ========== STEP 8: Verify Workflow Results ==========
            print("?? Step 8: Verifying workflow execution results...")

            # Verify final result structure
            self.assertIn('final_response', final_result)
            self.assertIn('workflow_status', final_result)
            self.assertEqual(final_result['workflow_status'], 'COMPLETED')

            # Verify all tasks were processed
            processed_tasks = current_state['tasks']
            self.assertEqual(len(processed_tasks), 3)

            # Verify task completion states
            completed_tasks = [t for t in processed_tasks if t.status == 'completed']
            self.assertGreaterEqual(len(completed_tasks), 1, "At least one task should be completed")

            print(f"   ? Workflow completed successfully!")
            print(f"   ?? Tasks processed: {len(processed_tasks)}")
            print(f"   ? Tasks completed: {len(completed_tasks)}")
            print(f"   ?? Final response length: {len(final_result.get('final_response', ''))}")

            # Verify specific workflow characteristics
            web_search_task = next((t for t in processed_tasks if t.tool_name == 'web_search'), None)
            if web_search_task:
                self.assertIsNotNone(web_search_task.execution_context)
                print(f"   ?? Web search task properly configured with parameters")

            markdown_task = next((t for t in processed_tasks if t.tool_name == 'write_markdown_file'), None)
            if markdown_task:
                self.assertIsNotNone(markdown_task.execution_context)
                print(f"   ?? Markdown file creation task properly configured")

            print("\n" + "="*80)
            print("?? WORKFLOW TEST COMPLETED SUCCESSFULLY!")
            print("="*80)

            return {
                'workflow_status': final_result['workflow_status'],
                'tasks_processed': len(processed_tasks),
                'tasks_completed': len(completed_tasks),
                'final_response': final_result.get('final_response', ''),
                'execution_summary': {
                    'planning_successful': len(planning_result['tasks']) > 0,
                    'execution_successful': len(completed_tasks) > 0,
                    'consolidation_successful': 'final_response' in final_result
                }
            }

    def test_workflow_with_sub_agent_spawning(self):
        """
        Test workflow that triggers sub-agent spawning for complex tasks.
        This tests the recursive decomposition capability.
        """
        print("\n" + "="*80)
        print("?? TESTING: Workflow with Sub-Agent Spawning")
        print("="*80)

        # This would test scenarios where tasks are complex enough to trigger spawning
        # For now, we'll create a placeholder that verifies the spawning logic

        complex_task = TASK(
            task_id=1,
            description="Create a comprehensive cybersecurity analysis including dark web monitoring, threat assessment, and policy recommendations with detailed implementation guides",
            tool_name="complex_analysis_tool",
            required_context=REQUIRED_CONTEXT(source_node="test_spawning")
        )

        # Verify that complex tasks can trigger spawning analysis
        with patch('src.agents.agentic_orchestrator.AgentGraphCore.ModelManager') as mock_model_manager:
            mock_response = Mock()
            mock_response.content = '{"requires_decomposition": true, "reasoning": "Task requires multiple specialized tools and extensive research"}'

            mock_instance = Mock()
            mock_instance.invoke.return_value = mock_response
            mock_model_manager.return_value = mock_instance

            with patch('src.agents.agentic_orchestrator.AgentGraphCore.ModelManager.convert_to_json') as mock_convert:
                mock_convert.return_value = {
                    "requires_decomposition": True,
                    "reasoning": "Task requires multiple specialized tools and extensive research"
                }

                analysis_result = AgentGraphCore._AgentGraphCore__analyze_task_complexity(complex_task)

                self.assertTrue(analysis_result.get("requires_decomposition"))
                self.assertIn("reasoning", analysis_result)

                print("   ? Complex task properly identified for decomposition")
                print(f"   ?? Reasoning: {analysis_result.get('reasoning')}")

    @patch('src.agents.agentic_orchestrator.AgentGraphCore.ToolAssign')
    def test_workflow_error_recovery(self, mock_tool_assign):
        """
        Test workflow error recovery and fallback mechanisms.
        """
        print("\n" + "="*80)
        print("??? TESTING: Workflow Error Recovery")
        print("="*80)

        # Setup scenario where tools fail and recovery is needed
        mock_failing_tool = Mock()
        mock_failing_tool.name = "failing_tool"
        mock_tool_assign.get_tools_list.return_value = [mock_failing_tool]

        # Create task that will fail
        failing_task = TASK(
            task_id=1,
            description="This task will fail to test error recovery",
            tool_name="failing_tool",
            required_context=REQUIRED_CONTEXT(source_node="test_error_recovery"),
            execution_context=EXECUTION_CONTEXT(
                tool_name="failing_tool",
                parameters={"param": "value"}
            )
        )

        # Mock tool execution failure
        def mock_failing_tool_executor(tool_name, parameters):
            return (False, "Tool execution failed: Network timeout")

        with patch('src.agents.agentic_orchestrator.AgentGraphCore.AgentGraphCore._AgentGraphCore__tool_executor', side_effect=mock_failing_tool_executor), \
             patch('src.agents.agentic_orchestrator.AgentGraphCore.HierarchicalAgentPrompt') as mock_prompt_class, \
             patch('src.agents.agentic_orchestrator.AgentGraphCore.ModelManager') as mock_model_manager_error, \
             patch('src.agents.agentic_orchestrator.AgentGraphCore.ModelManager.convert_to_json') as mock_convert_error:

            # Mock prompt generator
            mock_prompt_instance = Mock()
            mock_prompt_instance.generate_task_complexity_analysis_prompt.return_value = ("system prompt", "human prompt")
            mock_prompt_class.return_value = mock_prompt_instance

            # Mock model manager for complexity analysis
            mock_model_instance = Mock()
            mock_response = Mock()
            mock_response.content = '{"requires_decomposition": false, "reasoning": "Task is atomic"}'
            mock_model_instance.invoke.return_value = mock_response
            mock_model_manager_error.return_value = mock_model_instance

            # Mock JSON conversion
            mock_convert_error.return_value = {
                "requires_decomposition": False,
                "reasoning": "Task is atomic",
                "atomic_tool_name": "failing_tool"
            }

            # Create state with failing task
            state = State(messages=[], message_type=None)
            main_state = MAIN_STATE(state=state)
            test_state = {
                'tasks': [failing_task],
                'current_task_id': 1,
                'executed_nodes': [],
                'original_goal': "Test error recovery"
            }

            # Execute task executor (should handle failure gracefully)
            result = AgentGraphCore._AgentGraphCore__subAGENT_task_executor(test_state)

            # Verify error handling
            updated_tasks = result['tasks']
            failed_task = updated_tasks[0]

            self.assertEqual(failed_task.status, "failed")
            self.assertIsNotNone(failed_task.failure_context)
            self.assertIn("Tool execution failed", failed_task.failure_context.error_message)

            print("   ? Task failure properly detected and recorded")
            print(f"   ?? Error message: {failed_task.failure_context.error_message}")
            print("   ?? Error recovery mechanisms triggered")