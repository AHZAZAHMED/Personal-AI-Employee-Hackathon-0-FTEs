"""
AI Email Response Generator for AI Employee

Uses Qwen Code to generate professional email responses.
Automatically detects if AI asks questions and falls back to template.

Usage:
    from ai_email_generator import generate_ai_response
    result = generate_ai_response(email_data)
    if result['method'] == 'fallback_template':
        # AI asked questions, used template
    else:
        # AI generated email successfully
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


def analyze_email_context(email_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Analyze incoming email to extract context for AI generation.
    Pre-answers Qwen Code's standard questions.
    """
    
    from_email = email_data.get('from', '')
    subject = email_data.get('subject', '').lower()
    body = email_data.get('body', email_data.get('content', '')).lower()
    full_text = f"{subject} {body}"
    
    # 1. Determine Recipient Type
    recipient = "client"  # Default
    if any(word in from_email.lower() for word in ['@gmail', '@yahoo', '@hotmail']):
        recipient = "individual"
    elif any(word in full_text for word in ['colleague', 'team', 'coworker']):
        recipient = "colleague"
    elif any(word in full_text for word in ['vendor', 'supplier', 'partner']):
        recipient = "vendor"
    elif any(word in full_text for word in ['manager', 'boss', 'supervisor']):
        recipient = "manager"
    elif any(word in full_text for word in ['client', 'customer', 'customer']):
        recipient = "client"
    
    # 2. Determine Email Topic/Context
    topic = "general inquiry"
    if any(word in full_text for word in ['invoice', 'payment', 'bill', 'price']):
        topic = "billing/payment inquiry"
    elif any(word in full_text for word in ['meeting', 'schedule', 'appointment', 'call']):
        topic = "scheduling request"
    elif any(word in full_text for word in ['job', 'career', 'position', 'hiring']):
        topic = "job/career inquiry"
    elif any(word in full_text for word in ['support', 'help', 'issue', 'problem']):
        topic = "support request"
    elif any(word in full_text for word in ['information', 'learn', 'know more']):
        topic = "information request"
    elif any(word in full_text for word in ['complaint', 'unhappy', 'disappointed']):
        topic = "complaint"
    
    # 3. Determine Desired Outcome
    outcome = "provide information and offer assistance"
    if any(word in full_text for word in ['meeting', 'call', 'schedule']):
        outcome = "schedule a meeting or call"
    elif any(word in full_text for word in ['quote', 'pricing', 'cost']):
        outcome = "provide pricing information"
    elif any(word in full_text for word in ['urgent', 'asap', 'immediately']):
        outcome = "address urgent matter promptly"
    elif any(word in full_text for word in ['reply', 'response', 'answer']):
        outcome = "provide requested information"
    
    # 4. Determine Tone
    tone = "professional and friendly"
    if any(word in full_text for word in ['urgent', 'emergency', 'asap']):
        tone = "professional and prompt"
    elif any(word in full_text for word in ['complaint', 'unhappy', 'issue']):
        tone = "professional and empathetic"
    elif any(word in full_text for word in ['thanks', 'thank you', 'appreciate']):
        tone = "warm and appreciative"
    elif any(word in full_text for word in ['formal', 'official']):
        tone = "formal and professional"
    
    # Extract sender name
    sender_name = "Valued Contact"
    if '<' in from_email:
        sender_name = from_email.split('<')[0].strip()
    elif from_email:
        sender_name = from_email.split('@')[0].replace('.', ' ').title()
    
    return {
        'recipient': recipient,
        'topic': topic,
        'outcome': outcome,
        'tone': tone,
        'sender_name': sender_name
    }


def contains_questions(response: str) -> bool:
    """
    Check if response contains questions (indicating AI didn't generate email).
    
    Returns True if response contains questions, False if it's a proper email.
    """
    
    # Question patterns that indicate AI is asking instead of generating
    question_patterns = [
        'could you',
        'can you',
        'would you',
        'please provide',
        'please share',
        'please tell',
        'i need',
        'i need to know',
        'what is',
        'what are',
        'who is',
        'how can',
        'let me know',
        'more information',
        'additional details',
        'i can help',
        'happy to help',
        'once you provide',
        'to better assist',
        '?',  # Question mark
    ]
    
    response_lower = response.lower()
    
    # Count how many question patterns are found
    question_count = sum(1 for pattern in question_patterns if pattern in response_lower)
    
    # If 2 or more question patterns found, it's likely asking questions
    if question_count >= 2:
        return True
    
    # Check if response looks like an email (has greeting and sign-off)
    has_greeting = any(word in response_lower for word in ['dear ', 'hello ', 'hi '])
    has_signoff = any(word in response_lower for word in ['best regards', 'sincerely', 'kind regards'])
    
    # If it has greeting and sign-off, it's probably an email
    if has_greeting and has_signoff:
        return False
    
    # If no greeting/sign-off but has questions, it's asking questions
    return question_count >= 1


