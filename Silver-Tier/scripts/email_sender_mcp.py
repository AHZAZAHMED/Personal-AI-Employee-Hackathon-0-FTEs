"""
Email Sender for AI Employee - Silver Tier (Gmail API)

Sends emails via Gmail API.
Integrates with Approval Handler for HITL workflow.

Usage:
    python scripts/email_sender_mcp.py --vault AI_Employee_Vault
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    EMAIL_LIB_AVAILABLE = True
except:
    EMAIL_LIB_AVAILABLE = False


class EmailSender:
    """Sends emails via Gmail API."""

    def __init__(self, vault_path: str):
        self.vault = Path(vault_path)
        self.logs = self.vault / 'Logs'
        self.logs.mkdir(parents=True, exist_ok=True)

        # Approved contacts
        self.approved_contacts = self._load_approved_contacts()

    def _load_approved_contacts(self) -> set:
        """Load approved contacts from vault."""
        contacts_file = self.vault.parent / 'approved_contacts.json'
        if contacts_file.exists():
            try:
                with open(contacts_file, 'r') as f:
                    data = json.load(f)
                    return set(data.get('emails', []))
            except:
                pass
        return set()
    
    def send_email(self, to: str, subject: str, body: str,
                   in_reply_to: str = None) -> Dict[str, Any]:
        """
        Send an email via Gmail API.
        """
        print(f"    Sending email via Gmail API...")
        print(f"    To: {to}")
        print(f"    Subject: {subject}")

        # Send via Gmail API
        return self._send_email_gmail_api(to, subject, body, in_reply_to)

    def _send_email_gmail_api(self, to: str, subject: str, body: str,
                                   in_reply_to: str = None) -> Dict[str, Any]:
        """Send email via Gmail API."""
        try:
            from email.mime.text import MIMEText
            import base64
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            
            token_path = self.vault / '.gmail_token.json'
            credentials_path = Path(__file__).parent.parent / 'credentails.json'
            
            # Authenticate with FULL permissions (read + send + compose)
            creds = None
            if token_path.exists():
                creds = Credentials.from_authorized_user_file(
                    token_path,
                    [
                        'https://www.googleapis.com/auth/gmail.readonly',
                        'https://www.googleapis.com/auth/gmail.send',
                        'https://www.googleapis.com/auth/gmail.compose'
                    ]
                )
            
            if not creds or not creds.valid:
                if credentials_path.exists():
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(credentials_path),
                        [
                            'https://www.googleapis.com/auth/gmail.readonly',
                            'https://www.googleapis.com/auth/gmail.send',
                            'https://www.googleapis.com/auth/gmail.compose'
                        ]
                    )
                    creds = flow.run_local_server(port=0)
                    with open(token_path, 'w') as token:
                        token.write(creds.to_json())
                else:
                    return {'success': False, 'error': 'No credentials'}
            
            # Send email
            service = build('gmail', 'v1', credentials=creds)

            # Create email with proper formatting for email clients
            # Email clients need \r\n\r\n for paragraph breaks
            email_body = body.replace('\n\n', '\r\n\r\n').replace('\n', ' ')

            message = f"""From: AI Employee <AI Employee>
To: {to}
Subject: {subject}
MIME-Version: 1.0
Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: 7bit

{email_body}"""

            # Encode message
            raw_message = base64.urlsafe_b64encode(message.encode('utf-8')).decode('utf-8')
            
            sent_message = service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            print(f"    [OK] Email sent via Gmail API!")
            self._log_event('email_sent', {
                'to': to,
                'subject': subject,
                'message_id': sent_message['id']
            })
            
            return {
                'success': True,
                'message_id': sent_message['id'],
                'method': 'fallback_gmail'
            }
            
        except Exception as e:
            print(f"    [ERROR] Fallback failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _log_event(self, event_type: str, details: Dict[str, Any]):
        """Log an event to the daily log file."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            **details
        }
        
        log_file = self.logs / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')


def execute_approved_email(action_type: str, metadata: Dict[str, Any],
                           content: str) -> Dict[str, Any]:
    """Callback for Approval Handler to execute email actions."""
    print(f"    Executing email action: {action_type}")
    
    if action_type not in ['email', 'email_send', 'email_reply']:
        return {'success': False, 'error': 'Not an email action'}
    
    vault_path = Path(__file__).parent.parent / 'AI_Employee_Vault'
    sender = EmailSender(str(vault_path))
    
    to = metadata.get('to', '')
    subject = metadata.get('subject', '')
    draft_body = metadata.get('draft_body', '')
    gmail_id = metadata.get('gmail_id')
    
    print(f"    To: {to}")
    print(f"    Subject: {subject}")
    
    if not to or to == 'Unknown':
        return {'success': False, 'error': 'No recipient'}
    
    if not draft_body:
        draft_body = f"Re: {subject}\n\n(Automated reply from AI Employee)"
    
    result = sender.send_email(to, subject, draft_body, gmail_id)
    
    if result.get('success'):
        print(f"    [OK] Email sent successfully!")
    else:
        print(f"    [ERROR] Email failed: {result.get('error', 'Unknown error')}")
    
    return result


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='AI Employee Email Sender (Gmail API)')
    parser.add_argument('--vault', required=True, help='Vault path')
    parser.add_argument('--send', help='Send email to this address')
    parser.add_argument('--subject', help='Email subject')
    parser.add_argument('--body', help='Email body')

    args = parser.parse_args()

    sender = EmailSender(args.vault)

    if args.send and args.subject:
        body = args.body or "Test email from AI Employee"
        result = sender.send_email(args.send, args.subject, body)

        if result['success']:
            print("\n[OK] Email sent!")
        else:
            print(f"\n[FAIL] Failed: {result.get('error', 'Unknown')}")
    else:
        print("Email Sender (Gmail API) ready")
        print(f"Using: Gmail API Direct")
