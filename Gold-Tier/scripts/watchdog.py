"""
Watchdog Process for AI Employee - Gold Tier

Monitors all watcher processes and auto-restarts them if they crash.
Provides health monitoring and alerting.

Usage:
    python scripts/watchdog.py --vault AI_Employee_Vault
"""

import subprocess
import time
import logging
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass

# Import error recovery
from error_recovery import HealthChecker, ErrorLogger, CircuitBreaker, with_retry


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class WatcherConfig:
    """Configuration for a watcher process."""
    name: str
    script: str
    args: List[str]
    check_interval: int = 60  # How often to check if running
    restart_delay: int = 5  # Seconds to wait before restarting
    max_restarts_per_hour: int = 5  # Max restarts before giving up


# Default watcher configurations
DEFAULT_WATCHERS = {
    'gmail_watcher': WatcherConfig(
        name='Gmail Watcher',
        script='gmail_watcher.py',
        args=['--vault', 'AI_Employee_Vault', '--interval', '120'],
        check_interval=60,
        restart_delay=5
    ),
    'filesystem_watcher': WatcherConfig(
        name='File System Watcher',
        script='filesystem_watcher.py',
        args=['--vault', 'AI_Employee_Vault', '--watch', 'watch_folder'],
        check_interval=60,
        restart_delay=5
    ),
    'orchestrator': WatcherConfig(
        name='Orchestrator',
        script='orchestrator.py',
        args=['--vault', 'AI_Employee_Vault', '--interval', '60'],
        check_interval=60,
        restart_delay=5
    )
}


# ============================================================================
# WATCHDOG CLASS
# ============================================================================

