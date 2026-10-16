# ✅ LIGHTWEIGHT CORE IMPORTS ONLY
import asyncio
import hashlib
import json
import os
from asyncio import Semaphore
from typing import Awaitable
from pathlib import Path

import dotenv

# ✅ LIGHTWEIGHT LANGCHAIN IMPORTS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document

# ✅ LOCAL IMPORTS (lightweight)
from src.RAG.RAG_FILES import neo4j_rag
from src.config import settings
from src.utils.model_manager import ModelManager
import pathlib


# ✅ LAZY LOADING: Heavy imports google_sheet.md to function level
# torch, cosine_similarity, genai, Chroma, OllamaEmbeddings, ChatOllama
# will be imported only when needed

# Socket connection now centralized in settings - no longer needed


# ✅ HELPER FUNCTION: Lazy loading for rich prompts
def _get_user_input(prompt_text: str, default: str = "y") -> str:
    """Helper function to get user input with lazy loading of rich.prompt"""
    try:
        import rich.prompt

        return rich.prompt.Prompt.ask(prompt_text, default=default)
    except ImportError:
        # Fallback to built-in input if rich not available
        response = input(f"{prompt_text} (default: {default}): ").strip()
        return response if response else default


def load_pdf_document(
    doc_path: str = settings.DEFAULT_RAG_EXAMPLE_FILE_PATH,
) -> list[Document]:
    """
    Loads a PDF document or Text file and returns its content as a list of Document objects.
    :param doc_path: Path to the PDF file.
    :return: List of Document objects containing the content of the PDF.
    """
    # print(Path(doc_path).suffix.lower() == ".txt", Path(doc_path).suffix.lower())
    if Path(doc_path).suffix.lower() == ".txt":
        with Path(doc_path).open("r", encoding="utf-8") as file:
            content = file.read()
        return [Document(page_content=content)]
    elif Path(doc_path).suffix.lower() == ".pdf":
        loader = PyPDFLoader(doc_path)
        return loader.load()
    # if the file is on web then we can use the web loader
    elif doc_path.split("https://docs.google.com/spreadsheets/")[0].lower() == "":
        # ✅ LAZY LOADING: Import Google Sheets RAG only when needed
        try:
            from src.RAG.RAG_FILES.sheets_rag import GoogleSheetsRAG
        except ImportError as e:
            raise ImportError(f"Google Sheets RAG module not available: {e}")

        # Define schema mapping for better triple extraction
        schema_config = {
            "entity_columns": "Columns that represent main entities (people, companies, products)",
            "relationship_columns": "Columns that define relationships or roles",
            "attribute_columns": "Columns that contain properties or values",
        }

        sheets = GoogleSheetsRAG(doc_path, schema_config)

        # Use the new structured documents method for better knowledge graph extraction
        return sheets.get_structured_documents_for_kg()
    else:
        print(
            "Unsupported file format. Please provide a .pdf or .txt or link of spread sheet file."
        )
        raise ValueError(
            "Unsupported file format. Please provide a .pdf or .txt or link of spread sheet file."
        )


