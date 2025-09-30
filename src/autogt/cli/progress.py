"""Progress display utilities for AutoGT CLI.

Reference: Performance requirements for long-running TARA analysis operations
Provides progress indicators, status updates, and completion estimates.
"""

import time
import threading
from typing import Optional, Callable, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

import click


@dataclass
class ProgressInfo:
    """Progress information for long-running operations."""
    current_step: int
    total_steps: int
    step_name: str
    start_time: datetime
    estimated_completion: Optional[datetime] = None
    status_message: str = ""
    

class ProgressDisplay:
    """Handles progress display for long-running CLI operations."""
    
    def __init__(self, total_steps: int, show_progress: bool = True):
        self.total_steps = total_steps
        self.current_step = 0
        self.show_progress = show_progress
        self.start_time = datetime.now()
        self.step_times = []
        self.current_message = ""
        self._stop_spinner = False
        self._spinner_thread = None
        
    def start_step(self, step_name: str, step_number: Optional[int] = None):
        """Start a new progress step."""
        if step_number is not None:
            self.current_step = step_number
        else:
            self.current_step += 1
            
        self.current_message = step_name
        step_start = datetime.now()
        self.step_times.append(step_start)
        
        if self.show_progress:
            percentage = (self.current_step / self.total_steps) * 100
            click.echo(f"[{self.current_step}/{self.total_steps}] {step_name}... ({percentage:.1f}%)")
            
    def update_status(self, message: str):
        """Update the current status message."""
        if self.show_progress:
            click.echo(f"  {message}")
    
    def complete_step(self, success: bool = True, message: Optional[str] = None):
        """Mark the current step as completed."""
        if self.show_progress:
            status = "✓" if success else "✗"
            final_message = message or ("completed" if success else "failed")
            click.echo(f"  {status} {final_message}")
    
    def start_spinner(self, message: str = "Processing..."):
        """Start a spinner for indeterminate progress."""
        if not self.show_progress:
            return
            
        self._stop_spinner = False
        self._spinner_thread = threading.Thread(
            target=self._spinner_worker, 
            args=(message,)
        )
        self._spinner_thread.start()
    
    def stop_spinner(self, final_message: Optional[str] = None):
        """Stop the spinner."""
        if self._spinner_thread:
            self._stop_spinner = True
            self._spinner_thread.join()
            self._spinner_thread = None
            
        if self.show_progress and final_message:
            click.echo(f"\r{final_message}")
    
    def _spinner_worker(self, message: str):
        """Worker thread for spinner animation."""
        spinner_chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        i = 0
        while not self._stop_spinner:
            if self.show_progress:
                char = spinner_chars[i % len(spinner_chars)]
                click.echo(f"\r{char} {message}", nl=False)
            time.sleep(0.1)
            i += 1
    
    def get_estimated_completion(self) -> Optional[datetime]:
        """Calculate estimated completion time."""
        if self.current_step == 0:
            return None
            
        elapsed = datetime.now() - self.start_time
        avg_step_time = elapsed.total_seconds() / self.current_step
        remaining_steps = self.total_steps - self.current_step
        
        return datetime.now() + timedelta(seconds=avg_step_time * remaining_steps)
    
    def show_summary(self):
        """Show completion summary."""
        if not self.show_progress:
            return
            
        elapsed = datetime.now() - self.start_time
        click.echo(f"\n✓ Analysis completed in {elapsed.total_seconds():.1f} seconds")
        click.echo(f"Total steps: {self.total_steps}")


class TaraProgressTracker:
    """Specialized progress tracker for TARA analysis workflow."""
    
    TARA_STEPS = [
        "Asset Identification",
        "Threat Scenario Identification", 
        "Attack Path Analysis",
        "Attack Feasibility Rating",
        "Impact Rating", 
        "Risk Value Determination",
        "Risk Treatment Decision",
        "Cybersecurity Goals"
    ]
    
    def __init__(self, show_progress: bool = True):
        self.progress = ProgressDisplay(len(self.TARA_STEPS), show_progress)
        self.step_results = {}
    
    def start_tara_step(self, step_number: int, custom_message: Optional[str] = None):
        """Start a specific TARA step (1-8)."""
        if not (1 <= step_number <= 8):
            raise ValueError(f"TARA step must be 1-8, got {step_number}")
        
        step_name = custom_message or self.TARA_STEPS[step_number - 1]
        self.progress.start_step(step_name, step_number)
    
    def update_tara_progress(self, message: str):
        """Update progress within current TARA step."""
        self.progress.update_status(message)
    
    def complete_tara_step(self, step_number: int, success: bool = True, 
                          result_count: Optional[int] = None):
        """Complete a TARA step with optional result metrics."""
        if result_count is not None:
            message = f"completed ({result_count} items processed)"
        else:
            message = "completed"
            
        self.step_results[step_number] = {
            'success': success,
            'result_count': result_count,
            'completed_at': datetime.now()
        }
        
        self.progress.complete_step(success, message)
    
    def show_tara_summary(self):
        """Show TARA analysis completion summary."""
        self.progress.show_summary()
        
        # Show step-by-step results
        click.echo("\nTARA Step Results:")
        for i, step_name in enumerate(self.TARA_STEPS, 1):
            if i in self.step_results:
                result = self.step_results[i]
                status = "✓" if result['success'] else "✗"
                count = f" ({result['result_count']} items)" if result['result_count'] else ""
                click.echo(f"  {status} Step {i}: {step_name}{count}")
            else:
                click.echo(f"  ○ Step {i}: {step_name} (not completed)")


def with_progress(show_progress: bool = True):
    """Decorator to add progress tracking to CLI commands."""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # Add progress parameter to context
            ctx = None
            for arg in args:
                if isinstance(arg, click.Context):
                    ctx = arg
                    break
            
            if ctx:
                ctx.obj = ctx.obj or {}
                ctx.obj['show_progress'] = show_progress and not ctx.obj.get('quiet', False)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def create_progress_tracker(operation_type: str = 'generic', show_progress: bool = True):
    """Factory function to create appropriate progress tracker."""
    if operation_type == 'tara':
        return TaraProgressTracker(show_progress)
    else:
        return ProgressDisplay(8, show_progress)  # Default to 8 steps


# Convenience functions for common progress patterns
def show_analysis_progress(analysis_id: str, current_step: int, total_steps: int = 8):
    """Show quick progress for analysis operations."""
    percentage = (current_step / total_steps) * 100
    step_name = TaraProgressTracker.TARA_STEPS[current_step - 1] if current_step <= 8 else "Processing"
    click.echo(f"Analysis {analysis_id[:8]}: [{current_step}/{total_steps}] {step_name} ({percentage:.1f}%)")


def show_operation_status(operation: str, status: str, details: Optional[str] = None):
    """Show status for generic operations."""
    status_icons = {
        'started': '▶',
        'running': '⚡', 
        'completed': '✓',
        'failed': '✗',
        'warning': '⚠'
    }
    
    icon = status_icons.get(status, '•')
    message = f"{icon} {operation}: {status}"
    
    if details:
        message += f" ({details})"
    
    click.echo(message)