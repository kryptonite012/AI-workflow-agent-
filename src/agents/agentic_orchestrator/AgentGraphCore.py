import uuid
from typing import TYPE_CHECKING, Any, Literal

from langgraph.constants import END
from pydantic import BaseModel, Field

from src.utils.timestamp_util import get_formatted_timestamp
from .hierarchical_agent_prompts import HierarchicalAgentPrompt
from ...config import settings
# Fixed imports - use relative imports instead of src.
from ...tools.lggraph_tools.tool_assign import ToolAssign

try:
    from ...ui.diagnostics.debug_helpers import (
        debug_info,
        debug_warning,
        debug_critical,
        debug_error,
    )
except Exception:
    # Fallback no-op loggers for environments where the diagnostics module
    # may not be importable during static analysis or testing.
    def debug_info(*args, **kwargs):
        return None


    def debug_warning(*args, **kwargs):
        return None


    def debug_critical(*args, **kwargs):
        return None


    def debug_error(*args, **kwargs):
        return None
from ...utils.argument_schema_util import get_tool_argument_schema
from ...utils.model_manager import ModelManager

# Forward reference for TASK to avoid circular import issues

if TYPE_CHECKING:
    TaskListType = list["TASK"]
else:
    TaskListType = list["TASK"]


class MAIN_STATE(BaseModel):
    # TODO we are removed main state from the workflow because workflow should work isolated but if we feel context is needed we can add it back

    WORKFLOW_STATUS: Literal["RUNNING", "COMPLETED", "FAILED", "RESTART", "STARTED"] = Field(default="STARTED")
    EXECUTED_NODES: list[str] = Field(default_factory=list, description="List of executed nodes in the workflow")


class REQUIRED_CONTEXT(BaseModel):
    source_node: str = Field(..., description="Which node created this task")
    triggering_task_id: str | int | float | None = Field(default=None,
                                                         description="The ID of the parent task that spawned this one")
    creation_timestamp: str = Field(default_factory=lambda: get_formatted_timestamp())
    pre_execution_context: dict | None = Field(default=None,
                                               description="Any context relevant before executing the task")


class EXECUTION_CONTEXT(BaseModel):
    tool_name: str = Field(..., description="The specific tool required to execute this task")
    parameters: dict = Field(..., description="Parameters required for the tool execution")
    result: str | None = Field(default=None, description="The output or result from the last execution attempt")
    analysis: str | None = Field(default=None, description="Any analysis derived from the tool execution result")
    goal_achieved: bool = Field(default=False, description="Indicates if the task's specific goal was met")


class FAILURE_CONTEXT_STRATEGY(BaseModel):
    recovery_strategy: Literal["PARAMETER_REPAIR", "ALTERNATIVE_TOOL", "TASK_DECOMPOSITION", "NO_STRATEGY", "SKIP"] = Field(
        default="PARAMETER_REPAIR",
        description="The recovery strategy attempted"
    )
    reasoning: str = Field(..., description="Reasoning behind choosing this strategy")
    confidence_level: Literal["HIGH", "MEDIUM", "LOW"] = Field(default="LOW", description="Confidence in this strategy")
    estimated_success_probability: int = Field(default=0,
                                               description="Estimated probability (0-100) of success with this strategy",
                                               ge=0, le=100)
    next_steps: str | None = Field(default=None, description="Recommended next steps after this strategy")
    outcome: Literal["FAILURE", "APPLIED", "NOT_APPLIED"] = Field(default="NOT_APPLIED",
                                                                  description="Outcome after attempting this strategy")
    timestamp: str = Field(default_factory=lambda: get_formatted_timestamp(),
                                description="Timestamp when this strategy was attempted")

    details: dict[str, Any] | None = Field(default={},
                                           description="contains Additional details about the strategy attempt")


class FAILURE_CONTEXT(BaseModel):
    error_message: str = Field(..., description="Detailed error message from the last failure")
    fail_count: int = Field(description="number of times the task has failed", default=1, ge=1)
    last_failure_timestamp: str | None = Field(default=None, description="Timestamp of the last failure")
    stack_trace: str | None = Field(default=None, description="Stack trace or debug info from the failure")
    recovery_actions: dict[str, Any] | None = Field(default=None, description="Any recovery actions taken")
    error_type: str | None = Field(default=None, description="Type or category of the error")
    failed_parameters: dict[str, Any] | None = Field(default=None,
                                                     description="The parameters that caused the failure")  # <-- NEW FIELD
    strategy_history: list[FAILURE_CONTEXT_STRATEGY] | None = Field(default_factory=list,
                                                                    description="History of all recovery strategies attempted with outcomes")  # <-- NEW FIELD
    # Cooldown timestamp to avoid tight retry loops
    next_attempt_timestamp: str | None = Field(default=None, description="Earliest time allowed for next retry")
    recovery_attempts: int = Field(default=0, ge=0, description="Times the error fallback node has handled this task")


class subAgent_CONTEXT(BaseModel):
    subAgent_id: str | int | float | None = Field(default=None, description="Unique identifier for the sub-agent")
    subAgent_persona: str | None = Field(default=None, description="The persona or role assigned to the sub-agent")
    subAgent_status: Literal["idle", "active", "completed", "failed"] | None = Field(default=None,
                                                                                     description="Current status")
    subAgent_tasks: TaskListType | None = Field(default=None, description="List of tasks assigned to the sub-agent")
    parent_task_id: str | int | float | None = Field(default=None,
                                                     description="The ID of the parent task that spawned this sub-agent")
    creation_timestamp: str | None = Field(default=None,
                                                description="Timestamp of when the sub-agent was created")
    completion_timestamp: str | None = Field(default=None, description="Timestamp of completion")
    notes: str | None = Field(default=None, description="Additional notes about the sub-agent's operations")
    result: str | None = Field(default=None, description="Overall result from the sub-agent's operations")


class TASK(BaseModel):
    task_id: str = Field(description="Unique identifier for the task", default_factory=lambda: str(uuid.uuid4()))
    description: str = Field(..., description="A clear description of what the task is supposed to achieve")
    tool_name: str = Field(..., description="The specific tool required to execute this task")
    status: Literal["pending", "in_progress", "completed", "failed", "skip"] = Field(description="current status",
                                                                             default="pending")
    max_retries: int = Field(description="maximum number of retries allowed", default=1, ge=0)
    depth: int = Field(description="recursion depth of the task", default=0,
                       ge=0)  # for tracking how deep we are in sub-agent spawning and preventing infinite loops
    requires_high_fidelity_context: bool = Field(
        description="If true, the raw results of parent/sibling tasks should be prioritized in the context.",
        default=False
    )

    required_context: REQUIRED_CONTEXT = Field(..., description="Context required before executing the task")
    execution_context: EXECUTION_CONTEXT | None = Field(default=None, description="Context for executing the task")
    failure_context: FAILURE_CONTEXT | None = Field(default=None, description="Context for any failures")
    subAgent_context: subAgent_CONTEXT | None = Field(default=None, description="Context for sub-agents")
    # Optional earliest next attempt timestamp (for exponential backoff / cooldown)
    next_attempt_at: str | None = Field(default=None,
                                             description="Earliest timestamp when this task can be attempted again")


class AgentState(BaseModel):
    TASKS: list[TASK]
    CURRENT_TASK_ID: int | float = Field(..., description="current task id being executed")
    original_goal: str = Field(..., description="The original high-level goal provided by the user")
    persona: str | None = Field(default=None, description="The persona for the next action")


class WorkflowStateModel(BaseModel):
    tasks: list[TASK]
    current_task_id: str | int | float
    executed_nodes: list[str]
    original_goal: str
    persona: str | None = None
    workflow_status: str | None = None
    final_response: Any | None = None


# Resolve forward references after all models are defined
subAgent_CONTEXT.model_rebuild()
TASK.model_rebuild()


# ================================================================================================================ 
# CORE DESIGN PHILOSOPHY & ROUTING ARCHITECTURE DOCUMENTATION 
# ================================================================================================================ 

# The hierarchical agent system implements a sophisticated state machine that can handle: 
# 1. COMPLEX TASK DECOMPOSITION: Breaking down abstract goals into executable atomic tasks 
# 2. DYNAMIC SUB-AGENT SPAWNING: Creating specialized agents for complex sub-problems 
# 3. ERROR RECOVERY WITH SPAWNING: Intelligent failure handling through sub-agent creation 
# 4. TOOL PRE-FILTERING: 90% token reduction while maintaining 100% functionality 

# The main architectural challenge solved here is maintaining state consistency across: 
# - Parent tasks that spawn sub-agents 
# - Sub-task execution and completion tracking 
# - Error recovery and fallback scenarios 
# - Tool selection and parameter generation 

# ** ROUTING LOGIC TEMPLATE - WHEN TO ROUTE TO WHICH NODE ** 
# This is the core state machine that determines workflow progression 

#################################################################################################### 
# 🚀 ROUTE TO: initial_planner 
# WHEN: WORKFLOW_STATUS is 'STARTED' only 
# PURPOSE: High-level goal decomposition into executable tasks 
# RESPONSIBILITY: Parse user goal and create initial task breakdown using tool pre-filtering 
#################################################################################################### 

#################################################################################################### 
# 🏁 ROUTE TO: END node 
# WHEN: ALL task statuses are 'completed' OR 'failed' 
# PURPOSE: Workflow termination when no more work remains 
# LOGIC: task1.status == 'completed' AND task2.status == 'completed' AND ... taskN.status == 'completed' 
#################################################################################################### 

#################################################################################################### 
# ⚙️ ROUTE TO: task_executor 
# WHEN: 
#   - persona is 'AGENT_PERFORM_TASK' 
#   - CURRENT_TASK.status is 'pending' OR 'in_progress' 
#   - CURRENT_TASK.result is empty OR None 
# PURPOSE: Execute atomic tasks OR trigger spawning for complex tasks 
# KEY FEATURE: Complexity analysis determines direct execution vs. sub-agent spawning 
#################################################################################################### 

#################################################################################################### 
# 🔧 ROUTE TO: error_fallback 
# WHEN: 
#   - persona is 'AGENT_PERFORM_ERROR_FALLBACK' 
#   - CURRENT_TASK.status is 'in_progress' OR 'pending' 
#   - CURRENT_TASK.result is empty OR None 
#   - CURRENT_TASK has failed at least 2 times (tracked via fail_count) 
# PURPOSE: Advanced error recovery including potential sub-agent spawning for complex failures 
#################################################################################################### 

#################################################################################################### 
# 📝 ROUTE TO: task_updater (IMPLICIT - handled by task completion logic) 
# WHEN: 
#   - CURRENT_TASK.status is 'completed' 
#   - CURRENT_TASK.result is not empty AND not None 
#   - persona is 'AGENT_PERFORM_TASK' OR 'AGENT_PERFORM_ERROR_FALLBACK' 
# PURPOSE: Update task state and prepare for next task selection 
#################################################################################################### 

#################################################################################################### 
# 📋 ROUTE TO: task_planner 
# WHEN: 
#   - CURRENT_TASK.status is 'completed' 
#   - CURRENT_TASK.result is not empty AND not None 
#   - persona is 'AGENT_PERFORM_TASK' OR 'AGENT_PERFORM_ERROR_FALLBACK' 
#   - MORE tasks exist in TASKS list with status 'pending' 
# PURPOSE: Select next pending task and manage parent-child task relationships 
# SPECIAL LOGIC: Handles spawned sub-task completion and parent task status updates 
#################################################################################################### 

#################################################################################################### 
# 🎯 ROUTE TO: classifier 
# WHEN: 
#   - CURRENT_TASK.status is 'completed' 
#   - CURRENT_TASK.result is not empty AND not None 
#   - persona is 'AGENT_PERFORM_TASK' OR 'AGENT_PERFORM_ERROR_FALLBACK' 
#   - NO MORE tasks in TASKS list with status 'pending' 
#   - WORKFLOW_STATUS is 'RUNNING' OR 'RESTART' 
#   - EXECUTED_NODES does NOT contain 'subAGENT_finalizer' 
# PURPOSE: Determine next action when no pending tasks remain 
#################################################################################################### 

#################################################################################################### 
# 🎉 ROUTE TO: finalizer 
# WHEN: 
#   - WORKFLOW_STATUS is 'COMPLETED' OR 'FAILED' 
#   - EXECUTED_NODES does NOT contain 'subAGENT_finalizer' 
#   - ALL tasks in TASKS list have status 'completed' OR 'failed' 
#   - CURRENT_TASK.status is 'completed' 
#   - CURRENT_TASK.result is not empty AND not None 
# PURPOSE: Generate final consolidated response from all task results 
#################################################################################################### 

# ================================================================================================================ 
# SPAWNING SYSTEM INTEGRATION NOTES 
# ================================================================================================================ 

# The spawning system (Spawn_subAgent class) integrates seamlessly with this routing logic: 
# 
# 1. COMPLEXITY ANALYSIS: task_executor analyzes if a task needs decomposition 
# 2. SPAWNING DECISION: Based on tool schema and task description complexity 
# 3. SUB-TASK INJECTION: New tasks are injected into the workflow with float IDs (e.g., 1.1, 1.2) 
# 4. PARENT TRACKING: Parent tasks are marked 'in_progress' while sub-tasks execute 
# 5. COMPLETION LOGIC: Parent tasks are marked complete only when ALL sub-tasks finish 
# 6. ERROR SPAWNING: Failed tasks can spawn recovery sub-agents for specialized handling 
# 
# This creates a true hierarchical execution model where complex problems are recursively 
# broken down into manageable atomic operations while maintaining full traceability. 

# ================================================================================================================ 


