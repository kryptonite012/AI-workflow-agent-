# 🏗️ Core Package

**Core Application Logic for AI-Agent-Workflow**

> Central orchestration, initialization, and workflow management.

---

## 📋 **Table of Contents**

1. [Why We Need This Package](#why-we-need-this-package)
2. [Components](#components)
3. [Application Flow](#application-flow)
4. [Quick Start Guide](#quick-start-guide)

---

## 🎯 **Why We Need This Package**

This package contains:
- ✅ **Initialization** - App startup logic
- ✅ **Orchestration** - Main workflow coordinator
- ✅ **Chat Management** - Conversation handling
- ✅ **Graph Workflow** - LangGraph agent flow

---

## 🧩 **Components**

### **1. Chat Initializer**

Sets up the chat system:
```python
from src.core.chat_initializer import ChatInitializer

initializer = ChatInitializer()
initializer.initialize()
```

### **2. Main Orchestrator**

Main entry point:
```python
from src.main_orchestrator import main

main()
```

### **3. Graph Workflow**

LangGraph agent workflow:
- Message classification
- Tool selection
- Agent execution
- Response generation

---

## 📊 **Application Flow**

```
Start
  ↓
Initialize (chat_initializer.py)
  ↓
Main Loop (main_orchestrator.py)
  ↓
User Input
  ↓
Process (graph workflow)
  ↓
Response
  ↓
Loop or Exit
```

---

## 🚀 **Quick Start Guide**

### **Run Application**

```bash
python src/main_orchestrator.py
```

### **Initialize Components**

```python
from src.core.chat_initializer import ChatInitializer

init = ChatInitializer()
init.initialize()
```

---

## 🆘 **Support**

**Questions?** Check:
1. Main orchestrator code
2. Chat initializer docs

---

**Status:** ✅ **Production-Ready**

**Maintainer:** AI-Agent-Workflow Team

**Last Updated:** December 24, 2025

