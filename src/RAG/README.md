# 📖 RAG Package

**Retrieval Augmented Generation System**

> Enhance LLM responses with relevant document retrieval.

---

## 📋 **Table of Contents**

1. [What is RAG](#what-is-rag)
2. [How RAG Works](#how-rag-works)
3. [Components](#components)
4. [Quick Start Guide](#quick-start-guide)
5. [Indexing Documents](#indexing-documents)

---

## 🎯 **What is RAG**

**Retrieval Augmented Generation** enhances LLM responses by:
1. **Retrieving** relevant documents
2. **Augmenting** the prompt with context
3. **Generating** informed responses

### **Why RAG?**

- ✅ **Accuracy** - Ground answers in facts
- ✅ **Up-to-date** - Use latest documents
- ✅ **Specific** - Company/domain knowledge
- ✅ **Cited** - Reference sources

---

## ⚙️ **How RAG Works**

```
User Query: "What is Kafka?"
    ↓
1. Embed Query → Vector
    ↓
2. Search Vector DB → Find similar docs
    ↓
3. Retrieve Top K Documents
    ↓
4. Augment Prompt with Context
    ↓
5. LLM Generates Answer
    ↓
Response: "Apache Kafka is a distributed streaming platform..."
```

---

## 🧩 **Components**

### **1. Document Loader**

Load documents from files:
```python
from src.RAG.document_loader import load_pdf

chunks = load_pdf("kafka.pdf")
```

### **2. Embeddings**

Convert text to vectors:
```python
from src.RAG.embeddings import create_embeddings

vectors = create_embeddings(chunks)
```

### **3. Vector Store**

Store and search embeddings:
```python
from src.RAG.vector_store import VectorStore

store = VectorStore()
store.add_documents(chunks, vectors)

results = store.search(query="What is Kafka?")
```

### **4. Retriever**

High-level retrieval interface:
```python
from src.RAG.retriever import retrieve_context

context = retrieve_context("What is Kafka?")
```

---

## 🚀 **Quick Start Guide**

### **Step 1: Index Documents**

```python
from src.RAG.indexer import index_document

# Index a PDF
index_document("kafka.pdf")
```

### **Step 2: Query with RAG**

```python
from src.RAG.rag_chain import RAGChain

rag = RAGChain()
response = rag.query("What is Kafka?")
print(response)
```

---

## 📄 **Indexing Documents**

### **Supported Formats**

- PDF
- TXT
- DOCX
- MD

### **Index a File**

```python
from src.RAG.indexer import index_document

index_document("my_document.pdf")
```

### **Batch Indexing**

```python
from src.RAG.indexer import batch_index

batch_index([
    "doc1.pdf",
    "doc2.pdf",
    "doc3.txt"
])
```

---

## 🆘 **Support**

**Questions?** Check:
1. RAG documentation
2. LangChain RAG guides

---

**Status:** ✅ **Production-Ready**

**Maintainer:** AI-Agent-Workflow Team

**Last Updated:** December 24, 2025

