"""
Deadlock Watchdog for AI Employee

Monitors services for deadlocks and stuck processes by:
- Checking heartbeat files
- Monitoring process activity
- Detecting infinite loops
- Tracking file lock ages
- Alerting on stuck services

Features:
- Heartbeat monitoring
- Process activity tracking
- Lock age detection
- Automatic alerting
- Recovery suggestions

Usage:
    # Run watchdog
    python scripts/deadlock_watchdog.py --vault AI_Employee_Vault --interval 60

    # Or use programmatically
    from deadlock_watchdog import DeadlockWatchdog

    watchdog = DeadlockWatchdog(vault_path)
    watchdog.check_all_services()
"""

import os
import psutil
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple


class DeadlockWatchdog:
    """Monitors services for deadlocks and stuck processes."""

    def __init__(
        self,
        vault_path: str,
        heartbeat_timeout_seconds: int = 300,
        lock_timeout_seconds: int = 600,
        alerter=None
    ):
        """
        Initialize watchdog.

        Args:
            vault_path: Path to vault
            heartbeat_timeout_seconds: Max seconds since last heartbeat (default: 5 min)
            lock_timeout_seconds: Max seconds for a lock to be held (default: 10 min)
            alerter: Optional alerter instance for notifications
        """
        self.vault = Path(vault_path)
        self.heartbeat_dir = self.vault / "Logs" / "heartbeats"
        self.heartbeat_dir.mkdir(parents=True, exist_ok=True)

        self.locks_dir = self.vault / "Logs" / "locks"
        self.locks_dir.mkdir(parents=True, exist_ok=True)

        self.heartbeat_timeout = timedelta(seconds=heartbeat_timeout_seconds)
        self.lock_timeout = timedelta(seconds=lock_timeout_seconds)

        self.alerter = alerter

        # Services to monitor
        self.services = [
            'orchestrator',
            'approval_handler',
            'gmail_watcher',
            'ralph_wiggum',
            'instagram_watcher',
            'facebook_watcher',
            'whatsapp_watcher'
        ]

    def record_heartbeat(self, service: str):
        """
        Record a heartbeat for a service.

        Args:
            service: Service name
        """
        heartbeat_file = self.heartbeat_dir / f"{service}.heartbeat"
        heartbeat_file.write_text(datetime.now().isoformat())

    def check_heartbeat(self, service: str) -> Tuple[bool, Optional[timedelta]]:
        """
        Check if service heartbeat is recent.

        Args:
            service: Service name

        Returns:
            Tuple of (is_healthy, time_since_heartbeat)
        """
        heartbeat_file = self.heartbeat_dir / f"{service}.heartbeat"

        if not heartbeat_file.exists():
            return False, None

        try:
            last_heartbeat_str = heartbeat_file.read_text().strip()
            last_heartbeat = datetime.fromisoformat(last_heartbeat_str)
            time_since = datetime.now() - last_heartbeat

            is_healthy = time_since < self.heartbeat_timeout
            return is_healthy, time_since

        except Exception as e:
            print(f"[ERROR] Failed to check heartbeat for {service}: {e}")
            return False, None

    def check_all_heartbeats(self) -> Dict[str, Dict[str, Any]]:
        """
        Check heartbeats for all services.

        Returns:
            Dict mapping service names to status info
        """
        results = {}

        for service in self.services:
            is_healthy, time_since = self.check_heartbeat(service)

            results[service] = {
                'healthy': is_healthy,
                'time_since_heartbeat': time_since,
                'status': 'healthy' if is_healthy else 'stale' if time_since else 'missing'
            }

            # Alert if unhealthy
            if not is_healthy and self.alerter:
                if time_since:
                    message = f"Service {service} heartbeat is stale ({time_since.total_seconds():.0f}s old)"
                else:
                    message = f"Service {service} has no heartbeat file"

                from alerting import AlertSeverity
                self.alerter.send_alert(
                    title=f"Service Heartbeat Stale: {service}",
                    message=message,
                    severity=AlertSeverity.WARNING,
                    service=service
                )

        return results

    def check_stale_locks(self) -> List[Dict[str, Any]]:
        """
        Check for stale file locks.

        Returns:
            List of stale lock info
        """
        stale_locks = []

        if not self.locks_dir.exists():
            return stale_locks

        for lock_file in self.locks_dir.glob('*.lock'):
            try:
                # Get lock age
                lock_age = datetime.now() - datetime.fromtimestamp(lock_file.stat().st_mtime)

                if lock_age > self.lock_timeout:
                    # Read lock info
                    lock_info = {}
                    try:
                        lock_content = lock_file.read_text()
                        for line in lock_content.split('\n'):
                            if ':' in line:
                                key, value = line.split(':', 1)
                                lock_info[key.strip()] = value.strip()
                    except:
                        pass

                    stale_locks.append({
                        'lock_file': lock_file.name,
                        'age_seconds': lock_age.total_seconds(),
                        'pid': lock_info.get('pid'),
                        'acquired_by': lock_info.get('acquired_by'),
                        'acquired_at': lock_info.get('acquired_at')
                    })

                    # Alert
                    if self.alerter:
                        from alerting import AlertSeverity
                        self.alerter.send_alert(
                            title=f"Stale Lock Detected: {lock_file.name}",
                            message=f"Lock held for {lock_age.total_seconds():.0f}s (timeout: {self.lock_timeout.total_seconds():.0f}s)",
                            severity=AlertSeverity.ERROR,
                            metadata=lock_info
                        )

            except Exception as e:
                print(f"[ERROR] Failed to check lock {lock_file}: {e}")

        return stale_locks

    def check_process_activity(self, service: str, pid: Optional[int] = None) -> Dict[str, Any]:
        """
        Check if a process is active or stuck.

        Args:
            service: Service name
            pid: Process ID (optional, will try to find it)

        Returns:
            Dict with process status info
        """
        try:
            # Find process if PID not provided
            if pid is None:
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        cmdline = ' '.join(proc.info['cmdline'] or [])
                        if service in cmdline:
                            pid = proc.info['pid']
                            break
                    except:
                        continue

            if pid is None:
                return {'status': 'not_found', 'pid': None}

            # Get process info
            process = psutil.Process(pid)

            # Check CPU usage (averaged over 1 second)
            cpu_percent = process.cpu_percent(interval=1)

            # Check if process is responsive
            status = process.status()

            # Check thread count
            num_threads = process.num_threads()

            # Check memory usage
            memory_info = process.memory_info()

            result = {
                'status': 'active' if status == psutil.STATUS_RUNNING else status,
                'pid': pid,
                'cpu_percent': cpu_percent,
                'num_threads': num_threads,
                'memory_mb': memory_info.rss / (1024 * 1024),
                'is_stuck': status in [psutil.STATUS_ZOMBIE, psutil.STATUS_DEAD]
            }

            # Alert if stuck
            if result['is_stuck'] and self.alerter:
                from alerting import AlertSeverity
                self.alerter.send_alert(
                    title=f"Process Stuck: {service}",
                    message=f"Process {pid} is in {status} state",
                    severity=AlertSeverity.CRITICAL,
                    service=service,
                    metadata={'pid': pid, 'status': status}
                )

            return result

        except psutil.NoSuchProcess:
            return {'status': 'not_running', 'pid': pid}
        except Exception as e:
            print(f"[ERROR] Failed to check process activity for {service}: {e}")
            return {'status': 'error', 'error': str(e)}

    def check_infinite_loops(self) -> List[Dict[str, Any]]:
        """
        Detect potential infinite loops by checking CPU usage.

        Returns:
            List of processes with suspiciously high CPU usage
        """
        suspicious_processes = []

        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])

                    # Check if it's one of our services
                    is_our_service = any(service in cmdline for service in self.services)

                    if is_our_service:
                        # Get CPU usage
                        cpu_percent = proc.cpu_percent(interval=1)

                        # Flag if using >80% CPU for extended period
                        if cpu_percent > 80:
                            suspicious_processes.append({
                                'pid': proc.info['pid'],
                                'name': proc.info['name'],
                                'cmdline': cmdline,
                                'cpu_percent': cpu_percent
                            })

                            # Alert
                            if self.alerter:
                                from alerting import AlertSeverity
                                self.alerter.send_alert(
                                    title=f"High CPU Usage Detected",
                                    message=f"Process {proc.info['pid']} using {cpu_percent:.1f}% CPU",
                                    severity=AlertSeverity.WARNING,
                                    metadata={'pid': proc.info['pid'], 'cpu_percent': cpu_percent}
                                )

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

        except Exception as e:
            print(f"[ERROR] Failed to check for infinite loops: {e}")

        return suspicious_processes

    def check_all_services(self) -> Dict[str, Any]:
        """
        Run all watchdog checks.

        Returns:
            Dict with all check results
        """
        print("\n" + "="*60)
        print("DEADLOCK WATCHDOG - Running Checks")
        print("="*60)

        results = {
            'timestamp': datetime.now().isoformat(),
            'heartbeats': {},
            'stale_locks': [],
            'process_activity': {},
            'infinite_loops': []
        }

        # Check heartbeats
        print("\n[1/4] Checking heartbeats...")
        results['heartbeats'] = self.check_all_heartbeats()

        healthy_count = sum(1 for s in results['heartbeats'].values() if s['healthy'])
        print(f"  {healthy_count}/{len(self.services)} services have healthy heartbeats")

        # Check stale locks
        print("\n[2/4] Checking for stale locks...")
        results['stale_locks'] = self.check_stale_locks()
        print(f"  Found {len(results['stale_locks'])} stale lock(s)")

        # Check process activity
        print("\n[3/4] Checking process activity...")
        for service in self.services:
            results['process_activity'][service] = self.check_process_activity(service)

        active_count = sum(1 for s in results['process_activity'].values() if s['status'] == 'active')
        print(f"  {active_count}/{len(self.services)} services are active")

        # Check for infinite loops
        print("\n[4/4] Checking for infinite loops...")
        results['infinite_loops'] = self.check_infinite_loops()
        print(f"  Found {len(results['infinite_loops'])} suspicious process(es)")

        print("\n" + "="*60)
        print("WATCHDOG CHECKS COMPLETE")
        print("="*60)

        return results

    def run_continuous(self, interval_seconds: int = 60):
        """
        Run watchdog continuously.

        Args:
            interval_seconds: Seconds between checks
        """
        print(f"[OK] Deadlock watchdog started (interval: {interval_seconds}s)")

        try:
            while True:
                self.check_all_services()
                time.sleep(interval_seconds)

        except KeyboardInterrupt:
            print("\n[OK] Watchdog stopped")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Deadlock Watchdog')
    parser.add_argument('--vault', default='AI_Employee_Vault', help='Path to vault')
    parser.add_argument('--interval', type=int, default=60, help='Check interval in seconds')
    parser.add_argument('--heartbeat-timeout', type=int, default=300, help='Heartbeat timeout in seconds')
    parser.add_argument('--lock-timeout', type=int, default=600, help='Lock timeout in seconds')
    parser.add_argument('--enable-alerts', action='store_true', help='Enable alerting')

    args = parser.parse_args()

    # Initialize alerter if enabled
    alerter = None
    if args.enable_alerts:
        from alerting import get_alerter
        alerter = get_alerter(args.vault)

    # Create watchdog
    watchdog = DeadlockWatchdog(
        vault_path=args.vault,
        heartbeat_timeout_seconds=args.heartbeat_timeout,
        lock_timeout_seconds=args.lock_timeout,
        alerter=alerter
    )

    # Run continuously
    watchdog.run_continuous(interval_seconds=args.interval)


if __name__ == '__main__':
    main()