class AgentCoreHelpers:
    """
    HELPER FUNCTION FOR AGENT AND SUB-AGENT CLASSES
    Common utility functions for agent and sub-agent classes.
    todo : the all function those are not nodes should be moved here
    """
    synthesis_tool_description = "• perform_synthesis: A virtual tool to review the results of previous tasks and synthesize them into a single, comprehensive summary or answer. Use this when you need to combine information from multiple sources before taking a final action, like writing a file. Parameters: {'instructions': 'A clear, natural language instruction on what to synthesize and how to format it.'}"

    @classmethod
    def perform_internal_synthesis(cls, current_task: TASK, full_history: list[TASK]) -> tuple[bool, str]:
        """
        Executes the virtual 'perform_synthesis' tool by calling an LLM.
        """
        debug_info("Internal Synthesis", f"Performing synthesis for task: {current_task.description}",
                   metadata={"function_name": "_perform_internal_synthesis", "task_id": current_task.task_id})

        # Extract the raw results from the history
        context_from_history = "\n\n".join([
            f"Result from Task {t.task_id} ({t.tool_name}):\n{t.execution_context.result}"
            for t in full_history
            if t.execution_context and t.execution_context.result
        ])

        if not context_from_history:
            return False, "Synthesis failed: No previous results found to synthesize."

        # Get the specific instructions from the current task's parameters
        synthesis_instructions = current_task.execution_context.parameters.get("instructions",
                                                                               "Summarize the provided context.")

        # This prompt needs to be added to hierarchical_agent_prompts.py
        prompt_generator = HierarchicalAgentPrompt()
        system_prompt, human_prompt = prompt_generator.generate_synthesis_execution_prompt(
            synthesis_instructions,
            context_from_history
        )

        try:
            model = ModelManager()
            response = model.invoke([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": human_prompt},
            ])
            synthesis_result = response.content
            return True, synthesis_result
        except Exception as e:
            error_msg = f"Internal synthesis LLM call failed: {e}"
            debug_error("Internal Synthesis", error_msg, metadata={"exception": str(e)})
            return False, error_msg

    # ----------- these are tool list helpers ----------- 
    @classmethod
    def get_safe_tools_list(cls):
        """Get a safe list of tools, raising an error if no tools are available."""
        # todo virtual tools could add up here
        tools = ToolAssign.get_tools_list()
        if not tools:
            raise RuntimeError("No tools available - system cannot function")
        return tools

    @classmethod
    def get_detailed_tool_context(cls, recommended_tools: list[str]) -> str:
        """Get detailed context (name, description, schema) for only the recommended tools.
        Uses the same approach as main_orchestrator.py
        """
        try:
            all_tools = AgentCoreHelpers.get_safe_tools_list()
            tool_context = []

            # --- INJECT VIRTUAL TOOL ---
            if "perform_synthesis" in recommended_tools:
                tool_context.append(cls.synthesis_tool_description)
            # --- END INJECTION ---

            for tool in all_tools:
                if tool.name in recommended_tools:
                    # Get name and description
                    name = getattr(tool, "name", "N/A")
                    desc = getattr(tool, "description", "No description available")

                    # Get arguments using the same function as main_orchestrator.py
                    args_schema = get_tool_argument_schema(tool)

                    tool_context.append(f"• {name}: {desc}\n  Parameters: {args_schema}")

            return "\n\n".join(tool_context)

        except Exception as e:
            # print_log_message(f"Failed to get detailed tool context: {e}", "Tool Context")
            debug_warning("Tool Context", f"Failed to get detailed tool context: {e}", metadata={
                "function_name": "get_detailed_tool_context",
                "exception": str(e),
            })
            return "Tool context unavailable"

    @classmethod
    def recommend_tools_for_task(cls, task_description: str, max_tools: int = 10, parent_context: str | None = None) -> \
            list[str]:
        """Use LLM to recommend 5-10 most relevant tools for a specific task.
        This is the pre-filtering step that makes the system much more efficient.
        """
        try:
            # Get all available tool names
            all_tools = AgentCoreHelpers.get_safe_tools_list()
            all_tool_names = [tool.name for tool in all_tools]

            # Create a concise tool list for the recommender, including the virtual tool
            tool_list_for_prompt = [f"• {tool.name}" for tool in all_tools]
            tool_list_for_prompt.append("perform_synthesis")  # Make the virtual tool visible
            tool_list = "\n".join(tool_list_for_prompt)

            recommend_prompt = f'''
                TOOL RECOMMENDATION SYSTEM

                Task: "{task_description}"

                Available Tools:
                {tool_list}
                
                parent_context:
                {parent_context if parent_context else "No additional context provided"}

                Select up to {max_tools} tools from the list above that are most relevant for this task.
                Consider broad categories such as: file operations (e.g., list/read/write), web research, analysis, shell/OS commands, and memory/graph operations and others.
                Do not invent tool names — return only names that appear in the Available Tools section and match them exactly.

                Respond with ONLY a JSON array of tool names, for example:
                ["tool1", "tool2", "tool3"]
                '''

            model = ModelManager()
            response = model.invoke([
                {"role": "system",
                 "content": "You are a tool recommendation expert. Select the most relevant tools for the given task."},
                {"role": "user", "content": recommend_prompt},
            ])

            recommended_tools = ModelManager.convert_to_json(response.content)

            # Validate and filter
            if isinstance(recommended_tools, list):
                # Also consider the virtual tool as valid
                valid_tools = [tool for tool in recommended_tools if
                               tool in all_tool_names or tool == "perform_synthesis"]
                return valid_tools[:max_tools]
            # Fallback to common tools
            return ["list_directory", "google_search", "write_file"]

        except Exception as e:
            # Use module-level debug_warning (fallback defined earlier) instead of re-importing
            debug_warning("Tool Recommender", f"Tool recommendation failed: {e}", metadata={
                'function name': "recommend_tools_for_task",
                "task_description": task_description,
                "max_tools": max_tools,
            })
            # Safe fallback
            return ["list_directory", "google_search", "write_file", "perform_synthesis"]

    # ^^^^^^^^^^^^^^ these are tool list helpers ^^^^^^^^^^^^^^^^^^
    @staticmethod
    def evaluate_skip_cascade(current_task: TASK, skipped_tasks: list[TASK]) -> tuple[bool, str]:
        """
        Evaluate if the current task should be skipped based on previous skips.

        Uses RULE-BASED dependency detection (NO AI calls needed):
        1. PARENT-CHILD: Sub-tasks depend on parent tasks (via float IDs)
        2. SEQUENTIAL: Task N depends on Task N-1 if it references N-1's output
        3. RESOURCE: Task B depends on Task A if it needs A's file/data

        Returns:
            tuple[bool, str]: (should_skip, reason)
        """
        # Early exit: no skipped tasks means no cascade possible
        if len(skipped_tasks) == 0:
            return False, "No skipped tasks to evaluate for cascade skip."

        # Extract current task info for analysis
        current_id = current_task.task_id
        current_desc = current_task.description.lower() if current_task.description else ""
        current_params = current_task.execution_context.parameters if current_task.execution_context else {}

        # DEPENDENCY TYPE 1: PARENT-CHILD RELATIONSHIP (via float IDs)
        # Example: Task 1.1, 1.2 are children of Task 1
        # If parent (1) is skipped, children (1.1, 1.2) should also skip
        if isinstance(current_id, str) and '.' in current_id:
            # Extract parent ID from current task (e.g., "1" from "1.1" or "1.1" from "1.1.2")
            parent_id = current_id.rsplit('.', 1)[0]  # Get parent by removing last segment

            # Check if parent task is in skipped list
            for skipped in skipped_tasks:
                skipped_id_str = str(skipped.task_id)
                if skipped_id_str == parent_id:
                    return True, f"Parent task {parent_id} was skipped. This sub-task cannot proceed without parent."

        # DEPENDENCY TYPE 2: SEQUENTIAL DEPENDENCY
        # If current task's description mentions a previous skipped task's tool or references "previous task"
        # Example: Task 2 says "Use search results from previous task" → depends on Task 1
        for skipped in skipped_tasks:
            skipped_tool = skipped.tool_name.lower() if skipped.tool_name else ""

            # Check if current task description explicitly mentions the skipped task's tool
            # e.g., "write the search results" when google_search was skipped
            if skipped_tool and skipped_tool in current_desc:
                return True, f"Task references '{skipped_tool}' which was skipped (Task {skipped.task_id})."

            # Check for explicit sequential references like "previous task", "from earlier", etc.
            sequential_keywords = ["previous task", "earlier task", "from task", "using the"]
            if any(keyword in current_desc for keyword in sequential_keywords):
                # Conservative: only skip if the skipped task was IMMEDIATELY before current task
                try:
                    current_id_num = float(str(current_id).split('-')[0]) if isinstance(current_id, str) else float(current_id)
                    skipped_id_num = float(str(skipped.task_id).split('-')[0]) if isinstance(skipped.task_id, str) else float(skipped.task_id)

                    # If skipped task is right before current (e.g., Task 1 skipped, Task 2 current)
                    if abs(current_id_num - skipped_id_num) <= 1.0:
                        return True, f"Task has sequential dependency on skipped Task {skipped.task_id} (detected via context keywords)."
                except (ValueError, TypeError):
                    pass  # Skip numeric comparison if IDs aren't numeric

        # DEPENDENCY TYPE 3: RESOURCE DEPENDENCY
        # If current task's parameters reference a file/resource that should have been created by skipped task
        # Example: Task A creates "report.txt", Task B needs "report.txt" → B depends on A
        if isinstance(current_params, dict):
            # Check if current task parameters contain file paths
            param_values = [str(v).lower() for v in current_params.values() if v]

            for skipped in skipped_tasks:
                # Check if skipped task was supposed to create/modify a file
                skipped_params = skipped.execution_context.parameters if skipped.execution_context else {}
                if isinstance(skipped_params, dict):
                    skipped_values = [str(v).lower() for v in skipped_params.values() if v]

                    # Look for common file references between current and skipped task parameters
                    for current_val in param_values:
                        for skipped_val in skipped_values:
                            # If both tasks reference the same file path
                            if len(current_val) > 5 and len(skipped_val) > 5:  # Ignore short strings
                                if current_val in skipped_val or skipped_val in current_val:
                                    # Check if skipped task was a write operation (likely creates the file)
                                    if skipped.tool_name in ["mcp_filesystem_write_file", "write_file", "create_file"]:
                                        return True, f"Task requires file resource from skipped Task {skipped.task_id} (file: {skipped_val[:50]})."

        # DEFAULT: No clear dependency detected - DO NOT skip (conservative approach)
        # Better to attempt execution and fail explicitly than skip incorrectly
        return False, "No clear dependency on skipped tasks detected."



    class ErrorFallbackHelpers:
        """Enhanced helper functions for error fallback node with LLM-driven decision making."""

        @staticmethod
        def attempt_parameter_repair(task: TASK, state: "WorkflowStateModel") -> tuple[bool, dict]:
            """Use LLM to intelligently repair the parameters of a failed task."""
            # Check if we have enough context to attempt repair
            if not task.failure_context or not task.failure_context.failed_parameters:
                debug_warning("Parameter Repair",
                              f"Task {task.task_id} has no failure context or failed parameters. Cannot attempt repair.",
                              metadata={"function_name": "attempt_parameter_repair", "task_id": task.task_id})
                return False, {}

            # Get additional context that's now available
            tool_schema = AgentGraphCore.get_tool_schema(task.tool_name)
            error_message = task.failure_context.error_message
            error_type = task.failure_context.error_type or ""
            fail_count = task.failure_context.fail_count
            failed_params = task.failure_context.failed_parameters

            # Get context from goal validator if available
            validator_feedback = None
            if error_type == "GoalValidationFailure":
                validator_feedback = error_message

            debug_info("Parameter Repair",
                       f"Attempting parameter repair for task {task.task_id} with {fail_count} failures",
                       metadata={"function_name": "attempt_parameter_repair", "task_id": task.task_id,
                                 "error_type": error_type, "fail_count": fail_count})

            # Use LLM to analyze the failure and suggest parameter repairs
            prompt_generator = HierarchicalAgentPrompt()
            system_prompt, human_prompt = prompt_generator.generate_enhanced_parameter_repair_prompt(
                task, state, tool_schema
            )

            try:
                model = ModelManager()
                response = model.invoke([
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": human_prompt},
                ])
                repair_result = ModelManager.convert_to_json(response.content)

                # Extract repaired parameters from LLM response
                repaired_params = repair_result.get("repaired_parameters", {})

                # Validate that the repaired parameters meet the schema
                is_valid, error_msg = AgentCoreHelpers.ParameterGeneratorHelpers.validate_params(
                    task.tool_name, repaired_params
                )

                if is_valid:
                    debug_info("Parameter Repair", f"Successfully repaired parameters for task {task.task_id}",
                               metadata={"function_name": "attempt_parameter_repair", "task_id": task.task_id,
                                         "repaired_params": repaired_params})
                    return True, repaired_params
                else:
                    debug_warning("Parameter Repair", f"LLM-suggested parameters failed validation: {error_msg}",
                                  metadata={"function_name": "attempt_parameter_repair", "task_id": task.task_id,
                                            "validation_error": error_msg})
                    return False, {}

            except Exception as e:
                debug_error("Parameter Repair", f"Failed to repair parameters with LLM: {e}",
                            metadata={"function_name": "attempt_parameter_repair", "task_id": task.task_id,
                                      "exception": str(e)})
                # Fallback to basic repair
                required_keys = tool_schema.get("required", [])
                missing_keys = [key for key in required_keys if key not in failed_params]

                if missing_keys:
                    debug_warning("Parameter Repair",
                                  f"Task {task.task_id} is missing required parameters: {missing_keys}. Attempting to add default values.",
                                  metadata={"function_name": "attempt_parameter_repair", "task_id": task.task_id})
                    # Simple repair: Add empty strings for missing keys
                    repaired_params = failed_params.copy()
                    for key in missing_keys:
                        repaired_params[key] = ""
                    return True, repaired_params

                return False, {}

        @staticmethod
        def convert_decision_task(whole_context:list[str], available_tools_str:str, parent_task:TASK) -> list[TASK] | None:
            """
            this convert that whole decision, error recovery strategy, parent failure context, original goal and create return lists of tasks
            :return: list of tasks
            """

            hierarchy_prompt = HierarchicalAgentPrompt()
            system_prompt, human_prompt = hierarchy_prompt.generate_plan_to_tasks_prompt(whole_context, available_tools_str)
            try:
                model = ModelManager()
                response = model.invoke([
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": human_prompt},
                ])
                task_list = ModelManager.convert_to_json(response.content)
                if isinstance(task_list, list):
                    tasks = []
                    for idx, task_dict in enumerate(task_list):
                        tasks.append(
                            TASK(
                                task_id=str(f"{parent_task.task_id}_{idx}"),
                                description=task_dict.get("description", "No description provided"),
                                tool_name=task_dict.get("tool_name", "unknown_tool"),
                                status="pending",
                                required_context=REQUIRED_CONTEXT(source_node="error_fallback", triggering_task_id=parent_task.task_id)
                            )
                        )
                    return tasks if tasks else None
                else:
                    debug_warning("Task Conversion", "LLM response is not a list of tasks.",
                                  metadata={"function_name": "convert_decision_task",
                                            "response_content": response.content})
                    return None
            except Exception as e:
                debug_error("Task Conversion", f"Failed to convert decision to tasks with LLM: {e}",
                            metadata={"function_name": "convert_decision_task", "exception": str(e)})
                return None


        @staticmethod
        def find_alternative_tool(task: TASK, state: "WorkflowStateModel") -> str | None:
            """Use LLM to intelligently find a safer, alternative tool to accomplish the task's goal."""
            # Check if we have enough context to attempt alternative tool selection
            if not task.failure_context or not task.failure_context.error_message:
                debug_warning("Alternative Tool",
                              f"Task {task.task_id} has no failure context or error message. Cannot find alternative tool.",
                              metadata={"function_name": "find_alternative_tool", "task_id": task.task_id})
                return None

            # Get error details
            error_message = task.failure_context.error_message
            error_type = task.failure_context.error_type or ""
            fail_count = task.failure_context.fail_count
            failed_params = task.failure_context.failed_parameters or {}

            # Get context from goal validator if available
            validator_feedback = None
            if error_type == "GoalValidationFailure":
                validator_feedback = error_message

            debug_info("Alternative Tool",
                       f"Finding alternative tool for task {task.task_id} with {fail_count} failures",
                       metadata={"function_name": "find_alternative_tool", "task_id": task.task_id,
                                 "error_type": error_type, "current_tool": task.tool_name})

            # Get all available tools for more intelligent selection
            all_tools = AgentCoreHelpers.get_safe_tools_list()
            available_tools_info = "\n".join([f"• {tool.name}: {tool.description}" for tool in all_tools])

            # Use LLM to analyze the failure and suggest an alternative tool
            prompt_generator = HierarchicalAgentPrompt()
            system_prompt, human_prompt = prompt_generator.generate_enhanced_alternative_tool_prompt(
                task, state, all_tools
            )

            try:
                model = ModelManager()
                response = model.invoke([
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": human_prompt},
                ])
                alternative_result = ModelManager.convert_to_json(response.content)

                # Extract alternative tool from LLM response
                alternative_tool = alternative_result.get("alternative_tool")

                # Validate that the alternative tool exists
                if alternative_tool and alternative_tool in [tool.name for tool in all_tools]:
                    debug_info("Alternative Tool",
                               f"Selected alternative tool '{alternative_tool}' for task {task.task_id}",
                               metadata={"function name": "find_alternative_tool", "task_id": task.task_id,
                                         "alternative_tool": alternative_tool,
                                         "reasoning": alternative_result.get("reasoning", "No reasoning provided")})
                    return alternative_tool
                else:
                    debug_warning("Alternative Tool",
                                  f"LLM-suggested tool '{alternative_tool}' not found in available tools",
                                  metadata={"function name": "find_alternative_tool", "task_id": task.task_id,
                                            "suggested_tool": alternative_tool})
                    return None

            except Exception as e:
                debug_error("Alternative Tool", f"Failed to find alternative tool with LLM: {e}",
                            metadata={"function name": "find_alternative_tool", "task_id": task.task_id,
                                      "exception": str(e)})
                # Fallback to basic pattern matching
                error_message_lower = error_message.lower()
                if "command not found" in error_message_lower and task.tool_name == "run_shell_command":
                    debug_info("Alternative Tool Finder", f"Suggesting google_search for 'command not found' error.",
                               metadata={"function name": "find_alternative_tool", "task_id": task.task_id})
                    return "google_search"

                if "summarize" in task.description.lower() and task.tool_name != "perform_synthesis":
                    return "perform_synthesis"

                return None

    class EnhancedErrorFallbackHelpers:
        """Enhanced error fallback helpers with LLM-driven strategy selection."""

        @staticmethod
        def decide_recovery_strategy(task: "TASK", state: "WorkflowStateModel") -> dict:
            """Use LLM to intelligently decide the best recovery strategy based on comprehensive context analysis."""

            # Validate we have enough context to make a decision
            if not task.failure_context:
                debug_warning("Strategy Decision",
                              f"Task {getattr(task, 'task_id', 'N/A')} has no failure context. Cannot decide strategy.",
                              metadata={"function name": "decide_recovery_strategy",
                                        "task_id": getattr(task, 'task_id', 'N/A')})
                # Return a safe default strategy
                return {
                    "recovery_strategy": "PARAMETER_REPAIR",
                    "reasoning": "No failure context available, starting with parameter repair as safest option.",
                    "confidence_level": "LOW",
                    "estimated_success_probability": 30,
                    "next_steps": "Attempt to repair parameters with basic logic."
                }

            # Get all relevant context
            error_message = task.failure_context.error_message
            error_type = task.failure_context.error_type or ""
            fail_count = task.failure_context.fail_count
            failed_parameters = task.failure_context.failed_parameters or {}

            debug_info("Strategy Decision",
                       f"Deciding recovery strategy for task {getattr(task, 'task_id', 'N/A')} with {fail_count} failures",
                       metadata={"function name": "decide_recovery_strategy",
                                 "task_id": getattr(task, 'task_id', 'N/A'), "error_type": error_type,
                                 "fail_count": fail_count})

            # Get tool schema
            tool_schema = AgentGraphCore.get_tool_schema(task.tool_name) if hasattr(AgentGraphCore,
                                                                                    'get_tool_schema') else {}

            # Get completed task history for context
            completed_tasks = [t for t in state.tasks if
                               t.status == "completed" and hasattr(t, 'execution_context') and t.execution_context]
            recent_completed_tasks_info = "\n".join([
                f"• Task {getattr(t, 'task_id', 'N/A')}: {getattr(t, 'description', 'N/A')} ({getattr(t, 'tool_name', 'N/A')}) -> {getattr(t.execution_context, 'analysis', 'No analysis') or 'No analysis'}"
                for t in completed_tasks[-3:]  # Last 3 completed tasks
            ]) or "No recent completed tasks"

            # Get failed tasks with validator feedback
            failed_tasks_with_feedback = [t for t in state.tasks
                                          if getattr(t, 'status', '') == "failed"
                                          and hasattr(t, 'failure_context') and t.failure_context
                                          and getattr(t.failure_context, 'error_type', '') == "GoalValidationFailure"]

            failed_tasks_info = "\n".join([
                f"• Task {getattr(t, 'task_id', 'N/A')}: {getattr(t, 'description', 'N/A')} -> Validator Feedback: {getattr(t.failure_context, 'error_message', 'N/A')}"
                for t in failed_tasks_with_feedback  # Last 2 failed tasks with feedback
            ]) or "No recent failed tasks with validator feedback"

            # Get all available tools
            all_tools = AgentCoreHelpers.get_safe_tools_list() if hasattr(AgentCoreHelpers,
                                                                          'get_safe_tools_list') else []
            available_tools_info = "\n".join([
                f"• {getattr(tool, 'name', 'N/A')}: {getattr(tool, 'description', 'N/A')}"
                for tool in all_tools
            ])
            strategy_history = '\n'.join(
                [f"• Attempt {i + 1}: {s.recovery_strategy} - reasoning: {s.reasoning} - outcome: {s.outcome} \n\t " for
                 i, s
                 in enumerate(task.failure_context.strategy_history)]) or "No previous recovery attempts."

            # Use LLM to analyze the failure and suggest the best recovery strategy
            prompt_generator = HierarchicalAgentPrompt()
            system_prompt, human_prompt = prompt_generator.generate_recovery_strategy_prompt(
                task_description=task.description,
                tool_name=task.tool_name,
                error_message=error_message,
                error_type=error_type,
                fail_count=fail_count,
                failed_parameters=failed_parameters,
                tool_schema=tool_schema,
                original_goal=state.original_goal,
                completed_tasks_context=recent_completed_tasks_info,
                failed_tasks_context=failed_tasks_info,
                available_tools=available_tools_info,
                strategy_hist=strategy_history
            )

            try:
                model = ModelManager()
                response = model.invoke([
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": human_prompt},
                ])
                strategy_result = ModelManager.convert_to_json(response.content)

                # Validate that we got a valid strategy
                valid_strategies = ["PARAMETER_REPAIR", "ALTERNATIVE_TOOL", "TASK_DECOMPOSITION", "LLM_RECOVERY", "SKIP"]
                recovery_strategy = strategy_result.get("recovery_strategy", "PARAMETER_REPAIR") if isinstance(
                    strategy_result, dict) else "PARAMETER_REPAIR"

                if not isinstance(strategy_result, dict):
                    # Ensure a mutable dict for downstream updates
                    strategy_result = {}

                if recovery_strategy not in valid_strategies:
                    debug_warning("Strategy Decision",
                                  f"LLM suggested invalid strategy '{recovery_strategy}'. Falling back to PARAMETER_REPAIR.",
                                  metadata={"function name": "decide_recovery_strategy",
                                            "task_id": getattr(task, 'task_id', 'N/A'),
                                            "suggested_strategy": recovery_strategy})
                    recovery_strategy = "PARAMETER_REPAIR"

                # FIX 3: Enhanced discovery logic - if LLM suggests multiple tools or discovery steps, force TASK_DECOMPOSITION
                next_steps = strategy_result.get("next_steps", "")
                if next_steps and isinstance(next_steps, str):
                    # Count discovery-related tool mentions in next_steps
                    discovery_tool_mentions = 0
                    discovery_keywords = ["list_allowed_directories", "search_files", "list_directory", "find",
                                          "discover", "explore", "search", "investigate", "verify", "check", "examine",
                                          "analyze"]
                    for keyword in discovery_keywords:
                        if keyword.lower() in next_steps.lower():
                            discovery_tool_mentions += 1

                    # # this is causing un intentional issues If LLM mentions multiple discovery tools/steps, force decomposition
                    # if discovery_tool_mentions >= 5:
                    #     debug_info("Strategy Decision",
                    #                f"LLM suggested multi-step discovery approach, forcing TASK_DECOMPOSITION for task {getattr(task, 'task_id', 'N/A')}",
                    #                metadata={"original_strategy": str(recovery_strategy), "next_steps": str(next_steps),
                    #                          "discovery_mentions": str(discovery_tool_mentions)})
                    #     recovery_strategy = "TASK_DECOMPOSITION"
                    #     strategy_result["recovery_strategy"] = "TASK_DECOMPOSITION"
                    #     strategy_result[
                    #         "reasoning"] = f"Original: {strategy_result.get('reasoning', '')} | ENHANCED: Multi-step discovery approach detected, forcing decomposition to implement: {next_steps}"

                debug_info("Strategy Decision",
                           f"Selected strategy '{recovery_strategy}' for task {getattr(task, 'task_id', 'N/A')}",
                           metadata={"function name": "decide_recovery_strategy",
                                     "task_id": getattr(task, 'task_id', 'N/A'), "recovery_strategy": recovery_strategy,
                                     "confidence_level": strategy_result.get("confidence_level", "UNKNOWN"),
                                     "estimated_success_probability": strategy_result.get(
                                         "estimated_success_probability", 0),
                                     "reasoning": strategy_result.get("reasoning", "No reasoning provided")})

                # The caller reads the strategy from this dict, so store the validated value
                strategy_result["recovery_strategy"] = recovery_strategy
                return strategy_result

            except Exception as e:
                debug_error("Strategy Decision", f"Failed to decide recovery strategy with LLM: {e}",
                            metadata={"function name": "decide_recovery_strategy",
                                      "task_id": getattr(task, 'task_id', 'N/A'), "exception": str(e)})
                # Fallback to rule-based decision making
                return AgentCoreHelpers.EnhancedErrorFallbackHelpers._fallback_strategy_selection(task, state)

        @staticmethod
        def _fallback_strategy_selection(task: "TASK", state: "WorkflowStateModel") -> dict:
            """Fallback rule-based strategy selection when LLM fails."""

            if not task.failure_context:
                return {
                    "recovery_strategy": "PARAMETER_REPAIR",
                    "reasoning": "No failure context, starting with parameter repair.",
                    "confidence_level": "LOW",
                    "estimated_success_probability": 30,
                    "next_steps": "Attempt basic parameter repair."
                }

            error_type = task.failure_context.error_type or ""
            fail_count = task.failure_context.fail_count
            error_message = task.failure_context.error_message.lower()

            # Rule-based decision-making
            if fail_count > 2:
                # High fail count, time for decomposition
                return {
                    "recovery_strategy": "TASK_DECOMPOSITION",
                    "reasoning": f"Task has failed {fail_count} times, suggesting inherent complexity. Decomposition recommended.",
                    "confidence_level": "HIGH",
                    "estimated_success_probability": 70,
                    "next_steps": "Spawn sub-agent to break task into smaller steps."
                }
            elif "command not found" in error_message or "file not found" in error_message:
                # Common tool execution errors
                return {
                    "recovery_strategy": "ALTERNATIVE_TOOL",
                    "reasoning": "Tool execution error (command/file not found), suggesting alternative tool needed.",
                    "confidence_level": "MEDIUM",
                    "estimated_success_probability": 60,
                    "next_steps": "Find and switch to alternative tool."
                }
            elif "parameter" in error_message or "missing" in error_message:
                # Parameter-related errors
                return {
                    "recovery_strategy": "PARAMETER_REPAIR",
                    "reasoning": "Parameter-related error, suggesting parameter repair needed.",
                    "confidence_level": "HIGH",
                    "estimated_success_probability": 65,
                    "next_steps": "Repair missing or invalid parameters."
                }
            else:
                # Default to parameter repair for any other errors
                return {
                    "recovery_strategy": "PARAMETER_REPAIR",
                    "reasoning": "Default strategy for unspecified errors.",
                    "confidence_level": "LOW",
                    "estimated_success_probability": 40,
                    "next_steps": "Attempt parameter repair as starting point."
                }

    class ParameterGeneratorHelpers:
        @staticmethod
        def validate_params(tool_name: str, parameters: dict) -> tuple[bool, str]:
            """Validate parameters against tool schema.
            - Checks required keys
            - Performs basic JSON Schema type validation for common types
            Returns (is_valid, error_message).
            """
            tool_schema = AgentGraphCore.get_tool_schema(tool_name)
            # Required keys check
            required_keys = tool_schema.get("required", [])
            missing = [k for k in required_keys if k not in parameters]
            if missing:
                return False, f"Missing required parameters: {missing} of tool: {tool_name}"

            # Basic type checks (no external dependency)
            properties = tool_schema.get("properties", {}) if isinstance(tool_schema, dict) else {}
            if properties and isinstance(parameters, dict):
                type_map = {
                    "string": str,
                    "number": (int, float),
                    "integer": int,
                    "boolean": bool,
                    "array": list,
                    "object": dict,
                }
                type_errors: list[str] = []
                for key, value in parameters.items():
                    prop_schema = properties.get(key)
                    if not prop_schema or not isinstance(prop_schema, dict):
                        continue
                    expected_type = prop_schema.get("type")
                    if isinstance(expected_type, list):
                        expected_python_types = tuple(type_map.get(t) for t in expected_type if t in type_map)
                    else:
                        expected_python_types = type_map.get(expected_type)
                    if expected_python_types is None:
                        continue
                    # Special-cases for number/integer
                    if expected_type == "number" and isinstance(value, (int, float)):
                        pass
                    elif expected_type == "integer" and isinstance(value, int) and not isinstance(value, bool):
                        pass
                    else:
                        try:
                            if not isinstance(value, expected_python_types):
                                type_errors.append(f"{key} expected {expected_type}, got {type(value).__name__}")
                        except TypeError:
                            # In case expected_python_types is not a proper type/tuple
                            continue
                if type_errors:
                    return False, f"Type validation failed: {type_errors[:5]}"

            return True, ""

    class ToolExecutionHelpers:
        @classmethod
        def _tool_executor(cls, tool_name: str, parameters: dict) -> tuple[bool, str]:
            """Execute tool and return (success, result)."""
            from ...tools.lggraph_tools.tool_response_manager import ToolResponseManager

            debug_info("Tool Executor",
                       f"Executing tool: '{tool_name}' with parameters: {parameters}",
                       metadata={"function name": "__tool_executor", "tool_name": tool_name, "parameters": parameters})

            try:
                registered_tools = AgentCoreHelpers.get_safe_tools_list()
            except RuntimeError as e:
                return (False, str(e))

            tool_to_execute = next((tool for tool in registered_tools if tool.name.lower() == tool_name.lower()), None)
            if not tool_to_execute:
                return (False, f"Tool '{tool_name}' not found")

            try:
                invoke_params = parameters.copy()
                invoke_params["tool_name"] = tool_name
                tool_to_execute.invoke(invoke_params)

                responses = ToolResponseManager().get_response()
                if not responses:
                    return (False, f"No response received from tool {tool_name}")

                last_response = responses[-1]
                if not hasattr(last_response, "content"):
                    return (False, f"Invalid response format from tool {tool_name}")

                # Enhanced error detection for RunShellCommand and other tools
                # todo this needs to be more robust and handle more edge cases by llm reasoning about the output
                is_logical_success = True
                logical_failure_message = ""

                if tool_name == "run_shell_command":
                    content = last_response.content
                    is_logical_success = True  # Assume success unless proven otherwise
                    logical_failure_message = ""

                    # Priority 1: Check for a non-zero exit code. This is the most reliable indicator.
                    try:
                        import re
                        exit_code_match = re.search(r"Exit Code:\s*(\d+)", content)
                        if exit_code_match:
                            exit_code = int(exit_code_match.group(1))
                            if exit_code != 0:
                                is_logical_success = False
                                logical_failure_message = f"Command failed with non-zero exit code {exit_code}. Full output: {content}"
                    except Exception:
                        pass  # Ignore parsing errors, will rely on string checks

                    # Priority 2: If exit code is 0 or absent, check for common error strings in output.
                    if is_logical_success:
                        error_indicators = [
                            "Error (code",
                            "Error:",
                            "Stderr:",  # Check if Stderr has content
                            "command not found",
                            "is not recognized as an internal or external command",
                            "The syntax of the command is incorrect",
                            "Access is denied",
                            "No such file or directory",
                            "Permission denied",
                            "was unexpected at this time"
                        ]
                        # Check for Stderr content specifically
                        import re
                        stderr_match = re.search(r"Stderr:\s*(.+)", content, re.DOTALL)
                        if stderr_match and stderr_match.group(1).strip() and stderr_match.group(
                                1).strip() != "(empty)":
                            is_logical_success = False
                            logical_failure_message = f"Command produced output on Stderr. Full output: {content}"
                        else:
                            for error_indicator in error_indicators:
                                if error_indicator.lower() in content.lower():
                                    is_logical_success = False
                                    logical_failure_message = f"Command output contained error indicator '{error_indicator}'. Full output: {content}"
                                    break

                elif tool_name in ["read_file", "read_text_file", "write_file"]:
                    # Enhanced error detection for file operations
                    content = last_response.content.lower()
                    file_error_indicators = [
                        "file not found",
                        "no such file",
                        "permission denied",
                        "access denied",
                        "invalid path",
                        "directory not found",
                        "cannot read",
                        "cannot write"
                    ]
                    for error_indicator in file_error_indicators:
                        if error_indicator in content:
                            is_logical_success = False
                            logical_failure_message = last_response.content
                            break

                if is_logical_success:
                    debug_info("Tool Executor", f"Tool '{tool_name}' executed successfully.",
                               metadata={"function name": "__tool_executor", "tool_name": tool_name,
                                         "response_content": last_response.content[:200] + "..." if len(
                                             last_response.content) > 200 else last_response.content})
                    return (True, last_response.content)
                else:
                    debug_warning("Tool Executor", f"Tool '{tool_name}' executed but detected logical failure.",
                                  metadata={"function name": "__tool_executor", "tool_name": tool_name,
                                            "response_content": last_response.content[:200] + "..." if len(
                                                last_response.content) > 200 else last_response.content,
                                            "logical_failure": True})
                    return (False, logical_failure_message)
            except Exception as e:
                debug_error("Tool Executor", f"Exception during tool execution: {str(e)}",
                            metadata={"function name": "__tool_executor", "tool_name": tool_name, "exception": str(e)})
                return (False, f"Error executing tool {tool_name}: {e!s}")

        @staticmethod
        def exeCuteTool(parameters: dict, tool_name: str, timeout: int = 60) -> tuple[bool, str]:
            """
            Execute a tool via a separate worker process and enforce a timeout.

            Intended behavior:
            - Run the internal `__tool_executor` in an isolated process or worker.
            - Terminate the worker if it exceeds a configured timeout to avoid hangs.
            - Return a tuple `(success: bool, result: str)` where `result` is the tool output or an error message.

            Return:
            - tuple[bool, str]

            Implementation notes:
            - Use `multiprocessing` or `concurrent.futures.ProcessPoolExecutor` to isolate execution.
            - Ensure proper cleanup of processes and robust exception handling to avoid resource leaks.
            """
            from concurrent.futures import ThreadPoolExecutor, TimeoutError

            executor = ThreadPoolExecutor(max_workers=1)
            future = executor.submit(AgentCoreHelpers.ToolExecutionHelpers._tool_executor, tool_name, parameters)
            try:
                success, result = future.result(timeout=timeout)
                executor.shutdown(wait=True)  # Wait for the future to complete if it finishes on time.
                return success, result
            except TimeoutError:
                # The future timed out. Don't wait for it to complete.
                # This will leave a zombie thread if the underlying tool call is stuck,
                # but it will prevent the main workflow from hanging.
                executor.shutdown(wait=False)
                debug_error("Tool Executor", f"Tool '{tool_name}' execution timed out after {timeout} seconds.",
                            metadata={"function name": "exeCuteTool", "tool_name": tool_name, "timeout": timeout})
                return False, f"Tool execution timed out after {timeout} seconds"
            except Exception as e:
                # Handle other exceptions during execution.
                executor.shutdown(wait=True)
                debug_error("Tool Executor", f"Exception during tool execution: {str(e)}",
                            metadata={"function name": "exeCuteTool", "tool_name": tool_name, "exception": str(e)})
                return False, f"Error executing tool {tool_name}: {e!s}"

    class ComplexityAnalyzer:
        """Analyzes task complexity and determines decomposition requirements."""

        @staticmethod
        def analyze_task_complexity(task: TASK, spawn_reason: str | None = None) -> dict:
            """Analyze if task is atomic or needs decomposition using tool schema awareness."""
            debug_info("Complexity Analyzer",
                       f"Analyzing complexity for Task {task.task_id}: '{task.description}'",
                       metadata={"function name": "__analyze_task_complexity", "task_id": task.task_id,
                                 "task_description": task.description, "tool_name": task.tool_name})

            tool_schema = AgentGraphCore.get_tool_schema(task.tool_name)

            prompt_generator = HierarchicalAgentPrompt()
            # Pass the spawn_reason to the prompt generator
            system_prompt, human_prompt = prompt_generator.generate_tool_schema_complexity_prompt(
                task.description, task.tool_name, tool_schema, task.depth, parent_context=spawn_reason
            )

            model = ModelManager()
            response = model.invoke([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": human_prompt},
            ])

            analysis_result = ModelManager.convert_to_json(response.content)

            if not isinstance(analysis_result, dict) or "requires_decomposition" not in analysis_result:
                simple_tools = ["list_directory", "read_text_file", "write_file", "create_directory", "google_search"]
                is_simple = task.tool_name in simple_tools

                return {
                    "requires_decomposition": not is_simple,
                    "reasoning": f"Fallback analysis - {task.tool_name} is {'simple' if is_simple else 'complex'} based on patterns.",
                    "atomic_tool_name": task.tool_name if is_simple else None,
                }

            debug_info("Complexity Analyzer", f"Complexity Analysis Result: {analysis_result}",
                       metadata={"function name": "__analyze_task_complexity", "task_id": task.task_id,
                                 "analysis_result": analysis_result})
            return analysis_result


