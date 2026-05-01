"""
Qwen AI Integration - The Brain

Qwen Code acts as the reasoning engine that:
1. Reads task content and decides what action is needed
2. Selects the appropriate skill
3. Generates responses (emails, plans, etc.)

This replaces the hardcoded template fallback with actual AI reasoning.
"""

import subprocess
import json
import logging
import shutil
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def call_qwen(prompt: str, vault_path: str = "AI_Employee_Vault", timeout: int = 180) -> Optional[str]:
    """
    Call Qwen Code with a prompt and get response.
    Writes prompt to temp file but formats it so Qwen executes it directly.
    
    Note: Timeout increased to 180s to allow Qwen Code sufficient time for
    model startup, prompt processing, and response generation.
    """
    qwen_path = shutil.which("qwen")
    if not qwen_path:
        logger.warning("Qwen Code not found on PATH")
        return None
    
    try:
        # Write prompt to temp file with explicit instruction format
        prompt_file = Path(vault_path).absolute() / ".qwen_prompt_temp.txt"
        prompt_file.write_text(prompt, encoding="utf-8")
        
        result = subprocess.run(
            [qwen_path, "--prompt", str(prompt_file)],
            capture_output=True, text=True, timeout=timeout,
            cwd=str(Path(vault_path).absolute()),
            encoding="utf-8", errors="replace"
        )
        prompt_file.unlink(missing_ok=True)

        logger.info(f"Qwen exit: {result.returncode}, stdout_len: {len(result.stdout)}, stderr_len: {len(result.stderr)}")
        
        # ALWAYS log stderr (this is where the error message is!)
        if result.stderr:
            logger.error(f"Qwen STDERR: {result.stderr[:1000]}")
        
        if result.stdout:
            logger.info(f"Qwen stdout preview: {result.stdout[:300]}")
        
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        
        # If exit code != 0, log it as error
        if result.returncode != 0:
            logger.error(f"Qwen failed with exit code: {result.returncode}")
        
        return None
    except subprocess.TimeoutExpired:
        logger.warning(f"Qwen timed out after {timeout}s")
        return None
    except Exception as e:
        logger.error(f"Qwen call failed: {e}")
        return None


def ai_select_skill(task_content: str, available_skills: list) -> Optional[str]:
    """
    Use Qwen to decide which skill should handle a task.
    
    Args:
        task_content: The task file content
        available_skills: List of skill names with descriptions
    
    Returns:
        Selected skill name, or None
    """
    skills_desc = "\n".join(f"- {s['name']}: {s['description']}" for s in available_skills)
    
    prompt = f"""You are an AI Employee task router. Given a task and available skills, select the most appropriate skill.

AVAILABLE SKILLS:
{skills_desc}

TASK CONTENT:
{task_content[:3000]}

Respond with ONLY the skill name that should handle this task. If no skill matches, respond with "NONE".

Skill name:"""
    
    response = call_qwen(prompt)
    if response:
        # Extract skill name from response
        skill = response.strip().split("\n")[0].strip()
        # Match against available skills
        for s in available_skills:
            if s["name"].lower() in skill.lower() or skill.lower() in s["name"].lower():
                return s["name"]
    return None


def ai_generate_email_response(from_email: str, subject: str, body: str) -> Optional[str]:
    """
    Use Qwen to generate a professional email response.
    """
    body = body[:500]
    prompt = f"""Write ONLY the email reply text. No other commentary.

FROM: {from_email}
SUBJECT: {subject}
EMAIL: {body[:300]}

EMAIL REPLY:"""
    
    response = call_qwen(prompt, timeout=30)
    if response and len(response) > 30:
        return response
    return None


def ai_generate_plan(task_type: str, task_data: Dict, task_content: str) -> Optional[str]:
    """
    Use Qwen to generate a detailed action plan.
    """
    subject = task_data.get("subject", task_data.get("from", "Unknown task"))
    prompt = f"""Write a task plan. Output ONLY the plan text. No questions, no commentary.

TASK: {subject}
DETAILS: {task_content[:300]}

# Task Plan
## Steps
1. [ ] Action step 1
2. [ ] Action step 2
3. [ ] Action step 3

PLAN:"""
    
    response = call_qwen(prompt, timeout=30)
    if response and len(response) > 50:
        return response
    return None


def ai_analyze_email(email_content: str) -> Dict[str, Any]:
    """
    Use Qwen to analyze an email and extract key information.
    
    Args:
        email_content: Full email content
    
    Returns:
        Dict with analysis results
    """
    prompt = f"""Analyze this email and extract key information:

EMAIL:
---
{email_content[:3000]}
---

Respond in JSON format:
{{
  "intent": "what the sender wants",
  "urgency": "Low/Medium/High/Critical",
  "requires_reply": true/false,
  "sentiment": "positive/neutral/negative",
  "key_topics": ["topic1", "topic2"],
  "suggested_action": "what should be done"
}}

JSON:"""
    
    response = call_qwen(prompt, timeout=60)
    if response:
        try:
            # Try to parse JSON from response
            if "```" in response:
                response = response.split("```")[1].strip()
                if response.startswith("json"):
                    response = response[4:].strip()
            return json.loads(response)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse Qwen JSON response")
    return {
        "intent": "unknown",
        "urgency": "Medium",
        "requires_reply": True,
        "sentiment": "neutral",
        "key_topics": [],
        "suggested_action": "review manually"
    }
