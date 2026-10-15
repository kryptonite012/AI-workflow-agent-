# 📝 Prompts Package

**Prompt Templates for AI Agents**

> Carefully crafted prompts for different agent behaviors and task types.

---

## 📋 **Table of Contents**

1. [Why We Need This Package](#why-we-need-this-package)
2. [Available Prompts](#available-prompts)
3. [How to Use Prompts](#how-to-use-prompts)
4. [Creating Custom Prompts](#creating-custom-prompts)

---

## 🎯 **Why We Need This Package**

### **The Problem**

Prompt engineering is hard:
- ❌ Inconsistent prompt formats
- ❌ Duplicated prompt logic
- ❌ Hard to maintain prompts
- ❌ No versioning

### **What This Package Provides**

**Centralized prompts** that are:
- ✅ **Reusable** - One prompt, many uses
- ✅ **Maintainable** - Edit in one place
- ✅ **Versioned** - Track changes
- ✅ **Optimized** - Tested and refined

---

## 📚 **Available Prompts**

### **1. System Prompts**

```python
from src.prompts.system_prompts import get_system_prompt

# Get agent system prompt
prompt = get_system_prompt("agent_mode")
```

### **2. Task Prompts**

```python
from src.prompts.task_prompts import get_task_prompt

# Get tool selection prompt
prompt = get_task_prompt("tool_selection")
```

### **3. Formatting Prompts**

```python
from src.prompts.formatting import format_with_context

# Format prompt with context
formatted = format_with_context(
    template=prompt_template,
    context={"user_query": "What's the weather?"}
)
```

---

## 🚀 **Quick Start Guide**

### **Using a Prompt**

```python
from src.prompts.agent_prompts import Prompt

prompt_gen = Prompt()
system_prompt = prompt_gen.get_agent_mode_prompt()

# Use with LLM
response = llm.invoke([
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": "Help me"}
])
```

---

## 🎨 **Creating Custom Prompts**

### **Step 1: Create Prompt File**

```python
# src/prompts/my_prompts.py

CUSTOM_PROMPT = """
You are a helpful assistant specializing in {domain}.

Your task: {task}

Guidelines:
- Be concise
- Be accurate
- Cite sources
"""

def get_custom_prompt(domain: str, task: str) -> str:
    return CUSTOM_PROMPT.format(domain=domain, task=task)
```

### **Step 2: Use Custom Prompt**

```python
from src.prompts.my_prompts import get_custom_prompt

prompt = get_custom_prompt(
    domain="Python programming",
    task="Help debug code"
)
```

---

## 🆘 **Support**

**Questions?** Check:
1. Prompt engineering guides
2. Example prompts in package

---

**Status:** ✅ **Production-Ready**

**Maintainer:** AI-Agent-Workflow Team

**Last Updated:** December 24, 2025