def split_into_unique_chunks(
    documents: list, chunking_size: int, remove_duplicates: bool = True
) -> list[Document]:
    """
    Splits a list of Document objects into text chunks using a recursive character splitter.

    Args:
        documents (list): List of Document objects to be split.
        chunking_size (int): The size of each chunk to be created.
        remove_duplicates (bool): Whether to remove duplicate chunks. Default True.

    Returns:
        list[Document]: List of Document chunks (unique if remove_duplicates=True).
    """
    print(f"DEBUG: Number of documents: {len(documents)}")
    if documents and isinstance(documents[0], Document):
        print(f"DEBUG: First document metadata: {documents[0].metadata}")
        print(f"DEBUG: data_type exists: {'data_type' in documents[0].metadata}")
        print(f"DEBUG: data_type value: '{documents[0].metadata.get('data_type')}'")

        # Check if this is structured data that shouldn't be chunked
        if documents[0].metadata.get("data_type") == "structured_spreadsheet":
            print("Structured data detected - returning documents without chunking")
            return documents

    # If chunking_size is 0 or negative, return original documents
    if chunking_size <= 0:
        print("Invalid chunking size - returning original documents")
        return documents

    # Calculate total content length for validation
    total_content_length = sum(len(doc.page_content) for doc in documents)
    print(
        f"DEBUG: Total content length: {total_content_length}, Chunking size: {chunking_size}"
    )

    # If chunking size is larger than total content, return original documents
    if chunking_size >= total_content_length:
        print("Chunking size larger than content - returning original documents")
        return documents

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunking_size,
        chunk_overlap=max(50, chunking_size // 10),  # Ensure minimum overlap
    )
    doc_splits = splitter.split_documents(documents)

    if not remove_duplicates:
        print(f"📊 Total chunks created (with duplicates): {len(doc_splits)}")
        return doc_splits

    # Remove duplicates if requested
    seen = set()
    unique_chunks = []
    duplicate_count = 0

    for doc in doc_splits:
        content_hash = doc.page_content.strip()
        if (
            content_hash not in seen and len(content_hash) > 10
        ):  # Ignore very short chunks
            seen.add(content_hash)
            unique_chunks.append(doc)
        else:
            duplicate_count += 1

    print("📊 Chunk Statistics:")
    print(f"   - Total chunks created: {len(doc_splits)}")
    print(f"   - Unique chunks kept: {len(unique_chunks)}")
    print(f"   - Duplicate chunks removed: {duplicate_count}")

    return unique_chunks


# similarity search using vector store with Ollama embeddings
def find_similar_documents(query: str, file_path: str) -> list:
    """
    Finds and returns documents from a PDF file that are most similar to the given query using vector similarity search.

    Args:
        query (str): The search query.
        file_path (str): Path to the PDF file.

    Returns:
        list: List of Document objects most similar to the query.
    """
    # ✅ LAZY LOADING: Import heavy libraries only when this function is called
    try:
        from langchain_community.vectorstores import Chroma
        from langchain_ollama import OllamaEmbeddings
    except ImportError as e:
        raise ImportError(f"Required libraries not installed for vector search: {e}")

    documents = load_pdf_document(file_path)
    chunks = split_into_unique_chunks(documents)
    vector_store = Chroma.from_documents(
        chunks,
        OllamaEmbeddings(model="nomic-embed-text:v1.5"),
        persist_directory="./RAG_FILES/chromaDB_patents",
    )
    return vector_store.similarity_search(query)


# similarity search using Google Generative AI embeddings
def get_genai_embedding(texts: list[str], task: str = "RETRIEVAL_QUERY") -> list:
    """
    Retrieves embeddings for a list of texts using Google Generative AI embedding API.
    This function is explicitly designed to handle different embedding tasks because the Google charge 0 for converting embeddings
    by which the conversation is fast and efficient.

    Args:
        texts (list[str]): List of input texts to embed.
        task (str): The embedding task type (e.g., "RETRIEVAL_QUERY" or "RETRIEVAL_DOCUMENT").

    Returns:
        list: Embedding vectors for the input texts.
    """
    # ✅ LAZY LOADING: Import Google AI only when this function is called
    try:
        import google.generativeai as genai
    except ImportError as e:
        raise ImportError(f"Google Generative AI library not installed: {e}")

    dotenv.load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables.")
    genai.configure(api_key=api_key)
    response = genai.embed_content(
        model="models/text-embedding-004", content=texts, task_type=task
    )
    if "embedding" not in response:
        raise ValueError("Embedding not found in the API response.")
    return response["embedding"]


def search_similar_chunks_genai(query: str, chunks: list[Document], top_k=5) -> list:
    """
    Searches for the top-k most similar text chunks to a query using GenAI embeddings and cosine similarity.
        :param query: query (str): The search query.
        :param chunks: chunks (list[str]): List of text chunks to compare.
        :param top_k: int: The number of top similar chunks to return.
    """
    # ✅ LAZY LOADING: Import PyTorch only when this function is called
    try:
        import torch
        from torch import cosine_similarity
    except ImportError as e:
        raise ImportError(f"PyTorch not installed. Required for similarity search: {e}")

    chunks = [
        doc.page_content for doc in chunks
    ]  # Extract text content from Document objects
    query_embedding = get_genai_embedding([query], task="RETRIEVAL_QUERY")
    chunk_embeddings = get_genai_embedding(chunks, task="RETRIEVAL_DOCUMENT")
    # Convert to PyTorch tensors
    chunk_embeddings_tensor = torch.tensor(chunk_embeddings, dtype=torch.float32)
    query_embedding_tensor = torch.tensor(query_embedding, dtype=torch.float32).reshape(
        1, -1
    )
    similarities = cosine_similarity(
        chunk_embeddings_tensor, query_embedding_tensor
    ).flatten()
    top_indices = torch.argsort(similarities, descending=True)[:top_k]
    return [Document(page_content=chunks[i]) for i in top_indices]


