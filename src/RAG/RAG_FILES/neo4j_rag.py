import asyncio
import json
import os
import subprocess
from typing import Any

# Optional google.generativeai dependency
try:  # pragma: no cover - external dependency may be absent
    import google.generativeai as genai  # type: ignore

    _gemini_available = True
except Exception:  # noqa: BLE001
    genai = None  # type: ignore
    _gemini_available = False

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_ollama import ChatOllama

# --- Optional neo4j dependency (graceful degradation) ---
try:  # pragma: no cover - environment dependent
    from neo4j import GraphDatabase  # type: ignore

    _neo4j_available = True
except Exception:  # neo4j not installed
    GraphDatabase = None  # type: ignore
    _neo4j_available = False

from src.config import settings
from src.utils.open_ai_integration import OpenAIIntegration
import pathlib

# Corrected path: structured_triple_prompt lives under prompts, not utils
try:
    from src.prompts.structured_triple_prompt import Prompt  # type: ignore
except Exception:  # Fallback minimal Prompt implementation

    class Prompt:  # type: ignore
        @staticmethod
        def create_structured_prompt(schema_headers, record_data):
            return (
                "You are extracting triples from provided structured schema headers and a single record.",
                f"Headers: {schema_headers}\nRecord: {record_data}",
            )


SYSTEM_PROMPT_GENERATE_TRIPLE_ENHANCED = """
You are an intelligent knowledge graph extraction system that identifies meaningful relationships between entities in text.

**CRITICAL: Respond with JSON array only. No reasoning, explanation, or additional text.**

**Your Mission:**
Extract clear, factual relationships from the provided text to build a comprehensive knowledge graph that captures how different entities connect to each other.

**What You're Looking For:**
- **Entities**: People, organizations, products, concepts, locations, technologies
- **Relationships**: How these entities connect, interact, or relate to each other
- **Facts**: Concrete, verifiable information about these connections

**Extraction Guidelines:**

1. **Entity Identification:**
   - Focus on concrete nouns: companies, people, products, technologies, locations
   - Use the most specific name available (e.g., "Microsoft Azure" not just "Azure")
   - Keep entity names consistent throughout

2. **Relationship Types:**
   - Use clear, descriptive verbs: "owns", "provides", "develops", "partners with", "located in"
   - Capture different relationship types: ownership, creation, usage, location, collaboration
   - Make relationships specific and meaningful

3. **Quality Standards:**
   - Extract only factual, verifiable relationships
   - Avoid vague or unclear connections
   - Focus on the most important relationships in the text
   - Ensure each triple adds meaningful information

**Output Format:**
Return ONLY a JSON array where each triple has exactly these keys:
- "subject": the main entity (string)
- "predicate": the relationship type (string)
- "object": the connected entity (string)

**CRITICAL REQUIREMENTS:**
- Return ONLY the JSON OBJECT, no additional text
- No reasoning or explanation text
- No "thinking" or "let me think" phrases
- Format: [{"subject": "entity1", "predicate": "relationship", "object": "entity2"}]

**Examples:**

Input: "Microsoft developed Azure to provide cloud computing services. Many enterprises use Azure for their digital transformation initiatives."

Output as JSON array:
[
  {"subject": "Microsoft", "predicate": "developed", "object": "Azure"},
  {"subject": "Azure", "predicate": "provides", "object": "cloud computing services"},
  {"subject": "enterprises", "predicate": "use", "object": "Azure"},
  {"subject": "enterprises", "predicate": "use Azure for", "object": "digital transformation"}
]

**Important Notes:**
- Return [] if no clear relationships exist
- Focus on quality over quantity
- Each triple should be independently meaningful
- Use consistent entity naming

**Text to analyze:**
"""

# --- Neo4j driver setup (optional) ---
# if _neo4j_available:
#     try:
#         if getattr(settings, "neo4j_driver", None) is None:
#             driver = GraphDatabase.driver(
#                 settings.NEO4J_URI,
#                 auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
#             )
#         else:
#             driver = settings.neo4j_driver  # type: ignore
#     except Exception as e:  # Connection issue – degrade instead of crash
#         if getattr(settings, "socket_con", None):  # pragma: no cover
#             settings.socket_con.send_error(f"[Neo4j Disabled] Connection failed: {e}")
#         driver = None
#         _neo4j_available = False
# else:
#     driver = None  # Neo4j features disabled

