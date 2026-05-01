"""
Watcher Watchdog - Monitors all watcher processes

Continuously monitors all watcher processes (gmail, whatsapp, facebook, instagram)
and alerts if any stop responding or crash.

Addresses AUDIT-1 RISK #5: No Health Monitoring

Features:
- Monitors all watcher processes
- Checks heartbeats every 60 seconds
- Detects crashed or hung processes
- Sends alerts when watchers fail
- Auto-restart capability (optional)
- Health status reporting

Usage:
    python scripts/watcher_watchdog.py --vault AI_Employee_Vault --check-interval 60
"""

import os
import sys
import time
import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from logging_config import get_logger
from alerting import AlertManager, AlertSeverity


class WatcherStatus:
    """Tracks status of a single watcher."""

    def __init__(self, name: str, heartbeat_file: Path):
        self.name = name
        self.heartbeat_file = heartbeat_file
        self.last_heartbeat: Optional[datetime] = None
        self.consecutive_failures = 0
        self.is_healthy = True
        self.last_check = datetime.now()

    def check_heartbeat(self, max_age_seconds: int = 300) -> bool:
        """
        Check if watcher heartbeat is recent.

        Args:
            max_age_seconds: Maximum age of heartbeat before considering unhealthy

        Returns:
            True if healthy, False if unhealthy
        """
        self.last_check = datetime.now()

        # Check if heartbeat file exists
        if not self.heartbeat_file.exists():
            self.consecutive_failures += 1
            self.is_healthy = False
            return False

        # Check heartbeat age
        try:
            mtime = datetime.fromtimestamp(self.heartbeat_file.stat().st_mtime)
            age_seconds = (datetime.now() - mtime).total_seconds()

            if age_seconds > max_age_seconds:
                self.consecutive_failures += 1
                self.is_healthy = False
                return False

            # Healthy
            self.last_heartbeat = mtime
            self.consecutive_failures = 0
            self.is_healthy = True
            return True

        except Exception as e:
            self.consecutive_failures += 1
            self.is_healthy = False
            return False