# graph rag implementation of knowledge graph extracting the triples using  cli api --------------------------
async def save_knowledge_graph_local_llm(file_path: str):
    """
    Save the knowledge graph to the neo4j database using gemini cli.
    Get the triple, save it to the json file, then mark the chunk as processed.
    If all the chunks are processed then save the knowledge graph to the neo4j database.
    """

    document_pdf = load_pdf_document(file_path)

    processed_chunks = get_processed_chunks()
    print(f"no of words: {sum(len(doc.page_content.split()) for doc in document_pdf)}")
    print(
        f"total no of characters: {sum(len(doc.page_content.strip()) for doc in document_pdf)}"
    )

    if _get_user_input("do you want chunking? (y/n)", default="y") == "y":
        no_of_chunks = int(
            _get_user_input("enter how many chunks you want", default="10")
        )
        chunking_size = (
            sum(len(doc.page_content.strip()) for doc in document_pdf) // no_of_chunks
        )
        all_text_doc = ""
        for doc in document_pdf:
            all_text_doc += doc.page_content
    else:
        all_text_doc = ""
        no_of_char = 0
        for doc in document_pdf:
            all_text_doc += doc.page_content
            no_of_char += len(doc.page_content)
        chunking_size = no_of_char
    # Ask user if they want to keep duplicates for better coverage
    keep_duplicates = (
        _get_user_input("Keep duplicate chunks for better coverage? (y/n)", default="n")
        == "y"
    )

    chunks = split_into_unique_chunks(
        [Document(page_content=all_text_doc.strip())],
        chunking_size,
        remove_duplicates=not keep_duplicates,
    )
    print(f"📊 Final chunk count for processing: {len(chunks)}")
    print(f"Total processed chunks: {len(processed_chunks)}")
    if (
        _get_user_input(
            "do you want to over write the processed chunks? (y/n)", default="n"
        )
        == "y"
    ):
        # Use async file operations
        await _clear_rag_files_async()

    # ✅ LAZY LOADING: Import rich progress only when needed
    try:
        import rich.progress
    except ImportError:
        # Fallback to simple iteration if rich not available
        rich = None

    chunks_iter = rich.progress.track(chunks) if rich else chunks
    for chunk in chunks_iter:
        if (
            hashlib.sha256(chunk.page_content.encode()).hexdigest()
            not in processed_chunks
        ):
            triples = neo4j_rag.prompt_local_llm_for_triples(chunk)
            chunk_hash = hashlib.sha256(
                chunk.page_content.encode()
            ).hexdigest()  # Create a unique hash for the chunk content
            await mark_triple_chunk(triples, chunk_hash)
            print(
                f"Processed chunk: {chunk.page_content[:50]}... with hash {chunk_hash}"
            )
        else:
            continue
    processed_chunks = get_processed_chunks()
    print(f"Processed chunks after processing: {len(processed_chunks)}")

    for triple in get_all_triples_from_file():
        subject = triple.get("subject") or triple.get("Subject")
        predicate = (
            triple.get("predicate")
            or triple.get("relation")
            or triple.get("Predicate")
            or triple.get("Relation")
        )
        object = triple.get("object") or triple.get("Object")
        if subject and predicate and object is not None:
            neo4j_rag.insert_triples([(subject, predicate, object)])

    if len(processed_chunks) == len(chunks):
        print("All chunks processed, saving knowledge graph to Neo4j database.")
    else:
        print(
            f"Not all chunks processed. Processed: {len(processed_chunks)}, Total: {len(chunks)}"
        )