class AgentGraphCore:
    """🏗️ HIERARCHICAL AGENT SYSTEM WITH INTELLIGENT TOOL PRE-FILTERING

    This is the core implementation of a sophisticated agent orchestration system that:

    ⚡ PERFORMANCE OPTIMIZATIONS:
    - Reduces LLM token usage by 90% through intelligent tool pre-filtering
    - Uses 2-stage approach: recommend relevant tools first, then plan with focused tool set
    - Eliminates tool hallucination through validation and schema-aware prompting

    🧠 INTELLIGENT CAPABILITIES:
    - Dynamic task complexity analysis using tool schema awareness
    - Automatic sub-agent spawning for complex tasks (Progressive Refinement pattern)
    - Advanced error recovery with spawning-based recovery agents
    - Hierarchical parent-child task relationship management

    🔄 WORKFLOW ORCHESTRATION:
    - 7-node LangGraph workflow with conditional routing
    - State-machine-based execution with comprehensive error handling
    - Tool execution with safe bounds checking and validation
    - Schema-aware parameter generation for optimal tool usage

    🎯 PRODUCTION FEATURES:
    - Defensive programming patterns throughout
    - Graceful degradation when tools unavailable
    - Comprehensive system_logging and error tracking
    - Integration with existing agent_mode_node.py system

    The system embodies enterprise-grade reliability while maintaining the flexibility
    to handle abstract, complex goals through intelligent decomposition and execution.
    """

    # Limits before error fallback abandons a task (prevents classifier <-> fallback livelock):
    # consecutive fallback runs without a new execution, and total failed executions
    MAX_RECOVERY_ATTEMPTS = 3
    MAX_TASK_FAILURES = 5

    # TODO we need to fix the debugs logs and user displaying logs
    # TODO we need to fix ~updated task thing and iteration to find the current task in the task list
    # :-- current_task = next((task for task in updated_tasks if task.task_id == current_task_id), None)

    @classmethod
    def __subAGENT_initial_planner(cls, state: "WorkflowStateModel") -> dict:
        """Creates high-level plan using tool pre-filtering and self-healing for efficiency."""
        AgentStatusUpdater.update_status('Initial Planner')
        goal = state.original_goal
        debug_info("--- NODE: Initial Planner ---", f"Decomposing goal: {goal}",
                   metadata={"function name": "__subAGENT_initial_planner", "original_goal": goal})

        llm_returned = []
        validated_tasks = []
        error_feedback = None
        plan_is_valid = False

        for attempt in range(2):  # Try to generate a valid plan up to 2 times
            debug_info("Initial Planner", f"Planning attempt {attempt + 1}", metadata={"attempt": attempt + 1})

            # STEP 1 & 2: Recommend and get tool context
            recommended_tools = AgentCoreHelpers.recommend_tools_for_task(goal)
            detailed_tool_context = AgentCoreHelpers.get_detailed_tool_context(recommended_tools)

            # STEP 3: Generate plan, providing feedback on failure
            prompt_generator = HierarchicalAgentPrompt()
            system_prompt, human_prompt = prompt_generator.generate_tool_aware_initial_plan_prompt(
                goal,
                detailed_tool_context,
                error_feedback=error_feedback  # Pass feedback from previous failed attempt
            )

            model = ModelManager()
            response = model.invoke([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": human_prompt},
            ])
            llm_returned = ModelManager.convert_to_json(response.content)

            # Basic validation of response format
            if not isinstance(llm_returned, list):
                error_feedback = "The response was not a valid JSON array of tasks. Please format the output correctly."
                continue

            # STEP 4 & 5: Validate the plan
            current_validated_tasks = []
            has_invalid_tool = False
            invalid_tool_name = None
            validation_error_details = None

            # Using a safe list of tool names for case-insensitive comparison
            safe_tool_names = [tool.name.lower() for tool in AgentCoreHelpers.get_safe_tools_list()]
            # Add our virtual tool to the list of valid names for the planner's validation step
            safe_tool_names.append("perform_synthesis")

            for item_idx, item in enumerate(llm_returned):
                if not isinstance(item, dict):
                    has_invalid_tool = True
                    invalid_tool_name = f"Item at index {item_idx} is not a dictionary: {item}"
                    break

                if "tool_name" not in item:
                    has_invalid_tool = True
                    invalid_tool_name = f"Task at index {item_idx} missing 'tool_name' key"
                    break

                if "description" not in item:
                    has_invalid_tool = True
                    invalid_tool_name = f"Task at index {item_idx} missing 'description' key"
                    break

                # NEW: Capture the high-fidelity flag from the plan
                requires_high_fidelity = item.get("requires_high_fidelity_context", False)

                original_tool_name = item.get("tool_name")  # Use .get() for safety
                if not original_tool_name:
                    has_invalid_tool = True
                    invalid_tool_name = f"Task at index {item_idx} has empty or null 'tool_name'"
                    break

                tool_name_lower = original_tool_name.lower()

                if tool_name_lower not in safe_tool_names:
                    has_invalid_tool = True
                    invalid_tool_name = original_tool_name
                    # Get available tools for better error message
                    available_tools = ", ".join(
                        [t.name for t in AgentCoreHelpers.get_safe_tools_list()][:10])  # Show first 10 tools
                    validation_error_details = f"Tool '{original_tool_name}' not found. Available tools: {available_tools}"
                    break

                # Handle case correction and virtual tool
                if tool_name_lower == "perform_synthesis":
                    item["tool_name"] = "perform_synthesis"
                else:
                    # It's a real tool, find the correct case-sensitive name
                    correct_tool_name = next(
                        (t.name for t in AgentCoreHelpers.get_safe_tools_list() if t.name.lower() == tool_name_lower),
                        None)
                    # If we couldn't find an exact match, try a more lenient matching approach
                    if correct_tool_name is None:
                        # Try to find a tool that contains the tool name (for partial matches)
                        correct_tool_name = next((t.name for t in AgentCoreHelpers.get_safe_tools_list() if
                                                  tool_name_lower in t.name.lower() or t.name.lower() in tool_name_lower),
                                                 None)

                    # If we still couldn't find it, keep the original name but validate it exists
                    if correct_tool_name is None:
                        # Check if the original tool name exists in the safe tool list (case-insensitive)
                        tool_exists = any(
                            t.name.lower() == tool_name_lower for t in AgentCoreHelpers.get_safe_tools_list())
                        if tool_exists:
                            correct_tool_name = original_tool_name  # Keep original case

                    item["tool_name"] = correct_tool_name

                # Final check to ensure a valid tool name was assigned before appending
                if item["tool_name"] is None:
                    has_invalid_tool = True
                    invalid_tool_name = original_tool_name  # Use the original name in the error
                    break

                # Add the high-fidelity flag to the validated task item
                item['requires_high_fidelity_context'] = requires_high_fidelity
                current_validated_tasks.append(item)

            if not has_invalid_tool:
                plan_is_valid = True
                validated_tasks = current_validated_tasks
                debug_info("Initial Planner", "Successfully generated a valid plan.", metadata={"attempt": attempt + 1})
                break  # Exit loop on success
            else:
                # Create feedback for the next attempt
                if validation_error_details:
                    error_feedback = f"You previously planned to use the tool '{invalid_tool_name}', which is not a valid tool. {validation_error_details}. Please only use tools from the provided list and ensure correct spelling and capitalization."
                else:
                    error_feedback = f"You previously planned to use the tool '{invalid_tool_name}', which is not a valid tool. Please only use tools from the provided list and ensure correct spelling and capitalization."
                debug_warning("Initial Planner",
                              f"Invalid plan generated on attempt {attempt + 1}. Feedback: {error_feedback}",
                              metadata={"attempt": attempt + 1})

        # After the loop, proceed with a valid plan or use the final fallback
        if plan_is_valid:
            # Remove duplicates from the successfully validated plan
            filtered_tasks = []
            seen_descriptions = set()
            for item in validated_tasks:
                if item["description"] not in seen_descriptions:
                    filtered_tasks.append(item)
                    seen_descriptions.add(item["description"])

            # --- ENFORCE FINAL COLLECTOR (MANDATORY) ---
            # try:
            #     has_final_collector = any(
            #         isinstance(it, dict)
            #         and str(it.get("tool_name", "")).lower() == "perform_synthesis"
            #         and "collector" in str(it.get("description", "")).lower()
            #         for it in filtered_tasks
            #     )
            #     if not has_final_collector:
            #         filtered_tasks.append({
            #             "description": "Collector: Synthesize outputs of all previous tasks into concise, structured notes (Findings, Evidence, Risks).",
            #             "tool_name": "perform_synthesis",
            #             "requires_high_fidelity_context": False,
            #         })
            # except Exception:
            #     # Defensive: never fail planning because of enforcement
            #     pass

            # Get skip threshold from settings (default 70)
            skip_threshold = getattr(settings, 'SKIP_THRESHOLD', 70)

            actual_tasks = []
            for idx, item in enumerate(filtered_tasks):
                skip_probability = item.get("skip_probability", 0)
                skip_reason = item.get("skip_reason", "")

                # Determine initial status based on skip probability
                initial_status: Literal["pending", "skip"] = "skip" if skip_probability >= skip_threshold else "pending"

                # Log skip decisions for visibility
                if initial_status == "skip":
                    debug_info("Initial Planner - Pre-Flight Skip",
                              f"Task {idx + 1} marked as SKIP (probability: {skip_probability}%): {item['description'][:60]}...",
                              metadata={
                                  "task_id": str(idx + 1),
                                  "skip_reason": skip_reason,
                                  "skip_probability": skip_probability,
                                  "threshold": skip_threshold
                              })

                task = TASK(
                    task_id=str(idx + 1),
                    description=item["description"],
                    tool_name=item["tool_name"],
                    status=initial_status,  # 🔥 Set status based on skip probability
                    requires_high_fidelity_context=item.get("requires_high_fidelity_context", False),
                    required_context=REQUIRED_CONTEXT(
                        source_node="initial_planner",
                        pre_execution_context={
                            "skip_probability": skip_probability,
                            "skip_reason": skip_reason
                        } if skip_probability > 0 else None
                    ),
                )
                actual_tasks.append(task)
        else:
            # Final fallback if all attempts fail
            actual_tasks = []

        if not actual_tasks:
            debug_error("Initial Planner", "All planning attempts failed. Using final fallback task.", metadata={})
            actual_tasks.append(
                TASK(
                    task_id="1",
                    description="List current directory to understand project structure, as initial planning failed.",
                    tool_name="list_directory",
                    required_context=REQUIRED_CONTEXT(source_node="initial_planner_fallback"),
                )
            )

        debug_info("Initial Planner", f"Final plan generated with {len(actual_tasks)} tasks.",
                   metadata={"task_count": len(actual_tasks), "tasks": [task.model_dump() for task in actual_tasks]})

        return {
            "tasks": actual_tasks,
            "current_task_id": actual_tasks[0].task_id if actual_tasks else "1",
            "workflow_status": "RUNNING",
            "executed_nodes": state.executed_nodes + ["subAGENT_initial_planner"],
        }

    @classmethod
    def __subAGENT_classifier(cls, state: "WorkflowStateModel") -> dict:
        """🎯 DECISION POINT: Analyzes current task and decides next workflow step.

        This is a critical routing node that determines whether to:
        - Proceed with normal task execution (AGENT_PERFORM_TASK)
        - Trigger error recovery procedures (AGENT_PERFORM_ERROR_FALLBACK)
        - Skip tasks marked in pre-flight check (status='skip')

        The decision is based on task failure count and retry limits, implementing
        a graduated response system for handling task failures.
        """
        current_task_id = state.current_task_id
        AgentStatusUpdater.update_status("complexity_analysis", task_id=current_task_id, extra_info="Analyzing task")
        debug_info("--- NODE: Classifier ---", "Deciding next action based on task status and failure history",
                   metadata={"function name": "__subAGENT_classifier"})
        tasks = state.tasks
        current_task = next((t for t in tasks if t.task_id == current_task_id), None)

        # Handle pre-flight skipped tasks - create execution context and mark as ready for task_planner
        if current_task and current_task.status == "skip":
            skip_reason = "No reason provided"
            skip_probability = 0
            if current_task.required_context and current_task.required_context.pre_execution_context:
                skip_reason = current_task.required_context.pre_execution_context.get("skip_reason", skip_reason)
                skip_probability = current_task.required_context.pre_execution_context.get("skip_probability", 0)

            debug_info("Classifier - Skip Handler",
                      f"Task {current_task_id} was PRE-FLIGHT SKIPPED (prob: {skip_probability}%): {skip_reason}",
                      metadata={
                          "task_id": current_task_id,
                          "skip_reason": skip_reason,
                          "skip_probability": skip_probability,
                          "task_description": current_task.description[:60] + "..."
                      })

            # Create minimal execution context so task appears "complete" to workflow
            if not current_task.execution_context:
                current_task.execution_context = EXECUTION_CONTEXT(
                    tool_name=current_task.tool_name,
                    parameters={},
                    result=f"⏭️ Task skipped: {skip_reason}",
                    analysis=f"Pre-flight check (probability: {skip_probability}%) determined this task should be skipped: {skip_reason}",
                    goal_achieved=False
                )

            # Task remains in skip status and has execution_context, so it will be treated as "done"
            # The workflow will route to task_planner to select next pending task
            # We still set persona to allow normal flow through router
            return {
                "tasks": tasks,
                "executed_nodes": state.executed_nodes + ["subAGENT_classifier"],
                "persona": "AGENT_PERFORM_TASK"  # Use normal persona so router works
            }

        # handle that if the previous task got skipped and this task is depend on that (cascade skip effect)
        elif current_task.status == "pending":
            skipped_tasks = [t for t in tasks if t.status == "skip"]
            should_skip, reason = AgentCoreHelpers.evaluate_skip_cascade(current_task, skipped_tasks)
            if should_skip:
                debug_info("Classifier - Cascade Skip Handler",
                           f"Task {current_task_id} is being SKIPPED due to dependency on skipped tasks: {reason}",
                           metadata={
                               "task_id": current_task_id,
                               "skip_reason": reason,
                               "task_description": current_task.description[:60] + "..."
                           })

                # Create minimal execution context so task appears "complete" to workflow
                if not current_task.execution_context:
                    current_task.execution_context = EXECUTION_CONTEXT(
                        tool_name=current_task.tool_name,
                        parameters={},
                        result=f"⏭️ Task skipped due to dependency: {reason}",
                        analysis=f"Cascade skip effect triggered by dependency on skipped tasks: {reason}",
                        goal_achieved=False
                    )

                current_task.status = "skip"  # Mark task as skipped

                return {
                    "tasks": tasks,
                    "executed_nodes": state.executed_nodes + ["subAGENT_classifier"],
                    "persona": "AGENT_PERFORM_TASK"  # Use normal persona so router works
                }
        # 🔍 CRITICAL DECISION: Determine execution persona based on task readiness and failure history
        persona = "AGENT_PERFORM_TASK"

        # Priority 1: If task is pending AND already has execution parameters, force execution next
        if current_task and current_task.status == "pending" and \
                current_task.execution_context and isinstance(current_task.execution_context.parameters, dict) and \
                current_task.execution_context.parameters:
            # We have updated parameters (possibly from recovery) ready to execute — do not bounce back to fallback
            persona = "AGENT_PERFORM_TASK"
        elif current_task and current_task.failure_context:
            # Check if we've exceeded retry limits to prevent infinite loops
            if current_task.failure_context.fail_count > 3:
                AgentStatusUpdater.update_status("complexity_analysis", task_id=current_task_id,
                                                 extra_info="FAILED: Exceeded retry limit")
                debug_error("Classifier",
                            f"Task {current_task_id} has failed {current_task.failure_context.fail_count} times. Exceeded retry limit of 2 attempts. Marking as permanently failed.",
                            metadata={"function name": "__subAGENT_classifier", "task_id": current_task_id,
                                      "fail_count": current_task.failure_context.fail_count,
                                      "max_retries": current_task.max_retries})
                current_task.status = "failed"
                persona = "AGENT_PERFORM_ERROR_FALLBACK"
            elif current_task.failure_context.fail_count >= 2:
                persona = "AGENT_PERFORM_ERROR_FALLBACK"
            elif current_task.failure_context.fail_count >= current_task.max_retries:
                # if the task got more failures than max retries, we skip it
                persona = "AGENT_PERFORM_ERROR_FALLBACK"
                current_task.status = "skip"

        # print_log_message(f"Task ID: {current_task_id}, Persona: {persona}", "Classifier")
        debug_info("Classifier", f"Task ID: {current_task_id}, Persona: {persona}",
                   metadata={"function name": "__subAGENT_classifier", "task_id": current_task_id, "persona": persona})
        return {"executed_nodes": state.executed_nodes + ["subAGENT_classifier"], "persona": persona}

    @classmethod
    def subAGENT_parameter_generator(cls, state: "WorkflowStateModel") -> dict:
        """🧠 PARAMETER GENERATOR: Generates and validates parameters using the Dual Context system."""
        debug_info("--- NODE: Parameter Generator ---", "Generating and validating parameters",
                   metadata={"function name": "subAGENT_parameter_generator"})

        tasks = state.tasks
        current_task_id = state.current_task_id
        current_task: TASK = next((task for task in tasks if task.task_id == current_task_id), None)

        if current_task:
            # 🔥 SKIP BYPASS: Skip parameter generation for skipped tasks
            if current_task.status == "skip":
                debug_info("Parameter Generator - Skip Bypass",
                           "Task is skipped, bypassing parameter generation.",
                           metadata={"function name": "subAGENT_parameter_generator", "task_id": current_task_id})
                return {"tasks": tasks, "executed_nodes": state.executed_nodes + ["subAGENT_parameter_generator"]}

            if current_task.status == "pending" and current_task.execution_context and \
                    isinstance(current_task.execution_context.parameters,
                               dict) and current_task.execution_context.parameters:
                debug_info("Parameter Generator",
                           "Reusing existing parameters for pending task; skipping regeneration.",
                           metadata={"function name": "subAGENT_parameter_generator", "task_id": current_task_id})
                return {"tasks": tasks, "executed_nodes": state.executed_nodes + ["subAGENT_parameter_generator"]}

            tool_schema = cls.get_tool_schema(current_task.tool_name)
            context_data = current_task.required_context.pre_execution_context or {}
            full_history = context_data.get("completed_tasks_history", [])
            # Ensure full_history is a list of TASK objects
            failed_tasks_with_feedback_raw = context_data.get("failed_tasks_with_validator_feedback", [])
            failed_tasks_with_feedback: list[TASK] = []
            for item in failed_tasks_with_feedback_raw:
                if isinstance(item, TASK):
                    failed_tasks_with_feedback.append(item)
                elif isinstance(item, dict):
                    try:
                        failed_tasks_with_feedback.append(TASK(**item))
                    except Exception:
                        # Skip entries that can't be converted to TASK
                        continue

            analysis_summary = [
                f"Task {t.task_id} ({t.tool_name}): {t.execution_context.analysis}"
                for t in full_history
                if t.execution_context and t.execution_context.analysis
            ]

            # Build validator feedback context from failed tasks
            validator_feedback_summary = []
            for failed_task in failed_tasks_with_feedback:
                if failed_task.failure_context and failed_task.failure_context.error_type == "GoalValidationFailure":
                    validator_feedback_summary.append(
                        f"VALIDATOR REJECTED Task {failed_task.task_id} ({failed_task.tool_name}): {failed_task.failure_context.error_message}"
                        f"\n FAILED Parameters: {failed_task.failure_context.failed_parameters if failed_task.failure_context.failed_parameters else 'N/A'}"
                    )

            # Combine completed task analysis and validator feedback
            context_parts = []
            if analysis_summary:
                context_parts.append("COMPLETED TASKS (Summarized):\n" + "\n".join(analysis_summary))

            # NEW: Check for high-fidelity flag
            if current_task.requires_high_fidelity_context:
                raw_results_summary = [
                    f"Task {t.task_id} ({t.tool_name}) Raw Result:\n{t.execution_context.result}"
                    for t in full_history
                    if t.execution_context and t.execution_context.result
                ]
                if raw_results_summary:
                    context_parts.append("--- HIGH-FIDELITY RAW RESULTS (as requested by current task) ---\
" + "\n\n".join(raw_results_summary))

            if validator_feedback_summary:
                context_parts.append(
                    "VALIDATOR FEEDBACK (avoid these patterns):\n" + "\n".join(validator_feedback_summary))

            context_string = "\n\n".join(context_parts) if context_parts else None

            # 🚨 CRITICAL FIX: Include failure_context and platform information
            failure_context_info = None
            platform_info = None

            # Extract failure context from current task if available
            if current_task.failure_context:
                failure_context_info = {
                    "error_message": current_task.failure_context.error_message,
                    "error_type": current_task.failure_context.error_type,
                    "fail_count": current_task.failure_context.fail_count,
                    "failed_parameters": current_task.failure_context.failed_parameters,
                    "strategy_history": [
                        {
                            "strategy": s.recovery_strategy,
                            "reasoning": s.reasoning,
                            "outcome": s.outcome
                        } for s in (current_task.failure_context.strategy_history or [])
                    ]
                }
                debug_info("Parameter Generator",
                           f"Including failure context for task {current_task_id}: {current_task.failure_context.error_type}",
                           metadata={"function name": "subAGENT_parameter_generator", "task_id": current_task_id,
                                     "error_type": current_task.failure_context.error_type,
                                     "fail_count": current_task.failure_context.fail_count})

            # Get platform information
            import os
            platform_info = {
                "os_name": os.name,
                "platform": "Windows" if os.name == "nt" else "Unix/Linux",
                "supports_posix": os.name != "nt"
            }

            prompt_generator = HierarchicalAgentPrompt()
            system_prompt, human_prompt = prompt_generator.generate_schema_aware_parameter_prompt(
                task_description=current_task.description,
                tool_name=current_task.tool_name,
                tool_schema=tool_schema,
                context=context_string,
                full_history=full_history,
                depth=current_task.depth,
                failure_context=failure_context_info,  # 🚨 NEW: Pass failure context
                platform_info=platform_info,  # 🚨 NEW: Pass platform info
                requires_high_fidelity=current_task.requires_high_fidelity_context,  # 🚨 NEW: Pass high-fidelity flag
            )

            model = ModelManager()
            response = model.invoke([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": human_prompt},
            ])
            parameters = ModelManager.convert_to_json(response.content)

            if not isinstance(parameters, dict):
                parameters = cls.__generate_fallback_parameters(current_task.tool_name, current_task.description)

            # --- Proactive Parameter Validation ---
            is_valid, error_message = AgentCoreHelpers.ParameterGeneratorHelpers.validate_params(
                current_task.tool_name, parameters
            )

            if is_valid:
                current_task.execution_context = EXECUTION_CONTEXT(
                    tool_name=current_task.tool_name,
                    parameters=parameters,
                )
                debug_info("Parameter Generator", f"Generated and validated parameters for task {current_task_id}",
                           metadata={"function name": "subAGENT_parameter_generator", "task_id": current_task_id,
                                     "parameters": parameters})
            else:
                # If validation fails, set task to failed and route to error fallback
                current_task.status = "failed"
                current_task.failure_context = FAILURE_CONTEXT(
                    error_message=error_message,
                    fail_count=(current_task.failure_context.fail_count + 1) if current_task.failure_context else 1,
                    last_failure_timestamp=get_formatted_timestamp(),
                    error_type="ParameterValidationError",
                    failed_parameters=parameters,
                )
                debug_error("Parameter Generator",
                            f"Parameter validation failed for task {current_task_id}: {error_message}",
                            metadata={"function name": "subAGENT_parameter_generator", "task_id": current_task_id,
                                      "tool_name": current_task.tool_name, "invalid_parameters": parameters})

        return {"tasks": tasks, "executed_nodes": state.executed_nodes + ["subAGENT_parameter_generator"]}

    @classmethod
    def get_tool_schema(cls, tool_name: str) -> dict:
        """Get schema for a specific tool."""
        try:
            tools = AgentCoreHelpers.get_safe_tools_list()
            target_tool = next((tool for tool in tools if tool.name.lower() == tool_name.lower()), None)

            if target_tool:
                schema_str = get_tool_argument_schema(target_tool)
                import json
                return json.loads(schema_str)
            return {}
        except Exception as e:
            # print_log_message(f"Failed to get schema for {tool_name}: {e}", "Tool Schema")
            debug_error("Tool Schema", f"Failed to get schema for {tool_name}: {e}",
                        metadata={"function name": "__get_tool_schema", "tool_name": tool_name})
            return {}

    @classmethod
    def __generate_fallback_parameters(cls, tool_name: str, task_description: str) -> dict:
        """Generate sensible fallback parameters when LLM parameter generation fails."""
        fallback_patterns = {
            "list_directory": {"directory_path": "."},
            "read_text_file": {"file_path": "README.md"},
            "write_file": {"file_path": "output.txt", "content": f"Generated content for: {task_description}"},
            "create_directory": {"directory_path": "new_directory"},
            "google_search": {"query": task_description[:100], "num_results": 5},
            "run_shell_command": {"command": 'echo "Command execution for task"'},
            "perform_synthesis": {"instructions": f"Synthesize the context related to: {task_description}"},
        }
        return fallback_patterns.get(tool_name, {"task_description": task_description})

    @classmethod
    def __subAGENT_task_executor(cls, state: "WorkflowStateModel") -> dict:
        """⚙️ CORE EXECUTION ENGINE: Executes tasks OR triggers intelligent decomposition.

        This is the heart of the hierarchical system, implementing the key decision:
        "Should this task be executed directly, or does it need sub-agent spawning?"

        EXECUTION FLOW:
        1. Analyze task complexity using tool schema and description
        2. If COMPLEX → Trigger spawning system for decomposition
        3. If ATOMIC → Execute directly with tool pre-filtering
        4. Handle all failure scenarios with proper error context

        The spawning integration here enables true hierarchical problem-solving
        where abstract goals are recursively refined into executable operations.
        """
        debug_info("--- NODE: Task Executor ---", "Executing or decomposing current task",
                   metadata={"function name": "__subAGENT_task_executor"})
        current_task_id = state.current_task_id
        updated_tasks = state.tasks
        current_task = next((task for task in updated_tasks if task.task_id == current_task_id), None)
        AgentStatusUpdater.update_status("task_execution", task_id=current_task_id)

        if not current_task:
            debug_error("Task Executor", f"Could not find current task with ID {current_task_id}",
                        metadata={"function name": "__subAGENT_task_executor", "current_task_id": current_task_id})
            return {"workflow_status": "FAILED"}

        # 🔥 SKIP BYPASS: Tasks already marked as skip bypass execution entirely
        if current_task.status == "skip":
            debug_info("Task Executor - Skip Bypass",
                      f"Task {current_task_id} is SKIPPED, bypassing execution",
                      metadata={
                          "task_id": current_task_id,
                          "skip_reason": current_task.execution_context.result if current_task.execution_context else "Pre-flight skip"
                      })
            # Task already has execution_context from classifier, just pass through
            return {
                "tasks": updated_tasks,
                "executed_nodes": state.executed_nodes + ["subAGENT_task_executor"],
            }

        # --- VIRTUAL TOOL INTERCEPTION ---
        if current_task.tool_name == "perform_synthesis":
            debug_info("Task Executor", "Intercepted virtual tool 'perform_synthesis'.",
                       metadata={"task_id": current_task.task_id})
            context_data = current_task.required_context.pre_execution_context or {}
            full_history = context_data.get("completed_tasks_history", [])
            success, result = AgentCoreHelpers.perform_internal_synthesis(current_task, full_history)
            if success:
                current_task.status = "completed"
                current_task.execution_context.result = result
            else:
                current_task.status = "failed"
                current_task.failure_context = FAILURE_CONTEXT(
                    error_message=result,
                    error_type="SynthesisFailed",
                )
            return {"tasks": updated_tasks, "executed_nodes": state.executed_nodes + ["subAGENT_task_executor"]}
        # --- END VIRTUAL TOOL INTERCEPTION ---

        try:
            # Ensure a failure_context exists for the parent BEFORE we call any analysis or decomposition.
            # Some failure paths set task.status = 'failed' but don't populate failure_context; the spawner and
            # recovery logic rely on that context to choose discovery-first decompositions.
            if getattr(current_task, 'status', None) == 'failed' and not getattr(current_task, 'failure_context', None):
                # Create a minimal synthetic failure_context from available execution_context so downstream nodes
                # (strategy decision, decomposer) have the failed parameters and an error message to reason about.
                synthetic_failed_params = None
                try:
                    if current_task.execution_context and isinstance(current_task.execution_context.parameters, dict):
                        synthetic_failed_params = current_task.execution_context.parameters.copy()
                except Exception:
                    synthetic_failed_params = None

                current_task.failure_context = FAILURE_CONTEXT(
                    error_message=(current_task.execution_context.result if current_task.execution_context and getattr(
                        current_task.execution_context, 'result',
                        None) else f"Parent task {current_task.task_id} failed without explicit failure_context."),
                    fail_count=1,
                    last_failure_timestamp=get_formatted_timestamp(),
                    error_type="SyntheticFailureContext",
                    failed_parameters=synthetic_failed_params,
                    strategy_history=[]
                )
                debug_info("SubAgent Spawner",
                           f"Injected synthetic failure_context into parent task {current_task.task_id}",
                           metadata={"function name": "spawn_subAgent_recursive",
                                     "parent_task_id": current_task.task_id,
                                     "injected_failed_parameters": synthetic_failed_params})

            complexity_analysis = AgentCoreHelpers.ComplexityAnalyzer.analyze_task_complexity(current_task)

            if complexity_analysis.get("requires_decomposition"):
                AgentStatusUpdater.update_status("task complexity analysis", task_id=current_task_id,
                                                 extra_info="Decomposing complex task")
                debug_info("Task Executor", f"Task {current_task_id} is complex - triggering spawning",
                           metadata={"function name": "__subAGENT_task_executor", "task_id": current_task_id,
                                     "complexity_analysis": complexity_analysis})

                # *** FIX: Gather context BEFORE spawning ***
                completed_tasks = [t for t in updated_tasks if
                                   t.status == "completed" and t.execution_context and t.execution_context.result]

                # Create comprehensive context string (consistent with error_fallback approach)
                parent_context_str = (
                        f"Original Goal: {state.original_goal}\n"
                        f"Workflow Progress: {len(completed_tasks)}/{len(updated_tasks)} tasks completed\n"
                        f"Completed Tasks: {[f'Task {t.task_id}: {t.description}' for t in completed_tasks]}\n"
                        f"COMPLEXITY ANALYSIS CONTEXT:\n"
                        f"- Current Task ID: {current_task.task_id}\n"
                        f"- Description: {current_task.description}\n"
                        f"- Tool: {current_task.tool_name}\n"
                        f"- Reasoning: {complexity_analysis.get('reasoning', 'Complex task requiring decomposition')}\n"
                        + (
                            f"- Failure Context: {current_task.failure_context.error_message}\n" if current_task.failure_context else "- No previous failures\n")
                        + (
                            f"- Failed Parameters: {current_task.failure_context.failed_parameters}\n" if current_task.failure_context and current_task.failure_context.failed_parameters else "")
                )

                spawn_result = Spawn_subAgent.spawn_subAgent_recursive(
                    state=state,
                    parent_task=current_task,
                    spawn_reason=complexity_analysis.get("reasoning", "Complex task requiring decomposition"),
                    parent_context=parent_context_str  # Pass the context as string
                )

                if spawn_result and spawn_result.get("spawn_triggered"):
                    return {
                        "tasks": spawn_result["tasks"],
                        "current_task_id": spawn_result["current_task_id"],
                        "executed_nodes": state.executed_nodes + ["subAGENT_task_executor"],
                    }

                current_task.status = "failed"
                current_task.failure_context = FAILURE_CONTEXT(
                    error_message="Task requires decomposition but spawning failed",
                    error_type="SpawningFailure",
                )
                return {
                    "tasks": updated_tasks,
                    "executed_nodes": state.executed_nodes + ["subAGENT_task_executor"],
                }

            AgentStatusUpdater.update_status("task_execution", task_id=current_task_id, extra_info="Executing tool")
            debug_info("Task Executor", f"Task {current_task_id} is atomic - executing directly",
                       metadata={"function name": "__subAGENT_task_executor", "task_id": current_task_id})

            # --- SAFETY FIX: mark task as in_progress before attempting execution to avoid immediate retry loops ---
            try:
                if current_task.status != "in_progress":
                    current_task.status = "in_progress"
                    debug_info("Task Executor", f"Marked Task {current_task_id} as in_progress",
                               metadata={"function name": "__subAGENT_task_executor", "task_id": current_task_id})
            except Exception:
                pass

            success, result = AgentCoreHelpers.ToolExecutionHelpers.exeCuteTool(
                tool_name=current_task.execution_context.tool_name,
                parameters=current_task.execution_context.parameters,
                timeout=settings.BROWSER_USE_TIMEOUT + 10 if current_task.execution_context.tool_name == "browser_agent" else 60
            )

            if success:
                current_task.status = "completed"
                current_task.execution_context.result = result
            else:
                current_task.status = "failed"
                if not current_task.failure_context:
                    current_task.failure_context = FAILURE_CONTEXT(
                        error_message=result,
                        fail_count=1,
                        error_type="ToolExecutionError",
                        failed_parameters=current_task.execution_context.parameters,
                    )
                else:
                    current_task.failure_context.fail_count += 1
                    current_task.failure_context.error_message = result
                    current_task.failure_context.failed_parameters = current_task.execution_context.parameters

                # Add explicit debug when failures repeat to help root cause analysis
                debug_error("Task Executor",
                            f"Task {current_task_id} execution failed (fail_count={current_task.failure_context.fail_count}): {result}",
                            metadata={"function name": "__subAGENT_task_executor", "task_id": current_task_id,
                                      "failed_parameters": current_task.execution_context.parameters})

                if current_task.failure_context.fail_count > 3:
                    AgentStatusUpdater.update_status("task_execution", task_id=current_task_id,
                                                     extra_info="failed: exceeded retries")
                    debug_error("Task Executor",
                                f"Task {current_task_id} has failed {current_task.failure_context.fail_count} times. Exceeded retry limit of 3.",
                                metadata={"function name": "__subAGENT_task_executor", "task_id": current_task_id,
                                          "fail_count": current_task.failure_context.fail_count})
                    current_task.failure_context.error_message = f"Task failed after maximum retry attempts (3). Original error: {result}"
                    current_task.status = "failed"
                    return {"tasks": updated_tasks,
                            "executed_nodes": state.executed_nodes + ["subAGENT_task_executor"]}

        except Exception as e:
            debug_error("Task Executor", f"Error during task execution: {e!s}",
                        metadata={"function name": "__subAGENT_task_executor", "task_id": current_task_id,
                                  "exception": str(e)})
            # Ensure we preserve/record failed_parameters and strategy history when an unexpected exception occurs
            current_task.status = "failed"
            preserved_strategy_history = current_task.failure_context.strategy_history.copy() if current_task.failure_context and current_task.failure_context.strategy_history else []
            preserved_fail_count = (current_task.failure_context.fail_count + 1) if current_task.failure_context else 1
            preserved_failed_parameters = None
            try:
                if current_task.execution_context and isinstance(current_task.execution_context.parameters, dict):
                    preserved_failed_parameters = current_task.execution_context.parameters.copy()
            except Exception:
                preserved_failed_parameters = None

            current_task.failure_context = FAILURE_CONTEXT(
                error_message=str(e),
                fail_count=preserved_fail_count,
                last_failure_timestamp=get_formatted_timestamp(),
                error_type="UnhandledException",
                failed_parameters=preserved_failed_parameters,
                strategy_history=preserved_strategy_history,
            )

        return {"tasks": updated_tasks, "executed_nodes": state.executed_nodes + ["subAGENT_task_executor"]}

    @classmethod
    def __subAGENT_context_synthesizer(cls, state: "WorkflowStateModel") -> dict:
        """Summarizes the result of a completed task for cleaner context passing."""
        debug_info("--- NODE: Context Synthesizer ---", "Summarizing task result for context bridge",
                   metadata={"function name": "__subAGENT_context_synthesizer"})
        tasks = state.tasks
        current_task_id = state.current_task_id
        current_task: TASK = next((t for t in tasks if t.task_id == current_task_id), None)

        if current_task and current_task.status == "completed" and current_task.execution_context and current_task.execution_context.result:
            prompt_generator = HierarchicalAgentPrompt()
            system_prompt, human_prompt = prompt_generator.generate_context_synthesis_prompt(
                current_task.tool_name,
                current_task.execution_context.result,
                depth=current_task.depth
            )

            model = ModelManager()
            response = model.invoke([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": human_prompt},
            ])

            summary = response.content.strip()

            # --- MODIFICATION START ---
            if current_task.tool_name == "google_search" and current_task.execution_context.parameters:
                query = current_task.execution_context.parameters.get("query", "unknown query")
                summary = f"A web search for '{query}' was conducted and {summary.lower().lstrip('a web search was conducted and ')}"
            # --- MODIFICATION END ---

            if summary:
                current_task.execution_context.analysis = summary
                debug_info("Context Synthesizer", f"Generated analysis for Task {current_task_id}: '{summary}'",
                           metadata={"function name": "__subAGENT_context_synthesizer", "task_id": current_task_id,
                                     "summary": summary})
            else:
                current_task.execution_context.analysis = f"Task {current_task.tool_name} completed successfully."

        # 🔥 SKIP HANDLER: Generate analysis for skipped tasks
        elif current_task.status == "skip" and current_task.execution_context and current_task.execution_context.result:
            # Handle skipped tasks by summarizing the skip reason
            skip_summary = f"Task was skipped. Reason: {current_task.execution_context.result}"
            current_task.execution_context.analysis = skip_summary
            debug_info("Context Synthesizer - Skip Handler",
                       f"Generated analysis for SKIPPED Task {current_task_id}: '{skip_summary}'",
                       metadata={"function name": "__subAGENT_context_synthesizer", "task_id": current_task_id})

        return {"tasks": tasks}

    @classmethod
    def __subAGENT_goal_validator(cls, state: "WorkflowStateModel") -> dict:
        """Validates if the task's goal was achieved based on the result and analysis."""
        debug_info("--- NODE: Goal Validator ---", "Validating task goal achievement",
                   metadata={"function name": "__subAGENT_goal_validator"})
        tasks = state.tasks
        current_task_id = state.current_task_id
        current_task = next((t for t in tasks if t.task_id == current_task_id), None)

        # 🔥 SKIP BYPASS: Skip goal validation for skipped tasks entirely.
        if current_task and current_task.status == "skip":
            debug_info("Goal Validator - Skip Bypass",
                      f"Task {current_task_id} is SKIPPED, bypassing goal validation",
                      metadata={
                          "task_id": current_task_id,
                          "skip_reason": current_task.execution_context.result if current_task.execution_context else "Pre-flight skip"
                      })
            # Task already has execution_context from classifier, just pass through
            return {
                "tasks": tasks,
                "executed_nodes": state.executed_nodes + ["subAGENT_goal_validator"],
            }
        elif current_task and current_task.status == "completed" and current_task.execution_context:
            prompt_generator = HierarchicalAgentPrompt()
            system_prompt, human_prompt = prompt_generator.generate_goal_achievement_prompt(
                original_goal=state.original_goal,
                plan_created="\n\n".join([
                    f"Task {t.task_id}:\n  - Description: {t.description}\n  - Tool: `{t.tool_name}`\n  - Status: {t.status}\n"
                    for t in tasks
                ]),
                task_description=current_task.description,
                tool_result=current_task.execution_context.result or "N/A",
                analysis=current_task.execution_context.analysis or "N/A"
            )

            model = ModelManager()
            response = model.invoke([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": human_prompt},
            ])

            validation_result = ModelManager.convert_to_json(response.content)

            if isinstance(validation_result, dict) and "goal_achieved" in validation_result:
                current_task.execution_context.goal_achieved = validation_result.get("goal_achieved", False)
                debug_info("Goal Validator",
                           f"Validation for Task {current_task_id}: Goal Achieved = {validation_result.get('goal_achieved')}, Reasoning: {validation_result.get('reasoning')}",
                           metadata={"function name": "__subAGENT_goal_validator", "task_id": current_task_id,
                                     "validation_result": validation_result})
                if not validation_result.get("goal_achieved"):
                    current_task.status = "failed"
                    # CRITICAL FIX: Preserve the original failed_parameters when creating new failure context
                    original_failed_parameters = current_task.execution_context.parameters if current_task.execution_context else None
                    original_strategy_history = current_task.failure_context.strategy_history.copy() if current_task.failure_context and current_task.failure_context.strategy_history else []

                    current_task.failure_context = FAILURE_CONTEXT(
                        error_message=f"Goal not achieved: {validation_result.get('reasoning', 'No reasoning provided.')}",
                        fail_count=(current_task.failure_context.fail_count + 1) if current_task.failure_context else 1,
                        error_type="GoalValidationFailure",
                        failed_parameters=original_failed_parameters,  # PRESERVE the original failed parameters
                        strategy_history=original_strategy_history,  # PRESERVE the strategy history too
                    )
                    # Persist validator feedback into pre_execution_context so retries and parameter generator see corrective hints
                    try:
                        if not getattr(current_task, 'required_context', None):
                            current_task.required_context = REQUIRED_CONTEXT(source_node="subAGENT_goal_validator")
                        ctx = current_task.required_context.pre_execution_context or {}
                        failed_feedback = ctx.get("failed_tasks_with_validator_feedback", [])
                        failed_feedback.append({
                            "task_id": current_task.task_id,
                            "tool_name": current_task.tool_name,
                            "failure_reason": validation_result.get("reasoning", "No reasoning provided."),
                            "validator_payload": validation_result,
                        })
                        ctx["failed_tasks_with_validator_feedback"] = failed_feedback
                        ctx.setdefault("original_goal", state.original_goal)
                        current_task.required_context.pre_execution_context = ctx
                    except Exception:
                        # Defensive: avoid raising from validator persistence
                        pass
            else:
                debug_warning("Goal Validator",
                              f"Invalid response from validation LLM for Task {current_task_id}. Defaulting to goal not achieved.",
                              metadata={"function name": "__subAGENT_goal_validator", "task_id": current_task_id,
                                        "llm_response": response.content})
                current_task.execution_context.goal_achieved = False
                current_task.status = "failed"
                # CRITICAL FIX: Preserve the original failed_parameters here too
                original_failed_parameters = current_task.execution_context.parameters if current_task.execution_context else None
                original_strategy_history = []
                if current_task.failure_context:
                    original_strategy_history = current_task.failure_context.strategy_history or []

                current_task.failure_context = FAILURE_CONTEXT(
                    error_message="Failed to validate goal achievement due to invalid LLM response.",
                    fail_count=(current_task.failure_context.fail_count + 1) if current_task.failure_context else 1,
                    error_type="GoalValidationFailure",
                    failed_parameters=original_failed_parameters,  # PRESERVE the original failed parameters
                    strategy_history=original_strategy_history,  # PRESERVE the strategy history too
                )

        return {"tasks": tasks, "executed_nodes": state.executed_nodes + ["subAGENT_goal_validator"]}

    @classmethod
    def __subAGENT_error_fallback(cls, state: "WorkflowStateModel") -> dict:
        ## todo shifting fallback to use enhanced helper - pending
        """Handle task failures with a tiered, state-driven recovery system."""
        AgentStatusUpdater.update_status("error_recovery", task_id=state.current_task_id)
        debug_info("--- NODE: Error Fallback ---", "Handling task failure with tiered recovery strategies",
                   metadata={"function name": "__subAGENT_error_fallback"})
        current_task_id = state.current_task_id
        updated_tasks = state.tasks
        current_task: TASK = next((task for task in updated_tasks if task.task_id == current_task_id), None)

        if not current_task or not current_task.failure_context:
            return {"tasks": updated_tasks, "executed_nodes": state.executed_nodes + ["subAGENT_error_fallback"]}

        def give_up(reason: str) -> dict:
            # 'failed' always routes back here, so a task we cannot recover is skipped
            # (terminal for the planner/finalizer) instead of looping until the recursion limit
            current_task.status = "skip"
            if current_task.execution_context is None:
                current_task.execution_context = EXECUTION_CONTEXT(tool_name=current_task.tool_name, parameters={})
            current_task.execution_context.goal_achieved = False
            current_task.execution_context.result = f"⏭️ Task abandoned after failed recovery: {reason}"
            current_task.execution_context.analysis = (
                f"Task failed ({current_task.failure_context.error_message}) and could not be recovered: {reason}"
            )
            debug_warning("Error Fallback", f"Giving up on task {current_task_id}: {reason}",
                          metadata={"function name": "__subAGENT_error_fallback", "task_id": current_task_id})
            return {"tasks": updated_tasks, "executed_nodes": state.executed_nodes + ["subAGENT_error_fallback"]}

        if current_task.failure_context.recovery_attempts >= cls.MAX_RECOVERY_ATTEMPTS:
            return give_up(f"{current_task.failure_context.recovery_attempts} recovery attempts exhausted")
        if current_task.failure_context.fail_count > cls.MAX_TASK_FAILURES:
            return give_up(f"task failed {current_task.failure_context.fail_count} times")
        current_task.failure_context.recovery_attempts += 1

        # todo here the enhancement start to use the new helper
        # 1. DELEGATE to the new, intelligent helper
        recovery_decision = AgentCoreHelpers.EnhancedErrorFallbackHelpers.decide_recovery_strategy(current_task, state)
        strategy = recovery_decision.get("recovery_strategy", None)  # <-- Use the strategy from the helper
        # Canonicalize strategy names from LLM to internal enums
        if not strategy:
            reasoning = recovery_decision.get("reasoning", "No viable recovery strategy identified.")
            current_task.failure_context.strategy_history.append(
                FAILURE_CONTEXT_STRATEGY(
                    recovery_strategy="NO_STRATEGY",
                    reasoning=reasoning,
                    outcome="NOT_APPLIED",
                    details={"description": current_task.description,
                             "error_message": getattr(current_task.failure_context, "error_message", None)}
                )
            )
            return give_up(reasoning)
        # 2. ACT on the strategic decision
        try:
            if strategy == "PARAMETER_REPAIR":
                is_repaired, new_params = AgentCoreHelpers.ErrorFallbackHelpers.attempt_parameter_repair(current_task,
                                                                                                         state)
                if is_repaired:
                    # Ensure execution_context exists before assigning parameters
                    if current_task.execution_context is None:
                        current_task.execution_context = EXECUTION_CONTEXT(
                            tool_name=current_task.tool_name,
                            parameters={},
                        )
                    else:
                        # Keep tool_name in sync in case it changed elsewhere
                        current_task.execution_context.tool_name = current_task.tool_name
                    current_task.execution_context.parameters = new_params
                    current_task.status = "pending"
                    current_task.failure_context.strategy_history.append(
                        FAILURE_CONTEXT_STRATEGY(
                            recovery_strategy="PARAMETER_REPAIR",
                            reasoning=recovery_decision.get("reasoning",
                                                            "Parameters repaired based on failure context."),
                            outcome="APPLIED",
                            details={
                                "repaired_parameters": new_params,
                                "description": current_task.description,
                                "error_message": getattr(current_task.failure_context, "error_message", None)
                            }
                        )
                    )
                else:
                    current_task.status = "failed"
            elif strategy == "ALTERNATIVE_TOOL":
                new_tool = AgentCoreHelpers.ErrorFallbackHelpers.find_alternative_tool(current_task, state)
                if new_tool:
                    current_task.tool_name = new_tool
                    # 🚨 CRITICAL FIX: DO NOT reset parameters to {} - preserve failure_context for parameter generator
                    if current_task.execution_context is None:
                        current_task.execution_context = EXECUTION_CONTEXT(tool_name=new_tool, parameters={})
                    else:
                        # Preserve the failed parameters in failure_context - DO NOT reset to empty dict
                        current_task.execution_context.tool_name = new_tool
                        # 🚨 KEY FIX: Keep parameters empty but ensure failure_context is preserved
                        # The parameter generator will use failure_context.failed_parameters to avoid repetition
                        current_task.execution_context.parameters = {}
                        current_task.execution_context.result = None
                        current_task.execution_context.analysis = None
                        current_task.execution_context.goal_achieved = False
                    current_task.status = "pending"
                    current_task.failure_context.strategy_history.append(
                        FAILURE_CONTEXT_STRATEGY(
                            recovery_strategy="ALTERNATIVE_TOOL",
                            reasoning=recovery_decision.get("reasoning", "Alternative tool suggested by LLM."),
                            outcome="APPLIED",
                            details={"alternative_tool": new_tool, "description": current_task.description,
                                     "error_message": getattr(current_task.failure_context, "error_message", None)}
                        )
                    )
                else:
                    # Record no-op attempt for observability
                    current_task.failure_context.strategy_history.append(
                        FAILURE_CONTEXT_STRATEGY(
                            recovery_strategy="ALTERNATIVE_TOOL",
                            reasoning=recovery_decision.get("reasoning", "Alternative tool suggested by LLM."),
                            outcome="NOT_APPLIED",
                            details={"alternative_tool": None, "description": current_task.description,
                                     "error_message": getattr(current_task.failure_context, "error_message", None)}
                        )
                    )
                    current_task.status = "failed"

            elif strategy == "TASK_DECOMPOSITION":
                # Build parent context with completed tasks and failure context
                completed_tasks = [t for t in updated_tasks if
                                   t.status == "completed" and t.execution_context and t.execution_context.result]
                current_task.status = "skip"  # Mark as like this while we handle decomposition
                # this is the issue it passes the only last strategy context
                parent_context = {
                    "original_goal": state.original_goal,
                    "completed_tasks_history": completed_tasks,
                    "workflow_progress": f"{len(completed_tasks)}/{len(updated_tasks)} tasks completed",
                    "failed_task_context": {
                        "task_id": current_task.task_id,
                        "description": current_task.description,
                        "failure_reason": current_task.failure_context.error_message,
                        "fail_count": current_task.failure_context.fail_count,
                        "error_type": current_task.failure_context.error_type,
                        "failed_parameters": current_task.failure_context.failed_parameters,
                        "strategy_history": current_task.failure_context.strategy_history,
                    }
                }
                parent_context_str = (
                    f"Original Goal: {parent_context['original_goal']}\n"
                    f"Workflow Progress: {parent_context['workflow_progress']}\n"
                    f"Completed Tasks: {[f'Task {t.task_id}: {t.description}' for t in parent_context['completed_tasks_history']]}\n"
                    f"FAILED TASK CONTEXT:\n"
                    f"- Task ID: {parent_context['failed_task_context']['task_id']}\n"
                    f"- Description: {parent_context['failed_task_context']['description']}\n"
                    f"- Failure Reason: {parent_context['failed_task_context']['failure_reason']}\n"
                    f"- Fail Count: {parent_context['failed_task_context']['fail_count']}\n"
                    f"- Error Type: {parent_context['failed_task_context']['error_type']}\n"
                    f"- LAST Failed Parameters: {parent_context['failed_task_context']['failed_parameters']}\n"
                    f"**FAILED FULL HISTORY NEVER IGNORE THIS ***\n"
                    f" \n".join(
                        [f"  {idx + 1}. Strategy: {s.recovery_strategy}, Outcome: {s.outcome}, Reasoning: {s.reasoning}"
                         for idx, s in enumerate(parent_context['failed_task_context']['strategy_history'])])
                )

                # this needs to be got more verbose like what error we are facing and how to decompose such that,
                # we would be able to pass the last finding to next higher task
                detailed_spawn_reason = \
                    f"""
                      --- RECOVERY MANDATE: TASK DECOMPOSITION ---
                    
                      A task has failed, and the chosen recovery strategy is to decompose it into a new, investigative plan.
                    
                      Original User Goal:
                      {state.original_goal}
                    
                      Failed Task Details:
                      - Task Description: {current_task.description}
                      - Failed Tool: {current_task.tool_name}
                      - Failed Parameters: {current_task.failure_context.failed_parameters}
                    
                      Failure Analysis:
                      - Error Type: {current_task.failure_context.error_type}
                      - Error Message: {current_task.failure_context.error_message}
                    
                      Recovery Plan from Strategist:
                      - Chosen Strategy: {recovery_decision.get('recovery_strategy')}
                      - Strategist's Reasoning: {recovery_decision.get('reasoning')}
                      - Plan to Execute: {recovery_decision.get('next_steps')}
                    
                      Your Mission:
                      Your only job is to convert the 'Plan to Execute' above into a precise, executable list of new sub-tasks. Do not re-evaluate the strategy
                      or the original task. Your purpose is to implement the recovery plan exactly as specified.
                    """

                # there is we are adding the artificial tasks to TASK DECOMPOSER work on that
                sub_tasks:list[TASK] = AgentCoreHelpers.ErrorFallbackHelpers.convert_decision_task(
                    [parent_context_str, detailed_spawn_reason],
                    str(AgentCoreHelpers.recommend_tools_for_task(current_task.description))
                    , current_task)

                # insert that artificial TASKS created by the parser
                parent_task_idx = next((i for i, t in enumerate(state.tasks) if t.task_id == current_task.task_id), None)
                # insertion logic
                state.tasks = state.tasks[:parent_task_idx + 1] + sub_tasks + state.tasks[parent_task_idx + 1:]

                spawn_result = Spawn_subAgent.spawn_subAgent_recursive(state, sub_tasks[0],
                                                                    detailed_spawn_reason,
                                                                    parent_context_str,
                                                                    recovery_plan=recovery_decision.get(
                                                                    "recovery_plan"))
                if spawn_result.get("spawn_triggered"):
                    current_task.failure_context.strategy_history.append(
                        FAILURE_CONTEXT_STRATEGY(
                            recovery_strategy="TASK_DECOMPOSITION",
                            reasoning=recovery_decision.get("reasoning", "Decomposition suggested by LLM."),
                            outcome="APPLIED",
                            details={"spawned_subtasks": [t.tool_name for t in spawn_result["tasks"] if
                                                          t.task_id != current_task.task_id],
                                     "description": current_task.description,
                                     "error_message": getattr(current_task.failure_context, "error_message", None)}
                        )
                    )
                    return {
                        "tasks": spawn_result["tasks"],
                        "current_task_id": spawn_result["current_task_id"],
                        "executed_nodes": state.executed_nodes + ["subAGENT_error_fallback"],
                    }
                else:
                    current_task.status = "failed"

            elif strategy == "SKIP":
                current_task.status = "skip"
                current_task.execution_context = EXECUTION_CONTEXT(
                    tool_name=current_task.tool_name,
                    parameters={},
                    result="Task skipped as per recovery strategy.",
                    analysis="Task was skipped to allow workflow progression.",
                    goal_achieved=False,

                )

                current_task.failure_context.strategy_history.append(
                    FAILURE_CONTEXT_STRATEGY(
                        recovery_strategy="SKIP",
                        reasoning=recovery_decision.get("reasoning", "Skipping task as per recovery strategy."),
                        confidence_level=recovery_decision.get("confidence_level", "HIGH"),
                        estimated_success_probability=recovery_decision.get("estimated_success_probability", 0),
                        next_steps=recovery_decision.get("next_steps", "task got skipped as per strategy"),
                        outcome="APPLIED",
                        details={"description": current_task.description,
                                 "error_message": getattr(current_task.failure_context, "error_message", None)}
                    )
                )

                return {
                    "tasks": updated_tasks,
                    "executed_nodes": state.executed_nodes + ["subAGENT_error_fallback"],
                }
            else:
                current_task.status = "failed"

        except Exception as e:
            debug_error("Error Fallback", f"Error during LLM recovery processing: {e}",
                        metadata={"function name": "__subAGENT_error_fallback", "task_id": current_task_id,
                                  "exception": str(e)})
            current_task.status = "failed"
            current_task.failure_context.error_message += f" | Error during recovery processing: {e}"

        return {"tasks": updated_tasks, "executed_nodes": state.executed_nodes + ["subAGENT_error_fallback"]}

    @classmethod
    def __subAGENT_task_planner(cls, state: "WorkflowStateModel") -> dict:
        """📋 WORKFLOW ORCHESTRATOR: Manages task progression and parent-child relationships.
        🆕 DUAL CONTEXT BRIDGE: Passes both raw results and synthesized analysis to the next task.

        This node implements sophisticated logic for hierarchical task management:

        PARENT-CHILD LOGIC:
        - Monitors spawned sub-tasks (float IDs like 1.1, 1.2) for completion
        - Updates parent task status based on sub-task results
        - Handles both success (all sub-tasks complete) and failure scenarios

        TASK SELECTION WITH DUAL CONTEXT BRIDGE:
        - Finds next pending task in priority order (sorted by task_id)
        - 🆕 COLLECTS the full history of completed TASK objects.
        - 🆕 INJECTS this history (containing both raw `.result` and summarized `.analysis`) into the next task.
        - This prevents infinite loops by giving the next LLM clean, summarized context for decision-making, while preserving the full raw data for tools that need it.
        - Returns None when no more tasks remain (triggers finalizer).

        This is where the hierarchical magic happens - parent tasks are only
        considered complete when their spawned sub-tasks finish successfully.
        """
        debug_info("--- NODE: Task Planner ---", "Managing task progression and parent-child relationships",
                   metadata={"function name": "__subAGENT_task_planner"})

        tasks = state.tasks
        last_completed_id = state.current_task_id

        # If the last completed task was a sub-task (e.g., '1.1-abc'), update its parent
        if isinstance(last_completed_id, str) and '-' in last_completed_id:  # Check for new string format
            # Extract parent_id from string, e.g., '1' from '1.1-abc'
            parent_id_prefix = last_completed_id.rsplit('.')[0] # immediate parent before dot
            parent_task = next((t for t in tasks if str(t.task_id) == parent_id_prefix), None)  # Find parent by prefix
            if parent_task and parent_task.status == "in_progress":
                # Find sibling tasks that share the same parent prefix
                sibling_tasks = [t for t in tasks if
                                 isinstance(t.task_id, str) and t.task_id.startswith(f"{parent_id_prefix}.")]
                # 🔥 Include skip in terminal states to handle skipped sub-tasks
                TERMINAL_STATES = ["completed", "failed", "skip"]
                if all(t.status in TERMINAL_STATES for t in sibling_tasks):
                    failed_subtasks = [t for t in sibling_tasks if t.status == "failed"]
                    skipped_subtasks = [t for t in sibling_tasks if t.status == "skip"]
                    if not parent_task.execution_context:
                        parent_task.execution_context = EXECUTION_CONTEXT(
                            tool_name=parent_task.tool_name,
                            parameters={},
                        )
                    if failed_subtasks:
                        parent_task.status = "failed"
                        skip_msg = f", {len(skipped_subtasks)} skipped" if skipped_subtasks else ""
                        parent_task.execution_context.analysis = f"Failed due to {len(failed_subtasks)} failed subtasks{skip_msg}."
                    else:
                        parent_task.status = "completed"
                        completed_count = len([t for t in sibling_tasks if t.status == "completed"])
                        skip_msg = f" ({len(skipped_subtasks)} skipped)" if skipped_subtasks else ""
                        parent_task.execution_context.analysis = f"Successfully completed {completed_count} of {len(sibling_tasks)} subtasks{skip_msg}."

        # 🌉 DUAL CONTEXT BRIDGE: Collect the full history of completed tasks AND failed tasks with validator feedback
        completed_tasks = [t for t in tasks if t.status == "completed"]
        failed_tasks_with_context = [t for t in tasks if
                                     t.status == "failed" and t.failure_context and t.failure_context.error_type == "GoalValidationFailure"]

        # Find the next pending task
        pending_tasks = sorted([t for t in tasks if t.status == "pending"], key=lambda x: x.task_id)

        next_task_id = None
        if pending_tasks:
            next_task = pending_tasks[0]
            next_task_id = next_task.task_id

            # 🆕 INJECT DUAL CONTEXT: Pass the *entire list* of completed TASK objects AND validator feedback from failed tasks.
            # This gives the next node access to both raw .result and summarized .analysis from completed tasks,
            # PLUS validator reasoning from failed tasks to avoid repeating the same mistakes.
            # We also include the original goal for full context.
            accumulated_context = {
                "original_goal": state.original_goal,
                "completed_tasks_history": completed_tasks,
                "failed_tasks_with_validator_feedback": failed_tasks_with_context,
            }

            next_task.required_context.pre_execution_context = accumulated_context

            debug_info("Context Bridge",
                       f"Injected context from {len(completed_tasks)} completed tasks into Task {next_task_id}",
                       metadata={"function name": "__subAGENT_task_planner", "next_task_id": next_task_id,
                                 "completed_tasks_count": len(completed_tasks)})

        return {
            "current_task_id": next_task_id,
            "executed_nodes": state.executed_nodes + ["subAGENT_task_planner"],
            "tasks": tasks,
        }

    @classmethod
    def __subAGENT_finalizer(cls, state: "WorkflowStateModel") -> dict:
        """Generate final response consolidating all task results."""
        # print_log_message("--- NODE: Finalizer ---", "Finalizer")
        debug_info("--- NODE: Finalizer ---", "Generating final response consolidating all task results",
                   metadata={"function name": "__subAGENT_finalizer"})

        tasks = state.tasks

        # 🔥 CATEGORIZE tasks by status for clear visibility and skip awareness
        completed_tasks = [t for t in tasks if t.status == "completed"]
        failed_tasks = [t for t in tasks if t.status == "failed"]
        skipped_tasks = [t for t in tasks if t.status == "skip"]

        # Debug system_logging with skip statistics
        debug_info("Finalizer - Task Summary",
                   f"Workflow completed: {len(completed_tasks)} completed, {len(skipped_tasks)} skipped, {len(failed_tasks)} failed",
                   metadata={
                       "function name": "__subAGENT_finalizer",
                       "completed_count": len(completed_tasks),
                       "skipped_count": len(skipped_tasks),
                       "failed_count": len(failed_tasks),
                       "total_count": len(tasks),
                       "completion_rate": f"{len(completed_tasks)/len(tasks)*100:.1f}%" if tasks else "0%",
                       "skip_rate": f"{len(skipped_tasks)/len(tasks)*100:.1f}%" if tasks else "0%"
                   })

        # Build categorized results with clear status indicators
        all_results = []

        # ✅ COMPLETED TASKS - Show successful task outcomes
        if completed_tasks:
            all_results.append(f"\n✅ COMPLETED TASKS ({len(completed_tasks)}/{len(tasks)} total tasks):")
            for task in completed_tasks:
                if task.execution_context and task.execution_context.result:
                    # Clean up the task result to remove raw Python representations
                    result_content = task.execution_context.result

                    # If the result contains Python list/dict representations, clean them up
                    try:
                        import json as _json
                        # Try to extract just the meaningful content from MCP tool responses
                        if isinstance(result_content, str) and result_content.startswith("✅ **Action"):
                            # Extract the actual result from the MCP response format
                            if "Result: [{'type': 'text', 'text':" in result_content:
                                # Extract the text content from the MCP response format
                                import re
                                text_match = re.search(r"'text':\s*'([^']+)'", result_content)
                                if text_match:
                                    extracted_text = text_match.group(1)
                                    # Unescape newlines and clean up
                                    extracted_text = extracted_text.replace('\n', '\n').replace("\'", "'")
                                    result_content = extracted_text

                        all_results.append(f"  • Task {task.task_id} ({task.tool_name}): {result_content}")
                    except Exception:
                        # Fallback to original content if parsing fails
                        all_results.append(f"  • Task {task.task_id} ({task.tool_name}): {task.execution_context.result}")

        # ⏭️ SKIPPED TASKS - Explicitly highlight skipped tasks with reasons
        if skipped_tasks:
            all_results.append(f"\n⏭️ SKIPPED TASKS ({len(skipped_tasks)}/{len(tasks)} total tasks):")
            for task in skipped_tasks:
                if task.execution_context and task.execution_context.result:
                    # Skip result already formatted as "⏭️ Task skipped: reason" from error_fallback
                    skip_reason = task.execution_context.result
                    all_results.append(f"  • Task {task.task_id} ({task.tool_name}): {skip_reason}")
                else:
                    # Fallback if execution_context somehow missing
                    all_results.append(f"  • Task {task.task_id} ({task.tool_name}): ⏭️ Skipped (reason unknown)")

        # ❌ FAILED TASKS - Show task failures
        if failed_tasks:
            all_results.append(f"\n❌ FAILED TASKS ({len(failed_tasks)}/{len(tasks)} total tasks):")
            for task in failed_tasks:
                error_message = task.failure_context.error_message if task.failure_context else "Unknown error"
                all_results.append(f"  • Task {task.task_id} ({task.tool_name}): {error_message}")

        prompt_generator = HierarchicalAgentPrompt()
        system_prompt, human_prompt = prompt_generator.generate_final_response_prompt(
            all_results, state.original_goal,
        )

        model = ModelManager()
        response = model.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": human_prompt},
        ])

        raw = response.content

        # Try to convert LLM output into JSON using ModelManager helper
        parsed = None
        try:
            parsed = ModelManager.convert_to_json(raw)
        except Exception:
            parsed = None

        # If parsed is a dict matching the expected finalizer schema, return it directly.
        def is_valid_final_schema(obj) -> bool:
            if not isinstance(obj, dict):
                return False
            if "user_response" in obj and isinstance(obj["user_response"], dict) and isinstance(
                    obj["user_response"].get("message"), str):
                # Ensure analysis keys exist (maybe empty strings)
                if "analysis" in obj and isinstance(obj["analysis"], dict):
                    return True
            return False

        # If we got any parsed JSON from the LLM, consider it a successful LLM response.
        if parsed is not None:
            final_response_obj = parsed
            # Determine overall workflow status based on task outcomes (with skip awareness)
            any_failed = any(getattr(t, 'status', None) == 'failed' for t in tasks)
            any_goal_false = any(
                (t.status == 'completed' and t.execution_context and t.execution_context.goal_achieved is False)
                for t in tasks
            )
            any_skipped = any(getattr(t, 'status', None) == 'skip' for t in tasks)

            # Enhanced status determination with skip awareness
            if any_failed or any_goal_false:
                workflow_status = "FAILED"
            elif any_skipped and len(completed_tasks) > 0:
                workflow_status = "COMPLETED_WITH_SKIPS"  # Partial success - some tasks completed, some skipped
            elif any_skipped and len(completed_tasks) == 0:
                workflow_status = "ALL_SKIPPED"  # Nothing accomplished - all tasks skipped
            else:
                workflow_status = "COMPLETED"  # Full success - all tasks completed
            debug_info("Finalizer", "LLM produced parsable JSON. Returning parsed object as final_response.",
                       metadata={"function name": "__subAGENT_finalizer", "parsed_preview": str(parsed)[:200],
                                 "workflow_status": workflow_status})
            return {
                "final_response": final_response_obj,
                "final_response_source": "llm",
                "workflow_status": workflow_status,
                "executed_nodes": state.executed_nodes + ["subAGENT_finalizer"],
            }

        # If not valid JSON, attempt to repair by asking the model to convert its previous output into the exact schema.
        try:
            repair_system = "You are a JSON fixer. Convert the provided text into a JSON object that exactly matches the required schema. Return ONLY the JSON object."
            repair_human = (
                "The original assistant output is:\n\n"
                f"{raw}\n\n\n"
                "Now convert the above into a JSON object matching this schema exactly:\n"
                "{\n"
                '  "user_response": {\n'
                '    "message": "string",\n'
                '    "next_steps": "string"\n'
                '  },\n'
                '  "analysis": {\n'
                '    "issues": "string",\n'
                '    "reason": "string"\n'
                '  }\n'
                "}\n\nReturn only the JSON object, nothing else."
            )

            model = ModelManager()
            repair_resp = model.invoke([
                {"role": "system", "content": repair_system},
                {"role": "user", "content": repair_human},
            ])
            repaired = None
            try:
                repaired = ModelManager.convert_to_json(repair_resp.content)
            except Exception:
                repaired = None

            if repaired is not None:
                final_response_obj = repaired
                # Determine overall workflow status based on task outcomes (with skip awareness)
                any_failed = any(getattr(t, 'status', None) == 'failed' for t in tasks)
                any_goal_false = any(
                    (t.status == 'completed' and t.execution_context and t.execution_context.goal_achieved is False)
                    for t in tasks
                )
                any_skipped = any(getattr(t, 'status', None) == 'skip' for t in tasks)

                # Enhanced status determination with skip awareness
                if any_failed or any_goal_false:
                    workflow_status = "FAILED"
                elif any_skipped and len(completed_tasks) > 0:
                    workflow_status = "COMPLETED_WITH_SKIPS"  # Partial success
                elif any_skipped and len(completed_tasks) == 0:
                    workflow_status = "ALL_SKIPPED"  # Nothing accomplished
                else:
                    workflow_status = "COMPLETED"  # Full success
                debug_info("Finalizer", "Repaired final response successfully and returning as final_response.",
                           metadata={"function name": "__subAGENT_finalizer", "response_preview": str(repaired)[:200],
                                     "workflow_status": workflow_status})
                return {
                    "final_response": final_response_obj,
                    "final_response_source": "llm_repaired",
                    "workflow_status": workflow_status,
                    "executed_nodes": state.executed_nodes + ["subAGENT_finalizer"],
                }
        except Exception as e:
            debug_warning("Finalizer", f"JSON repair attempt failed: {e}",
                          metadata={"function name": "__subAGENT_finalizer", "exception": str(e)})

        # As a last resort, build a fallback wrapped schema so the caller can reliably extract a message.
        final_text = None
        try:
            if isinstance(parsed, (dict, list)):
                import json as _json
                final_text = _json.dumps(parsed, ensure_ascii=False, indent=2)
            else:
                final_text = str(raw)
        except Exception:
            final_text = str(raw)

        debug_info("Finalizer", f"Final Response (fallback text): {final_text}",
                   metadata={"function name": "__subAGENT_finalizer", "response_preview_length": len(final_text)})

        # Wrap fallback text into the exact schema so the caller can reliably extract
        # a human-friendly message. This guarantees the agent_node can always display
        # something meaningful to the user even if the LLM didn't return the strict schema.
        try:
            final_response_obj = {
                "user_response": {
                    "message": str(final_text),
                    "next_steps": "",
                },
                "analysis": {
                    "issues": "",
                    "reason": "",
                },
            }
        except Exception:
            # Ensure we never return None
            final_response_obj = {
                "user_response": {"message": "No response generated from workflow.", "next_steps": ""},
                "analysis": {"issues": "", "reason": ""},
            }

        debug_info("Finalizer", "Returning wrapped fallback final response as structured JSON schema",
                   metadata={"function name": "__subAGENT_finalizer",
                             "response_preview": str(final_response_obj)[0:200]})

        return {
            "final_response": final_response_obj,
            "final_response_source": "fallback",
            "workflow_status": "FAILED",
            "executed_nodes": state.executed_nodes + ["subAGENT_finalizer"],
        }

    # =================================================================
    # Graph Routing Logic
    # =================================================================

    @classmethod
    def __router_after_execution(cls, state: "WorkflowStateModel") -> Literal[
        "subAGENT_classifier", "subAGENT_task_planner", "subAGENT_finalizer"]:
        """Routes after a task execution. Decides whether to retry, plan the next task, or finalize.
        This is a critical routing function that enables the retry loop.
        """
        # print_log_message("--- ROUTER: After Execution ---", "Router")
        debug_info("--- ROUTER: After Execution ---", "Routing after task execution based on task status",
                   metadata={"function name": "__router_after_execution"})
        current_task_id = state.current_task_id
        tasks = state.tasks
        current_task = next((t for t in tasks if t.task_id == current_task_id), None)

        if current_task and current_task.status == "failed":
            # If the task failed, route back to the classifier to decide on a retry or fallback.
            # This creates the crucial "retry loop".
            # print_log_message(f"Task {current_task_id} failed. Routing to classifier for retry/fallback.", "Router")
            debug_info("Router", f"Task {current_task_id} failed. Routing to classifier for retry/fallback.",
                       metadata={"function name": "__router_after_execution", "task_id": current_task_id,
                                 "task_status": current_task.status})
            return "subAGENT_classifier"

        # If the task succeeded, check if there are more pending tasks.
        pending_tasks = [t for t in tasks if t.status == "pending"]
        if not pending_tasks:
            # If no more pending tasks, it's time to finalize the workflow.
            # print_log_message("All tasks completed. Routing to finalizer.", "Router")
            debug_info("Router", "All tasks completed. Routing to finalizer.",
                       metadata={"function name": "__router_after_execution"})
            return "subAGENT_finalizer"

        # If there are more pending tasks, route to the planner to select the next one.
        # print_log_message("Task completed. Routing to task planner for next task.", "Router")
        debug_info("Router", "Task completed. Routing to task planner for next task.",
                   metadata={"function name": "__router_after_execution"})
        return "subAGENT_task_planner"

    @classmethod
    def __router_classifier(cls, state: "WorkflowStateModel") -> Literal[
        "subAGENT_parameter_generator", "subAGENT_error_fallback"]:
        """Route to parameter generation or error fallback."""
        # print_log_message("--- ROUTER: Classifier ---", "Router")
        debug_info("--- ROUTER: Classifier ---", "Routing based on classifier decision",
                   metadata={"function name": "__router_classifier"})
        if state.persona == "AGENT_PERFORM_ERROR_FALLBACK":
            return "subAGENT_error_fallback"
        return "subAGENT_parameter_generator"

    @classmethod
    def __router_task_planner(cls, state: "WorkflowStateModel") -> Literal["subAGENT_classifier", "subAGENT_finalizer"]:
        """Route from task planner to either classifier or finalizer."""
        # print_log_message("--- ROUTER: Task Planner ---", "Router")
        debug_info("--- ROUTER: Task Planner ---", "Routing based on task planner decision",
                   metadata={"function name": "__router_task_planner"})
        # Check if all tasks are in terminal states (completed, failed, OR skip)
        tasks = state.tasks
        TERMINAL_STATES = ["completed", "failed", "skip"]  # 🔥 Include skip to prevent workflow hangs
        all_tasks_finished = all(t.status in TERMINAL_STATES for t in tasks)

        if all_tasks_finished:
            return "subAGENT_finalizer"
        return "subAGENT_classifier"

    @classmethod
    def build_graph(cls):
        """🏗️ LANGGRAPH WORKFLOW BUILDER: Constructs the complete hierarchical agent workflow.

        This method creates a sophisticated 7-node state machine that handles:
        - Dynamic task planning with tool pre-filtering
        - Intelligent task execution with spawning capabilities
        - Advanced error recovery with spawning-based recovery
        - Parent-child task relationship management
        - Schema-aware parameter generation
        - Comprehensive result finalization

        WORKFLOW ARCHITECTURE:
        Entry → initial_planner → classifier → [parameter_generator|error_fallback]
              → task_executor → [task_planner|finalizer] → classifier → ... → END

        The conditional routing enables sophisticated decision-making while maintaining
        clean separation of concerns and full observability throughout execution.
        """
        from langgraph.graph import StateGraph

        graph_builder = StateGraph(state_schema=WorkflowStateModel)

        # 🏗️ NODE REGISTRATION: Add all workflow nodes
        graph_builder.add_node("subAGENT_initial_planner", cls.__subAGENT_initial_planner)
        graph_builder.add_node("subAGENT_classifier", cls.__subAGENT_classifier)
        graph_builder.add_node("subAGENT_parameter_generator", cls.subAGENT_parameter_generator)
        graph_builder.add_node("subAGENT_task_executor", cls.__subAGENT_task_executor)
        graph_builder.add_node("subAGENT_context_synthesizer", cls.__subAGENT_context_synthesizer)
        graph_builder.add_node("subAGENT_goal_validator", cls.__subAGENT_goal_validator)  # New node
        graph_builder.add_node("subAGENT_error_fallback", cls.__subAGENT_error_fallback)
        graph_builder.add_node("subAGENT_task_planner", cls.__subAGENT_task_planner)
        graph_builder.add_node("subAGENT_finalizer", cls.__subAGENT_finalizer)

        # 🚀 WORKFLOW DEFINITION: Set entry point and routing
        graph_builder.set_entry_point("subAGENT_initial_planner")
        graph_builder.add_edge("subAGENT_initial_planner", "subAGENT_classifier")

        # 🎯 CONDITIONAL ROUTING: Dynamic decision-making based on task state
        graph_builder.add_conditional_edges(
            "subAGENT_classifier",
            cls.__router_classifier,
            {
                "subAGENT_parameter_generator": "subAGENT_parameter_generator",
                "subAGENT_error_fallback": "subAGENT_error_fallback",
            },
        )

        graph_builder.add_edge("subAGENT_parameter_generator", "subAGENT_task_executor")

        # MODIFIED: The executor and fallback now route to the new synthesizer node
        graph_builder.add_edge("subAGENT_task_executor", "subAGENT_context_synthesizer")
        graph_builder.add_edge("subAGENT_error_fallback", "subAGENT_classifier")

        # The synthesizer then routes to the new goal validator
        graph_builder.add_edge("subAGENT_context_synthesizer", "subAGENT_goal_validator")

        # The goal validator then routes to the main "after execution" router
        graph_builder.add_conditional_edges(
            "subAGENT_goal_validator",
            cls.__router_after_execution,
            {
                "subAGENT_classifier": "subAGENT_classifier",
                "subAGENT_task_planner": "subAGENT_task_planner",
                "subAGENT_finalizer": "subAGENT_finalizer",
            },
        )

        graph_builder.add_conditional_edges(
            "subAGENT_task_planner",
            cls.__router_task_planner,
            {
                "subAGENT_classifier": "subAGENT_classifier",
                "subAGENT_finalizer": "subAGENT_finalizer",
            },
        )
        graph_builder.add_edge("subAGENT_finalizer", END)

        return graph_builder.compile()