GEMINI_CLI_PATH = "C:\\Users\\pirat\\AppData\\Roaming\\npm\\gemini.cmd"
SUBPROCESS_TIMEOUT = 120  # 2 minutes timeout per request

task_count = 0  # Global counter for tracking the number of tasks


async def prompt_gemini_for_triples_cli(chunk: Document) -> dict[str, Any]:
    """Process a single chunk via Gemini CLI returning a mapping with chunk & triples."""
    is_structured = (
        chunk.metadata.get("source") == "google_sheets"
        if hasattr(chunk, "metadata")
        else False
    )

    if (
        is_structured
        and hasattr(chunk, "metadata")
        and "structured_data" in chunk.metadata
    ):
        # Use structured data prompt
        schema_headers = chunk.metadata.get("schema", [])
        record_data = chunk.metadata.get("structured_data", {})
        prompt_tuple = Prompt.create_structured_prompt(schema_headers, record_data)
        system_part, user_part = (
            prompt_tuple
            if isinstance(prompt_tuple, (list, tuple)) and len(prompt_tuple) == 2
            else (prompt_tuple, "")
        )
        combined_prompt = f"{system_part}\n{user_part}".strip()
    else:
        combined_prompt = (
            SYSTEM_PROMPT_GENERATE_TRIPLE_ENHANCED + f"\nText:\n{chunk.page_content}\n"
        )

    if not pathlib.Path(GEMINI_CLI_PATH).exists():
        raise FileNotFoundError(
            f"Gemini command not found at {GEMINI_CLI_PATH}. Please ensure it is installed and the path is correct."
        )

    process = await asyncio.create_subprocess_exec(
        GEMINI_CLI_PATH,
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )

    try:
        stdout, stderr = await asyncio.wait_for(
            process.communicate(input=combined_prompt.encode("utf-8")),
            timeout=SUBPROCESS_TIMEOUT,
        )
        stdout = stdout.decode("utf-8").strip()
        stderr = stderr.decode("utf-8").strip()
        if process.returncode != 0:
            raise RuntimeError(
                f"Gemini command failed with return code {process.returncode}: {stderr}"
            )
    except asyncio.TimeoutError:
        process.kill()
        stdout, stderr = await process.communicate()
        raise FileNotFoundError(
            f"Gemini CLI call timed out after {SUBPROCESS_TIMEOUT} seconds, error:-{stderr.decode('utf-8')}"
        )

    triples = None
    try:
        triples = json.loads(stdout)
    except json.JSONDecodeError:
        json_start_pointer = stdout.find("[")
        json_end_pointer = stdout.rfind("]") + 1
        if json_start_pointer != -1 and json_end_pointer > json_start_pointer:
            json_part = stdout[json_start_pointer:json_end_pointer]
            try:
                triples = json.loads(json_part)
            except json.JSONDecodeError as extraction_error:
                print(f"Failed to extract JSON from response: {extraction_error}")
                print(f"Original output: {stdout}")
    if triples is None or not isinstance(triples, list):
        print("No triples extracted or empty response.")
        return {"chunk": chunk, "triples": []}
    return {"chunk": chunk, "triples": triples}


# 🚀 FIXED: Enhanced batch processing function keep this method to for if more batching related issue arises
async def prompt_gemini_for_triples_batch(
    chunks: list[Document], batch_size: int = 3
) -> list[list]:
    """
    Process chunks in smaller batches to prevent resource exhaustion.

    Args:
        chunks: List of Document chunks to process
        batch_size: Number of chunks to process concurrently

    Returns:
        List of triple lists for each chunk
    """
    results = []

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        print(
            f"Processing batch {i // batch_size + 1}/{(len(chunks) + batch_size - 1) // batch_size}"
        )

        batch_tasks = [prompt_gemini_for_triples_cli(chunk) for chunk in batch]
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

        # Handle exceptions in batch results
        for j, result in enumerate(batch_results):
            if isinstance(result, Exception):
                print(f"Error in chunk {i + j}: {result}")
                results.append([])  # Empty list for failed chunks
            else:
                results.append(result)

        # Small delay between batches
        if i + batch_size < len(chunks):
            await asyncio.sleep(1.0)

    return results


