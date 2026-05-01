import sys
sys.path.insert(0, 'scripts')
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8')

from skills.email_responder.service import EmailResponseService

email_data = {
    'from': 'client@example.com',
    'subject': 'Project timeline update needed',
    'body': 'Hi, we need the updated timeline for the project by next week. Please share the current status and any blockers. Thanks!',
    'date': ''
}

svc = EmailResponseService(vault_path='AI_Employee_Vault')

body = email_data['body']
for marker in ['## Email Content', '## Content', '## Suggested Actions', '---']:
    body = body.replace(marker, '').strip()
email_data['body'] = body

context = svc._analyze_context(email_data)
print('=== Context ===')
print(context)

prompt = svc._build_ai_prompt(email_data, context)
print('\n=== Prompt (first 400 chars) ===')
print(prompt[:400])