def save_knowledge_graph_gemini_cli(file_path: str):
    documents = load_pdf_document(file_path)
    processed_chunks = get_processed_chunks()

    print(f"Total words: {sum(len(doc.page_content.split()) for doc in documents)}")
    print(
        f"Total characters: {sum(len(doc.page_content.strip()) for doc in documents)}"
    )
    print(f"recommended chunk size: {len(documents)}")

    if documents[0].metadata.get("data_type") == "structured_spreadsheet":
        print(
            "Structured spreadsheet data detected. Please use the structured processing function."
        )
        chunks_to_process = [
            chunk
            for chunk in documents
            if hashlib.sha256(chunk.page_content.encode()).hexdigest()
            not in processed_chunks
        ]
    else:
        #  # If the document is not structured, we can proceed with chunking
        all_text_doc = "".join(doc.page_content.strip() for doc in documents)
        if _get_user_input("Do you want chunking? (y/n)", default="y") == "y":
            no_of_chunks = int(
                _get_user_input("Enter how many chunks you want", default="10")
            )
            chunking_size = len(all_text_doc) // no_of_chunks

        else:
            chunking_size = len(
                all_text_doc
            )  # no chunking, use the whole document as one chunk

        # Ask user if they want to keep duplicates for better coverage
        keep_duplicates = (
            _get_user_input(
                "Keep duplicate chunks for better coverage? (y/n)", default="n"
            )
            == "y"
        )

        chunks = split_into_unique_chunks(
            [Document(page_content=all_text_doc.strip())],
            chunking_size,
            remove_duplicates=not keep_duplicates,
        )
        print(f"📊 Final chunk count for processing: {len(chunks)}")

        # remove the processed chunks from the chunks list (this is unique chunk that has to be processed)
        chunks_to_process = [
            chunk
            for chunk in chunks
            if hashlib.sha256(chunk.page_content.encode()).hexdigest()
            not in processed_chunks
        ]

        if len(chunks) != len(chunks_to_process):
            print(
                f"📊 {len(chunks) - len(chunks_to_process)} chunks already processed, skipping them."
            )
            # if the chunks are not processed then we will clear the database
            print("All chunks processed")
            neo4j_rag.clear_database()

    print(f"Total processed chunks: {len(processed_chunks)}")
    if (
        _get_user_input(
            "Do you want to overwrite the processed chunks? (y/n)", default="n"
        )
        == "y"
    ):
        with Path(settings.DEFAULT_RAG_FILES_HASH_TXT_PATH).open("w") as file:
            file.write("")
        with Path(settings.DEFAULT_RAG_FILES_PROCESSED_TRIPLES_PATH).open("w") as file:
            file.write("[]")

        asyncio.run(
            process_chunks_with_immediate_saving(
                chunks_to_process, neo4j_rag.prompt_gemini_for_triples_cli
            )
        )