async def prompt_gemini_for_triples_api(
    chunk: Document,
) -> None | dict[str, Document | list[Any]] | dict[str, Document | list]:
    """
    Enhanced version that detects structured vs unstructured data and uses appropriate prompts
    """
    # Check if this is structured spreadsheet data
    is_structured = (
        chunk.metadata.get("source") == "google_sheets"
        if hasattr(chunk, "metadata")
        else False
    )

    if (
        is_structured
        and hasattr(chunk, "metadata")
        and "structured_data" in chunk.metadata
    ):
        # Use structured data prompt
        schema_headers = chunk.metadata.get("schema", [])
        record_data = chunk.metadata.get("structured_data", {})
        prompt = Prompt.create_structured_prompt(schema_headers, record_data)
    else:
        # Use original unstructured text prompt
        prompt = (
            SYSTEM_PROMPT_GENERATE_TRIPLE_ENHANCED
            + f"""\n
        Text:\n
        {chunk.page_content}
        """
        )
    load_dotenv()
    api_key_gemini = os.getenv("GEMINI_API_KEY")
    genai.configure(api_key=api_key_gemini)
    model = genai.GenerativeModel(model_name="gemini-1.5-flash")

    # sending the prompt to the Gemini API using asyncio to avoid blocking the event loop
    def get_response(prompt_g: str):  # type: ignore
        """Helper function to get response from Gemini API with error handling"""
        try:
            return model.generate_content(prompt_g)
        except Exception as e_G:  # pragma: no cover
            if getattr(settings, "socket_con", None):
                settings.socket_con.send_error(f"Error calling Gemini API: {e_G}")
            return None

    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, get_response, prompt)

    if not response or response.text.strip() == "" or response.text.strip() == "[]":
        print("No response or empty response from Gemini API.")
        return {"chunk": chunk, "triples": []}
    output = response.text.strip()

    #   Parse the output as JSON
    try:
        triples = json.loads(output)
        if not isinstance(triples, list):
            print(
                f"Warning: Expected list, got {type(triples)}. Attempting to extract..."
            )
            raise json.JSONDecodeError("Not a list", output, 0)
        return {"chunk": chunk, "triples": triples}
    except json.JSONDecodeError:
        print("JSON decode error; attempting extraction")
        try:
            json_start = output.find("[")
            json_end = output.rfind("]") + 1
            if json_start != -1 and json_end > json_start:
                json_part = output[json_start:json_end]
                triples = json.loads(json_part)
                if isinstance(triples, list):
                    return {"chunk": chunk, "triples": triples}
                else:
                    return {"chunk": chunk, "triples": []}
            else:
                return {"chunk": chunk, "triples": []}
        except Exception:
            return {"chunk": chunk, "triples": []}


async def prompt_openai_for_triples(
    chunk: Document,
) -> dict[str, Document | list[Any]] | dict[str, Document | str]:
    """
    🔧 FIXED: Enhanced async version with proper response type handling and reasoning content suppression
    """
    from src.utils.model_manager import ModelManager

    system_prompt = SYSTEM_PROMPT_GENERATE_TRIPLE_ENHANCED
    user_prompt = ""

    is_structured = (
        chunk.metadata.get("source") == "google_sheets"
        if hasattr(chunk, "metadata")
        else False
    )

    if (
        is_structured
        and hasattr(chunk, "metadata")
        and "structured_data" in chunk.metadata
    ):
        schema_headers = chunk.metadata.get("schema", [])
        record_data = chunk.metadata.get("structured_data", {})
        prompt_tuple = Prompt.create_structured_prompt(schema_headers, record_data)
        system_prompt = prompt_tuple[0]
        user_prompt = prompt_tuple[1]
    else:
        user_prompt = f"""
        **Your Task:**
        Extract clear, factual relationships between entities in the text below.
        Focus on concrete entities (people, companies, products, technologies) and their connections.
        MOST IMPORTANT INSTRUCTIONS: ***Do not include any reasoning or explanation text in your response.
                                        RESPOND WITH VALID JSON ARRAY OF TRIPLES AS MENTIONED***
        **Text to Analyze:**      
        {chunk.page_content}    
        """

    try:
        client = OpenAIIntegration()
        response = await client.generate_text_async(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        )

        if not response or response.strip() == "" or response.strip() == "[]":
            if getattr(settings, "socket_con", None):
                settings.socket_con.send_error(
                    "[WARNING] No response or empty response from OpenAI API."
                )
            return {"chunk": chunk, "triples": []}

        parsed_response = ModelManager.convert_to_json(response)

        if isinstance(parsed_response, list):
            return {"chunk": chunk, "triples": parsed_response}
        elif isinstance(parsed_response, dict):
            if "content" in parsed_response and isinstance(
                parsed_response["content"], str
            ):
                try:
                    content_json = json.loads(parsed_response["content"])
                    if isinstance(content_json, list):
                        return {"chunk": chunk, "triples": content_json}
                except json.JSONDecodeError:
                    content_str = parsed_response["content"]
                    json_start = content_str.find("[")
                    json_end = content_str.rfind("]") + 1
                    if json_start != -1 and json_end > json_start:
                        try:
                            json_part = content_str[json_start:json_end]
                            extracted_json = json.loads(json_part)
                            if isinstance(extracted_json, list):
                                return {"chunk": chunk, "triples": extracted_json}
                        except json.JSONDecodeError:
                            pass
                return {"chunk": chunk, "triples": []}
            else:
                return {
                    "chunk": chunk,
                    "triples": [parsed_response] if parsed_response else [],
                }
        else:
            if getattr(settings, "socket_con", None):
                settings.socket_con.send_error(
                    f"[WARNING] Unexpected response type: {type(parsed_response)}"
                )
            return {"chunk": chunk, "triples": []}

    except Exception as api_error:  # pragma: no cover
        if getattr(settings, "socket_con", None):
            settings.socket_con.send_error(
                f"[ERROR] OpenAI API call failed: {api_error}"
            )
        return {"chunk": chunk, "triples": [], "error": str(api_error)}