# ================================================================================================================ 
# HIERARCHICAL SUB-AGENT SPAWNING AND ROUTING LOGIC 
# ================================================================================================================ 

# The Spawn_subAgent class implements the "Progressive Refinement" pattern: 
# 
# CORE CONCEPT: When a task is too complex for direct execution, dynamically create 
# specialized sub-agents that break the problem into smaller, atomic operations. 
# 
# SPAWNING TRIGGERS: 
# 1. COMPLEXITY ANALYSIS: LLM determines task needs decomposition 
# 2. ERROR RECOVERY: Task fails multiple times, spawn recovery agent 
# 3. TOOL MISMATCH: Task requires tools not in the pre-filtered set 
# 
# SPAWNING PROCESS: 
# 1. analyze_spawn_requirement() → Should we spawn? (LLM decision) 
# 2. decompose_task_for_subAgent() → Break into sub-tasks (with tool pre-filtering) 
# 3. inject_subAgent_into_workflow() → Insert sub-tasks into main workflow 
# 4. spawn_subAgent_recursive() → Orchestrate the entire process
#
# SUB-TASK ID SYSTEM: 
# - Parent task: 1, 2, 3, etc. 
# - Sub-tasks: 1.1, 1.2, 1.3, etc. (float IDs) 
# - Sub-sub-tasks: 1.1.1, 1.1.2, etc. (recursive spawning) 
# 
# TOOL PRE-FILTERING INTEGRATION: 
# - Each spawning operation uses tool recommendation system 
# - Sub-tasks are created with validated, relevant tools only 
# - Prevents tool hallucination in decomposed sub-tasks 
# - Maintains 90% token efficiency even in spawned contexts 
# ================================================================================================================ 