async def process_chunks_with_immediate_saving(
    chunks_to_process: list[Document], function=neo4j_rag.prompt_gemini_for_triples_api
):
    """
    Process chunks with true parallelism (up to semaphore limit) and save results immediately.
    """
    print("\n🚀 CHUNK PROCESSING STARTED")
    print(f"📊 Chunks to process: {len(chunks_to_process)}")
    print(f"🔧 Using function: {function.__name__}")
    print(
        f"⚡ Max concurrent tasks: {settings.SEMAPHORE_API if function == neo4j_rag.prompt_gemini_for_triples_api else settings.SEMAPHORE_CLI}"
    )
    print("-" * 50)

    # Create semaphore with correct limit of 10
    lock = asyncio.Lock()
    active_task = 0
    # --------- FIXED: Enhanced semaphore with better resource management ---------
    semaphore = Semaphore(
        settings.SEMAPHORE_CLI
        if function == neo4j_rag.prompt_gemini_for_triples_cli
        else settings.SEMAPHORE_API
    )  # Set limit based on function  # Reduced from 5 to 3 for better stability

    async def using_semaphore(chunk: Document):
        """Process a single chunk within semaphore limit"""
        async with semaphore:
            nonlocal active_task
            active_task += 1
            print(f"🔄 Active tasks before processing: {active_task}")
            print(f"🚀 Starting processing chunk: {chunk.page_content[:50]}...")
            start_time_u_s = asyncio.get_event_loop().time()

            try:
                # Call Gemini API (properly awaiting the async function)
                result = await function(chunk)

                # Log completion with timing information
                duration = asyncio.get_event_loop().time() - start_time_u_s
                print(
                    f"✅ Completed chunk in {duration:.2f}s: {chunk.page_content[:50]}..."
                )

                return result
            except Exception as e:
                if settings.socket_con:
                    settings.socket_con.send_error(
                        f"❌ Error processing chunk, active taskc count {active_task}: {e}"
                    )
                else:
                    print(
                        f"❌ Error processing chunk, active taskc count {active_task}: {e}"
                    )
                return {"chunk": chunk, "triples": []}

            finally:
                async with lock:
                    active_task -= 1
                    print(f"🔄 Active tasks after completion: {active_task}")

    # ⚠️ CRITICAL: Create ALL tasks first before awaiting any
    tasks: list[Awaitable] = [
        asyncio.create_task(using_semaphore(chunk)) for chunk in chunks_to_process
    ]
    print(f"Created {len(tasks)} tasks for parallel execution")

    # Track progress and timing
    start_time = asyncio.get_event_loop().time()
    completed_tasks_count = 0
    saved_results = []

    # Process results as they complete (not in sequential order)
    for completed_task in asyncio.as_completed(tasks):
        result = await completed_task  # This allows parallel execution
        completed_tasks_count += 1
        saved_results.append(result.get("chunk"))
        print(
            f"✅ Processed chunk #{completed_tasks_count}/{len(tasks)}: {result['chunk'].page_content[:20]}..."
        )

        if result.get("triples") and isinstance(result["triples"], list):
            triples = result["triples"]
            chunk = result["chunk"]
            if triples or len(triples) > 0:
                print("💾 Saving triples immediately...")
                try:
                    await mark_triple_chunk(
                        triples, hashlib.sha256(chunk.page_content.encode()).hexdigest()
                    )
                except Exception as e:
                    if settings.socket_con:
                        settings.socket_con.send_error(
                            f"❌ Error saving triples: {e} chunk : {chunk.page_content[:20]}"
                        )
                    else:
                        print(
                            f"❌ Error saving triples: {e} chunk : {chunk.page_content[:20]}"
                        )
            else:
                print(
                    "⚠️ No triples found in this chunk, skipping save. for chunk: ",
                    result["chunk"].page_content[:20],
                )

    # save triples to Neo4j immediately (this is taking long time going to it async in future)
    if len(saved_results) == len(chunks_to_process):
        # we are not clearing the database here, because even though chunks are got no change this use to run every time
        # print("All chunks processed, saving triples to Neo4j database...")
        # neo4j_rag.clear_database()
        for triples in get_all_triples_from_file():
            subject = triples.get("subject") or triples.get("Subject")
            predicate = (
                triples.get("predicate")
                or triples.get("relation")
                or triples.get("Predicate")
                or triples.get("Relation")
            )
            object_val = triples.get("object") or triples.get("Object")
            if subject and predicate and object_val is not None:
                try:
                    neo4j_rag.insert_triples([(subject, predicate, object_val)])
                except Exception as e:
                    if settings.socket_con:
                        settings.socket_con.send_error(
                            f"❌ Error inserting triples to Neo4j:"
                            f" {e} \n subject: {subject}, predicate: {predicate}, object: {object_val}"
                        )
                    else:
                        print(
                            f"❌ Error inserting triples to Neo4j:"
                            f" {e} \n subject: {subject}, predicate: {predicate}, object: {object_val}"
                        )

        #   # Show progress
    elapsed = asyncio.get_event_loop().time() - start_time
    print(
        f"⏱️ Progress: {completed_tasks_count}/{len(tasks)} chunks processed in {elapsed:.2f}s"
    )

    return saved_results