def generate_fallback_response(email_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate professional email response using template (fallback when AI unavailable).
    """
    sender_email = email_data.get('from', 'Unknown')
    subject = email_data.get('subject', 'your inquiry')
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    
    # Extract sender name
    sender_name = 'Valued Contact'
    if '<' in sender_email:
        sender_name = sender_email.split('<')[0].strip()
    elif sender_email and sender_email != 'Unknown':
        sender_name = sender_email.split('@')[0].replace('.', ' ').title()
    
    # Professional template with EXTRA line breaks for email clients
    # Use \n\n for paragraph breaks (email clients need double line breaks)
    response = f"""Dear {sender_name},


Thank you for contacting us regarding "{subject}".


We have received your message and our team will review it shortly. If your inquiry matches our current requirements, we will reach out to you regarding the next steps.


We appreciate your interest and look forward to assisting you.


Best regards,


AI Employee Response System
Automated Customer Service

---
Reference ID: {timestamp}
This is an automated response. For urgent matters, please reply with "URGENT" in the subject line."""

    print("  [Fallback] [OK] Email generated using professional template")
    
    return {
        'success': True,
        'response': response,
        'method': 'fallback_template'
    }


def generate_ai_response(email_data: Dict[str, Any], vault_path: str = "AI_Employee_Vault") -> Dict[str, Any]:
    """
    Generate AI-powered email response using Qwen Code.
    Falls back to professional template if AI asks questions.
    
    Args:
        email_data: Dictionary with email details (from, subject, body, etc.)
        vault_path: Path to Obsidian vault
        
    Returns:
        Dictionary with generated response and method used
    """
    
    # Analyze email context to pre-answer Qwen's questions
    context = analyze_email_context(email_data)
    
    # AI Prompt with PRE-ANSWERED questions
    prompt = f"""You are a professional AI Employee assistant. Generate a complete email response NOW.

CONTEXT (I've already analyzed this for you):
- **Recipient:** {context['recipient']}
- **Sender:** {context['sender_name']}
- **Topic:** {context['topic']}
- **Desired Outcome:** {context['outcome']}
- **Tone:** {context['tone']}

ORIGINAL EMAIL:
---
From: {email_data.get('from', 'Unknown')}
Subject: {email_data.get('subject', 'No Subject')}
Date: {email_data.get('date', 'Unknown')}

{email_data.get('body', email_data.get('content', 'No content available'))}
---

YOUR TASK:
Write a COMPLETE, PROFESSIONAL email response. Do NOT ask questions. Do NOT provide instructions. Just write the email.

REQUIREMENTS:
1. Use sender name: {context['sender_name']}
2. Address topic: {context['topic']}
3. Achieve outcome: {context['outcome']}
4. Use tone: {context['tone']}
5. Include 3-4 paragraphs with proper line breaks
6. Professional greeting and sign-off

OUTPUT FORMAT (EXACTLY THIS - NO OTHER TEXT):

Dear {context['sender_name']},

[Paragraph 1: Thank them and acknowledge their message]

[Paragraph 2: Address their specific inquiry with helpful information]

[Paragraph 3: Next steps, offer further assistance, or call-to-action]

Best regards,

AI Employee Response System
Automated Customer Service

---
Reference ID: {datetime.now().strftime('%Y%m%d%H%M%S')}
This is an automated response. For urgent matters, please reply with "URGENT" in the subject line.

---

Generate ONLY the email response text below (no additional commentary):
"""

    try:
        # Try to call Qwen Code
        print("  [AI] Calling Qwen Code for email generation...")
        
        # Find qwen executable
        import shutil
        qwen_path = shutil.which('qwen')
        
        if not qwen_path:
            print("  [AI] Qwen Code not found - using fallback template")
            return generate_fallback_response(email_data)
        
        # Call Qwen Code
        result = subprocess.run(
            [qwen_path, '--prompt', prompt],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=vault_path
        )
        
        if result.returncode == 0:
            ai_response = result.stdout.strip()
            
            # Check if response contains questions
            if contains_questions(ai_response):
                print("  [AI] ⚠️  AI response contains questions - using fallback template")
                return generate_fallback_response(email_data)
            else:
                print("  [AI] [OK] Email generated successfully by Qwen Code")
                return {
                    'success': True,
                    'response': ai_response,
                    'method': 'qwen_code_ai'
                }
        else:
            print(f"  [AI] Qwen Code error - using fallback template")
            return generate_fallback_response(email_data)
            
    except subprocess.TimeoutExpired:
        print("  [AI] Timeout - using fallback template")
        return generate_fallback_response(email_data)
        
    except Exception as e:
        print(f"  [AI] Error: {e} - using fallback template")
        return generate_fallback_response(email_data)


def test_ai_generation():
    """Test AI email generation."""
    test_email = {
        'from': 'John Smith <john@example.com>',
        'subject': 'Inquiry about services',
        'body': 'Hi,\n\nI am interested in your services.\n\nThanks,\nJohn'
    }
    
    print("=" * 60)
    print("AI EMAIL GENERATOR - TEST")
    print("=" * 60)
    print()
    
    result = generate_ai_response(test_email)
    
    print()
    print("=" * 60)
    print("GENERATED RESPONSE:")
    print("=" * 60)
    print()
    print(result.get('response', 'No response generated'))
    print()
    print(f"Method: {result.get('method', 'unknown')}")
    print(f"Success: {result.get('success', False)}")


if __name__ == '__main__':
    test_ai_generation()
