"""
Gmail Authentication for AI Employee - WITH SEND PERMISSIONS

This script authenticates with BOTH read AND send permissions.
Run this to enable email sending functionality.
"""

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from pathlib import Path

# Configuration
CREDENTIALS_FILE = Path('credentails.json')
TOKEN_FILE = Path('AI_Employee_Vault/.gmail_token.json')

# IMPORTANT: Include BOTH read AND send scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.compose'
]

print("=" * 60)
print("GMAIL API AUTHENTICATION (WITH SEND PERMISSIONS)")
print("=" * 60)
print()

# Delete old token
if TOKEN_FILE.exists():
    print(f"[OK] Deleting old token: {TOKEN_FILE}")
    TOKEN_FILE.unlink()

print(f"[OK] Credentials file: {CREDENTIALS_FILE}")
print()
print("Starting authentication...")
print("A browser window will open.")
print("Please sign in and click 'Allow' to grant permissions.")
print()
print("REQUIRED PERMISSIONS:")
print("  - Read your email (to detect new messages)")
print("  - Send email on your behalf (to send replies)")
print("  - Manage drafts (to create draft replies)")
print()

try:
    # Create OAuth flow with ALL required scopes
    flow = InstalledAppFlow.from_client_secrets_file(
        str(CREDENTIALS_FILE),
        SCOPES
    )
    
    # Run local server to handle OAuth callback
    creds = flow.run_local_server(port=0, open_browser=True)
    
    # Save token
    print()
    print("Saving authentication token...")
    with open(TOKEN_FILE, 'w') as token:
        token.write(creds.to_json())
    
    print(f"[OK] Token saved to: {TOKEN_FILE}")
    print()
    print("=" * 60)
    print("[OK] AUTHENTICATION SUCCESSFUL!")
    print("=" * 60)
    print()
    print("Gmail Watcher can now:")
    print("  - Detect new emails")
    print("  - Send email replies")
    print("  - Create draft emails")
    print()
    print("Next steps:")
    print("1. Send a test email to your Gmail account")
    print("2. Wait for it to be detected")
    print("3. Approve the reply")
    print("4. Email will be sent automatically!")
    
except Exception as e:
    print()
    print("=" * 60)
    print("[ERROR] AUTHENTICATION FAILED")
    print("=" * 60)
    print(f"Error: {e}")
    print()
    print("Troubleshooting:")
    print("1. Make sure you're connected to the internet")
    print("2. Check that credentails.json is valid")
    print("3. Try running the script again")
