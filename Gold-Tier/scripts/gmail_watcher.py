"""
Gmail Watcher for AI Employee - Gold Tier

Monitors Gmail for new unread messages and creates action files.
Uses credentials.json from project root for Gmail API authentication.

Gold Tier Features:
- Error recovery with retry logic
- Circuit breaker for API failures
- Health monitoring
- 90-day error log retention

Setup:
1. Ensure credentails.json is in project root
2. First run will create .gmail_token.json in vault
3. Subsequent runs use saved token
"""

import base64
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from base_watcher import BaseWatcher

# Import error recovery system
from error_recovery import (
    with_retry,
    classify_error,
    ErrorType,
    create_error_recovery,
    safe_execute
)


class GmailWatcher(BaseWatcher):
    """
    Watches Gmail for new messages and creates action files in the vault.
    """
    
    # Keywords that indicate urgent/important messages
    URGENT_KEYWORDS = ['urgent', 'asap', 'immediate', 'emergency', 'invoice', 'payment', 'help']
    
    def __init__(self, vault_path: str, credentials_path: str = None,
                 check_interval: int = 120, dry_run: bool = False):
        """
        Initialize the Gmail watcher.

        Args:
            vault_path: Path to the Obsidian vault root
            credentials_path: Path to Gmail API credentials (default: credentails.json in project root)
            check_interval: Seconds between checks (default: 120)
            dry_run: If True, log actions but don't create files
        """
        super().__init__(vault_path, check_interval, dry_run)

        # Find credentials file
        if credentials_path:
            self.credentials_path = Path(credentials_path)
        else:
            # Default to project root credentails.json
            self.credentials_path = Path(__file__).parent.parent / 'credentails.json'

        self.token_path = self.vault_path / '.gmail_token.json'

        # Initialize Gold Tier error recovery
        self.error_logger, self.health_checker, self.circuit_breaker = create_error_recovery(vault_path)
        self.logger = logging.getLogger(self.__class__.__name__)

        # Track processed message IDs
        self.processed_ids_file = self.logs_dir / 'gmail_processed_ids.json'
        self.processed_ids = self._load_processed_ids()

        # Try to import Gmail API
        self.service = None
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
            from google.auth.transport.requests import Request

            self.Credentials = Credentials
            self.InstalledAppFlow = InstalledAppFlow
            self.build = build
            self.Request = Request

            self.service = self._authenticate()
        except ImportError as e:
            self.logger.error(f"Missing Gmail API dependencies: {e}")
            self.logger.error("Install with: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
        except Exception as e:
            self.logger.error(f"Error initializing Gmail API: {e}")
        
        self.logger.info(f"Gmail Watcher initialized (credentials: {self.credentials_path})")
    
    def _load_processed_ids(self) -> set:
        """Load previously processed Gmail message IDs."""
        if self.processed_ids_file.exists():
            try:
                with open(self.processed_ids_file, 'r') as f:
                    data = json.load(f)
                    return set(data.get('message_ids', []))
            except Exception as e:
                self.logger.warning(f"Could not load processed IDs: {e}")
        return set()
    
    def _save_processed_ids(self):
        """Save processed Gmail message IDs to disk."""
        try:
            data = {
                'last_updated': datetime.now().isoformat(),
                'message_ids': list(self.processed_ids)
            }
            with open(self.processed_ids_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Could not save processed IDs: {e}")
    
    @with_retry(max_attempts=3, base_delay=1, max_delay=10)
    def _authenticate(self):
        """Authenticate with Gmail API (with BOTH read and send permissions)."""
        from google.auth.exceptions import RefreshError

        creds = None

        # Load existing token with FULL permissions (read + send)
        if self.token_path.exists():
            try:
                creds = self.Credentials.from_authorized_user_file(self.token_path,
                    [
                        'https://www.googleapis.com/auth/gmail.readonly',
                        'https://www.googleapis.com/auth/gmail.send',
                        'https://www.googleapis.com/auth/gmail.compose'
                    ])
            except RefreshError:
                self.logger.warning("Token expired, will re-authenticate")
                self.token_path.unlink()

        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            if not self.credentials_path.exists():
                self.logger.error(f"Credentials file not found: {self.credentials_path}")
                self.logger.error("Please ensure credentails.json exists in project root")
                return None

            try:
                # Authenticate with FULL permissions (read + send + compose)
                flow = self.InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path),
                    [
                        'https://www.googleapis.com/auth/gmail.readonly',
                        'https://www.googleapis.com/auth/gmail.send',
                        'https://www.googleapis.com/auth/gmail.compose'
                    ]
                )
                creds = flow.run_local_server(port=0)

                # Save token for future use
                with open(self.token_path, 'w') as token:
                    token.write(creds.to_json())
                self.logger.info("Gmail authentication successful (with send permissions)")

            except Exception as e:
                self.logger.error(f"Authentication failed: {e}")
                self.error_logger.log_error('gmail_auth', e, {'action': 'authenticate'})
                return None

        # Build Gmail service
        try:
            service = self.build('gmail', 'v1', credentials=creds)
            return service
        except Exception as e:
            self.logger.error(f"Failed to build Gmail service: {e}")
            return None
    
    def _decode_message(self, service, user_id: str, msg_id: str) -> Optional[Dict[str, Any]]:
        """Decode a Gmail message."""
        try:
            message = service.users().messages().get(
                userId=user_id, 
                id=msg_id,
                format='full'
            ).execute()
            
            # Extract headers
            headers = {h['name']: h['value'] for h in message['payload']['headers']}
            
            # Get body
            body = ''
            if 'parts' in message['payload']:
                for part in message['payload']['parts']:
                    if part['mimeType'] == 'text/plain':
                        if 'data' in part['body']:
                            body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                            break
            elif 'body' in message['payload']:
                if 'data' in message['payload']['body']:
                    body = base64.urlsafe_b64decode(message['payload']['body']['data']).decode('utf-8')
            
            # Extract clean email address (remove name part)
            from_email = headers.get('From', 'Unknown')
            if '<' in from_email:
                # Extract email from "Name <email@domain.com>"
                from_email = from_email.split('<')[1].strip('>')
            
            return {
                'id': msg_id,
                'from': from_email,  # Clean email address only
                'from_name': headers.get('From', 'Unknown'),  # Full with name
                'to': headers.get('To', ''),
                'subject': headers.get('Subject', 'No Subject'),
                'date': headers.get('Date', ''),
                'body': body,
                'snippet': message.get('snippet', '')
            }
            
        except Exception as e:
            self.logger.error(f"Error decoding message: {e}")
            return None
    
    def check_for_updates(self) -> List[Dict[str, Any]]:
        """
        Check Gmail for new unread messages.
        
        Returns:
            List of message dictionaries
        """
        if not self.service:
            return []
        
        new_messages = []
        
        try:
            # Search for unread messages
            results = self.service.users().messages().list(
                userId='me',
                q='is:unread',
                maxResults=10
            ).execute()
            
            messages = results.get('messages', [])
            
            for msg in messages:
                if msg['id'] not in self.processed_ids:
                    message_data = self._decode_message(self.service, 'me', msg['id'])
                    if message_data:
                        # Check for urgent keywords
                        subject_lower = message_data['subject'].lower()
                        snippet_lower = message_data['snippet'].lower()
                        message_data['is_urgent'] = any(
                            kw in subject_lower or kw in snippet_lower
                            for kw in self.URGENT_KEYWORDS
                        )
                        new_messages.append(message_data)
                        self.processed_ids.add(msg['id'])
            
            # Save processed IDs
            self._save_processed_ids()
            
        except Exception as e:
            self.logger.error(f"Error checking Gmail: {e}")
        
        return new_messages
    
    def create_action_file(self, item: Dict[str, Any]) -> Optional[Path]:
        """
        Create an action file for the Gmail message.
        
        Args:
            item: Message dictionary
            
        Returns:
            Path to created action file, or None if dry_run
        """
        # Generate unique ID from message ID
        unique_id = item['id'][:8]
        
        # Determine priority
        priority = 'high' if item.get('is_urgent', False) else 'normal'
        
        # Create suggested actions based on content
        suggested_actions = [
            "Read full email content",
            "Determine if reply needed",
            "Archive after processing"
        ]
        
        if item.get('is_urgent'):
            suggested_actions.insert(0, "URGENT: Respond within 24 hours")
        
        if 'invoice' in item['subject'].lower() or 'payment' in item['subject'].lower():
            suggested_actions.append("Forward to accounting")
            suggested_actions.append("Check payment status")
        
        # Truncate body for display
        body_preview = item['body'][:500] if item['body'] else item['snippet']
        if len(item['body'] or '') > 500:
            body_preview += "..."
        
        # Create markdown content with ALL email fields
        content = f"""---
type: email
from: {item['from']}
from_name: {item.get('from_name', item['from'])}
to: {item.get('to', '')}
subject: {item['subject']}
date: {item['date']}
gmail_id: {item['id']}
priority: {priority}
is_urgent: {str(item.get('is_urgent', False))}
created: {datetime.now().isoformat()}
status: pending
---

## Email Content

From: {item.get('from_name', item['from'])}
Subject: {item['subject']}

{body_preview}

## Suggested Actions

"""
        for action in suggested_actions:
            content += f"- [ ] {action}\n"
        
        content += f"""
---
*Created by AI Employee Gmail Watcher v0.2.0*
"""
        
        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would create action file for email from {item['from']}")
            return None
        
        # Generate filename and write file
        filename = self._generate_filename('EMAIL', unique_id)
        filepath = self.needs_action / filename
        filepath.write_text(content, encoding='utf-8')
        
        # Log the action
        self.log_action('email_processed', {
            'from': item['from'],
            'subject': item['subject'],
            'urgent': item.get('is_urgent', False),
            'action_file': filename
        })
        
        return filepath


def main():
    """Run the Gmail watcher."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Gmail Watcher for AI Employee')
    parser.add_argument('--vault', required=True, help='Path to Obsidian vault')
    parser.add_argument('--credentials', help='Path to credentails.json (default: project root)')
    parser.add_argument('--interval', type=int, default=120, help='Check interval in seconds')
    parser.add_argument('--dry-run', action='store_true', help='Log actions without creating files')
    
    args = parser.parse_args()
    
    watcher = GmailWatcher(
        vault_path=args.vault,
        credentials_path=args.credentials,
        check_interval=args.interval,
        dry_run=args.dry_run
    )
    
    if watcher.service:
        print(f"Gmail Watcher started - checking every {args.interval} seconds")
        print(f"Credentials: {watcher.credentials_path}")
        print(f"Token: {watcher.token_path}")
        watcher.run()
    else:
        print("Gmail Watcher could not start - check credentials and dependencies")
        print(f"Credentials file exists: {watcher.credentials_path.exists()}")


if __name__ == '__main__':
    main()
