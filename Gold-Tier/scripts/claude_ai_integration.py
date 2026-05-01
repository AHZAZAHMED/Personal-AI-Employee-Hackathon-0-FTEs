"""
Claude AI Integration - The Brain

Acts as the reasoning engine that:
1. Reads task content and decides what action is needed
2. Selects the appropriate skill
3. Generates responses (emails, plans, etc.)

Uses Anthropic's Claude API (Sonnet 4.6) instead of Qwen/Ollama.
"""

import os
import json
import re
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Try to import Anthropic SDK
try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("Anthropic SDK not installed. Run: pip install anthropic")

# Try to import Google Gemini SDK (new package)
try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("Google GenAI SDK not installed. Run: pip install google-genai")


def sanitize_unicode(text: str) -> str:
    """
    Remove emojis and problematic Unicode characters for Windows compatibility.

    Args:
        text: Text that may contain emojis

    Returns:
        Text with emojis removed/replaced
    """
    if not text:
        return text

    # Replace common problematic characters first
    replacements = {
        '✓': '[OK]',
        '✅': '[OK]',
        '✗': '[X]',
        '❌': '[X]',
        '⚠': '[!]',
        '⚠️': '[!]',
        '→': '->',
        '←': '<-',
        '↑': '^',
        '↓': 'v',
        '•': '-',
        '◦': '-',
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # Remove remaining emojis
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\U0001F900-\U0001F9FF"
        "\U0001FA70-\U0001FAFF"
        "]+",
        flags=re.UNICODE
    )

    text = emoji_pattern.sub('', text)

    return text


def get_gemini_client():
    """Get Gemini API client."""
    if not GEMINI_AVAILABLE:
        return None

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY not found in environment variables")
        return None

    try:
        client = genai.Client(api_key=api_key)
        return client
    except Exception as e:
        logger.error(f"Failed to create Gemini client: {e}")
        return None


def get_claude_client() -> Optional[Anthropic]:
    """Get Claude API client."""
    if not ANTHROPIC_AVAILABLE:
        return None

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY not found in environment variables")
        return None

    # Check for custom base URL (for local proxy)
    base_url = os.getenv("ANTHROPIC_BASE_URL")

    if base_url:
        logger.info(f"[Claude] Using custom base URL: {base_url}")
        return Anthropic(api_key=api_key, base_url=base_url)
    else:
        return Anthropic(api_key=api_key)


def call_gemini(prompt: str, model: str = "gemini-2.5-flash",
                max_tokens: int = 2048, temperature: float = 0.7,
                timeout: int = 300) -> Optional[str]:
    """
    Call Gemini API with a prompt and get response.

    Args:
        prompt: The prompt to send to Gemini
        model: Gemini model to use (default: gemini-2.5-flash - newest free model)
        max_tokens: Maximum tokens in response
        temperature: Sampling temperature (0.0-1.0)
        timeout: Timeout in seconds

    Returns:
        Response from Gemini or None if failed
    """
    client = get_gemini_client()
    if not client:
        logger.error("Gemini client not available")
        return None

    try:
        logger.info(f"[Gemini] Calling {model} (max_tokens: {max_tokens}, timeout: {timeout}s)...")

        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config={
                'max_output_tokens': max_tokens,
                'temperature': temperature,
            }
        )

        if response.text:
            result = response.text.strip()
            # Sanitize Unicode characters for Windows compatibility
            result = sanitize_unicode(result)
            logger.info(f"[Gemini] Response received ({len(result)} chars)")
            return result

        logger.warning("[Gemini] Empty response received")
        return None

    except Exception as e:
        logger.error(f"[Gemini] API call failed: {e}")
        return None


