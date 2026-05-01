import subprocess
import shutil
import sys

# Test different ways of calling Qwen
qwen_path = shutil.which("qwen")
print(f"Qwen path: {qwen_path}")

# Test 1: Direct text prompt via --prompt
print("\n=== Test 1: Direct text prompt ===")
prompt1 = "Write a short professional email reply to: Hi, I need the project timeline by next week. Thanks!"
result1 = subprocess.run([qwen_path, "--prompt", prompt1], capture_output=True, text=True, timeout=30)
print(f"Exit: {result1.returncode}, Len: {len(result1.stdout)}")
print(f"Response: {result1.stdout[:300]}")

# Test 2: File-based prompt
print("\n=== Test 2: File-based prompt ===")
import tempfile
with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
    f.write("Write a short professional email reply to: Hi, I need the project timeline by next week. Thanks!")
    temp_file = f.name

result2 = subprocess.run([qwen_path, "--prompt", temp_file], capture_output=True, text=True, timeout=30)
print(f"Exit: {result2.returncode}, Len: {len(result2.stdout)}")
print(f"Response: {result2.stdout[:300]}")

import os
os.unlink(temp_file)
