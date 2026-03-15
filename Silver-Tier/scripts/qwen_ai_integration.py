"""
Qwen Code AI Integration for AI Employee

Uses Qwen Code to analyze emails and generate contextual, intelligent responses
based on Company Handbook and Business Goals.

Usage:
    from qwen_ai_integration import generate_ai_response
    result = generate_ai_response(email_data, vault_path)
"""

import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


def read_company_handbook(vault_path: str) -> str:
    """Read Company Handbook for response guidelines."""
    handbook_path = Path(vault_path) / 'Company_Handbook.md'
    if handbook_path.exists():
        return handbook_path.read_text(encoding='utf-8')
    return ""


def read_business_goals(vault_path: str) -> str:
    """Read Business Goals for context."""
    goals_path = Path(vault_path) / 'Business_Goals.md'
    if goals_path.exists():
        return goals_path.read_text(encoding='utf-8')
    return ""


def generate_ai_response(email_data: Dict[str, Any], vault_path: str = "AI_Employee_Vault") -> Dict[str, Any]:
    """
    Generate AI-powered email response using Qwen Code.
    
    Analyzes:
    - Email content and intent
    - Company Handbook rules
    - Business Goals context
    
    Returns:
        Dictionary with AI-generated response
    """
    
    # Read Company Handbook and Business Goals
    handbook = read_company_handbook(vault_path)
    business_goals = read_business_goals(vault_path)
    
    # Build comprehensive AI prompt (ASCII only for Windows compatibility)
    prompt = f"""You are an intelligent AI Employee assistant. Your task is to analyze an incoming email and generate a professional, context-aware response.

## CONTEXT INFORMATION

### Company Handbook (Rules & Guidelines):
{handbook[:3000] if handbook else "No handbook available"}

### Business Goals (Current Objectives):
{business_goals[:2000] if business_goals else "No business goals available"}

## INCOMING EMAIL TO ANALYZE

From: {email_data.get('from', 'Unknown')}
Subject: {email_data.get('subject', 'No Subject')}
Date: {email_data.get('date', 'Unknown')}

Content:
---
{email_data.get('body', email_data.get('content', 'No content available'))}
---

## YOUR TASK

Analyze this email and generate a professional response following these steps:

### Step 1: Analysis
1. **Intent**: What does the sender want?
2. **Urgency**: Is this urgent? (Look for: urgent, asap, immediately, emergency)
3. **Category**: What type of inquiry? (sales, support, partnership, job, etc.)
4. **Sentiment**: Positive, neutral, or negative?
5. **Action Required**: What should we do?

### Step 2: Generate Response
Create a professional email response that:
- Addresses the sender by name (extract from email)
- Acknowledges their specific inquiry
- Provides helpful, relevant information
- Matches the tone of their message
- Follows Company Handbook guidelines
- Aligns with Business Goals
- Has proper paragraph breaks for readability

### Step 3: Output Format

Provide your response in this EXACT format:

ANALYSIS:
- Intent: [sender's intent]
- Urgency: [Low/Medium/High]
- Category: [category]
- Sentiment: [Positive/Neutral/Negative]
- Action Required: [what we should do]

RESPONSE:
Dear [Sender Name],

[Paragraph 1: Acknowledge their specific message]

[Paragraph 2: Address their inquiry with relevant information]

[Paragraph 3: Next steps or offer further assistance]

Best regards,

AI Employee Response System
[Your Company Name]

---
Reference ID: [timestamp]

## IMPORTANT RULES

1. **Be Specific**: Reference details from their email
2. **Be Helpful**: Provide actual value, not generic responses
3. **Be Professional**: Match their tone (formal/casual)
4. **Be Concise**: 3-4 paragraphs maximum
5. **No Questions**: Don't ask clarifying questions - just respond
6. **Proper Formatting**: Use clear paragraph breaks

Generate your complete analysis and response now:
"""

    try:
        print("  [AI] Calling Qwen Code for intelligent email analysis...")

        # Find Qwen Code executable
        import shutil
        qwen_path = shutil.which('qwen')

        if not qwen_path:
            print("  [AI] ⚠️  Qwen Code not found - using smart template")
            return generate_smart_template_response(email_data, handbook, business_goals)

        # Call Qwen Code with proper encoding
        result = subprocess.run(
            [qwen_path],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=90,
            encoding='utf-8',
            errors='replace'
        )

        if result.returncode != 0:
            print("  [AI] ❌ Qwen Error:", result.stderr[:500] if result.stderr else "Unknown error")

        if result.returncode == 0 and result.stdout:
            ai_response = result.stdout.strip()
            
            # Check if Qwen generated useful content (not questions)
            if contains_questions(ai_response) or len(ai_response) < 100:
                print("  [AI] ⚠️  Qwen Code asked questions - using smart template")
                return generate_smart_template_response(email_data, handbook, business_goals)
            
            # Parse AI response
            analysis, response = parse_ai_response(ai_response)
            
            print("  [AI] ✅ AI-generated intelligent response")
            return {
                'success': True,
                'response': response,
                'analysis': analysis,
                'method': 'qwen_code_ai'
            }
        else:
            print(f"  [AI] ⚠️  Qwen Code error - using smart template")
            return generate_smart_template_response(email_data, handbook, business_goals)
            
    except subprocess.TimeoutExpired:
        print("  [AI] ⚠️  Qwen Code timeout - using smart template")
        return generate_smart_template_response(email_data, handbook, business_goals)
        
    except Exception as e:
        print(f"  [AI] ⚠️  Error: {e} - using smart template")
        return generate_smart_template_response(email_data, handbook, business_goals)