class Watchdog:
    """
    Watchdog that monitors and restarts watcher processes.
    """
    
    def __init__(
        self,
        vault_path: str,
        watchers: Optional[Dict[str, WatcherConfig]] = None
    ):
        """
        Initialize watchdog.
        
        Args:
            vault_path: Path to Obsidian vault
            watchers: Dictionary of watcher configurations
        """
        self.vault_path = Path(vault_path)
        self.watchers = watchers or DEFAULT_WATCHERS
        
        # Initialize error recovery
        self.error_logger = ErrorLogger(vault_path)
        self.health_checker = HealthChecker(vault_path)
        
        # Track process state
        self.processes: Dict[str, subprocess.Popen] = {}
        self.restart_counts: Dict[str, int] = {}
        self.last_restart_time: Dict[str, datetime] = {}
        self.pid_files: Dict[str, Path] = {}
        
        # Setup logging
        self._setup_logging()
        
        # PID file directory
        self.pid_dir = self.vault_path / 'Logs' / 'pids'
        self.pid_dir.mkdir(parents=True, exist_ok=True)
    
    def _setup_logging(self):
        """Setup logging configuration."""
        log_file = self.vault_path / 'Logs' / 'watchdog.log'
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('Watchdog')
    
    def start_watcher(self, watcher_id: str) -> bool:
        """
        Start a watcher process.
        
        Args:
            watcher_id: Watcher identifier
            
        Returns:
            True if started successfully
        """
        config = self.watchers.get(watcher_id)
        if not config:
            self.logger.error(f"Unknown watcher: {watcher_id}")
            return False
        
        try:
            # Build command
            cmd = ['python', config.script] + config.args
            
            self.logger.info(f"Starting {config.name}: {' '.join(cmd)}")
            
            # Start process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(Path(__file__).parent)
            )
            
            # Save PID
            self.processes[watcher_id] = process
            self._save_pid(watcher_id, process.pid)
            
            self.logger.info(f"{config.name} started (PID: {process.pid})")
            
            # Report health
            self.health_checker.report_status(
                f'watchdog_{watcher_id}',
                'healthy',
                {'pid': process.pid}
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start {config.name}: {e}")
            self.error_logger.log_error(
                f'watchdog_{watcher_id}',
                e,
                {'action': 'start'}
            )
            return False
    
    def stop_watcher(self, watcher_id: str) -> bool:
        """
        Stop a watcher process.
        
        Args:
            watcher_id: Watcher identifier
            
        Returns:
            True if stopped successfully
        """
        process = self.processes.get(watcher_id)
        if not process:
            return True  # Already stopped
        
        config = self.watchers.get(watcher_id)
        name = config.name if config else watcher_id
        
        try:
            self.logger.info(f"Stopping {name} (PID: {process.pid})")
            
            # Terminate process
            process.terminate()
            
            # Wait for graceful shutdown
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                # Force kill if not responding
                self.logger.warning(f"{name} didn't stop gracefully, force killing...")
                process.kill()
                process.wait()
            
            # Cleanup
            del self.processes[watcher_id]
            self._remove_pid(watcher_id)
            
            self.logger.info(f"{name} stopped")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping {name}: {e}")
            self.error_logger.log_error(
                f'watchdog_{watcher_id}',
                e,
                {'action': 'stop'}
            )
            return False
    
    def check_watcher(self, watcher_id: str) -> bool:
        """
        Check if a watcher is running, restart if needed.
        
        Args:
            watcher_id: Watcher identifier
            
        Returns:
            True if running (or restarted successfully)
        """
        config = self.watchers.get(watcher_id)
        if not config:
            return False
        
        process = self.processes.get(watcher_id)
        
        # Check if process exists and is running
        if process and process.poll() is None:
            # Process is running
            return True
        
        # Process is not running
        self.logger.warning(f"{config.name} is not running")
        
        # Check restart limits
        if not self._can_restart(watcher_id):
            self.logger.error(
                f"{config.name} exceeded max restarts "
                f"({config.max_restarts_per_hour}/hour)"
            )
            self.health_checker.report_status(
                f'watchdog_{watcher_id}',
                'unhealthy',
                {'error': 'Max restarts exceeded'}
            )
            return False
        
        # Attempt restart
        self.logger.info(f"Restarting {config.name}...")
        
        # Wait before restart
        time.sleep(config.restart_delay)
        
        # Start process
        if self.start_watcher(watcher_id):
            self._record_restart(watcher_id)
            return True
        
        return False
    
    def _can_restart(self, watcher_id: str) -> bool:
        """
        Check if a watcher can be restarted (within rate limits).
        
        Args:
            watcher_id: Watcher identifier
            
        Returns:
            True if restart is allowed
        """
        config = self.watchers[watcher_id]
        now = datetime.now()
        
        # Get restart count for this hour
        last_restart = self.last_restart_time.get(watcher_id)
        
        if last_restart and (now - last_restart).total_seconds() < 3600:
            # Within the same hour
            count = self.restart_counts.get(watcher_id, 0)
            if count >= config.max_restarts_per_hour:
                return False
        
        return True
    
    def _record_restart(self, watcher_id: str):
        """
        Record a restart event.
        
        Args:
            watcher_id: Watcher identifier
        """
        now = datetime.now()
        last_restart = self.last_restart_time.get(watcher_id)
        
        if last_restart and (now - last_restart).total_seconds() < 3600:
            # Increment count
            self.restart_counts[watcher_id] = self.restart_counts.get(watcher_id, 0) + 1
        else:
            # Reset count for new hour
            self.restart_counts[watcher_id] = 1
        
        self.last_restart_time[watcher_id] = now
    
    def _save_pid(self, watcher_id: str, pid: int):
        """Save PID to file."""
        pid_file = self.pid_dir / f"{watcher_id}.pid"
        pid_file.write_text(str(pid))
    
    def _remove_pid(self, watcher_id: str):
        """Remove PID file."""
        pid_file = self.pid_dir / f"{watcher_id}.pid"
        if pid_file.exists():
            pid_file.unlink()
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get watchdog status.
        
        Returns:
            Status dictionary
        """
        status = {
            'timestamp': datetime.now().isoformat(),
            'watchers': {}
        }
        
        for watcher_id, config in self.watchers.items():
            process = self.processes.get(watcher_id)
            is_running = process and process.poll() is None
            
            status['watchers'][watcher_id] = {
                'name': config.name,
                'running': is_running,
                'pid': process.pid if process else None,
                'restart_count': self.restart_counts.get(watcher_id, 0),
                'health': self.health_checker.get_status(f'watchdog_{watcher_id}')
            }
        
        return status
    
    def run(self):
        """Run the watchdog (main loop)."""
        self.logger.info("=" * 60)
        self.logger.info("WATCHDOG STARTED")
        self.logger.info("=" * 60)
        self.logger.info(f"Monitoring {len(self.watchers)} watchers:")
        
        for watcher_id, config in self.watchers.items():
            self.logger.info(f"  - {config.name}: {config.script} {' '.join(config.args)}")
        
        self.logger.info("=" * 60)
        
        # Start all watchers
        for watcher_id in self.watchers:
            self.start_watcher(watcher_id)
            time.sleep(2)  # Stagger starts
        
        # Main monitoring loop
        try:
            while True:
                for watcher_id, config in self.watchers.items():
                    # Check if watcher is running
                    if not self.check_watcher(watcher_id):
                        self.logger.error(
                            f"Failed to restart {config.name}, "
                            f"will retry in {config.check_interval}s"
                        )
                    
                    # Update health status
                    process = self.processes.get(watcher_id)
                    if process and process.poll() is None:
                        self.health_checker.report_status(
                            f'watchdog_{watcher_id}',
                            'healthy',
                            {'pid': process.pid}
                        )
                    else:
                        self.health_checker.report_status(
                            f'watchdog_{watcher_id}',
                            'unhealthy',
                            {'error': 'Process not running'}
                        )
                
                # Wait before next check
                time.sleep(config.check_interval)
                
        except KeyboardInterrupt:
            self.logger.info("Watchdog received shutdown signal")
            self.shutdown()
        except Exception as e:
            self.logger.error(f"Watchdog error: {e}")
            self.error_logger.log_error('watchdog', e)
            self.shutdown()
            raise
    
    def shutdown(self):
        """Shutdown watchdog and all watchers."""
        self.logger.info("Shutting down watchdog...")
        
        # Stop all watchers
        for watcher_id in list(self.processes.keys()):
            self.stop_watcher(watcher_id)
        
        self.logger.info("Watchdog stopped")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI Employee Watchdog')
    parser.add_argument(
        '--vault',
        required=True,
        help='Path to Obsidian vault'
    )
    parser.add_argument(
        '--watchers',
        nargs='+',
        choices=list(DEFAULT_WATCHERS.keys()),
        default=list(DEFAULT_WATCHERS.keys()),
        help='Watchers to monitor'
    )
    
    args = parser.parse_args()
    
    # Filter watchers
    watchers = {
        k: v for k, v in DEFAULT_WATCHERS.items()
        if k in args.watchers
    }
    
    # Create and run watchdog
    watchdog = Watchdog(args.vault, watchers)
    watchdog.run()


if __name__ == '__main__':
    main()
