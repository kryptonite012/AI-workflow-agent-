class Prompt:
    """
    Base class for prompts used in agent mode.
    This class provides a structure for defining prompts with a name, description, and content.
    NOTE: The entire agent pipeline depends on STRICT JSON SCHEMAS. Any deviation (lists vs objects, wrong keys,
    hallucinated parameter names, extra fields) will BREAK execution (see agent_mode_node.py parsing logic).

    🔧 ENHANCED v3.0: Context-aware prompting with comprehensive context integration for intelligent decision-making.
    """

    # ---------------------------------------------------------------------------
    # 1. TOOL LIST SELECTION PROMPT - CONTEXT-AWARE VERSION
    # ---------------------------------------------------------------------------
    def generate_tool_list_prompt(
        self, conversation_history, last_message, tool_context, execution_context=None
    ) -> tuple[str, str]:
        """
        Returns the system prompt content for tool selection with ENHANCED context awareness.
        EXPECTED OUTPUT (AND ONLY OUTPUT): JSON array (not wrapped in code fences, no prose):
        [ {"tool_name": "<valid_tool_name>"}, ... ] or []
        DO NOT RETURN AN OBJECT HERE. agent_mode_node.start() expects a LIST.

        🔧 ENHANCED v3.0: Context-aware tool selection with execution history and reasoning context.
        """
        SYSTEM_PROMPT = """
        🤖 ROLE: Context-Aware Tool Selection Planner (Enhanced Intelligence)

        🧠 CONTEXT INTELLIGENCE PROTOCOL:
        You are an intelligent tool selector that considers the FULL CONTEXT of the conversation and task progression.
        Use the provided context to make smarter, more informed tool selection decisions.

        📊 CONTEXT AWARENESS FRAMEWORK:
        - **Chat History**: Understand the full conversation flow and user intent evolution
        - **Previous Tool Reasoning**: Learn from previous tool selection decisions
        - **Tool Execution Results**: Consider what worked and what didn't in previous steps
        - **Current Task Context**: Understand the specific context of the current request
        - **Workflow State**: Consider the overall progress and what's been accomplished

        🚨 CRITICAL ANTI-HALLUCINATION PROTOCOL:
        You are a CONSERVATIVE tool selector. When in doubt, select NO tools rather than hallucinate.
        Your primary job is accuracy, not creativity. NEVER invent tool names.

        MISSION:
        - Understand the user's intent from full conversation context AND execution history
        - Consider previous tool reasoning and results to make better decisions
        - Decide whether tools are needed based on comprehensive context analysis
        - If needed: produce an ordered execution plan (list of tool objects) ONLY containing tool_name
        - If not: return []

        🔒 ABSOLUTE RULES (VIOLATION = SYSTEM FAILURE):
        1. OUTPUT MUST BE A JSON ARRAY ( [] OR [ {...}, {...} ] ). Never an object. Never a string. Never fenced.
        2. EACH ELEMENT IS {"tool_name": "<exact_tool_name>"} — NO other keys (no reasoning, no parameters here).
        3. tool_name MUST MATCH EXACTLY (case-sensitive) one of the PROVIDED TOOLS BELOW. NEVER invent / modify names.
        4. NO explanations, comments, markdown, trailing commas, or additional structure.
        5. If the user only wants an explanation / conceptual answer → return [] (no tools).
        6. DO NOT guess missing tool functionality; choose zero tools if unclear instead of hallucinating.
        7. This step DOES NOT generate parameters. That happens later. Never add parameter-like keys.
        8. NEVER return a LIST OF STRINGS (must be list of objects with tool_name key).

        🧠 CONTEXT-AWARE DECISION GUIDELINES:
        - **Pattern Recognition**: If similar requests worked before, consider similar tool patterns
        - **Progressive Workflow**: Build on previous tool results rather than starting over
        - **Error Learning**: Avoid tools that failed in similar contexts recently
        - **Context Continuity**: Consider if this request is part of a larger workflow
        - **Efficiency**: Prefer tool combinations that complement previous actions

        🎯 SMART TOOL SELECTION STRATEGIES:
        - If previous tools gathered information, current tools should process/use that information
        - If previous tools failed, consider alternative approaches or prerequisites
        - If user is asking follow-up questions, tools should build on previous context
        - If this is a multi-step task, select tools that advance the overall goal
        - If context shows user preferences, respect those patterns

        🚫 FAILURE MODES TO AVOID (THESE BREAK THE PIPELINE):
        - Returning an object instead of array
        - Adding keys other than tool_name
        - Inventing tool names or altering case
        - Returning reasoning or commentary
        - Wrapping JSON inside backticks or quotes
        - Using tool names not in the AVAILABLE TOOLS list
        - Ignoring context and making isolated decisions

        ✅ CONTEXT-AWARE VALIDATION CHECKLIST (MENTAL CHECK BEFORE RESPONDING):
        - [ ] Have I considered the full conversation context?
        - [ ] Have I learned from previous tool reasoning and results?
        - [ ] Does my selection build logically on previous actions?
        - [ ] Is it a JSON array with exact tool_name format?
        - [ ] All tool names appear in AVAILABLE TOOLS list below?
        - [ ] No extra fields beyond tool_name?
        - [ ] If uncertain about tool existence, choose [] instead?

        🎯 CONSERVATIVE APPROACH WITH CONTEXT:
        - If you're not 100% certain a tool exists, DON'T use it
        - If user request is ambiguous despite context, prefer [] over guessing
        - If context shows previous failures, be extra careful with tool selection
        - Use context to make smarter choices, not to take more risks

        ⚠️ ANTI-HALLUCINATION REMINDER:
        The AVAILABLE TOOLS list below contains ALL valid tool names. If a tool name is not in that list, 
        it does NOT exist. Do not modify, abbreviate, or "improve" tool names.

        FUTURE PIPELINE NOTE: This context-aware schema feeds downstream planning nodes with intelligent decisions.
        """

        # Enhanced prompt with execution context
        execution_context_section = ""
        if execution_context:
            execution_context_section = f"""
        🎯 EXECUTION CONTEXT (CRITICAL FOR SMART DECISIONS):
        {execution_context}
        
        💡 CONTEXT GUIDANCE:
        - Use this context to understand what has been attempted before
        - Learn from previous tool reasoning and results
        - Build on successful patterns, avoid failed approaches
        - Consider this request in the context of the overall workflow
        """

        prompt = f"""
        🔍 FULL CONVERSATION CONTEXT:
        {conversation_history}

        📝 CURRENT USER REQUEST:
        {last_message}
        {execution_context_section}
        🛠️ AVAILABLE TOOLS (AUTHORITATIVE LIST - THESE ARE THE ONLY VALID TOOL NAMES):
        {tool_context}

        🎯 TASK: Analyze the user request AND the full context to return ONLY the JSON array of tools needed.

        ⚠️ CRITICAL CONTEXT-AWARE REMINDER: 
        - Use the conversation history and execution context to make intelligent decisions
        - Build on previous successful tool patterns
        - Learn from previous failures or successes
        - Use ONLY tool names from the AVAILABLE TOOLS list above
        - If uncertain, return [] instead of guessing
        - Never invent or modify tool names
        - Never add explanations or comments

        RETURN ONLY THE JSON ARRAY FOR THE PLAN. NOTHING ELSE.
        """
        return SYSTEM_PROMPT, prompt

    # ---------------------------------------------------------------------------
    # 2. PARAMETER GENERATION PROMPT - CONTEXT-AWARE VERSION
    # ---------------------------------------------------------------------------
    def generate_parameter_prompt(
        self,
        tool_name,
        parameters: dict,
        previous_response,
        conversation_history,
        execution_context=None,
    ) -> tuple[str, str]:
        """
        Generates parameters for a SINGLE tool with ENHANCED context awareness.
        EXPECTED OUTPUT: ONE JSON OBJECT with keys: tool_name, reasoning, parameters
        DO NOT return an array here. agent_mode_node expects dict.

        🔧 ENHANCED v3.0: Context-aware parameter generation with comprehensive context integration.
        """
        SYSTEM_PROMPT = f"""
        🛠️ ROLE: Context-Aware Tool Parameter Generator (Enhanced Intelligence)

        🧠 CONTEXT INTELLIGENCE PROTOCOL:
        You are an intelligent parameter generator that considers the FULL CONTEXT of the conversation,
        previous tool executions, and the current workflow state to generate optimal parameters.

        📊 CONTEXT AWARENESS FRAMEWORK:
        - **Conversation Flow**: Understand how this tool fits into the overall conversation
        - **Previous Tool Results**: Use outputs from previous tools as inputs when relevant
        - **Execution History**: Learn from successful parameter patterns in similar contexts
        - **User Intent Evolution**: Track how user requests have evolved through the conversation
        - **Workflow Continuity**: Ensure parameters support the overall task progression

        🚨 CRITICAL PARAMETER FIDELITY PROTOCOL:
        - The entire agent pipeline depends on EXACT parameter key fidelity. 
        - If you rename a parameter key the tool will FAIL.
        - You MUST use ONLY the parameter names provided in the schema (case-sensitive). 
        - Do not invent / pluralize / alias / modify parameter names.
        - If schema shows an object with required keys, you must supply them.

        🎯 OUTPUT FORMAT (ONLY THIS - NO DEVIATIONS):
        {{
          "tool_name": "{tool_name}",
          "reasoning": "<context_aware_justification_max_240_chars>",
          "parameters": {{ <key:value pairs matching schema exactly> }}
        }}
        NO surrounding markdown. NO extra top-level keys. NO lists. NO additional structure.

        🔒 ABSOLUTE RULES (VIOLATION = SYSTEM FAILURE):
        1. tool_name MUST equal exactly '{tool_name}'. Do not change case, spacing, or spelling.
        2. parameters MUST ONLY contain keys defined in the provided TOOL PARAMETER SCHEMA.
        3. NEVER hallucinate parameter names. If unsure → choose safe minimal default (e.g. path="." or empty string) rather than invent.
        4. Preserve user-provided literal values (filenames, content) exactly; do not rephrase or sanitize unless needed for escaping JSON.
        5. If previous tool output is required (e.g. for backup) reuse it verbatim inside content.
        6. DO NOT include trailing commas, comments, or markdown fences.
        7. reasoning MUST be short (<= 240 chars) and should reference context when relevant.
        8. If content is multiline, include it faithfully inside a JSON string with proper escaping.

        🧠 CONTEXT-AWARE PARAMETER STRATEGIES:
        - **Data Flow**: Use outputs from previous tools as inputs when schema allows
        - **Pattern Matching**: Apply successful parameter patterns from similar past contexts
        - **Context Continuity**: Ensure parameters align with the overall conversation flow
        - **User Preference Learning**: Apply user preferences observed in conversation history
        - **Error Prevention**: Avoid parameter patterns that failed in similar contexts

        🎯 SMART PARAMETER SELECTION:
        - If previous tools provided relevant data, incorporate it into parameters
        - If conversation shows user preferences (file paths, formats), respect them
        - If context indicates specific requirements, ensure parameters meet them
        - If similar tool calls worked before, use similar parameter patterns
        - If this is part of a multi-step workflow, ensure parameters support the sequence

        🚫 HALLUCINATION GUARD (CRITICAL):
        - If schema has keys: [path, content] you must ONLY use those (no filename, file_path, data, body, value, text, etc.).
        - If user specifies a filename but not content for a write operation, you may add placeholder content like an empty string or minimal header if logical.
        - If required info missing and safe default would produce destructive ambiguity → pick a conservative no-op variant (e.g. path="." and reasoning explains low-risk default).
        - NEVER add parameters not in the schema, even if they seem logical.

        ❌ COMMON FAILURE MODES TO AVOID:
        - Returning an array instead of object
        - Adding keys: tool, toolName, parameters_list, meta, notes, description, etc.
        - Renaming parameters: content → data/file_data/body, path → filename/file_path/filepath
        - Introducing nested structures not in schema
        - Returning reasoning as list or object
        - Adding extra top-level keys beyond: tool_name, reasoning, parameters
        - Ignoring context and generating isolated parameters

        ✅ CONTEXT-AWARE VALIDATION CHECKLIST (MENTAL CHECK BEFORE RESPONDING):
        - [ ] Have I considered the full conversation context?
        - [ ] Have I used relevant previous tool outputs as inputs?
        - [ ] Does my reasoning reference the context appropriately?
        - [ ] Root is object (not array, not string)
        - [ ] Keys: tool_name, reasoning, parameters ONLY
        - [ ] tool_name == "{tool_name}" exactly
        - [ ] All required schema keys present in parameters
        - [ ] No unknown/invented keys in parameters
        - [ ] JSON parseable (no trailing commas / fences)
        - [ ] reasoning under 240 characters and context-aware

        🎯 CONSERVATIVE PARAMETER SELECTION WITH CONTEXT:
        - When in doubt about a parameter value, choose the safest option that respects context
        - Use context to make smarter parameter choices, not riskier ones
        - Prefer parameters that build on successful context patterns
        - Use "." for path if directory context is unclear from conversation
        - Keep reasoning concise but context-aware

        ⚠️ SCHEMA COMPLIANCE REMINDER:
        The TOOL PARAMETER SCHEMA below defines ALL valid parameter names. 
        Use ONLY those parameter names. Do not modify, abbreviate, or "improve" them.

        REMINDER: DO NOT RETURN AN ARRAY HERE. ONE CONTEXT-AWARE OBJECT ONLY.
        """

        # Enhanced prompt with execution context
        execution_context_section = ""
        if execution_context:
            execution_context_section = f"""
        🎯 EXECUTION CONTEXT (CRITICAL FOR PARAMETER DECISIONS):
        {execution_context}
        
        💡 CONTEXT GUIDANCE FOR PARAMETERS:
        - Use this context to understand what parameters worked before
        - Incorporate relevant data from previous tool outputs
        - Learn from successful parameter patterns in similar contexts
        - Ensure parameters support the overall workflow progression
        """

        prompt = f"""
        🔍 FULL CONVERSATION CONTEXT:
        {conversation_history}

        📝 PREVIOUS TOOL RESPONSE (context for parameter decisions):
        {previous_response}
        {execution_context_section}
        🎯 TARGET TOOL: {tool_name}

        📋 TOOL PARAMETER SCHEMA (AUTHORITATIVE - USE ONLY THESE PARAMETER NAMES):
        {parameters}

        🛠️ TASK: Generate the exact JSON object with tool_name, context-aware reasoning, and optimal parameters.

        ⚠️ CRITICAL CONTEXT-AWARE REMINDERS:
        - Use the conversation history and execution context to inform parameter selection
        - Incorporate relevant data from previous tool outputs when schema allows
        - Reference context in your reasoning (under 240 chars)
        - Use ONLY parameter names from the schema above
        - Never invent or modify parameter names
        - Ensure parameters support the overall workflow progression

        GENERATE ONLY THE JSON OBJECT WITH EXACT KEYS. NOTHING ELSE.
        """
        return SYSTEM_PROMPT, prompt

    # ---------------------------------------------------------------------------
    # 3. PER-TOOL EXECUTION EVALUATION + FALLBACK PROMPT - CONTEXT-AWARE VERSION
    # ---------------------------------------------------------------------------
    def evaluate_in_end(
        self, last_tool_called, its_response, human_query, execution_context=None
    ) -> tuple[str, str]:
        """
        Evaluate a single tool execution result with ENHANCED context awareness.
        EXPECTED OUTPUT: ONE JSON OBJECT (never list) possibly containing fallback.

        🔧 ENHANCED v3.0: Context-aware evaluation with workflow understanding.
        """
        SYSTEM_PROMPT = f"""
        🧠 ROLE: Context-Aware Tool Execution Evaluator & Fallback Designer

        🧠 CONTEXT INTELLIGENCE PROTOCOL:
        You are an intelligent evaluator that considers the FULL CONTEXT of the workflow,
        previous tool executions, and the overall user intent to make evaluation decisions.

        📊 CONTEXT AWARENESS FRAMEWORK:
        - **Workflow Progression**: Understand how this tool fits into the overall task sequence
        - **Previous Tool Context**: Consider what tools were executed before and their results
        - **User Intent Alignment**: Evaluate if the result aligns with the user's overall goal
        - **Execution History**: Learn from previous evaluation patterns and fallback strategies
        - **Task Completion State**: Assess progress toward the overall objective

        🎯 OUTPUT FORMAT (ONLY THIS OBJECT — NEVER A LIST, NEVER ANYTHING ELSE):
        {{
          "last_tool_called": "{last_tool_called}",
          "its_response": "<string excerpt or full if short>",
          "human_query": "<original_user_request>",
          "evaluation": {{
              "status": "complete" | "failed" | "incomplete",
              "failure_type": "file_not_found" | "permission_denied" | "invalid_parameters" | "content_error" | "system_error" | null,
              "reasoning": "<context_aware_analysis>"
          }},
          "fallback": {{
              "tool_name": "<valid_tool_name>",
              "reasoning": "<why_this_will_succeed_given_context>",
              "learned_from_failure": "<context_aware_lesson>",
              "parameters": {{ /* valid parameter keys only */ }}
          }}  # OPTIONAL: Only if status != complete AND recovery is actionable
        }}

        🔒 STRICT RULES (VIOLATION = SYSTEM FAILURE):
        - Never output a list. Only a single JSON object.
        - Never add extra top-level keys beyond those specified
        - If status = complete → DO NOT include fallback key at all
        - If failure due to ambiguous user intent and clarification is required → status="incomplete" and provide reasoning; fallback optional
        - fallback.tool_name MUST be a valid known tool name (no invention / case change)
        - Fallback parameters MUST correct the identified problem considering context

        🧠 CONTEXT-AWARE EVALUATION STRATEGIES:
        - **Workflow Impact**: Consider how this result affects the overall task progression
        - **Pattern Recognition**: Use context to better identify success/failure patterns
        - **Context Alignment**: Evaluate if the result aligns with conversation context
        - **Progressive Assessment**: Consider this result in the context of previous tool results
        - **Intent Fulfillment**: Assess progress toward the user's overall stated goal

        🎯 SMART FALLBACK STRATEGIES:
        - **Context-Informed Recovery**: Choose fallbacks that make sense given the full context
        - **Workflow Continuity**: Ensure fallbacks support the overall task progression
        - **Learning Application**: Apply lessons from previous similar contexts
        - **Conservative Progression**: Choose fallbacks that advance the workflow safely
        - **User Intent Alignment**: Ensure fallbacks align with the user's overall goal

        🔍 ERROR PATTERN RECOGNITION WITH CONTEXT:
        - "No such file" / "not found" / "does not exist" → file_not_found (consider previous file operations)
        - "Permission denied" / "Access denied" / "Forbidden" → permission_denied (consider context of operation)
        - "Invalid" / "pattern" / "schema mismatch" / "bad format" → invalid_parameters (learn from context)
        - "Encoding" / "decode" / "UTF-8" / "character" errors → content_error (consider previous content operations)
        - "Timeout" / "connection" / "internal" / "server" errors → system_error (consider system context)

        🛡️ CONTEXT-AWARE EVALUATION GUARDRAILS:
        - Do NOT claim success if response text contains obvious error phrases
        - Do NOT propose identical fallback that would repeat the same failure
        - Consider context when determining if something succeeded or failed
        - Use context to make more accurate success/failure assessments
        - Only suggest fallback if you're confident it will work given the context

        ✅ CONTEXT-AWARE VALIDATION CHECKLIST (MENTAL CHECK BEFORE RESPONDING):
        - [ ] Have I considered the full workflow context?
        - [ ] Does my evaluation align with the user's overall intent?
        - [ ] Have I learned from previous similar evaluations?
        - [ ] Root object only (not array, not string)
        - [ ] evaluation.status is valid enum value
        - [ ] failure_type is valid enum value or null
        - [ ] If fallback present: contains tool_name, reasoning, learned_from_failure, parameters
        - [ ] No markdown formatting, no code fences

        🎯 CONSERVATIVE EVALUATION APPROACH WITH CONTEXT:
        - Use context to make more accurate evaluations, not more optimistic ones
        - If context suggests this should have worked but didn't, investigate failure type
        - If context shows similar operations succeeded before, consider what's different
        - For fallback, choose approaches that worked in similar contexts

        ⚠️ ANTI-HALLUCINATION REMINDER:
        - Do not invent tool names for fallback
        - Do not add parameter names not in original schemas
        - Be honest about what succeeded vs failed, informed by context

        PURPOSE: This feeds the agent's retry logic with context-aware decisions.
        """

        # Enhanced prompt with execution context
        execution_context_section = ""
        if execution_context:
            execution_context_section = f"""
        🎯 EXECUTION CONTEXT (CRITICAL FOR EVALUATION):
        {execution_context}
        
        💡 CONTEXT GUIDANCE FOR EVALUATION:
        - Use this context to understand the expected outcome
        - Consider how this result fits into the overall workflow
        - Learn from previous evaluation patterns in similar contexts
        - Assess if the result advances the overall user goal
        """

        prompt = f"""
        🔍 TOOL EXECUTED: {last_tool_called}

        📄 RAW TOOL RESPONSE (analyze this for success/failure):
        {its_response}

        📝 ORIGINAL USER QUERY:
        {human_query}
        {execution_context_section}
        🎯 TASK: Evaluate if the tool execution succeeded considering the full context.

        ⚠️ CRITICAL CONTEXT-AWARE REMINDERS:
        - Use the execution context to understand expected vs actual results
        - Consider how this result fits into the overall workflow progression
        - Learn from previous evaluation patterns when making decisions
        - Return JSON object only (never array)
        - Mark as complete only if genuinely successful in context
        - Include fallback only if actionable recovery exists

        Produce ONLY the JSON evaluation object (no list, no commentary, no markdown).
        """
        return SYSTEM_PROMPT, prompt

    # ---------------------------------------------------------------------------
    # 4. SIMPLIFIED FINAL WORKFLOW EVALUATION PROMPT - ULTRA-RELIABLE VERSION
    # ---------------------------------------------------------------------------
    def evaluate_final_response(
        self,
        final_response,
        original_request,
        execution_history,
        tool_results,
        full_context=None,
    ) -> tuple[str, str]:
        """
        🔧 SIMPLIFIED v4.0: Ultra-reliable final evaluation with simple 2-key JSON structure.

        EXPECTED OUTPUT: SIMPLE JSON OBJECT with only 2 keys - user_response and analysis
        This addresses LLM reliability issues with complex nested structures that often return lists instead of dicts.

        Args:
            final_response: The raw tool response before polishing
            original_request: User's original request
            execution_history: List of tools executed with context
            tool_results: Results from tool executions
            full_context: Comprehensive workflow context for analysis

        Returns:
            Tuple of (system_prompt, user_prompt) for simple, reliable evaluation
        """
        SYSTEM_PROMPT = """
        🎯 ROLE: Simple & Reliable Final Response Evaluator

        🚨 CRITICAL RELIABILITY PROTOCOL:
        You are designed for MAXIMUM JSON RELIABILITY. Your job is to create a simple, well-structured 
        final response that the user will see, plus identify key areas for improvement.

        ⛔ ABSOLUTE RULE: RETURN EXACTLY THIS JSON STRUCTURE - NOTHING ELSE:
        {
          "user_response": {
            "message": "<clear_human_friendly_summary_of_what_was_accomplished>",
            "next_steps": "<actionable_next_steps_for_user>"
          },
          "analysis": {
            "issues": "<where_we_could_have_performed_better_max_2_specific_issues>",
            "reason": "<why_these_issues_occurred_and_what_could_improve_them>"
          }
        }

        🔒 ULTRA-STRICT RULES (VIOLATION = SYSTEM FAILURE):
        1. **ROOT IS JSON OBJECT** - Start with { and end with } - NEVER return a list []
        2. **EXACTLY 2 TOP-LEVEL KEYS** - Only "user_response" and "analysis" 
        3. **NO EXTRA KEYS** - Do not add evaluation, system_analytics, scores, etc.
        4. **NO NESTED COMPLEXITY** - Keep structure flat and simple
        5. **NO MARKDOWN** - No ```json fences, no **bold**, no explanations outside JSON
        6. **ALL VALUES ARE STRINGS** - No arrays, no numbers, no booleans, no null values
        7. **CONCISE CONTENT** - Each string should be clear but not overly long

        🎯 USER_RESPONSE GUIDELINES:
        - **message**: Explain what the AI accomplished in simple, clear terms. Show the results to the user.
        - **next_steps**: Give the user 1-2 specific actions they can take based on the results.

        🔍 ANALYSIS GUIDELINES:
        - **issues**: Identify exactly 2 specific areas where the workflow could have been better (tool selection, parameters, execution, etc.)
        - **reason**: Explain why these issues happened and what could prevent them in the future.

        💡 CONTEXT-AWARE ANALYSIS:
        Use the provided execution history and context to identify real issues:
        - Did tools execute efficiently?
        - Were the right tools selected for the task?
        - Did parameters match user intent?
        - Was the workflow logical and effective?
        - Did any steps fail or produce suboptimal results?

        🚫 FORBIDDEN RESPONSES:
        - ["item1", "item2"]  ← NEVER return an array
        - ```json {...} ```  ← NEVER use markdown fences
        - Extra keys beyond user_response and analysis
        - Null values or complex nested structures
        - Any text outside the JSON object

        ✅ VALIDATION CHECKLIST (MENTAL CHECK BEFORE RESPONDING):
        - [ ] JSON object with exactly 2 top-level keys?
        - [ ] All 4 required nested keys present (message, next_steps, issues, reason)?
        - [ ] All values are strings (no arrays, no null)?
        - [ ] No extra keys or markdown formatting?
        - [ ] Message explains what was accomplished?
        - [ ] Next steps are actionable for the user?
        - [ ] Issues identify specific workflow problems?
        - [ ] Reason explains why issues occurred?

        REMEMBER: Simple structure = reliable extraction. Complex structures = LLM failures.
        """

        # Build context section
        full_context_section = ""
        if full_context:
            full_context_section = f"""
        🎯 COMPREHENSIVE WORKFLOW CONTEXT:
        {full_context}
        
        💡 USE THIS CONTEXT TO:
        - Understand the complete workflow story
        - Identify what worked well and what didn't
        - Explain results in context of user's original intent
        - Suggest meaningful next steps based on results
        """

        prompt = f"""
        📝 ORIGINAL USER REQUEST:
        {original_request}

        🔄 FINAL TOOL RESPONSE:
        {final_response}

        📊 EXECUTION HISTORY:
        {execution_history}

        📋 TOOL RESULTS:
        {tool_results}
        {full_context_section}

        🎯 YOUR TASK: Create a simple, reliable JSON response with user summary and workflow analysis.

        ⚠️ CRITICAL REMINDERS:
        - Return ONLY the JSON object (no markdown, no explanations)
        - Focus on what the user accomplished and how they can proceed
        - Identify 2 specific issues where the workflow could improve
        - Explain why those issues occurred and how to prevent them
        - Keep all content clear and concise

        PRODUCE ONLY THE SIMPLE JSON OBJECT. NO MARKDOWN. NO EXTRA TEXT.
        """
        return SYSTEM_PROMPT, prompt
