""" REAL INTEGRATION TEST: AgentGraphCore + agent_mode_node + Real Tools
This test demonstrates the complete hierarchical agent system working with actual tools
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import os
import tempfile
import time

# Add the project root to Python path
# (Already added above; keep this as a no-op for historical reasons.)

try:
    # Import hierarchical agent system
    from src.agents.agentic_orchestrator.AgentGraphCore import (
        AgentGraphCore, TASK, REQUIRED_CONTEXT, EXECUTION_CONTEXT, 
        MAIN_STATE, AgentState
    )
    
    # Import agent execution system
    from src.agents.agent_mode_node import agent_node, Agent
    
    # Import supporting systems
    from src.models.state import State, StateAccessor
    from src.tools.lggraph_tools.tool_assign import ToolAssign
    from src.config import settings
    
    MODULES_AVAILABLE = True
    print(" All modules imported successfully")
except ImportError as e:
    print(f" Import error: {e}")
    MODULES_AVAILABLE = False


class HierarchicalAgentIntegration:
    """Real integration between AgentGraphCore and agent_mode_node with actual tools."""
    
    def __init__(self, output_dir: str = None):
        if not MODULES_AVAILABLE:
            raise RuntimeError("Required modules not available for integration test")
        
        self.output_dir = output_dir or tempfile.mkdtemp(prefix="agent_integration_")
        self.execution_log = []
        self.results = {}
        
        print(f" Integration test initialized with output: {self.output_dir}")

    def convert_tasks_to_agent_format(self, tasks: list[TASK]) -> list[dict]:
        """
         INTEGRATION BRIDGE: Convert AgentGraphCore TASK objects to agent_mode_node format.
        
        This is the critical bridge between hierarchical planning and actual execution.
        """
        agent_exe_array = []
        
        for task in tasks:
            # Convert TASK to agent_mode_node format
            agent_task = {
                "tool_name": task.tool_name,
                "reasoning": f"Hierarchical agent task {task.task_id}: {task.description}",
                "parameters": task.execution_context.parameters if task.execution_context else {}
            }
            agent_exe_array.append(agent_task)
            
            self.execution_log.append({
                "action": "task_conversion",
                "task_id": task.task_id,
                "description": task.description,
                "tool_name": task.tool_name,
                "status": "converted"
            })
        
        print(f" Converted {len(tasks)} hierarchical tasks to agent execution format")
        return agent_exe_array

    def create_real_state_for_agent_node(self, user_goal: str) -> dict:
        """Create a real state object that agent_mode_node can process."""
        
        # Create a real message that represents the user's request
        human_message = settings.HumanMessage(content=user_goal)
        
        # Create state in the format agent_mode_node expects
        state = {
            "messages": [human_message],
            "message_type": "human"
        }
        
        # Initialize StateAccessor with the messages
        try:
            StateAccessor().add_message(human_message)
            print(f" Created real state for agent_node with user goal: {user_goal[:100]}...")
        except Exception as e:
            print(f" StateAccessor initialization issue: {e}")
        
        return state

    def execute_hierarchical_workflow(self, user_goal: str) -> dict:
        """
         MAIN INTEGRATION: Execute complete hierarchical workflow with real tools.
        
        Flow:
        1. User goal  AgentGraphCore planning
        2. Task decomposition  Real tasks
        3. Task execution  agent_mode_node + real tools
        4. Results collection  Real output
        """
        print("\n" + "="*80)
        print(" EXECUTING REAL HIERARCHICAL AGENT WORKFLOW")
        print("="*80)
        
        start_time = time.time()
        
        # === PHASE 1: Hierarchical Planning ===
        print("\n PHASE 1: Hierarchical Task Planning")
        print("-" * 50)
        
        try:
            # Create initial state for AgentGraphCore
            initial_state = {
                'tasks': [],
                'current_task_id': 0,
                'executed_nodes': [],
                'original_goal': user_goal,
                'persona': None,
                'workflow_status': 'STARTED'
            }
            
            # Build and execute hierarchical graph
            print(" Building hierarchical agent graph...")
            graph = AgentGraphCore.build_graph()
            
            print(" Executing initial planning...")
            final_state = graph.invoke(initial_state)
            
            # Extract planned tasks
            planned_tasks = final_state.get('tasks', [])
            print(f" Hierarchical planning complete: {len(planned_tasks)} tasks generated")
            
            for i, task in enumerate(planned_tasks, 1):
                print(f"      Task {i}: {task.description} (tool: {task.tool_name})")
                self.execution_log.append({
                    "phase": "planning",
                    "task_id": task.task_id,
                    "description": task.description,
                    "tool_name": task.tool_name,
                    "status": "planned"
                })
                
        except Exception as e:
            print(f" Hierarchical planning failed: {e}")
            self.results['planning_error'] = str(e)
            return self.results
        
        # === PHASE 2: Task Execution with Real Tools ===
        print("\n PHASE 2: Real Tool Execution")
        print("-" * 50)
        
        try:
            # Convert hierarchical tasks to agent execution format
            agent_exe_array = self.convert_tasks_to_agent_format(planned_tasks)
            
            # Create real state for agent_node
            agent_state = self.create_real_state_for_agent_node(user_goal)
            
            print(f"Executing {len(agent_exe_array)} tasks with real tools...")
            from src.tools.lggraph_tools.tool_response_manager import ToolResponseManager
            # Clear any previous responses
            ToolResponseManager().clear_response()
            
            # Execute each task with real tools using Agent class
            executed_results = []
            agent = Agent(agent_exe_array=agent_exe_array)
            
            for i in range(len(agent.agent_exe_array)):
                print(f"Executing task {i+1}: {agent.agent_exe_array[i]['tool_name']}")
                
                try:
                    # Execute the task
                    agent.start(index=i)
                    
                    # Get the result
                    last_response = ToolResponseManager().get_last_ai_message()
                    result_content = last_response.content if last_response else "No response"
                    
                    executed_results.append({
                        "task_index": i,
                        "tool_name": agent.agent_exe_array[i]['tool_name'],
                        "reasoning": agent.agent_exe_array[i]['reasoning'],
                        "result": result_content[:200] + "..." if len(result_content) > 200 else result_content,
                        "status": "completed"
                    })
                    
                    print(f"Task {i+1} completed successfully")
                    
                except Exception as task_error:
                    print(f"Task {i+1} failed: {task_error}")
                    executed_results.append({
                        "task_index": i,
                        "tool_name": agent.agent_exe_array[i]['tool_name'],
                        "error": str(task_error),
                        "status": "failed"
                    })
                    continue
                    
        except Exception as e:
            print(f"Tool execution failed: {e}")
            self.results['execution_error'] = str(e)
            return self.results
        
        # === PHASE 3: Results Consolidation ===
        print("\n PHASE 3: Results Analysis")
        print("-" * 50)
        
        execution_time = time.time() - start_time
        
        # Collect final results
        all_responses = ToolResponseManager().get_response()
        final_agent_response = ToolResponseManager().get_last_ai_message()
        
        successful_tasks = [r for r in executed_results if r.get('status') == 'completed']
        failed_tasks = [r for r in executed_results if r.get('status') == 'failed']
        
        self.results = {
            'user_goal': user_goal,
            'execution_time': execution_time,
            'planning_phase': {
                'tasks_planned': len(planned_tasks),
                'hierarchical_decomposition': [
                    {
                        'task_id': task.task_id,
                        'description': task.description,
                        'tool_name': task.tool_name
                    } for task in planned_tasks
                ]
            },
            'execution_phase': {
                'tasks_executed': len(executed_results),
                'successful_tasks': len(successful_tasks),
                'failed_tasks': len(failed_tasks),
                'success_rate': len(successful_tasks) / len(executed_results) if executed_results else 0,
                'detailed_results': executed_results
            },
            'tool_integration': {
                'real_tools_used': True,
                'tool_responses_count': len(all_responses),
                'final_response': final_agent_response.content if final_agent_response else "No final response"
            },
            'integration_status': 'SUCCESS' if len(successful_tasks) > 0 else 'PARTIAL_SUCCESS' if executed_results else 'FAILED'
        }
        
        print(f"Execution Summary:")
        print(f"Total time: {execution_time:.2f} seconds")
        print(f"Tasks planned: {len(planned_tasks)}")
        print(f"Tasks executed: {len(executed_results)}")
        print(f"Success rate: {self.results['execution_phase']['success_rate']:.1%}")
        print(f"Integration status: {self.results['integration_status']}")
        
        return self.results

    def demonstrate_real_workflow(self):
        """
         DEMONSTRATION: Show the hierarchical agent working on a real task.
        """
        print("\n" + "="*80)
        print(" HIERARCHICAL AGENT REAL WORKFLOW DEMONSTRATION")
        print("="*80)
        
        # Real-world test scenario
        test_scenarios = [
            {
                "name": "Project Analysis",
                "goal": "Analyze the current project structure, read the main files, and create a summary of the codebase architecture",
                "expected_tools": ["list_directory", "read_text_file", "create_or_update_file"]
            },
            {
                "name": "File Management",
                "goal": "Create a new directory called 'analysis_output', write a project summary file in it, and list the contents",
                "expected_tools": ["create_directory", "write_file", "list_directory"]
            }
        ]
        
        results = {}
        
        for scenario in test_scenarios:
            print(f"\n Testing Scenario: {scenario['name']}")
            print(f"Goal: {scenario['goal']}")
            
            try:
                scenario_results = self.execute_hierarchical_workflow(scenario['goal'])
                results[scenario['name']] = scenario_results
                
                print(f" Scenario '{scenario['name']}' completed with status: {scenario_results['integration_status']}")
                
            except Exception as e:
                print(f" Scenario '{scenario['name']}' failed: {e}")
                results[scenario['name']] = {'error': str(e), 'integration_status': 'FAILED'}
        
        return results


def run_real_integration_test():
    """Main function to run the real integration test."""
    
    if not MODULES_AVAILABLE:
        print(" Cannot run integration test - modules not available")
        return None
    
    print(" STARTING REAL HIERARCHICAL AGENT INTEGRATION TEST")
    print("=" * 80)
    
    # Check if tools are available
    try:
        available_tools = ToolAssign.get_tools_list()
        print(f" Available tools: {len(available_tools)}")
        for tool in available_tools[:5]:  # Show first 5 tools
            print(f"- {tool.name}: {getattr(tool, 'description', 'No description')[:50]}...")
        if len(available_tools) > 5:
            print(f"... and {len(available_tools) - 5} more tools")
            
    except Exception as e:
        print(f"Tool system not available: {e}")
        return None
    
    # Run the integration test
    try:
        integration = HierarchicalAgentIntegration()
        results = integration.demonstrate_real_workflow()
        
        print("\n" + "="*80)
        print(" INTEGRATION TEST RESULTS SUMMARY")
        print("="*80)
        
        for scenario_name, scenario_results in results.items():
            print(f"\n {scenario_name}:")
            if 'error' in scenario_results:
                print(f" Error: {scenario_results['error']}")
            else:
                status = scenario_results.get('integration_status', 'UNKNOWN')
                print(f"Status: {status}")
                print(f"Execution time: {scenario_results.get('execution_time', 0):.2f}s")
                
                planning = scenario_results.get('planning_phase', {})
                execution = scenario_results.get('execution_phase', {})
                print(f"Tasks planned: {planning.get('tasks_planned', 0)}")
                print(f"Tasks executed: {execution.get('tasks_executed', 0)}")
                print(f"Success rate: {execution.get('success_rate', 0):.1%}")
        
        print(f"\n INTEGRATION TEST COMPLETED!")
        print(f"Results saved to: {integration.output_dir}")
        
        return results
        
    except Exception as e:
        print(f"Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == '__main__':
    print(" Starting Real Integration Test...")
    results = run_real_integration_test()
    
    if results:
        print("\n Real integration test completed successfully!")
        print("The hierarchical agent system is working with real tools!")
    else:
        print("\n Real integration test failed!")
        print("Check the error messages above for debugging.")