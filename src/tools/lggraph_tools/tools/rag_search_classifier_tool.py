import json

from src.utils.sound import beep
from rich.prompt import Prompt

import src.prompts.rag_search_classifier_prompts

# from lggraph import console  # this need to fixed we are importing console from "lggraph" file
from src.RAG.RAG_FILES import neo4j_rag
from src.RAG.RAG_FILES import rag
from src.config import settings
from src.config.settings import console
from src.models.state import StateAccessor  # Import the global state object
from src.tools.lggraph_tools.tool_response_manager import ToolResponseManager
from src.utils.model_manager import ModelManager


def retrieve_knowledge_graph(query: str) -> str:
    """
    Retrieves information from the knowledge graph based on a query.
    Convert the user's query to the Cypher query format and return the results from the knowledge graph.
    """
    get_all_l_n = neo4j_rag.get_all_labels_and_names()
    labels = get_all_l_n.get("labels", [])
    names = get_all_l_n.get("names", [])
    # Get actual relationship types from database
    relationship_types = neo4j_rag.get_all_relationship_types()

    from src.ui.diagnostics.debug_helpers import debug_info

    debug_info(
        heading="RAG_CLASSIFIER • CYPHER_GENERATION",
        body="Cypher query generation started",
        metadata={
            "labels_count": len(labels),
            "names_count": len(names),
            "relationship_types_count": len(relationship_types),
        },
    )

    # If no names available, return early
    if not names:
        from src.utils.debug_helpers import debug_error

        debug_error(
            heading="RAG_CLASSIFIER • NO_ENTITIES",
            body="No entity names available in knowledge graph",
            metadata={"error_type": "empty_knowledge_graph"},
        )
        return (
            "[ERROR] Knowledge graph appears to be empty. Please ensure data is loaded."
        )

    # Debug: Check if (user query name) and email-related terms exist
    # name_found = any(query in name.lower() for name in names)
    # email_relations = [rt for rt in relationship_types if "email" in rt.lower()]
    #
    # socket_con.send_error(f"[DEBUG] '{query}' found in entity names: {name_found}")
    # socket_con.send_error(f"[DEBUG] Email-related relationships: {email_relations}")
    # check if the query tokens match any entity names or relationship types

    query_tokens = [token.lower() for token in query.split() if len(token) > 2]
    name_found = any(token in name.lower() for name in names for token in query_tokens)
    relation_found = any(
        token in rel.lower() for rel in relationship_types for token in query_tokens
    )

    if not name_found and not relation_found:
        from src.utils.debug_helpers import debug_warning

        debug_warning(
            heading="RAG_CLASSIFIER • NO_MATCHES",
            body=f"No matching entity names or relationship types found for query: '{query}'",
            metadata={"query": query, "query_tokens": query_tokens},
        )

    from src.utils.debug_helpers import debug_info

    debug_info(
        heading="RAG_CLASSIFIER • QUERY_ANALYSIS",
        body="Query token analysis completed",
        metadata={
            "query_tokens": query_tokens,
            "name_found": name_found,
            "relation_found": relation_found,
            "user_query": query,
        },
    )

    # Create enhanced prompt with complete workflow and decision logic
    SYSTEM_PROMPT_CYPHER_GENERATION = (
        src.prompts.rag_search_classifier_prompts.Prompts.get_system_prompt_cypher(
            names, relationship_types, labels, query
        )
    )

    def try_generate_cypher(model_name, temperature=0.3):
        """Try to generate cypher with a specific model"""
        try:
            llm = ModelManager(model=model_name, temperature=temperature)

            # Add JSON format instruction to the prompt
            enhanced_prompt = """

**IMPORTANT:** Respond with valid JSON in this exact format:
{
    "cypher_query": "MATCH (n) RETURN n LIMIT 10",
    "reasoning": "Your reasoning for this cypher query"
}"""

            result = llm.invoke(
                [settings.HumanMessage(content=SYSTEM_PROMPT_CYPHER_GENERATION)]
                + [settings.HumanMessage(content=enhanced_prompt)]
            )
            # ✅ FIX 1: Use correct method name
            ToolResponseManager().set_response_base([result])

            # Use the new JSON conversion method
            json_result = ModelManager.convert_to_json(result)
            return json.dumps(json_result)  # Return as JSON string for compatibility
        except Exception as e:
            if settings.socket_con:
                settings.socket_con.send_error(
                    f"[ERROR] Failed to invoke model {model_name}: {e}"
                )
            return None

    # ✅ FIX 2: Actually call the function to generate cypher
    cypher_content = try_generate_cypher(settings.GPT_MODEL)

    # ✅ FIX 3: Add proper null checking and error handling
    try:
        # Check if cypher generation succeeded
        if not cypher_content:
            return f"[ERROR] Failed to generate cypher query for: {query}"

        # ✅ FIX 4: Parse JSON safely
        cypher_result = json.loads(cypher_content)

        # ✅ FIX 5: Safe dictionary access
        final_cypher = cypher_result.get("cypher_query", "")
        reasoning = cypher_result.get("reasoning", "")

    except json.JSONDecodeError as e:
        if settings.socket_con:
            settings.socket_con.send_error(
                f"[ERROR] Failed to parse JSON response: {e}"
            )
        return f"[ERROR] Invalid JSON response for query: {query}"
    except Exception as e:
        if settings.socket_con:
            settings.socket_con.send_error(
                f"[ERROR] Unexpected error processing response: {e}"
            )
        return f"[ERROR] Failed to process response for query: {query}"

    if not final_cypher:
        return f"[ERROR] Failed to generate any valid cypher query for: {query}"

    if settings.socket_con:
        settings.socket_con.send_error(f"[LOG] FINAL CYPHER QUERY: {final_cypher}")
        settings.socket_con.send_error(f"[LOG] REASONING: {reasoning}")

    # Execute the cypher query
    receive_triples = neo4j_rag.get_retrieve_triples(final_cypher)

    if not receive_triples:
        return f"[ERROR] No results found for the query: {query}. Please try a different query."

    # Convert the triples to a readable format by llm
    triples_text = "\n".join(
        [neo4j_rag.extract_triple_text(triple) for triple in receive_triples]
    )
    if settings.socket_con:
        settings.socket_con.send_error(f"[LOG] TRIPLES TEXT: {triples_text}")

    # Create a comprehensive, user-friendly explanation prompt (HYBRID APPROACH)
    from src.prompts.rag_search_classifier_prompts import Prompts

    explanation_prompt = f"""
    **What the user asked:** "{StateAccessor().get_last_message()}
    **What we searched for:** "{query}"
    
    **Here's the information I found from our knowledge base:**
    {triples_text}
    **Now, please explain this information in a natural, conversational way:**
    """

    # Use a conversational LLM for natural language responses
    explanation_llm = ModelManager(
        model=settings.GPT_MODEL,
        temperature=0.7,  # Slightly higher for more natural responses
        # No format specified - allows natural language output
    )

    with console.status(
        "[bold green]Generating explanation...[/bold green]", spinner="dots"
    ):
        explanation_result = explanation_llm.invoke(
            [
                settings.HumanMessage(content=Prompts.get_system_prompt_classifier()),
                settings.HumanMessage(content=explanation_prompt),
            ]
        )

    # Clean up the response and return just the explanation
    explanation = explanation_result.content.strip()

    # Remove any JSON formatting if it accidentally appears
    if explanation.startswith('{"explanation":') and explanation.endswith("}"):
        try:
            parsed = json.loads(explanation)
            explanation = parsed.get("explanation", explanation)
        except json.JSONDecodeError:
            pass  # Keep original if parsing fails

    return explanation


