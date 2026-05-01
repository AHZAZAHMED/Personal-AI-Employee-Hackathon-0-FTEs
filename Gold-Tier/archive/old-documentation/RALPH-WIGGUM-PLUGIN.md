# Ralph Wiggum Stop Hook for AI Employee

**Purpose:** Keep Claude Code working autonomously until tasks are complete.

---

## Installation

This plugin is automatically loaded by Claude Code when running in Ralph mode.

---

## Usage

### **Start Ralph Loop:**

```bash
cd E:\Personal-AI-Employee-Hackathon-0-FTEs\Gold-Tier

# Start Ralph loop with task
python scripts\ralph_wiggum.py --vault AI_Employee_Vault --prompt "Process all files in /Needs_Action/"
```

### **How It Works:**

1. **Creates state file** with task prompt
2. **Runs Claude Code** with the prompt
3. **Monitors output** for completion signal
4. **Checks /Done/ folder** for completed tasks
5. **If not complete** → Re-injects prompt (loop continues)
6. **If complete** → Allows exit

---

## Completion Detection

### **Method 1: File Movement (Recommended)**

Task is complete when file moves from `/Needs_Action/` to `/Done/`

### **Method 2: Promise Output**

Task is complete when Claude outputs: `<promise>TASK_COMPLETE</promise>`

### **Method 3: Max Iterations**

Loop stops after N iterations (safety limit)

---

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--max-iterations` | 10 | Maximum loop iterations |
| `--timeout` | 300 | Timeout per iteration (seconds) |
| `--completion-promise` | TASK_COMPLETE | Completion signal text |
| `--check-done-folder` | true | Check /Done/ for completion |

---

## Example Prompts

### **Process Emails:**
```bash
python scripts\ralph_wiggum.py --vault AI_Employee_Vault \
  --prompt "Process all email files in /Needs_Action/. Read Company Handbook for rules. Create responses. Move completed to /Done/."
```

### **Generate Plans:**
```bash
python scripts\ralph_wiggum.py --vault AI_Employee_Vault \
  --prompt "Review all tasks in /Needs_Action/. Create detailed Plan.md files for each complex task."
```

### **Clear Inbox:**
```bash
python scripts\ralph_wiggum.py --vault AI_Employee_Vault \
  --prompt "Process all files in /Inbox/. Categorize and move to appropriate folders."
```

---

## Safety Features

1. **Max Iterations** - Prevents infinite loops
2. **Timeout** - Each iteration has time limit
3. **Error Handling** - Catches and logs errors
4. **Progress Tracking** - Logs each iteration
5. **Manual Interrupt** - Ctrl+C stops loop anytime

---

## Troubleshooting

### **Problem: Loop runs forever**

**Solution:** Lower `--max-iterations` or check task complexity

### **Problem: Claude exits too early**

**Solution:** Ensure task moves file to /Done/ before exiting

### **Problem: Task doesn't complete**

**Solution:** Break into smaller subtasks or increase max iterations

---

*Ralph Wiggum Loop v1.0 | Gold Tier | AI Employee Hackathon 0*