def save_knowledge_graph_gemini_api(filepath: str):
    documents = load_pdf_document(filepath)
    processed_chunks = get_processed_chunks()

    print(f"Total words: {sum(len(doc.page_content.split()) for doc in documents)}")
    print(
        f"Total characters: {sum(len(doc.page_content.strip()) for doc in documents)}"
    )
    print(f"recommended chunk size: {len(documents)}")

    if documents[0].metadata.get("data_type") == "structured_spreadsheet":
        print(
            "Structured spreadsheet data detected. Please use the structured processing function."
        )
        chunks_to_process = [
            chunk
            for chunk in documents
            if hashlib.sha256(chunk.page_content.encode()).hexdigest()
            not in processed_chunks
        ]
    else:
        #  # If the document is not structured, we can proceed with chunking
        all_text_doc = "".join(doc.page_content.strip() for doc in documents)
        if _get_user_input("Do you want chunking? (y/n)", default="y") == "y":
            no_of_chunks = int(
                _get_user_input("Enter how many chunks you want", default="10")
            )
            chunking_size = len(all_text_doc) // no_of_chunks

        else:
            chunking_size = len(
                all_text_doc
            )  # no chunking, use the whole document as one chunk

        # Ask user if they want to keep duplicates for better coverage
        keep_duplicates = (
            _get_user_input(
                "Keep duplicate chunks for better coverage? (y/n)", default="n"
            )
            == "y"
        )

        chunks = split_into_unique_chunks(
            [Document(page_content=all_text_doc.strip())],
            chunking_size,
            remove_duplicates=not keep_duplicates,
        )
        print(f"📊 Final chunk count for processing: {len(chunks)}")

        # remove the processed chunks from the chunks list (this is unique chunk that has to be processed)
        chunks_to_process = [
            chunk
            for chunk in chunks
            if hashlib.sha256(chunk.page_content.encode()).hexdigest()
            not in processed_chunks
        ]

        if len(chunks) != len(chunks_to_process):
            print(
                f"📊 {len(chunks) - len(chunks_to_process)} chunks already processed, skipping them."
            )
            # if the chunks are not processed then we will clear the database
            print("All chunks processed")
            neo4j_rag.clear_database()

    print(f"Total processed chunks: {len(processed_chunks)}")
    # # Ask user if they want to overwrite the processed chunks if they have already processed the chunks
    if (
        _get_user_input(
            "Do you want to overwrite the processed chunks? (y/n)", default="n"
        )
        == "y"
    ):
        with Path(settings.DEFAULT_RAG_FILES_HASH_TXT_PATH).open("w") as file:
            file.write("")
        with Path(settings.DEFAULT_RAG_FILES_PROCESSED_TRIPLES_PATH).open("w") as file:
            file.write("[]")

        asyncio.run(
            process_chunks_with_immediate_saving(
                chunks_to_process, neo4j_rag.prompt_openai_for_triples
            )
        )


