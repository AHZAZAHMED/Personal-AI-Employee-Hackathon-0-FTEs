"""
Qwen/Ollama AI Integration - The Brain

Acts as the reasoning engine that:
1. Reads task content and decides what action is needed
2. Selects the appropriate skill
3. Generates responses (emails, plans, etc.)

Supports both Qwen3-Coder:480b-cloud and Ollama models.
Based on the original Qwen integration - preserved in backup_qwen/ directory.
"""

import subprocess
import json
import logging
import shutil
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def call_qwen_coder(prompt: str, vault_path: str = "AI_Employee_Vault", timeout: int = 300) -> Optional[str]:
    """
    Call Qwen3-Coder:480b-cloud model directly via HTTP API.

    Args:
        prompt: The prompt to send to Qwen
        vault_path: Path to the vault directory
        timeout: Timeout in seconds (increased for larger model)

    Note: Timeout increased to 300s to allow sufficient time for
    Qwen3-Coder:480b-cloud model processing.
    """
    try:
        # Prepare the payload for Qwen API
        payload = {
            "model": "qwen3-coder:480b-cloud",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 2048
        }

        # Write payload to temp file
        vault_path_obj = Path(vault_path).absolute()
        vault_path_obj.mkdir(parents=True, exist_ok=True)  # Ensure vault path exists
        payload_file = vault_path_obj / ".qwen_payload_temp.json"
        payload_file.write_text(json.dumps(payload), encoding="utf-8")

        # Call Qwen via curl
        result = subprocess.run(
            ["curl", "-s", "-X", "POST", "http://localhost:11434/v1/chat/completions",
             "-H", "Content-Type: application/json", "-d", "@" + str(payload_file)],
            capture_output=True, text=True, timeout=timeout,
            cwd=str(Path(vault_path).absolute()),
            encoding="utf-8", errors="replace"
        )
        payload_file.unlink(missing_ok=True)

        logger.info(f"Qwen exit: {result.returncode}, stdout_len: {len(result.stdout)}, stderr_len: {len(result.stderr)}")

        # ALWAYS log stderr (this is where the error message is!)
        if result.stderr:
            logger.error(f"Qwen STDERR: {result.stderr[:1000]}")

        if result.stdout:
            logger.info(f"Qwen stdout preview: {result.stdout[:300]}")
            try:
                response_data = json.loads(result.stdout)
                if "choices" in response_data and len(response_data["choices"]) > 0:
                    return response_data["choices"][0]["message"]["content"].strip()
            except json.JSONDecodeError:
                logger.error("Failed to parse Qwen response as JSON")
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


def call_ollama(prompt: str, vault_path: str = "AI_Employee_Vault", timeout: int = 180, model: str = "llama3") -> Optional[str]:
    """
    Call Ollama with a prompt and get response.

    Args:
        prompt: The prompt to send to Ollama
        vault_path: Path to the vault directory
        timeout: Timeout in seconds
        model: Ollama model to use (default: llama3)

    Note: Timeout increased to 180s to allow Ollama sufficient time for
    model startup, prompt processing, and response generation.
    """
    ollama_path = shutil.which("ollama")
    if not ollama_path:
        logger.warning("Ollama not found on PATH")
        return None

    try:
        # Prepare the payload for Ollama API
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }

        # Write payload to temp file
        vault_path_obj = Path(vault_path).absolute()
        vault_path_obj.mkdir(parents=True, exist_ok=True)  # Ensure vault path exists
        payload_file = vault_path_obj / ".ollama_payload_temp.json"
        payload_file.write_text(json.dumps(payload), encoding="utf-8")

        # Call Ollama via curl (most reliable way to interact with Ollama API)
        result = subprocess.run(
            ["curl", "-s", "-X", "POST", "http://localhost:11434/api/generate",
             "-H", "Content-Type: application/json", "-d", "@" + str(payload_file)],
            capture_output=True, text=True, timeout=timeout,
            cwd=str(Path(vault_path).absolute()),
            encoding="utf-8", errors="replace"
        )
        payload_file.unlink(missing_ok=True)

        logger.info(f"Ollama exit: {result.returncode}, stdout_len: {len(result.stdout)}, stderr_len: {len(result.stderr)}")

        # ALWAYS log stderr (this is where the error message is!)
        if result.stderr:
            logger.error(f"Ollama STDERR: {result.stderr[:1000]}")

        if result.stdout:
            logger.info(f"Ollama stdout preview: {result.stdout[:300]}")
            try:
                response_data = json.loads(result.stdout)
                if "response" in response_data:
                    return response_data["response"].strip()
            except json.JSONDecodeError:
                logger.error("Failed to parse Ollama response as JSON")
                return result.stdout.strip()

        # If exit code != 0, log it as error
        if result.returncode != 0:
            logger.error(f"Ollama failed with exit code: {result.returncode}")

        return None
    except subprocess.TimeoutExpired:
        logger.warning(f"Ollama timed out after {timeout}s")
        return None
    except Exception as e:
        logger.error(f"Ollama call failed: {e}")
        return None


def call_ai_model(prompt: str, vault_path: str = "AI_Employee_Vault", timeout: int = 300, model: str = "qwen3-coder:480b-cloud") -> Optional[str]:
    """
    Unified AI model calling function that supports both Qwen and Ollama models.

    Args:
        prompt: The prompt to send to the AI model
        vault_path: Path to the vault directory
        timeout: Timeout in seconds
        model: Model to use (default: qwen3-coder:480b-cloud)

    Returns:
        Response from the AI model or None if failed
    """
    if model == "qwen3-coder:480b-cloud":
        return call_qwen_coder(prompt, vault_path, timeout)
    else:
        return call_ollama(prompt, vault_path, timeout, model)


def ai_select_skill(task_content: str, available_skills: list) -> Optional[str]:
    """
    Use Qwen3-Coder:480b-cloud to decide which skill should handle a task.

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

    response = call_ai_model(prompt, model="qwen3-coder:480b-cloud")
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
    Use Qwen3-Coder:480b-cloud to generate a professional email response.
    """
    body = body[:500]
    prompt = f"""Write ONLY the email reply text. No other commentary.

FROM: {from_email}
SUBJECT: {subject}
EMAIL: {body[:300]}

EMAIL REPLY:"""

    response = call_ai_model(prompt, timeout=30, model="qwen3-coder:480b-cloud")
    if response and len(response) > 30:
        return response
    return None


def ai_generate_plan(task_type: str, task_data: Dict, task_content: str) -> Optional[str]:
    """
    Use Qwen3-Coder:480b-cloud to generate a detailed action plan.
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

    response = call_ai_model(prompt, timeout=30, model="qwen3-coder:480b-cloud")
    if response and len(response) > 50:
        return response
    return None


def ai_analyze_email(email_content: str) -> Dict[str, Any]:
    """
    Use Qwen3-Coder:480b-cloud to analyze an email and extract key information.

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

    response = call_ai_model(prompt, timeout=60, model="qwen3-coder:480b-cloud")
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