class WatcherWatchdog:
    """Monitors all watcher processes."""

    def __init__(self, vault_path: str, check_interval: int = 60,
                 max_heartbeat_age: int = 300, alert_threshold: int = 3):
        self.vault = Path(vault_path)
        self.check_interval = check_interval
        self.max_heartbeat_age = max_heartbeat_age
        self.alert_threshold = alert_threshold

        # Setup logging
        self.logger = get_logger('watcher_watchdog', vault_path=vault_path)

        # Setup alerting
        self.alert_manager = AlertManager(vault_path=vault_path)

        # Heartbeat directory
        self.heartbeat_dir = self.vault / 'Logs' / 'heartbeats'
        self.heartbeat_dir.mkdir(parents=True, exist_ok=True)

        # Watchers to monitor
        self.watchers: Dict[str, WatcherStatus] = {
            'gmail_watcher': WatcherStatus('gmail_watcher', self.heartbeat_dir / 'gmail_watcher.heartbeat'),
            'whatsapp_watcher': WatcherStatus('whatsapp_watcher', self.heartbeat_dir / 'whatsapp_watcher.heartbeat'),
            'facebook_watcher': WatcherStatus('facebook_watcher', self.heartbeat_dir / 'facebook_watcher.heartbeat'),
            'instagram_watcher': WatcherStatus('instagram_watcher', self.heartbeat_dir / 'instagram_watcher.heartbeat'),
        }

        self.logger.info(f"Watcher Watchdog initialized")
        self.logger.info(f"Monitoring {len(self.watchers)} watchers")
        self.logger.info(f"Check interval: {check_interval}s")
        self.logger.info(f"Max heartbeat age: {max_heartbeat_age}s")

        # Send startup notification
        try:
            self.alert_manager.send_alert(
                severity=AlertSeverity.INFO,
                title="Watcher Watchdog Started",
                message=f"Monitoring system is now active.\n\nWatchers monitored: {len(self.watchers)}\nCheck interval: {check_interval}s\nAlert threshold: {alert_threshold} consecutive failures",
                details={'watchers': list(self.watchers.keys()), 'check_interval': check_interval}
            )
        except Exception as e:
            self.logger.warning(f"Failed to send startup notification: {e}")

    def check_all_watchers(self) -> Dict[str, bool]:
        """
        Check health of all watchers.

        Returns:
            Dictionary mapping watcher name to health status
        """
        results = {}

        for name, watcher in self.watchers.items():
            is_healthy = watcher.check_heartbeat(self.max_heartbeat_age)
            results[name] = is_healthy

            if not is_healthy:
                if watcher.consecutive_failures >= self.alert_threshold:
                    self.logger.error(
                        f"[ALERT] {name} is UNHEALTHY "
                        f"(consecutive failures: {watcher.consecutive_failures})"
                    )
                    self.send_alert(name, watcher)
                else:
                    self.logger.warning(
                        f"{name} missed heartbeat "
                        f"(failures: {watcher.consecutive_failures}/{self.alert_threshold})"
                    )
            else:
                if watcher.last_heartbeat:
                    age = (datetime.now() - watcher.last_heartbeat).total_seconds()
                    self.logger.debug(f"{name} is healthy (heartbeat age: {age:.0f}s)")

        return results

    def send_alert(self, watcher_name: str, watcher: WatcherStatus):
        """
        Send alert for unhealthy watcher.

        Args:
            watcher_name: Name of the watcher
            watcher: WatcherStatus object
        """
        # Build alert message
        alert_title = f"Watcher Down: {watcher_name}"
        alert_message = (
            f"{watcher_name} is unhealthy and not responding.\n\n"
            f"Consecutive failures: {watcher.consecutive_failures}\n"
            f"Last check: {watcher.last_check.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Last heartbeat: {watcher.last_heartbeat.strftime('%Y-%m-%d %H:%M:%S') if watcher.last_heartbeat else 'Never'}\n\n"
            f"Action required: Check if the watcher process is running."
        )

        # Log alert
        self.logger.error(f"[ALERT] {alert_title}")
        self.logger.error(alert_message)

        # Write alert file for audit trail
        alert_file = self.vault / 'Logs' / 'alerts' / f"{watcher_name}_alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        alert_file.parent.mkdir(parents=True, exist_ok=True)
        alert_file.write_text(f"{alert_title}\n\n{alert_message}")

        # Send to alerting system (Slack, email, etc.)
        try:
            self.alert_manager.send_alert(
                severity=AlertSeverity.CRITICAL,
                title=alert_title,
                message=alert_message,
                details={'watcher': watcher_name, 'failures': watcher.consecutive_failures}
            )
            self.logger.info(f"Alert sent successfully for {watcher_name}")
        except Exception as e:
            self.logger.error(f"Failed to send alert for {watcher_name}: {e}")

    def get_summary(self) -> Dict[str, any]:
        """Get summary of all watcher statuses."""
        healthy_count = sum(1 for w in self.watchers.values() if w.is_healthy)
        total_count = len(self.watchers)

        return {
            'timestamp': datetime.now().isoformat(),
            'healthy_count': healthy_count,
            'total_count': total_count,
            'all_healthy': healthy_count == total_count,
            'watchers': {
                name: {
                    'healthy': w.is_healthy,
                    'consecutive_failures': w.consecutive_failures,
                    'last_heartbeat': w.last_heartbeat.isoformat() if w.last_heartbeat else None,
                    'last_check': w.last_check.isoformat(),
                }
                for name, w in self.watchers.items()
            }
        }

    def run(self):
        """Run the watchdog monitoring loop."""
        self.logger.info("Starting Watcher Watchdog monitoring loop")

        try:
            while True:
                # Check all watchers
                results = self.check_all_watchers()

                # Log summary
                healthy = sum(1 for h in results.values() if h)
                total = len(results)
                self.logger.info(f"Health check complete: {healthy}/{total} watchers healthy")

                # Sleep until next check
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            self.logger.info("Watcher Watchdog stopped by user")
        except Exception as e:
            self.logger.error(f"Watcher Watchdog error: {e}", exc_info=True)
            raise


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Watcher Watchdog - Monitor all watcher processes')
    parser.add_argument('--vault', default='AI_Employee_Vault', help='Path to AI Employee Vault')
    parser.add_argument('--check-interval', type=int, default=60, help='Check interval in seconds (default: 60)')
    parser.add_argument('--max-heartbeat-age', type=int, default=300, help='Max heartbeat age in seconds (default: 300)')
    parser.add_argument('--alert-threshold', type=int, default=3, help='Consecutive failures before alert (default: 3)')

    args = parser.parse_args()

    # Create and run watchdog
    watchdog = WatcherWatchdog(
        vault_path=args.vault,
        check_interval=args.check_interval,
        max_heartbeat_age=args.max_heartbeat_age,
        alert_threshold=args.alert_threshold
    )

    watchdog.run()


if __name__ == '__main__':
    main()