def save_knowledge_graph_open_ai(filepath: str):
    """
    Save the knowledge graph to the neo4j database using OpenAI API.
    Get the triple, save it to the json file, then mark the chunk as processed.
    If all the chunks are processed then save the knowledge graph to the neo4j database.
    :param filepath: str: Path to the PDF file.
    """
    documents = load_pdf_document(filepath)
    processed_chunks = get_processed_chunks()

    print(f"Total words: {sum(len(doc.page_content.split()) for doc in documents)}")
    print(
        f"Total characters: {sum(len(doc.page_content.strip()) for doc in documents)}"
    )
    print(f"recommended chunk size: {len(documents)}")

    if documents[0].metadata.get("data_type") == "structured_spreadsheet":
        print(
            "Structured spreadsheet data detected. Please use the structured processing function."
        )
        chunks_to_process = [
            chunk
            for chunk in documents
            if hashlib.sha256(chunk.page_content.encode()).hexdigest()
            not in processed_chunks
        ]
    else:
        # If the document is not structured, we can proceed with chunking
        if _get_user_input("Do you want chunking? (y/n)", default="y") == "y":
            no_of_chunks = int(
                _get_user_input("Enter how many chunks you want", default="10")
            )
            # Calculate total characters across all documents
            total_chars = sum(len(doc.page_content.strip()) for doc in documents)
            chunking_size = total_chars // no_of_chunks

            # Ensure minimum chunk size
            min_chunk_size = 100  # Minimum 100 characters per chunk
            if chunking_size < min_chunk_size:
                chunking_size = min_chunk_size
                actual_chunks = total_chars // chunking_size
                print(
                    f"Adjusted to {actual_chunks} chunks due to minimum size requirement"
                )
        else:
            # No chunking - calculate total size for validation
            chunking_size = sum(len(doc.page_content.strip()) for doc in documents)

        # Ask user if they want to keep duplicates for better coverage
        keep_duplicates = (
            _get_user_input(
                "Keep duplicate chunks for better coverage? (y/n)", default="n"
            )
            == "y"
        )

        # FIXED: Pass original documents instead of concatenated string
        chunks = split_into_unique_chunks(
            documents, chunking_size, remove_duplicates=not keep_duplicates
        )
        print(f"📊 Final chunk count for processing: {len(chunks)}")

        # remove the processed chunks from the chunks list (this is unique chunk that has to be processed)
        chunks_to_process = [
            chunk
            for chunk in chunks
            if hashlib.sha256(chunk.page_content.encode()).hexdigest()
            not in processed_chunks
        ]
        if len(chunks) != len(chunks_to_process):
            print(
                f"📊 {len(chunks) - len(chunks_to_process)} chunks already processed, skipping them."
            )
            # if the chunks are not processed then we will clear the database
            print("All chunks processed")
            neo4j_rag.clear_database()

    print(f"Total processed chunks: {len(processed_chunks)}")
    if (
        _get_user_input(
            "Do you want to overwrite the processed chunks? (y/n)", default="n"
        )
        == "y"
    ):
        # Use async file operations
        with Path(settings.DEFAULT_RAG_FILES_HASH_TXT_PATH).open("w") as file:
            file.write("")
        with Path(settings.DEFAULT_RAG_FILES_PROCESSED_TRIPLES_PATH).open("w") as file:
            file.write("[]")

        asyncio.run(
            process_chunks_with_immediate_saving(
                chunks_to_process, neo4j_rag.prompt_openai_for_triples
            )
        )


def extract_triples_process_query():
    """
    here we will get the query form tne user and then retrieve the triples from the knowledge graph
    then we will use llm to process the triples and relation with the query and return the result
    like if query is "who is Elon Musk?" then we will return the llm response of the triples related to Elon Musk
    :return:
    """
    pass


def get_all_triples_from_file() -> list:
    """
    Retrieves all triples from the processed_triple.json file.
    Returns:
        list: A list of all triples.
    """
    if not pathlib.Path(settings.DEFAULT_RAG_FILES_PROCESSED_TRIPLES_PATH).exists():
        raise FileNotFoundError(
            "Processed triples file not found. Please run the processing function first."
        )

    with Path(settings.DEFAULT_RAG_FILES_PROCESSED_TRIPLES_PATH).open("r") as file:
        return json.load(file)


async def mark_triple_chunk(triples: list, chunk_hash: str):
    """
    ASYNC VERSION: Non-blocking file operations using aiofiles
    """
    # ✅ LAZY LOADING: Import aiofiles only when this async function is called
    try:
        import aiofiles
        import aiofiles.os
    except ImportError as e:
        raise ImportError(f"aiofiles library required for async file operations: {e}")

    # Async file append for hash
    async with aiofiles.open(settings.DEFAULT_RAG_FILES_HASH_TXT_PATH, "a") as file:
        await file.write(chunk_hash + "\n")

    # Async file operations for triples
    if await aiofiles.os.path.exists(settings.DEFAULT_RAG_FILES_PROCESSED_TRIPLES_PATH):
        async with aiofiles.open(
            settings.DEFAULT_RAG_FILES_PROCESSED_TRIPLES_PATH, "r"
        ) as file:
            content = await file.read()
            existing_triples = json.loads(content)

        existing_triples.extend(triples)

        async with aiofiles.open(
            settings.DEFAULT_RAG_FILES_PROCESSED_TRIPLES_PATH, "w"
        ) as file:
            await file.write(json.dumps(existing_triples, indent=4))
    else:
        async with aiofiles.open(
            settings.DEFAULT_RAG_FILES_PROCESSED_TRIPLES_PATH, "w"
        ) as file:
            await file.write(json.dumps(triples, indent=4))


