"""
Ralph Wiggum Loop for AI Employee - Gold Tier

Keeps Claude Code working autonomously until tasks are complete.
Uses stop hook pattern to intercept Claude's exit and re-inject prompts.

Features:
- Autonomous multi-step task completion
- File-based completion detection
- Promise-based completion detection
- Max iterations safety limit
- Timeout per iteration
- Progress logging

Usage:
    python scripts/ralph_wiggum.py --vault AI_Employee_Vault --prompt "Process all emails"
"""

import subprocess
import sys
import time
import logging
import argparse
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any


# ============================================================================
# RALPH WIGGUM LOOP
# ============================================================================

class RalphWiggumLoop:
    """
    Ralph Wiggum Loop - Keeps Claude Code working until tasks are complete.
    
    Named after the Simpsons character who keeps repeating phrases.
    This pattern keeps Claude Code iterating until the task is done.
    """
    
    def __init__(
        self,
        vault_path: str,
        prompt: str,
        max_iterations: int = 10,
        timeout: int = 300,
        completion_promise: str = "TASK_COMPLETE",
        check_done_folder: bool = True,
        claude_command: Optional[str] = None
    ):
        """
        Initialize Ralph Wiggum Loop.

        Args:
            vault_path: Path to Obsidian vault
            prompt: Task prompt for Claude Code
            max_iterations: Maximum loop iterations (safety limit)
            timeout: Timeout per iteration in seconds
            completion_promise: Text that signals completion
            check_done_folder: Check /Done/ folder for completion
            claude_command: Claude Code command (default: auto-detect or use CLAUDE_CODE_PATH env var)
        """
        self.vault = Path(vault_path)
        self.prompt = prompt
        self.max_iterations = max_iterations
        self.timeout = timeout
        self.completion_promise = completion_promise
        self.check_done_folder = check_done_folder

        # Folders
        self.needs_action = self.vault / 'Needs_Action'
        self.done = self.vault / 'Done'

        # State
        self.iteration = 0
        self.start_time = datetime.now()

        # Progress tracking for loop protection
        self.progress_history = []
        self.stuck_threshold = 3  # Number of iterations with no progress before considering stuck

        # Exponential backoff settings
        self.min_delay = 2  # Minimum delay in seconds
        self.max_delay = 60  # Maximum delay in seconds
        self.backoff_multiplier = 1.5  # Multiplier for exponential backoff
        self.current_delay = self.min_delay

        # Setup logging
        self._setup_logging()

        # Find Claude Code
        self.claude_path = claude_command or self._find_claude_code()
    
    def _setup_logging(self):
        """Setup logging configuration."""
        log_file = self.vault / 'Logs' / 'ralph_wiggum.log'
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('RalphWiggum')
    
    def _find_claude_code(self) -> Optional[str]:
        """Find Claude Code executable."""
        import os

        # Check environment variable first
        env_path = os.getenv('CLAUDE_CODE_PATH')
        if env_path:
            if shutil.which(env_path):
                self.logger.info(f"Found Claude Code from CLAUDE_CODE_PATH: {env_path}")
                return env_path
            else:
                self.logger.warning(f"CLAUDE_CODE_PATH set but command not found: {env_path}")

        # Try common locations
        possible_paths = [
            'claude',
            'claude-code',
            'qwen',  # If using Qwen Code
            'qwen-code'
        ]

        for cmd in possible_paths:
            path = shutil.which(cmd)
            if path:
                self.logger.info(f"Found Claude Code at: {path}")
                return path

        self.logger.warning("Claude Code not found in PATH. Set CLAUDE_CODE_PATH environment variable.")
        return None
    
    def _count_files(self, folder: Path) -> int:
        """Count files in folder."""
        if not folder.exists():
            return 0
        return len(list(folder.glob('*.md')))
    
    def _is_task_complete(self, initial_needs_action_count: int) -> bool:
        """
        Check if task is complete.
        
        Args:
            initial_needs_action_count: Initial count in /Needs_Action/
            
        Returns:
            True if task is complete
        """
        if self.check_done_folder:
            # Check if files moved from Needs_Action to Done
            current_needs_action = self._count_files(self.needs_action)
            current_done = self._count_files(self.done)
            
            self.logger.info(
                f"Task status: Needs_Action={current_needs_action}, Done={current_done}"
            )
            
            # Task is complete if Needs_Action is empty or Done increased
            if current_needs_action == 0 and initial_needs_action_count > 0:
                self.logger.info("✓ Task complete: /Needs_Action/ is empty")
                return True
        
        return False

    def _track_progress(self, needs_action_count: int, done_count: int) -> bool:
        """
        Track progress and detect if we're stuck.

        Args:
            needs_action_count: Current count in Needs_Action
            done_count: Current count in Done

        Returns:
            True if progress was made, False if stuck
        """
        current_state = {
            'iteration': self.iteration,
            'needs_action': needs_action_count,
            'done': done_count,
            'timestamp': datetime.now()
        }

        self.progress_history.append(current_state)

        # Check if we're stuck (no progress in last N iterations)
        if len(self.progress_history) >= self.stuck_threshold:
            recent_history = self.progress_history[-self.stuck_threshold:]

            # Check if needs_action and done counts haven't changed
            needs_action_values = [h['needs_action'] for h in recent_history]
            done_values = [h['done'] for h in recent_history]

            if len(set(needs_action_values)) == 1 and len(set(done_values)) == 1:
                self.logger.warning(
                    f"No progress detected in last {self.stuck_threshold} iterations. "
                    f"Needs_Action={needs_action_values[0]}, Done={done_values[0]}"
                )
                return False

        return True

    def _calculate_backoff_delay(self, progress_made: bool) -> float:
        """
        Calculate delay using exponential backoff.

        Args:
            progress_made: Whether progress was made in last iteration

        Returns:
            Delay in seconds
        """
        if progress_made:
            # Progress made - reduce delay (faster iterations)
            self.current_delay = max(self.min_delay, self.current_delay / self.backoff_multiplier)
            self.logger.info(f"Progress detected - reducing delay to {self.current_delay:.1f}s")
        else:
            # No progress - increase delay (slower iterations)
            self.current_delay = min(self.max_delay, self.current_delay * self.backoff_multiplier)
            self.logger.info(f"No progress - increasing delay to {self.current_delay:.1f}s")

        return self.current_delay

    def _run_claude_iteration(self, iteration: int) -> bool:
        """
        Run one iteration of Claude Code.
        
        Args:
            iteration: Current iteration number
            
        Returns:
            True if completion signal detected
        """
        self.logger.info(f"=" * 60)
        self.logger.info(f"RALPH WIGGUM LOOP - Iteration {iteration}/{self.max_iterations}")
        self.logger.info(f"=" * 60)
        
        # Build Claude Code command
        cmd = [
            self.claude_path,
            '--prompt', self.prompt,
            '--cwd', str(self.vault)
        ]
        
        self.logger.info(f"Running: {' '.join(cmd)}")
        
        try:
            # Run Claude Code
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            # Read output line by line
            completion_detected = False
            output_lines = []
            
            while True:
                try:
                    line = process.stdout.readline()
                    if not line and process.poll() is not None:
                        break
                    
                    if line:
                        line = line.strip()
                        output_lines.append(line)
                        self.logger.info(f"Claude: {line}")
                        
                        # Check for completion promise
                        if self.completion_promise in line:
                            self.logger.info(f"✓ Completion promise detected!")
                            completion_detected = True
                
                except KeyboardInterrupt:
                    self.logger.info("User interrupted (Ctrl+C)")
                    process.terminate()
                    return False
            
            # Wait for process to finish
            try:
                process.wait(timeout=self.timeout)
            except subprocess.TimeoutExpired:
                self.logger.warning(f"Iteration {iteration} timed out after {self.timeout}s")
                process.terminate()
                return False
            
            return completion_detected
            
        except Exception as e:
            self.logger.error(f"Iteration {iteration} failed: {e}")
            return False
    
    def run(self) -> Dict[str, Any]:
        """
        Run the Ralph Wiggum Loop.
        
        Returns:
            Result dictionary with statistics
        """
        self.logger.info("=" * 60)
        self.logger.info("RALPH WIGGUM LOOP - STARTING")
        self.logger.info("=" * 60)
        self.logger.info(f"Vault: {self.vault}")
        self.logger.info(f"Prompt: {self.prompt[:100]}...")
        self.logger.info(f"Max iterations: {self.max_iterations}")
        self.logger.info(f"Timeout per iteration: {self.timeout}s")
        self.logger.info("=" * 60)
        
        # Check initial state
        initial_needs_action = self._count_files(self.needs_action)
        initial_done = self._count_files(self.done)
        
        self.logger.info(f"Initial state: Needs_Action={initial_needs_action}, Done={initial_done}")
        
        # Check if Claude Code is available
        if not self.claude_path:
            self.logger.error("Claude Code not found. Please install it first.")
            return {
                'success': False,
                'error': 'Claude Code not found',
                'iterations': 0
            }
        
        # Run loop
        completion_detected = False
        stuck_detected = False

        for iteration in range(1, self.max_iterations + 1):
            self.iteration = iteration

            # Get current state before iteration
            pre_needs_action = self._count_files(self.needs_action)
            pre_done = self._count_files(self.done)

            # Run iteration
            completion_detected = self._run_claude_iteration(iteration)

            # Get current state after iteration
            post_needs_action = self._count_files(self.needs_action)
            post_done = self._count_files(self.done)

            # Track progress
            progress_made = (post_needs_action < pre_needs_action) or (post_done > pre_done)
            is_stuck = not self._track_progress(post_needs_action, post_done)

            # Check if we're stuck
            if is_stuck:
                self.logger.error("=" * 60)
                self.logger.error("STUCK DETECTED - No progress in multiple iterations")
                self.logger.error("=" * 60)
                stuck_detected = True
                break

            # Check if task is complete
            if self._is_task_complete(initial_needs_action):
                self.logger.info("=" * 60)
                self.logger.info("[OK] TASK COMPLETE!")
                self.logger.info("=" * 60)
                break

            # Check if Claude signaled completion
            if completion_detected:
                self.logger.info("=" * 60)
                self.logger.info("[OK] COMPLETION PROMISE DETECTED!")
                self.logger.info("=" * 60)
                break

            # Check if we should continue
            if iteration < self.max_iterations:
                # Calculate delay with exponential backoff
                delay = self._calculate_backoff_delay(progress_made)
                self.logger.info(f"Task not complete. Waiting {delay:.1f}s before iteration {iteration + 1}...")
                time.sleep(delay)
        
        # Calculate statistics
        final_needs_action = self._count_files(self.needs_action)
        final_done = self._count_files(self.done)
        elapsed_time = (datetime.now() - self.start_time).total_seconds()
        
        # Determine success
        success = (
            completion_detected or
            (final_needs_action < initial_needs_action) or
            (final_done > initial_done)
        ) and not stuck_detected

        result = {
            'success': success,
            'iterations': self.iteration,
            'elapsed_time': elapsed_time,
            'initial_needs_action': initial_needs_action,
            'final_needs_action': final_needs_action,
            'initial_done': initial_done,
            'final_done': final_done,
            'tasks_completed': final_done - initial_done,
            'completion_detected': completion_detected,
            'stuck_detected': stuck_detected,
            'progress_history': self.progress_history
        }

        # Log final statistics
        self.logger.info("=" * 60)
        self.logger.info("RALPH WIGGUM LOOP - FINAL STATISTICS")
        self.logger.info("=" * 60)
        self.logger.info(f"Success: {success}")
        self.logger.info(f"Iterations: {self.iteration}/{self.max_iterations}")
        self.logger.info(f"Elapsed time: {elapsed_time:.1f}s")
        self.logger.info(f"Tasks completed: {result['tasks_completed']}")
        self.logger.info(f"Completion promise: {completion_detected}")
        self.logger.info("=" * 60)
        
        return result


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run Ralph Wiggum Loop."""
    parser = argparse.ArgumentParser(description='Ralph Wiggum Loop for AI Employee')
    parser.add_argument('--vault', required=True, help='Path to Obsidian vault')
    parser.add_argument('--prompt', required=True, help='Task prompt for Claude Code')
    parser.add_argument('--max-iterations', type=int, default=10, help='Maximum loop iterations')
    parser.add_argument('--timeout', type=int, default=300, help='Timeout per iteration (seconds)')
    parser.add_argument('--completion-promise', default='TASK_COMPLETE', help='Completion signal text')
    parser.add_argument('--no-check-done', action='store_true', help='Disable /Done/ folder checking')
    parser.add_argument('--claude-command', help='Claude Code command (default: auto-detect or use CLAUDE_CODE_PATH env var)')

    args = parser.parse_args()

    # Create and run loop
    loop = RalphWiggumLoop(
        vault_path=args.vault,
        prompt=args.prompt,
        max_iterations=args.max_iterations,
        timeout=args.timeout,
        completion_promise=args.completion_promise,
        check_done_folder=not args.no_check_done,
        claude_command=args.claude_command
    )

    result = loop.run()

    # Exit with appropriate code
    sys.exit(0 if result['success'] else 1)


if __name__ == '__main__':
    main()
