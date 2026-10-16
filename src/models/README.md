# 🗂️ Models Package

**Data Models and Schemas**

> Pydantic models and data structures for type-safe data handling.

---

## 📋 **Table of Contents**

1. [Why We Need This Package](#why-we-need-this-package)
2. [Available Models](#available-models)
3. [How to Use Models](#how-to-use-models)

---

## 🎯 **Why We Need This Package**

### **The Problem**

Without models:
- ❌ No type safety
- ❌ Invalid data
- ❌ Hard to validate
- ❌ Poor documentation

### **What This Package Provides**

**Type-safe models** with:
- ✅ **Validation** - Automatic data validation
- ✅ **Type Hints** - IDE support
- ✅ **Documentation** - Self-documenting code
- ✅ **Serialization** - Easy JSON conversion

---

## 📚 **Available Models**

### **State Models**

Graph state definitions:
```python
from src.models.state import AgentState

state = AgentState(
    messages=[...],
    tool_results=[...],
    final_answer="..."
)
```

### **Tool Models**

Tool parameter schemas:
```python
from src.models.tool_models import SearchParams

params = SearchParams(
    query="Python tutorials",
    max_results=10
)
```

---

## 🚀 **Quick Start Guide**

### **Using Models**

```python
from src.models.state import AgentState
from langchain_core.messages import HumanMessage

# Create state
state = AgentState(
    messages=[HumanMessage(content="Hello")]
)

# Access fields
print(state.messages)
```

### **Validation**

```python
from pydantic import ValidationError

try:
    params = SearchParams(query="", max_results=-1)
except ValidationError as e:
    print(e)
```

---

## 🆘 **Support**

**Questions?** Check:
1. Pydantic documentation
2. Model definitions

---

**Status:** ✅ **Production-Ready**

**Maintainer:** AI-Agent-Workflow Team

**Last Updated:** December 24, 2025