def parse_ai_response(ai_output: str) -> tuple:
    """Parse AI output into analysis and response."""
    
    analysis = {}
    response = ai_output
    
    # Try to extract ANALYSIS section
    if 'ANALYSIS:' in ai_output:
        parts = ai_output.split('ANALYSIS:')
        if len(parts) > 1:
            analysis_section = parts[1].split('RESPONSE:')[0] if 'RESPONSE:' in parts[1] else parts[1]
            
            # Parse analysis fields
            for line in analysis_section.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    analysis[key.strip().lower()] = value.strip()
    
    # Extract RESPONSE section
    if 'RESPONSE:' in ai_output:
        response = ai_output.split('RESPONSE:')[1].strip()
    
    return analysis, response


def contains_questions(response: str) -> bool:
    """Check if response contains questions."""
    question_patterns = [
        'could you', 'can you', 'would you',
        'please provide', 'please share',
        'what is', 'what are', 'who is',
         '?'
    ]
    
    response_lower = response.lower()
    question_count = sum(1 for pattern in question_patterns if pattern in response_lower)
    
    return question_count >= 2


def generate_smart_template_response(email_data: Dict[str, Any], handbook: str, business_goals: str) -> Dict[str, Any]:
    """
    Generate intelligent response using smart template when AI unavailable.
    Analyzes email content to create contextual response.
    """
    
    # Extract email details
    from_email = email_data.get('from', 'Unknown')
    subject = email_data.get('subject', 'No Subject')
    body = email_data.get('body', email_data.get('content', ''))
    
    # Extract sender name
    sender_name = 'Valued Contact'
    if '<' in from_email:
        sender_name = from_email.split('<')[0].strip()
    elif from_email and from_email != 'Unknown':
        sender_name = from_email.split('@')[0].replace('.', ' ').title()
    
    # Analyze email content for keywords
    body_lower = body.lower()
    subject_lower = subject.lower()
    full_text = f"{subject_lower} {body_lower}"
    
    # Determine category
    category = 'general inquiry'
    if any(word in full_text for word in ['price', 'cost', 'pricing', 'quote']):
        category = 'pricing inquiry'
    elif any(word in full_text for word in ['support', 'help', 'issue', 'problem', 'error']):
        category = 'support request'
    elif any(word in full_text for word in ['partnership', 'partner', 'collaborate']):
        category = 'partnership inquiry'
    elif any(word in full_text for word in ['job', 'career', 'position', 'hiring', 'resume']):
        category = 'career inquiry'
    elif any(word in full_text for word in ['sales', 'buy', 'purchase', 'order']):
        category = 'sales inquiry'
    
    # Determine urgency
    urgency = 'Normal'
    if any(word in full_text for word in ['urgent', 'asap', 'immediately', 'emergency']):
        urgency = 'High'
    
    # Generate contextual response based on category
    responses = {
        'pricing inquiry': f"""Dear {sender_name},


Thank you for your interest in our pricing information.


We offer flexible pricing plans tailored to your specific needs. Our team would be happy to provide you with a detailed quote based on your requirements.


Could you please share more details about what you're looking for? This will help us provide you with the most accurate pricing information.


Best regards,

AI Employee Response System
Automated Customer Service""",

        'support request': f"""Dear {sender_name},


Thank you for contacting our support team. We understand how important it is to resolve issues quickly.


We have received your support request and our technical team is reviewing it. We typically respond to support requests within 24-48 business hours.


If this is an urgent matter, please reply with "URGENT" in the subject line and we will prioritize your request.


Best regards,

AI Employee Response System
Technical Support Team""",

        'partnership inquiry': f"""Dear {sender_name},


Thank you for your interest in exploring a partnership opportunity with us.


We are always interested in discussing potential partnerships that align with our business goals. Our business development team would be happy to learn more about your proposal.


We will review your inquiry and get back to you within 2-3 business days to discuss next steps.


Best regards,

AI Employee Response System
Business Development Team""",

        'career inquiry': f"""Dear {sender_name},


Thank you for your interest in career opportunities with our organization.


We appreciate professionals like you who are interested in joining our team. Our HR department reviews all career inquiries and reaches out when relevant positions become available.


We will keep your information on file and contact you if a suitable opportunity arises.


Best regards,

AI Employee Response System
Human Resources Team""",

        'sales inquiry': f"""Dear {sender_name},


Thank you for your interest in our products/services.


We would be delighted to help you with your purchase. Our sales team is ready to assist you with product information, pricing, and the ordering process.


A member of our sales team will contact you within 24 hours to discuss your requirements and guide you through the process.


Best regards,

AI Employee Response System
Sales Team""",

        'general inquiry': f"""Dear {sender_name},


Thank you for contacting us regarding "{subject}".


We have received your message and appreciate you reaching out to us. Our team will review your inquiry carefully.


We typically respond to inquiries within 24-48 business hours. If your matter requires immediate attention, please don't hesitate to follow up.


Best regards,

AI Employee Response System
Automated Customer Service"""
    }
    
    # Select response based on category
    response = responses.get(category, responses['general inquiry'])
    
    # Add reference ID
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    response += f"\n\n---\nReference ID: {timestamp}\nFor urgent matters, reply with 'URGENT' in subject line."
    
    # Create analysis
    analysis = {
        'intent': f'{category}',
        'urgency': urgency,
        'category': category,
        'sentiment': 'Neutral',
        'action_required': f'Respond to {category}'
    }
    
    print(f"  [Template] ✅ Smart contextual response generated (Category: {category})")
    
    return {
        'success': True,
        'response': response,
        'analysis': analysis,
        'method': 'smart_template'
    }