class Spawn_subAgent:
    """Handles the logic for dynamically decomposing a complex task into a series of smaller, atomic sub-tasks.
    This class embodies the "Progressive Refinement" pattern, allowing the agent to handle abstract goals.
    """

    @classmethod
    def analyze_spawn_requirement(cls, parent_task: TASK, reason: str, state: "WorkflowStateModel") -> dict:
        """Uses an LLM to analyze if a task is too complex and requires decomposition. 
        """
        debug_info("--- SPAWNER: Analyzing Task for sub-agent spawning ---",
                   f"Task ID: {parent_task.task_id}, Reason: {reason}",
                   metadata={"function name": "analyze_spawn_requirement", "task_id": parent_task.task_id,
                             "reason": reason})

        prompt_generator = HierarchicalAgentPrompt()
        tool_schema = AgentGraphCore.get_tool_schema(parent_task.tool_name)

        # 🚨 FIX: Pass the `reason` (which contains the Recovery Mandate) to the prompt generator.
        system_prompt, human_prompt = prompt_generator.generate_tool_schema_complexity_prompt(
            parent_task.description, parent_task.tool_name, tool_schema, parent_task.depth, parent_context=reason
        )

        model = ModelManager()
        response = model.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": human_prompt},
        ])
        analysis_result = ModelManager.convert_to_json(response.content)

        if not isinstance(analysis_result, dict) or "requires_decomposition" not in analysis_result:
            debug_warning("SubAgent Spawner",
                          "LLM failed to provide a valid spawn analysis. Defaulting to NO spawn.",
                          metadata={"function name": "analyze_spawn_requirement", "task_id": parent_task.task_id,
                                    "reason": reason})
            return {"should_spawn": False, "reasoning": "Fallback due to invalid LLM response."}

        debug_info("SubAgent Spawner", f"Spawn Analysis Result: {analysis_result.get('reasoning')}",
                   metadata={"function name": "analyze_spawn_requirement", "task_id": parent_task.task_id,
                             "reason": reason, "should_spawn": analysis_result.get("requires_decomposition"),
                             "reasoning": analysis_result.get("reasoning")})
        analysis_result["should_spawn"] = analysis_result.get("requires_decomposition", False)
        return analysis_result

    @classmethod
    def decompose_task_for_subAgent(cls, parent_task: TASK, state: "WorkflowStateModel", parent_context: str | None,
                                    recovery_plan: str | None = None) -> \
            list[TASK]:
        """Uses LLM to decompose a complex parent task into smaller, atomic sub-tasks.
        Enhanced with tool pre-filtering and context passing.
        FIX 2: Now implements discovery-first approach when parent task has failure context.
        """
        debug_info("--- SPAWNER: Decomposing Task into smaller tasks ---",
                   f"Task ID: {parent_task.task_id}",
                   metadata={"function name": "decompose_task_for_subAgent", "task_id": parent_task.task_id,
                             "description": parent_task.description, "tool_name": parent_task.tool_name,
                             "depth": parent_task.depth})

        try:
            if parent_task.depth < 1:
                # only if depth is 1 we can also modify the description to get better tool recommendations like add recommended tools of fallbacks
                recommended_tools = AgentCoreHelpers.recommend_tools_for_task(
                    f"Break down complex task: {parent_task.description}", max_tools=8, parent_context=parent_context
                )
            else:
                # if depth is more than 1, we get all the tools so that we don't limit the capabilities of sub-agents
                # FIX: Convert tool objects to tool names for consistent string comparison
                all_tools = AgentCoreHelpers.get_safe_tools_list()
                recommended_tools = [tool.name for tool in all_tools]

            # Ensure the virtual Collector tool is always allowed during decomposition
            if "perform_synthesis" not in recommended_tools:
                recommended_tools.append("perform_synthesis")

            available_tools_str = AgentCoreHelpers.get_detailed_tool_context(recommended_tools)
        except Exception as e:
            # This is a critical internal error, not just a planning choice.
            debug_error("SubAgent Spawner",
                        f"CRITICAL: Failed to generate sub-task prompt due to an internal error: {e}",
                        metadata={"function name": "decompose_task_for_subAgent", "task_id": parent_task.task_id,
                                  "exception_type": type(e).__name__, "exception": str(e)})
            return []  # Return empty list to signal decomposition failure to the caller.

        prompt_generator = HierarchicalAgentPrompt()

        # FIX 2: Pass parent failure context to prompt generator for better decomposition

        failure_context_info = None
        if parent_task.failure_context:
            # Format a concise string for the decomposition prompt
            try:
                fp_preview = (str(parent_task.failure_context.failed_parameters)[
                                  :300] + '...') if parent_task.failure_context.failed_parameters else 'None'
            except Exception:
                fp_preview = 'None'
            chain_part = f" | Chain: {parent_task.failure_context.parent_failure_chain}" if getattr(
                parent_task.failure_context, 'parent_failure_chain', None) else ""
            failure_context_info = (
                f"PARENT FAILURE CONTEXT → Type: {parent_task.failure_context.error_type or 'Unknown'} | Message: {parent_task.failure_context.error_message} | "
                f"Fail Count: {getattr(parent_task.failure_context, 'fail_count', 1)} | Failed Params: {fp_preview}{chain_part}")

        system_prompt, human_prompt = prompt_generator.generate_task_decomposition_prompt(
            original_goal=state.original_goal,
            complex_task_description=parent_task.description,
            available_tools_str=available_tools_str,
            parent_context=parent_context,
            depth=parent_task.depth,
            failure_context=failure_context_info,  # Pass failure context to prompt
            recovery_plan=recovery_plan
        )

        model = ModelManager()
        response = model.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": human_prompt},
        ])
        decomposed_tasks_data = ModelManager.convert_to_json(response.content)

        if not isinstance(decomposed_tasks_data, list):
            debug_warning("SubAgent Spawner",
                          "LLM failed to return a valid list for decomposition.",
                          metadata={"function name": "decompose_task_for_subAgent", "task_id": parent_task.task_id})
            return []

        sub_tasks: list[TASK] = []
        for i, item in enumerate(decomposed_tasks_data):
            if isinstance(item, dict) and all(key in item for key in ["description", "tool_name"]):
                # FIX: Now recommended_tools is consistently list[str] for both depth cases
                if item["tool_name"] not in recommended_tools:
                    debug_warning("SubAgent Spawner",
                                  f"Tool '{item['tool_name']}' not in recommended set. Skipping.",
                                  metadata={"function name": "decompose_task_for_subAgent",
                                            "task_id": parent_task.task_id, "tool_name": item["tool_name"]})
                    continue

                base_id_str = str(parent_task.task_id)
                unique_suffix = uuid.uuid4().hex[:8]  # Short UUID part
                sub_task_id = f"{base_id_str}.{i + 1}-{unique_suffix}"

                sub_tasks.append(
                    TASK(
                        task_id=sub_task_id,
                        description=item["description"],
                        tool_name=item["tool_name"],
                        depth=parent_task.depth + 1,  # Increment depth for creating sub-tasks
                        requires_high_fidelity_context=item.get("requires_high_fidelity_context", False),
                        # Pass the flag
                        required_context=REQUIRED_CONTEXT(
                            source_node="subAgent_decomposer",
                            triggering_task_id=parent_task.task_id,
                            pre_execution_context={"parent_context_str": parent_context,
                                                   "context_type": "spawning_context",
                                                   "original_goal": state.original_goal} if parent_context else None,
                            # Pass parent's context (completed history + failure info) wrapped in dict
                        ),
                    ),
                )

        debug_info("SubAgent Spawner",
                   f"Decomposed into {len(sub_tasks)} validated sub-tasks.",
                   metadata={"function name": "decompose_task_for_subAgent", "task_id": parent_task.task_id,
                             "subtasks_created": len(sub_tasks)})
        return sub_tasks

    @classmethod
    def inject_subAgent_into_workflow(cls, parent_task: TASK, subtasks: list[TASK],
                                      state: "WorkflowStateModel") -> dict:
        """Injects the newly created sub-tasks into the main task list.
        """
        debug_info("--- SPAWNER: Injecting sub-tasks into the workflow ---",
                   f"Parent Task ID: {parent_task.task_id}, Sub-tasks to inject: {len(subtasks)}",
                   metadata={"function name": "inject_subAgent_into_workflow", "parent_task_id": parent_task.task_id,
                             "subtasks_to_inject": len(subtasks)})

        parent_task.status = "in_progress"
        if not parent_task.execution_context:
            parent_task.execution_context = EXECUTION_CONTEXT(
                tool_name=parent_task.tool_name,
                parameters={},
            )
        parent_task.execution_context.analysis = f"Decomposed into {len(subtasks)} sub-tasks."

        # FIX 1: Inherit parent's failure context for sub-tasks so parameter repair can work
        if parent_task.failure_context and parent_task.failure_context.failed_parameters:
            for subtask in subtasks:
                if not subtask.failure_context:
                    subtask.failure_context = FAILURE_CONTEXT(
                        error_message="Inherited from parent task",
                        fail_count=1,
                        error_type="InheritedContext",
                        failed_parameters=parent_task.failure_context.failed_parameters.copy(),
                        strategy_history=parent_task.failure_context.strategy_history.copy() if parent_task.failure_context.strategy_history else []
                    )
                debug_info("SubAgent Spawner",
                           f"Inherited failed_parameters from parent {parent_task.task_id} to subtask {subtask.task_id}",
                           metadata={"parent_failed_params": parent_task.failure_context.failed_parameters,
                                     "subtask_id": subtask.task_id})

        current_tasks = state.tasks
        try:
            current_task_index = current_tasks.index(parent_task)
        except ValueError:
            debug_warning("SubAgent Spawner",
                          f"Could not find parent task {parent_task.task_id} in state.",
                          metadata={"function name": "inject_subAgent_into_workflow",
                                    "parent_task_id": parent_task.task_id})
            return {"tasks": current_tasks}

        # --- START DEDUPLICATION LOGIC ---
        filtered_subtasks = []
        # Collect descriptions of all completed tasks for quick lookup
        completed_task_signatures = set()
        for t in current_tasks:
            if t.status == "completed":
                # Create a unique signature for comparison
                signature = f"{t.tool_name.lower()}:{t.description.lower()}"
                completed_task_signatures.add(signature)

        for new_sub_task in subtasks:
            new_signature = f"{new_sub_task.tool_name.lower()}:{new_sub_task.description.lower()}"

            if new_signature in completed_task_signatures:
                debug_warning("SubAgent Spawner",
                           f"Skipping redundant sub-task {new_sub_task.task_id} ('{new_sub_task.description}') as it's semantically equivalent to a completed task.",
                           metadata={"function name": "inject_subAgent_into_workflow",
                                     "redundant_task_id": new_sub_task.task_id,
                                     "redundant_task_description": new_sub_task.description})
            else:
                filtered_subtasks.append(new_sub_task)
        # --- END DEDUPLICATION LOGIC ---

        updated_tasks = current_tasks[:current_task_index + 1] + filtered_subtasks + current_tasks[
            current_task_index + 1:]
        return {"tasks": updated_tasks}

    @classmethod
    def spawn_subAgent_recursive(cls, state: "WorkflowStateModel", parent_task: TASK, spawn_reason: str,
                                 parent_context: str | None, recovery_plan: str | None = None) -> dict:
        """The main orchestrator for the spawning process.
        """
        # FIX: Ensure a failure_context exists for the parent BEFORE we call any analysis or decomposition.
        # Some failure paths set task.status = 'failed' but don't populate failure_context; the spawner and
        # recovery logic rely on that context to choose discovery-first decompositions.
        if getattr(parent_task, 'status', None) == 'failed' and not getattr(parent_task, 'failure_context', None):
            # Create a minimal synthetic failure_context from available execution_context so downstream nodes
            # (strategy decision, decomposer) have the failed parameters and an error message to reason about.
            synthetic_failed_params = None
            try:
                if parent_task.execution_context and isinstance(parent_task.execution_context.parameters, dict):
                    synthetic_failed_params = parent_task.execution_context.parameters.copy()
            except Exception:
                synthetic_failed_params = None

            parent_task.failure_context = FAILURE_CONTEXT(
                error_message=(parent_task.execution_context.result if parent_task.execution_context and getattr(
                    parent_task.execution_context, 'result',
                    None) else f"Parent task {parent_task.task_id} failed without explicit failure_context."),
                fail_count=1,
                last_failure_timestamp=get_formatted_timestamp(),
                error_type="SyntheticFailureContext",
                failed_parameters=synthetic_failed_params,
                strategy_history=[]
            )
            debug_info("SubAgent Spawner", f"Injected synthetic failure_context into parent task {parent_task.task_id}",
                       metadata={"function name": "spawn_subAgent_recursive", "parent_task_id": parent_task.task_id,
                                 "injected_failed_parameters": synthetic_failed_params})

        spawn_analysis = cls.analyze_spawn_requirement(parent_task, spawn_reason, state)
        if not spawn_analysis.get("should_spawn"):
            debug_info("SubAgent Spawner",
                       f"Analysis decided not to spawn a sub-agent for task {parent_task.task_id}.",
                       metadata={"function name": "spawn_subAgent_recursive", "task_id": parent_task.task_id})

        subtasks = cls.decompose_task_for_subAgent(parent_task, state, parent_context, recovery_plan)
        if not subtasks:
            debug_warning("SubAgent Spawner",
                          f"Decomposition failed for task {parent_task.task_id}.",
                          metadata={"function name": "spawn_subAgent_recursive", "task_id": parent_task.task_id})
            return {"spawn_triggered": False}

        injection_result = cls.inject_subAgent_into_workflow(parent_task, subtasks, state)

        parent_task.subAgent_context = subAgent_CONTEXT(
            subAgent_id=parent_task.task_id,
            subAgent_persona=spawn_analysis.get("spawn_strategy", "decomposer"),
            subAgent_status="active",
            subAgent_tasks=subtasks,
            parent_task_id=parent_task.task_id,
            creation_timestamp=get_formatted_timestamp(),
            notes=f"Spawned for: {spawn_reason}",
        )

        return {
            "spawn_triggered": True,
            "tasks": injection_result["tasks"],
            "current_task_id": subtasks[0].task_id,
            "subtasks_created": len(subtasks),
        }