def prompt_local_llm_for_triples(chunk: Document) -> list:
    """Existing function - unchanged."""
    llm = ChatOllama(model="llama3.1:8b", temperature=0.1, format="json")
    triples = []
    llm.invoke(SYSTEM_PROMPT_GENERATE_TRIPLE_ENHANCED)
    prompt = f"""
        You are analyzing text to extract meaningful relationships for a knowledge graph.
        \n        **Your Task:**\n        Extract clear, factual relationships between entities in the text below.\n        Focus on concrete entities (people, companies, products, technologies) and their connections.\n        \n        **Text to Analyze:**\n        \"\"\"{chunk.page_content}\"\"\"\n        \n        **Output Format:**\n        Return a JSON array where each relationship is represented as:\n        {{"subject": "entity1", "predicate": "relationship", "object": "entity2"}}\n        \n        Focus on quality over quantity - extract only meaningful, verifiable relationships.\n        """
    response = llm.invoke([settings.HumanMessage(content=prompt)])
    output = response.content

    print(f"LLM response: {output}")

    try:
        data = json.loads(output)
        if isinstance(data, dict):
            if all(isinstance(v, list) for v in data.values()):
                for s, p, o in zip(
                    data.get("subject", []),
                    data.get("predicate", []),
                    data.get("object", []),
                ):
                    triples.append({"subject": s, "predicate": p, "object": o})
            else:
                triples.append(data)
        elif isinstance(data, list):
            triples.extend(data)
        else:
            raise ValueError(
                f"Unexpected JSON format: {data}. Expected a list or dict of lists."
            )
    except json.JSONDecodeError:
        print("Failed to parse JSON, trying to extract JSON part from response.")
        try:
            json_start = output.index("[")
            json_end = output.rindex("]") + 1
            triples.append(json.loads(output[json_start:json_end]))
        except Exception as e:
            raise ValueError(
                f"Failed to extract JSON from response: {e}\n\n Response: {output}"
            )
    return triples


def clear_database():
    """Deletes all nodes and relationships from the Neo4j database if available."""
    from src.config.settings import neo4j_driver as driver  # type: ignore

    if not _neo4j_available or driver is None:
        print("Neo4j not available; clear_database skipped.")
        return
    try:
        with driver.session() as session:  # type: ignore
            session.run("MATCH (n) DETACH DELETE n")
    except Exception as e:  # pragma: no cover
        if getattr(settings, "socket_con", None):
            settings.socket_con.send_error(f"Error clearing Neo4j database: {e}")
        else:
            print(f"Error clearing Neo4j database: {e}")
    print("Database cleared successfully.")


def _insert_triple(tx, subject, relation, object):
    """Insert a single triple into Neo4j (internal helper)."""
    query = (
        "MERGE (s:Entity {name: $subject}) "
        "MERGE (o:Entity {name: $object}) "
        "MERGE (s)-[r:RELATION {type: $relation}]->(o)"
    )
    tx.run(query, subject=subject, relation=relation, object=object)


