#!/usr/bin/env python3
"""
Pre-commit hook to detect and block commits containing secrets.

This hook scans staged files for potential secrets like:
- API keys
- Tokens
- Passwords
- Private keys
- Database credentials

Installation:
    cp scripts/pre-commit-secret-scan.py .git/hooks/pre-commit
    chmod +x .git/hooks/pre-commit
"""

import re
import sys
import subprocess
from pathlib import Path

# Patterns that indicate potential secrets
SECRET_PATTERNS = [
    # API Keys
    (r'[A-Za-z0-9_]{32,}', 'Long alphanumeric string (potential API key)'),
    (r'api[_-]?key["\s:=]+[A-Za-z0-9_-]{20,}', 'API key pattern'),
    (r'secret[_-]?key["\s:=]+[A-Za-z0-9_-]{20,}', 'Secret key pattern'),

    # Tokens
    (r'token["\s:=]+[A-Za-z0-9_-]{20,}', 'Token pattern'),
    (r'bearer["\s:=]+[A-Za-z0-9_-]{20,}', 'Bearer token pattern'),
    (r'auth[_-]?token["\s:=]+[A-Za-z0-9_-]{20,}', 'Auth token pattern'),

    # AWS
    (r'AKIA[0-9A-Z]{16}', 'AWS Access Key ID'),
    (r'aws[_-]?secret[_-]?access[_-]?key', 'AWS Secret Access Key'),

    # Private Keys
    (r'-----BEGIN (RSA |DSA )?PRIVATE KEY-----', 'Private key'),
    (r'-----BEGIN OPENSSH PRIVATE KEY-----', 'OpenSSH private key'),

    # Database URLs with credentials
    (r'postgresql://[^:]+:[^@]+@', 'PostgreSQL URL with credentials'),
    (r'mysql://[^:]+:[^@]+@', 'MySQL URL with credentials'),
    (r'mongodb://[^:]+:[^@]+@', 'MongoDB URL with credentials'),

    # Generic password patterns
    (r'password["\s:=]+[^\s]{8,}', 'Password pattern'),
    (r'passwd["\s:=]+[^\s]{8,}', 'Passwd pattern'),

    # Specific service patterns
    (r'FACEBOOK_APP_SECRET["\s:=]+[A-Za-z0-9]{32}', 'Facebook App Secret'),
    (r'TWILIO_AUTH_TOKEN["\s:=]+[A-Za-z0-9]{32}', 'Twilio Auth Token'),
    (r'GEMINI_API_KEY["\s:=]+AIza[A-Za-z0-9_-]{35}', 'Gemini API Key'),
    (r'ANTHROPIC_API_KEY["\s:=]+sk-ant-[A-Za-z0-9_-]{40,}', 'Anthropic API Key'),
]

# Files to always skip
SKIP_FILES = {
    '.env.example',
    '.env.template',
    'pre-commit-secret-scan.py',
    'test_secret_scanning.py',
}

# Directories to skip
SKIP_DIRS = {
    'node_modules',
    'venv',
    'env',
    '.git',
    '__pycache__',
    'dist',
    'build',
}

def get_staged_files():
    """Get list of staged files."""
    try:
        result = subprocess.run(
            ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACM'],
            capture_output=True,
            text=True,
            check=True
        )
        return [f for f in result.stdout.strip().split('\n') if f]
    except subprocess.CalledProcessError:
        return []

def should_skip_file(filepath):
    """Check if file should be skipped."""
    path = Path(filepath)

    # Skip if filename matches
    if path.name in SKIP_FILES:
        return True

    # Skip if in excluded directory
    for part in path.parts:
        if part in SKIP_DIRS:
            return True

    # Skip binary files
    if path.suffix in {'.pyc', '.so', '.dll', '.exe', '.bin', '.db', '.sqlite', '.png', '.jpg', '.jpeg', '.gif', '.pdf'}:
        return True

    return False

def scan_file(filepath):
    """Scan a file for potential secrets."""
    if should_skip_file(filepath):
        return []

    findings = []

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        for line_num, line in enumerate(content.split('\n'), 1):
            # Skip comments in common languages
            stripped = line.strip()
            if stripped.startswith(('#', '//', '/*', '*', '--')):
                continue

            # Check each pattern
            for pattern, description in SECRET_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    findings.append({
                        'file': filepath,
                        'line': line_num,
                        'description': description,
                        'content': line.strip()[:100]  # First 100 chars
                    })

    except Exception as e:
        print(f"Warning: Could not scan {filepath}: {e}", file=sys.stderr)

    return findings

def main():
    """Main pre-commit hook logic."""
    print("[SECURITY] Scanning for secrets in staged files...")

    staged_files = get_staged_files()
    if not staged_files:
        print("[OK] No files to scan")
        return 0

    all_findings = []
    for filepath in staged_files:
        findings = scan_file(filepath)
        all_findings.extend(findings)

    if all_findings:
        print("\n" + "="*80)
        print("[BLOCKED] POTENTIAL SECRETS DETECTED - COMMIT BLOCKED")
        print("="*80)
        print("\nThe following files contain potential secrets:\n")

        for finding in all_findings:
            print(f"  File: {finding['file']}:{finding['line']}")
            print(f"  Warning: {finding['description']}")
            print(f"  Content: {finding['content']}")
            print()

        print("="*80)
        print("SECURITY RECOMMENDATIONS:")
        print("="*80)
        print("1. Remove secrets from the file")
        print("2. Use environment variables instead (.env file)")
        print("3. Add sensitive files to .gitignore")
        print("4. If secrets were already committed, rotate them immediately")
        print("5. Use 'git commit --no-verify' to bypass (NOT RECOMMENDED)")
        print("="*80)

        return 1

    print(f"[OK] Scanned {len(staged_files)} files - no secrets detected")
    return 0

if __name__ == '__main__':
    sys.exit(main())