# 🎭 User-friendly status updates with funny quotes
class AgentStatusUpdater:
    """Provides user-friendly status updates with funny quotes like Gemini CLI"""

    FUNNY_QUOTES = {
        "initial_planning": [
            " Putting on my thinking cap... Time to break down your request into bite-sized tasks!",
            "🎯 Analyzing your request like a detective with a magnifying glass...",
            "🔍 Dissecting your goal with surgical precision... Don't worry, no anesthesia needed!",
            "📋 Creating a master plan... Even Napoleon would be impressed!",
            "🎨 Crafting a strategy so elegant, it belongs in a museum!"
        ],
        "task_execution": [
            "⚡ Rolling up my sleeves and getting to work... This is where the magic happens!",
            "🛠️ Executing tasks with the precision of a Swiss watch... Tick tock!",
            "🎪 Time for the main event! Let's see what this tool can do...",
            "🚀 Launching into action... Houston, we have liftoff!",
            "⚙️ Turning gears and making things happen... Like a well-oiled machine!"
        ],
        "parameter_generation": [
            "🎛️ Fine-tuning parameters like a DJ mixing the perfect beat...",
            "🧪 Mixing the perfect cocktail of parameters... Shaken, not stirred!",
            "🎯 Calibrating tools with laser precision... Pew pew!",
            "⚗️ Brewing up the perfect parameter potion... *bubble bubble*",
            "🔧 Adjusting knobs and dials... We're going full scientist mode!"
        ],
        "error_recovery": [
            "🩹 Oops! Time to channel my inner surgeon and fix this...",
            "🔄 Plot twist! Let's try a different approach... Adapt and overcome!",
            "🛠️ Houston, we have a problem... But don't worry, I'm like MacGyver with code!",
            "🎭 That didn't go as planned... Time for Plan B (or C, or D)!",
            "🔍 Detective mode activated! Let's solve this mystery..."
        ],
        "task_planning": [
            "📊 Orchestrating tasks like a symphony conductor... Maestro at work!",
            "🎯 Playing task Tetris... Finding the perfect fit for each piece!",
            "🎮 Level up! Moving to the next quest in our adventure...",
            "🧩 Connecting the dots... It's all coming together beautifully!",
            "📈 Managing workflow like a boss... CEO of task execution!"
        ],
        "finalizing": [
            "🎉 Grand finale time! Putting together the masterpiece...",
            "🎭 The curtain falls... Time to reveal what we've accomplished!",
            "📝 Weaving together all the threads into a beautiful tapestry...",
            "🏆 Victory lap! Let's see what we've achieved together...",
            "✨ Ta-da! The moment you've been waiting for..."
        ],
        "complexity_analysis": [
            "🤔 Hmm, is this task simple or does it need the full treatment?",
            "🔬 Putting this under the microscope... Complex or atomic?",
            "⚖️ Weighing the complexity... Simple Simon or rocket science?",
            "🎭 To spawn or not to spawn... That is the question!",
            "🧩 Solving the complexity puzzle... Piece by piece!"
        ],
        "tool_recommendation": [
            "🛍️ Shopping for the perfect tools... Only the finest for you!",
            "🎯 Handpicking tools like a master craftsman choosing their instruments...",
            "🔧 Building the ultimate toolkit... Batman would be jealous!",
            "⚡ Assembling my dream team of tools... Avengers, assemble!",
            "🎪 Selecting the star performers for this show..."
        ]
    }

    @classmethod
    def update_status(cls, category: str, task_id: int = None, extra_info: str = ""):
        """Update user status with funny quotes and request count info"""
        try:
            from ...config import settings

            eval_listener = settings.listeners.get('eval', None)
            if eval_listener is None:
                return

            # Get a random funny quote for the category
            import random
            quotes = cls.FUNNY_QUOTES.get(category, ["🤖 Working on it..."])
            base_message = random.choice(quotes)

            # Add task info if provided
            if task_id is not None:
                base_message += f" [Task {task_id}]"

            # Add extra info if provided
            if extra_info:
                base_message += f" {extra_info}"

            # Get current request count from OpenAI integration
            from ...utils.open_ai_integration import OpenAIIntegration
            current_requests = OpenAIIntegration.requests_count

            # Format final message with request count
            final_message = f"{base_message} @ API calls: {current_requests}"

            # Update status via the eval listener
            eval_listener.emit_on_variable_change(
                cls,
                "agent_status",
                eval_listener.get_last_event().meta_data.get('new_value', '') if eval_listener.get_last_event() else '',
                final_message
            )

        except Exception as e:
            # Fail silently - status updates shouldn't break the workflow
            debug_warning("Status Updater", f"Failed to update status: {e}",
                          metadata={"category": category, "task_id": task_id, "extra_info": extra_info})