def insert_triples(triples):
    """Insert multiple triples into Neo4j if available."""
    from src.config.settings import neo4j_driver as driver  # type: ignore

    if not _neo4j_available or driver is None:
        return
    try:
        with driver.session() as session:  # type: ignore
            for subject, relation, object in triples:
                if all([subject, relation, object]):
                    session.write_transaction(_insert_triple, subject, relation, object)
    except Exception as e:  # pragma: no cover
        print(f"Error inserting triples: {e}")


def get_triples(cypher_query: str):
    """Retrieve triples via Cypher if Neo4j is available; else return empty list."""
    from src.config.settings import neo4j_driver as driver  # type: ignore
    from src.ui.diagnostics.debug_helpers import debug_error

    if not _neo4j_available or driver is None:
        return []
    try:
        with driver.session() as session:  # type: ignore
            result = session.run(cypher_query)
            triples = []
            for record in result:
                s = record["s"]
                o = record["o"]
                r = record["r"]
                if isinstance(r, list):
                    relation_types = " -> ".join(
                        [rel.get("type", str(rel)) for rel in r]
                    )
                else:
                    relation_types = r.get("type", str(r)) if r else ""
                triples.append(
                    {
                        "subject": s.get("name", str(s)),
                        "relation": relation_types,
                        "object": o.get("name", str(o)),
                    }
                )
            return triples
    except Exception as e:  # pragma: no cover
        debug_error(
            heading="Error retrieving triples",
            body=f"Failed to execute Cypher query: {cypher_query}\nError: {e}",
            metadata={
                "cypher_query": cypher_query,
                "error": str(e),
                "neo4j_available": _neo4j_available,
                "driver": driver is not None,
            },
        )
        return []


def extract_triple_text(triple):
    if "subject" in triple and "relation" in triple and "object" in triple:
        return f"{triple['subject']} - {triple['relation']} - {triple['object']}"
    elif "s" in triple and "r" in triple and "o" in triple:
        s = (
            triple["s"]["name"]
            if isinstance(triple["s"], dict) and "name" in triple["s"]
            else str(triple["s"])
        )
        o = (
            triple["o"]["name"]
            if isinstance(triple["o"], dict) and "name" in triple["o"]
            else str(triple["o"])
        )
        r = triple["r"]
        if isinstance(r, list):
            relation_types = "->".join([rel.get("type", str(rel)) for rel in r])
        elif isinstance(r, dict):
            relation_types = r.get("type", str(r))
        else:
            relation_types = str(r)
        return f"{s} - {relation_types} - {o}"
    else:
        return str(triple)


def get_retrieve_triples(cypher_query: str):
    """Retrieve raw records via Cypher if available; else empty list."""
    from src.config.settings import neo4j_driver as driver  # type: ignore
    from src.ui.diagnostics.debug_helpers import debug_error

    if not _neo4j_available or driver is None:
        return []
    try:
        with driver.session() as session:  # type: ignore
            result = session.run(cypher_query)
            records = []
            for record in result:
                records.append(dict(record))
            return records
    except Exception as e:  # pragma: no cover
        debug_error(
            heading="Error retrieving records",
            body=f"Failed to execute Cypher query: {cypher_query}\nError: {e}",
            metadata={
                "cypher_query": cypher_query,
                "error": str(e),
                "neo4j_available": _neo4j_available,
                "driver": driver is not None,
            },
        )
        return []


def get_all_labels_and_names() -> dict[str, list[str]]:
    """Return labels & names if Neo4j available; else empty placeholders."""
    from src.config.settings import neo4j_driver as driver  # type: ignore

    if not _neo4j_available or driver is None:
        return {"labels": [], "names": []}
    with driver.session() as session:  # type: ignore
        labels = [
            record["label"]
            for record in session.run("CALL db.labels() YIELD label RETURN label")
        ]
        names = [
            record["name"]
            for record in session.run("MATCH (n) RETURN DISTINCT n.name AS name")
            if record["name"]
        ]
    return {"labels": labels, "names": names}


def get_all_relationship_types() -> list[str]:
    """Return relation types if Neo4j available; else empty list."""
    from src.config.settings import neo4j_driver as driver  # type: ignore

    if not _neo4j_available or driver is None:
        return []
    with driver.session() as session:  # type: ignore
        relationship_types = [
            record["type"]
            for record in session.run(
                "MATCH ()-[r:RELATION]-() RETURN DISTINCT r.type AS type"
            )
            if record["type"]
        ]
    return relationship_types


if __name__ == "__main__":
    pass
