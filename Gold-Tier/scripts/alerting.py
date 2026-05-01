"""
Alerting System for AI Employee - Gold Tier

Sends notifications when critical errors occur, watchers crash, or health checks fail.
Addresses AUDIT-1 RISK #5: No Health Monitoring
"""

import os
import json
import time
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertManager:
    """Manages alert delivery across multiple channels."""

    def __init__(self, vault_path: str):
        self.vault = Path(vault_path)
        self.alerts_dir = self.vault / 'Logs' / 'alerts'
        self.alerts_dir.mkdir(parents=True, exist_ok=True)
        self.slack_webhook_url = os.getenv('SLACK_WEBHOOK_URL')

    def send_alert(self, severity: AlertSeverity, title: str, message: str,
                   details: Optional[Dict[str, Any]] = None) -> bool:
        """Send an alert through configured channels."""
        alert_data = {
            'severity': severity.value,
            'title': title,
            'message': message,
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        }
        
        # Log alert
        log_file = self.alerts_dir / f"{datetime.now().strftime('%Y-%m-%d')}_alerts.jsonl"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(alert_data) + '\n')
        
        # Send to Slack if configured
        if self.slack_webhook_url:
            try:
                # Use simple text format (blocks not supported by all webhooks)
                emoji = self._get_severity_emoji(severity)
                formatted_message = (
                    f"{emoji} *{title}*\n"
                    f"_{severity.value.upper()}_\n\n"
                    f"{message}\n\n"
                    f"_Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_"
                )

                slack_payload = {"text": formatted_message}

                response = requests.post(self.slack_webhook_url, json=slack_payload, timeout=10)

                # Log response for debugging
                if response.status_code != 200:
                    error_log = self.alerts_dir / 'slack_errors.log'
                    with open(error_log, 'a', encoding='utf-8') as f:
                        f.write(f"{datetime.now().isoformat()} - Slack returned {response.status_code}: {response.text}\n")
                    return False

                return True
            except Exception as e:
                # Log the error instead of silently failing
                error_log = self.alerts_dir / 'slack_errors.log'
                with open(error_log, 'a', encoding='utf-8') as f:
                    f.write(f"{datetime.now().isoformat()} - Failed to send Slack alert: {e}\n")
                return False

        return True

    def _get_severity_emoji(self, severity: AlertSeverity) -> str:
        """Get emoji for severity level."""
        emoji_map = {
            AlertSeverity.INFO: ":information_source:",
            AlertSeverity.WARNING: ":warning:",
            AlertSeverity.ERROR: ":x:",
            AlertSeverity.CRITICAL: ":rotating_light:"
        }
        return emoji_map.get(severity, ":loudspeaker:")


def send_alert(severity: str, title: str, message: str, details: Optional[Dict[str, Any]] = None, vault_path: str = 'AI_Employee_Vault') -> bool:
    """Convenience function to send an alert."""
    manager = AlertManager(vault_path)
    return manager.send_alert(AlertSeverity(severity), title, message, details)
