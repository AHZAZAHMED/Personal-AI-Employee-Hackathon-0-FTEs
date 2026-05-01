# 🚀 Agent Skill Refactor Prompt (Gold-Tier System)

## Role
You are a **senior AI systems architect**.

---

## 🧠 Context

I have an existing AI automation system with mixed execution patterns:

- **AI CLI Delegation** (Qwen/Claude spawning scripts via prompts)
- **Hardcoded Python imports** (direct function calls)
- **Standalone watcher/daemon scripts**

### Current Problems:
- Functionalities exist and work correctly ✅
- BUT they are NOT implemented as proper agent skills ❌
- `.md` files exist but are NOT used at runtime ❌
- There is NO dynamic skill discovery ❌
- No structured tool interface ❌

---

## 🎯 Goal

Convert functionality one by one into a **production-ready agent skill** that can:

- Be registered as a tool
- Be dynamically selected by an agent (LLM)
- Be executed via a clean interface

---

## ⚠️ Strict Requirements

### 1. DO NOT change business logic
- Keep original functionality EXACTLY the same
- Only refactor structure

---

### 2. Convert into this architecture
skills/<skill_name>/
│
├── skill.py # agent entry point (REQUIRED)
├── schema.json # tool definition (REQUIRED)
├── service.py # core logic (REQUIRED)
└── README.md # optional documentation


---

### 3. skill.py (VERY IMPORTANT)

- Acts as the bridge between agent and logic
- Must:
  - Validate inputs
  - Call service layer
  - Handle errors
  - Return structured output

#### Example:
```python
def <skill_name>(...):
    """
    Clear description:
    - When to use this skill
    - What problem it solves
    """
    try:
        result = service_function(...)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}



### 4. schema.json (CRITICAL FOR AGENT)
{
  "name": "send_email",
  "description": "Use this to send emails when a user requests communication or reply to a message.",
  "parameters": {
    "to": "string",
    "subject": "string",
    "body": "string"
  }
}

### 5. service.py
 - Move ALL business logic here
 - No agent-related code
 - Can call APIs, DB, subprocess, etc.


### 6. Handle existing patterns

A. AI CLI Delegation
Extract actual script being called
Wrap it into service.py
Remove dependency on prompt-based execution
B. Hardcoded Import
Move logic into service.py
Expose via skill.py
C. Standalone Script
Convert main logic into function
Wrap inside skill.py

### 7. Output Format (STRICT)
 You MUST return:

Folder structure
Full code for:
skill.py
schema.json
service.py
Short explanation of how it replaced old system


🧩 Functionality to Convert
<PASTE FUNCTIONALITY FROM FUNCTIONALITY_INVENTORY OR CODE HERE>

🧠 Additional Context

Previously the system:

Used AI (Qwen/Claude) to decide actions via prompts
Stored tasks in Inbox/, Needs_Action/
Called scripts via subprocess

Now we want:

👉 A clean AGENT SKILL SYSTEM
👉 Agent selects tools based on schema
👉 NOT based on prompt hacks

🚀 Final Instruction

Refactor this functionality into a clean, scalable, agent skill.

DO NOT:
Add unnecessary complexity
Change behavior
Skip error handling
Focus on:
Clean architecture
Agent compatibility
Reusability
Production readiness