def rag_search_classifier_tool(query: str) -> str:
    """
    Determines the appropriate RAG (Retrieval-Augmented Generation) search type based on the query and file type,
    and performs the search if supported.
    """
    if settings.ENABLE_SOUND_NOTIFICATIONS:
        beep(7200, 200)  # Play a sound to indicate the start of RAG search
    file_path = Prompt.ask(
        "Enter FILE PATH TO RAG SEARCH",
        default=str(settings.DEFAULT_RAG_EXAMPLE_FILE_PATH),
    )
    system_prompt = """
    You are an intelligent RAG system selector that understands both user intent and document characteristics.

    **Your Mission:**
    Analyze the user's question and the document content to choose the most effective search approach.

    **Understanding the User's Intent:**
    - Look at their current question AND the conversation history
    - Consider what type of answer they're seeking
    - Understand if they're asking about relationships, facts, summaries, or explanations

    **Available RAG Types:**

    1. **Knowledge Graph RAG** - Best for:
       - Questions about relationships: "How is X connected to Y?"
       - Entity-focused queries: "What companies work with Microsoft?"
       - Network analysis: "Show me the connections between..."
       - Structured data with clear entities and relationships

    2. **Text RAG** - Best for:
       - Content summaries: "What is this document about?"
       - Detailed explanations: "Explain how X works"
       - Narrative information: stories, procedures, descriptions
       - Unstructured text content

    **Decision Making:**
    - If the user previously mentioned a specific RAG type, respect their preference
    - Consider the document structure - does it contain entities and relationships, or is it narrative text?
    - Think about what would give the user the most useful answer

    **Context Awareness:**
    - Review the conversation history to understand the user's ongoing needs
    - If they're building on a previous question, consider continuity
    - Look for implicit preferences based on their question style

    **EXPLICIT INSTRUCTIONS:**
    - If the user explicitly asks for a knowledge graph search, prioritize that
    - If they ask for a text search, prioritize that

    **Response Format:**
    {
      "selected_rag_type": "knowledge_graph" or "text",
      "reasoning": "Clear explanation of why this choice best serves the user's needs, considering both their question and the document characteristics"
    }

    Make the choice that will be most helpful to the user based on what they're actually trying to accomplish.
"""
    prompt = f"""
    available_RAG_types: {"knowledge_graph", "text"}
    user_query: "{query}"
    chunks: "{rag.load_pdf_document(file_path)[0:5]}"
    history: {StateAccessor().get_messages()}
"""

    llm = ModelManager(
        model=settings.GPT_MODEL,
        temperature=0.7,
    )
    prompt_list = [
        settings.HumanMessage(content=system_prompt),
        settings.HumanMessage(content=prompt),
    ]
    with console.status("[bold green]Thinking...[/bold green]", spinner="dots"):
        llm_response = llm.invoke(prompt_list)
    print("\n\nLLM Response:", llm_response.content)

    try:
        # ✅ NULL CHECK: Ensure llm_response and content exist
        if not llm_response or not llm_response.content:
            return "[ERROR] LLM returned empty response. Please try again."

        # Use the new JSON conversion method
        response_json = ModelManager.convert_to_json(llm_response)

        # ✅ VALIDATE JSON STRUCTURE
        if not isinstance(response_json, dict):
            return f"[ERROR] LLM response is not a valid JSON object: {llm_response.content}"

    except Exception as e:
        return f"[ERROR] Failed to parse LLM response as JSON: {llm_response.content}. Error: {str(e)}"

    selected_rag_type = response_json.get("selected_rag_type")
    reasoning = response_json.get("reasoning", "No reasoning provided.")

    # ✅ VALIDATE RAG TYPE SELECTION
    if not selected_rag_type:
        return f"[ERROR] LLM did not specify a RAG type. Response: {response_json}"

    if selected_rag_type == "knowledge_graph":
        if settings.ENABLE_SOUND_NOTIFICATIONS:
            beep(
                7200, 200
            )  # Play a sound to indicate knowledge graph RAG search
        if (
            Prompt.ask(
                "LLm selected knowledge graph RAG type",
                choices=["yes", "no"],
                default="no",
            )
            == "no"
        ):
            exit()
        # clear the knowledge graph and save the new one
        rag.save_knowledge_graph_open_ai(file_path)
        result = retrieve_knowledge_graph(query)
        return f"Knowledge Graph Search Results for '{query}':\n\n{result}"
    elif selected_rag_type == "text":
        return (
            f"{rag.text_rag_search_using_llm(query, rag.load_pdf_document(file_path))}"
        )
    else:
        return (
            f"[ERROR] Unsupported RAG type: {selected_rag_type}. Reasoning: {reasoning}"
        )
