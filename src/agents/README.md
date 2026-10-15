# 🤖 Agents Package
**Last Updated:** December 24, 2025

**Maintainer:** AI-Agent-Workflow Team

**Status:** ✅ **Production-Ready**

---

3. LangGraph documentation
2. Individual agent files
1. This README
**Questions?** Check:

## 🆘 **Support**

---

```
print(get_all_tools())
from src.tools import get_all_tools
```python
**Fix:** Check tool registry:

**Cause:** Tool not registered

### **Agent Can't Find Tool**

---

```
agent = ToolAgent(max_iterations=10)
```python
**Fix:** Set max iterations:

**Cause:** No termination condition

### **Agent Loops Forever**

## 🐛 **Troubleshooting**

---

```
agent = ToolAgent(llm=model)
model = ModelManager(model="qwen2.5:32b-instruct")

from src.utils.model_manager import ModelManager
# Agents use ModelManager
```python

### **LLM Integration**

- 🖥️ **Browser** - Web automation
- 🌐 **API Calls** - External services
- 🧮 **Code Execution** - Run Python code
- 📄 **File Operations** - Read, write files
- 🗄️ **Database** - Neo4j queries
- 🔍 **Web Search** - Google, DuckDuckGo

### **Tools Available**

## 📚 **Agent Capabilities**

---

```
    return result
    result = tool.invoke(params)
    tool = self.tools[tool_name]
    """Execute tool"""
def use_tool(self, tool_name, params):
```python

### **Step 3: Add Tool Execution**

```
    return thought
    thought = self.llm.invoke(prompt)
    prompt = f"How should I solve: {task}"
    """Agent reasoning logic"""
def think(self, task):
```python

### **Step 2: Implement Reasoning**

```
        pass
        # Your agent logic here
    def invoke(self, messages):
    
        self.memory = []
        self.tools = tools
        self.llm = llm
    def __init__(self, llm, tools):
class MyCustomAgent:

from langchain_core.messages import HumanMessage, AIMessage
from langchain.agents import AgentExecutor
```python

### **Step 1: Define Agent Class**

## 🛠️ **Creating Custom Agents**

---

```
}
    "final_answer": "..."        # Response
    "reasoning": "...",          # Agent's thought process
    "tool_results": [...],        # Tool outputs
    "messages": [...],           # Conversation history
state = {
# Agent maintains state across turns
```python

### **Agent State**

```
print(result)

])
    HumanMessage(content="What's the weather in Tokyo?")
result = agent.invoke([
# Send message

agent = ToolAgent()
# Create agent

from langchain_core.messages import HumanMessage
from src.agents.tool_agent import ToolAgent
```python

### **Using an Agent**

## 🚀 **Quick Start Guide**

---

```
Final: "The current weather is 25°C and sunny."
↓
Agent synthesizes result
```python
**4. Response Generation**

```
Result: "Temperature: 25°C, Sunny"
↓
Execute: google_search("current weather")
```python
**3. Tool Execution**

```
Generates params: {"query": "current weather"}
↓
Selects: google_search tool
↓
Agent analyzes: "Need weather data"
```python
**2. Tool Selection**

```
Route to Tool Agent
↓
Classifier: tool_needed
↓
User: "What's the weather?"
```python
**1. Message Classification**

### **Step-by-Step Flow**

## 📊 **How Agents Work**

---

5. Return result
4. Execute tool
3. Generate parameters
2. Select appropriate tool
1. Classify if tools needed
**How it works:**

**What:** Uses tools to accomplish tasks

### **3. Tool-Calling Agent**

---

```
Execute each step...

5. Generate report
4. Compare features
3. Research each competitor
2. Find top 5 competitors
1. Identify industry
Plan:

User: "Analyze competitors for my startup"
```
**Example:**

4. **Adapt** - Re-plan if needed
3. **Verify** - Check results
2. **Execute** - Run each step
1. **Plan** - Break task into steps
**How it works:**

**What:** Creates plan first, then executes

### **2. Plan-and-Execute Agent**

---

```
Final Answer: The weather in Tokyo is 25°C and sunny.
Thought: I have the information needed

Observation: Temperature is 25°C, sunny
Action: google_search("Tokyo weather")
Thought: I need to search for Tokyo weather

User: "What's the weather in Tokyo?"
```
**Example:**

4. **Repeat** - Until task complete
3. **Observe** - See tool result
2. **Act** - Use a tool
1. **Reason** - Think about the task
**How it works:**

**What:** Reason + Act pattern

### **1. ReAct Agent**

## 🧠 **Agent Types**

---

```
└─────────────────────────────────────────────────────────┘
│                                                          │
│  └─────────────────────────────────────────────────────┘│
│  │    • Return to user                                 ││
│  │    • Generate final answer                          ││
│  │    • Synthesize tool results                        ││
│  │ 4. Response Generation                              ││
│  ┌─────────────────────────────────────────────────────┐│
│                          ↓                               │
│  └───────────────────────┬─────────────────────────────┘│
│  │    • Collect results                                ││
│  │    • Execute tools                                  ││
│  │    • Generate tool parameters                       ││
│  │ 3. Tool Selection & Execution                       ││
│  ┌─────────────────────────────────────────────────────┐│
│                          ↓                               │
│  └───────────────────────┬─────────────────────────────┘│
│  │    • Plans execution steps                          ││
│  │    • Decides which tools needed                     ││
│  │    • LLM analyzes task                              ││
│  │ 2. Reasoning Phase                                  ││
│  ┌─────────────────────────────────────────────────────┐│
│                          ↓                               │
│  └───────────────────────┬─────────────────────────────┘│
│  │    • Classify message type                          ││
│  │    • Parse user intent                              ││
│  │ 1. Agent Receives Task                             ││
│  ┌─────────────────────────────────────────────────────┐│
│      ↓                                                   │
│  User Query                                              │
│                                                          │
├─────────────────────────────────────────────────────────┤
│          (Intelligent Task Execution System)             │
│              AGENTS PACKAGE ARCHITECTURE                 │
┌─────────────────────────────────────────────────────────┐
```

## 🏗️ **Architecture Overview**

---

- ✅ **Remember** - Maintain conversation context
- ✅ **Execute** - Complete complex workflows
- ✅ **Reason** - Think through problems
- ✅ **Plan** - Break tasks into steps
- ✅ **Use Tools** - Search web, query databases, run code
**Intelligent agents** that can:

### **What This Package Provides**

- ❌ Can't execute multi-step workflows
- ❌ Can't remember context
- ❌ Can't break down complex tasks
- ❌ Can't use tools
Simple chatbots can only answer questions:

### **The Problem**

## 🎯 **Why We Need This Package**

---

6. [Creating Custom Agents](#creating-custom-agents)
5. [Quick Start Guide](#quick-start-guide)
4. [How Agents Work](#how-agents-work)
3. [Agent Types](#agent-types)
2. [Architecture Overview](#architecture-overview)
1. [Why We Need This Package](#why-we-need-this-package)

## 📋 **Table of Contents**

---

> Intelligent agents that can reason, plan, and execute complex tasks using tools and LLMs.

**AI Agent Implementations for AI-Agent-Workflow**


