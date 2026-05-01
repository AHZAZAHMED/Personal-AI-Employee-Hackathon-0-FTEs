import sys
sys.path.insert(0, 'scripts')
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8')

from scripts.qwen_ai_integration import call_qwen

# Simple direct prompt (not a template file, just a command)
prompt = "Write a professional email reply to this: Hi, please confirm you received this message. Thanks!"
print("Calling Qwen with simple prompt...")
response = call_qwen(prompt, vault_path="AI_Employee_Vault", timeout=30)
print(f"\n=== Response (len: {len(response) if response else 0}) ===")
print(response)