def call_claude(prompt: str, model: str = "claude-sonnet-4-6",
                max_tokens: int = 2048, temperature: float = 0.7,
                timeout: int = 300) -> Optional[str]:
    """
    Call AI API with a prompt and get response.
    Now uses Gemini as the primary brain, with Claude as fallback.

    Args:
        prompt: The prompt to send to the AI
        model: Model to use (ignored for Gemini, uses gemini-1.5-flash)
        max_tokens: Maximum tokens in response
        temperature: Sampling temperature (0.0-1.0)
        timeout: Timeout in seconds

    Returns:
        Response from AI or None if failed
    """
    # Try Gemini first (free tier)
    result = call_gemini(prompt, max_tokens=max_tokens, temperature=temperature, timeout=timeout)
    if result:
        return result

    # Fallback to Claude if Gemini fails
    logger.info("[AI] Gemini failed, trying Claude fallback...")
    client = get_claude_client()
    if not client:
        logger.error("Claude client not available")
        return None

    try:
        logger.info(f"[Claude] Calling {model} (max_tokens: {max_tokens}, timeout: {timeout}s)...")

        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {"role": "user", "content": prompt}
            ],
            timeout=timeout
        )

        if response.content and len(response.content) > 0:
            result = response.content[0].text.strip()
            # Sanitize Unicode characters for Windows compatibility
            result = sanitize_unicode(result)
            logger.info(f"[Claude] Response received ({len(result)} chars)")
            return result

        logger.warning("[Claude] Empty response received")
        return None

    except Exception as e:
        logger.error(f"[Claude] API call failed: {e}")
        return None


def call_ai_model(prompt: str, vault_path: str = "AI_Employee_Vault",
                  timeout: int = 300, model: str = "claude-sonnet-4-6") -> Optional[str]:
    """
    Unified AI model calling function using Claude API.

    This replaces the old Qwen/Ollama implementation.

    Args:
        prompt: The prompt to send to the AI model
        vault_path: Path to the vault directory (kept for compatibility)
        timeout: Timeout in seconds
        model: Model to use (default: claude-sonnet-4-6)

    Returns:
        Response from Claude or None if failed
    """
    # Map old model names to Claude models
    model_mapping = {
        "qwen3-coder:480b-cloud": "claude-sonnet-4-6",
        "llama3": "claude-sonnet-4-6",
        "qwen": "claude-sonnet-4-6",
    }

    claude_model = model_mapping.get(model, model)
    return call_claude(prompt, model=claude_model, timeout=timeout)


# Backward compatibility aliases
def call_qwen_coder(prompt: str, vault_path: str = "AI_Employee_Vault",
                    timeout: int = 300) -> Optional[str]:
    """
    Backward compatibility wrapper for call_qwen_coder.
    Now uses Claude API instead of Qwen.
    """
    logger.info("[Compatibility] call_qwen_coder -> using Claude API")
    return call_claude(prompt, timeout=timeout)


def call_ollama(prompt: str, vault_path: str = "AI_Employee_Vault",
                timeout: int = 180, model: str = "llama3") -> Optional[str]:
    """
    Backward compatibility wrapper for call_ollama.
    Now uses Claude API instead of Ollama.
    """
    logger.info("[Compatibility] call_ollama -> using Claude API")
    return call_claude(prompt, timeout=timeout)


def ai_select_skill(task_content: str, available_skills: list) -> Optional[str]:
    """
    Use Claude to decide which skill should handle a task.

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

    response = call_claude(prompt)
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
    Use Claude to generate a professional email response.
    """
    body = body[:500]
    prompt = f"""Write ONLY the email reply text. No other commentary.

FROM: {from_email}
SUBJECT: {subject}
EMAIL: {body[:300]}

EMAIL REPLY:"""

    response = call_claude(prompt, timeout=30)
    if response and len(response) > 30:
        return response
    return None


def ai_generate_plan(task_type: str, task_data: Dict, task_content: str) -> Optional[str]:
    """
    Use Claude to generate a detailed action plan.
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

    response = call_claude(prompt, timeout=30)
    if response and len(response) > 50:
        return response
    return None


def ai_analyze_email(email_content: str) -> Dict[str, Any]:
    """
    Use Claude to analyze an email and extract key information.

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

    response = call_claude(prompt, timeout=60)
    if response:
        try:
            # Try to parse JSON from response
            if "```" in response:
                response = response.split("```")[1].strip()
                if response.startswith("json"):
                    response = response[4:].strip()
            return json.loads(response)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse Claude JSON response")
    return {
        "intent": "unknown",
        "urgency": "Medium",
        "requires_reply": True,
        "sentiment": "neutral",
        "key_topics": [],
        "suggested_action": "review manually"
    }