def test_ai_generation():
    """Test AI email generation with sample email."""
    test_email = {
        'from': 'John Smith <john.smith@example.com>',
        'subject': 'Urgent: Pricing inquiry for enterprise plan',
        'body': '''Hi,

I hope this email finds you well.

I am the CTO at TechCorp and we are interested in your enterprise plan. We need:
- 500 user licenses
- Priority support
- Custom integration

This is quite urgent as we need to make a decision by end of week.

Could you please send me:
1. Pricing details for enterprise plan
2. Implementation timeline
3. Support SLA details

Looking forward to your prompt response.

Best regards,
John Smith
CTO, TechCorp'''
    }
    
    print("=" * 70)
    print("QWEN CODE AI INTEGRATION - TEST")
    print("=" * 70)
    print()
    
    result = generate_ai_response(test_email)
    
    print()
    print("=" * 70)
    print("AI ANALYSIS:")
    print("=" * 70)
    for key, value in result.get('analysis', {}).items():
        print(f"  {key.title()}: {value}")
    
    print()
    print("=" * 70)
    print("AI-GENERATED RESPONSE:")
    print("=" * 70)
    print()
    print(result.get('response', 'No response generated'))
    print()
    print(f"Method: {result.get('method', 'unknown')}")
    print(f"Success: {result.get('success', False)}")


if __name__ == '__main__':
    test_ai_generation()
