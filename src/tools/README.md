# 🛠️ Tools Package

**Tool Implementations for AI Agents**

> Extensible tool system that allows agents to interact with external services, databases, and APIs.

---

## 📋 **Table of Contents**

1. [Why We Need This Package](#why-we-need-this-package)
2. [Available Tools](#available-tools)
3. [How Tools Work](#how-tools-work)
4. [Quick Start Guide](#quick-start-guide)
5. [Creating Custom Tools](#creating-custom-tools)

---

## 🎯 **Why We Need This Package**

### **The Problem**

LLMs alone can't:
- ❌ Access real-time information
- ❌ Query databases
- ❌ Call APIs
- ❌ Execute code

### **What This Package Provides**

**Powerful tools** that agents can use:
- ✅ **Web Search** - Google, DuckDuckGo
- ✅ **Database** - Neo4j graph queries
- ✅ **File I/O** - Read/write files
- ✅ **APIs** - External service calls
- ✅ **Browser** - Web automation

---

## 🔧 **Available Tools**

### **1. Google Search**
```python
from src.tools.google_search import google_search

results = google_search("Python tutorials")
```

### **2. Neo4j Query**
```python
from src.tools.neo4j_tool import query_neo4j

result = query_neo4j("MATCH (n) RETURN n LIMIT 10")
```

### **3. File Reader**
```python
from src.tools.file_reader import read_file

content = read_file("data.txt")
```

### **4. Code Executor**
```python
from src.tools.code_executor import execute_python

output = execute_python("print('Hello')")
```

---

## ⚙️ **How Tools Work**

### **Tool Interface**

Every tool implements:
```python
class Tool:
    name: str
    description: str
    
    def invoke(self, params: dict) -> str:
        """Execute tool logic"""
        pass
```

### **Tool Registration**

```python
# Tools are auto-registered
from src.tools import get_all_tools

tools = get_all_tools()
```

---

## 🚀 **Quick Start Guide**

### **Using Tools Directly**

```python
from src.tools.google_search import google_search

# Simple search
results = google_search("AI news")
print(results)
```

### **Using Tools with Agents**

```python
from src.agents.tool_agent import ToolAgent

agent = ToolAgent()
response = agent.invoke("Search for Python tutorials")
```

---

## 🎨 **Creating Custom Tools**

### **Step 1: Create Tool File**

```python
# src/tools/my_tool.py

from langchain.tools import tool

@tool
def my_custom_tool(query: str) -> str:
    """
    My custom tool that does something useful.
    
    Args:
        query: The input query
        
    Returns:
        Tool result as string
    """
    # Your tool logic here
    result = do_something(query)
    return result
```

### **Step 2: Register Tool**

Tool is auto-registered when imported.

---

## 🆘 **Support**

**Questions?** Check:
1. This README
2. Individual tool files
3. LangChain tools documentation

---

**Status:** ✅ **Production-Ready**

**Maintainer:** AI-Agent-Workflow Team

**Last Updated:** December 24, 2025