def get_processed_chunks() -> set:
    """
    Retrieves a set of processed chunks from a txt file.
    :return: set: A set of processed chunk identifiers.
    """
    if not pathlib.Path(settings.DEFAULT_RAG_FILES_HASH_TXT_PATH).exists():
        Path(
            settings.DEFAULT_RAG_FILES_HASH_TXT_PATH
        ).open("w").close()  # Create the file if it doesn't exist
        # raise FileNotFoundError("Processed chunks file not found. Please run the processing function first.")
    with Path(settings.DEFAULT_RAG_FILES_HASH_TXT_PATH).open("r") as file:
        return {line.strip() for line in file if line.strip()}


def text_rag_search_using_llm(query: str, chunks: list[Document]) -> dict:
    """
    Perform a text-based RAG search using a query and a PDF file.
    This function uses the Google Generative AI to find similar chunks in the PDF document.
    :returns :list: A list of Document objects containing the most relevant chunks.
    :param query: The search query.
    :param chunks: List of Document objects representing the PDF content.
    """
    try:
        similar = search_similar_chunks_genai(query, chunks)
        system_prompt = (
            "You are an intelligent document analysis assistant that helps users find and understand information from text documents.\n\n"
            "**Your Mission:**\n"
            "Analyze the user's question and the most relevant document chunks to provide a comprehensive, accurate answer.\n\n"
            "**What You'll Receive:**\n"
            "- A specific question from the user\n"
            "- Text chunks from documents that are most similar to their question\n\n"
            "**Your Response Should:**\n"
            "1. **Directly answer the user's question** using information from the provided chunks\n"
            "2. **Synthesize information** from multiple chunks when they complement each other\n"
            "3. **Provide context and explanation** to help the user understand the topic fully\n"
            "4. **Be comprehensive yet focused** on what the user actually asked\n"
            "5. **Reference specific details** from the chunks to support your answer\n\n"
            "**Important Guidelines:**\n"
            "- Only use information that's actually present in the provided chunks\n"
            "- If the chunks don't contain enough information to answer the question, be honest about this\n"
            "- Organize your response logically and clearly\n"
            "- Write in a conversational, helpful tone\n"
            "- Include relevant details that add value to your answer\n\n"
            "**Response Format:**\n"
            "Return a JSON object with this structure:\n"
            "{\n"
            '  "answer": "Your comprehensive, well-organized answer based on the document chunks",\n'
            '  "source_chunks": ["Brief description of chunk 1 content", "Brief description of chunk 2 content"]\n'
            "}\n\n"
            "If you cannot answer the question based on the provided chunks, respond with:\n"
            "{\n"
            '  "answer": "I cannot find sufficient information in the provided document chunks to answer your question about [topic]. The available information covers [what is available], but doesn\'t address [what\'s missing].",\n'
            '  "source_chunks": ["Description of what information is available"]\n'
            "}\n\n"
            "Your goal is to be as helpful as possible while staying accurate to the source material."
        )
        prompt = f"User Query: {query}\nSimilar Chunks:\n" + "\n".join(
            [f"{i + 1} : {chunk.page_content}" for i, chunk in enumerate(similar)]
        )

        llm = ModelManager(model=settings.GPT_MODEL)
        response = llm.invoke([settings.HumanMessage(content=system_prompt), prompt])
        result = json.loads(response.content)
        if "answer" not in result or "source_chunks" not in result:
            raise ValueError(
                "Response format is incorrect. Expected keys 'answer' and 'source_chunks'."
            )
        return result
    except Exception as e:
        if settings.socket_con:
            settings.socket_con.send_error(f"Error during RAG search: {e}")
        else:
            print(f"Error during RAG search: {e}")
        return {"answer": "An error occurred during the search.", "source_chunks": []}


async def _clear_rag_files_async():
    """Helper async function to clear RAG files"""
    import aiofiles
    async with aiofiles.open(settings.DEFAULT_RAG_FILES_HASH_TXT_PATH, "w") as file:
        await file.write("")
    async with aiofiles.open(settings.DEFAULT_RAG_FILES_PROCESSED_TRIPLES_PATH, "w") as file:
        await file.write("[]")


if __name__ == "__main__":
    # print(search_similar_chunks_genai("kafka", load_pdf_document()))
    load_pdf_document(r"C:\Users\pirat\PycharmProjects\AI_llm\RAG_FILES\tech.txt")
    pass
