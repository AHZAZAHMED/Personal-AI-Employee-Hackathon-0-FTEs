"""
Gmail Authentication Script for AI Employee

This script authenticates with Gmail API and saves the token.
Run this when your Gmail token expires or is invalid.

Usage:
    python scripts/test_gmail.py
"""

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from pathlib import Path

# Configuration
CREDENTIALS_FILE = Path('credentails.json')
TOKEN_FILE = Path('AI_Employee_Vault/.gmail_token.json')
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def authenticate_gmail():
    """Authenticate with Gmail API and save token."""
    
    print("=" * 60)
    print("GMAIL API AUTHENTICATION")
    print("=" * 60)
    print()
    
    # Check credentials file
    if not CREDENTIALS_FILE.exists():
        print(f"ERROR: Credentials file not found: {CREDENTIALS_FILE}")
        print("Please ensure credentails.json exists in the Silver-Tier folder")
        return False
    
    print(f"[OK] Credentials file: {CREDENTIALS_FILE}")
    
    # Delete old token if exists
    if TOKEN_FILE.exists():
        print(f"[OK] Deleting old token: {TOKEN_FILE}")
        TOKEN_FILE.unlink()
    
    # Start authentication flow
    print()
    print("Starting authentication...")
    print("A browser window will open automatically.")
    print("Please sign in and click 'Allow' to grant permissions.")
    print()
    
    try:
        # Create OAuth flow
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
        print("Gmail Watcher will now be able to detect new emails.")
        print("The token is valid until you revoke access or change password.")
        print()
        
        # Verify token
        print("Verifying token...")
        verify_token = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        if verify_token.valid:
            print("[OK] Token is valid and ready to use!")
        else:
            print("[WARNING] Token may need refresh (try running again)")
        
        return True
        
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
        return False


def check_token_status():
    """Check if Gmail token exists and is valid."""
    
    print("=" * 60)
    print("GMAIL TOKEN STATUS")
    print("=" * 60)
    print()
    
    if not TOKEN_FILE.exists():
        print("[ERROR] Token file does not exist")
        print("Run authentication first: python scripts/test_gmail.py")
        return False
    
    print(f"[OK] Token file: {TOKEN_FILE}")
    
    try:
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        
        if creds.valid:
            print("[OK] Token is VALID")
            print()
            print("Gmail Watcher is ready to detect emails!")
            return True
        else:
            print("[ERROR] Token is INVALID or EXPIRED")
            print()
            print("Run authentication to get a new token:")
            print("  python scripts/test_gmail.py")
            return False
            
    except Exception as e:
        print(f"[ERROR] Error reading token: {e}")
        print()
        print("Run authentication to get a new token:")
        print("  python scripts/test_gmail.py")
        return False


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--check':
        # Check token status
        check_token_status()
    else:
        # Run authentication
        success = authenticate_gmail()
        
        if success:
            print()
            print("Next steps:")
            print("1. Send a test email to your Gmail account")
            print("2. Wait 2-3 minutes")
            print("3. Check: dir AI_Employee_Vault\\Needs_Action\\")
            print("4. You should see a new .md file!")
        else:
            sys.exit(1)
