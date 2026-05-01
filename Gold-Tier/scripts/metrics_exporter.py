"""
Prometheus Metrics Exporter for AI Employee

Exposes metrics in Prometheus format for monitoring dashboards.

Metrics exposed:
- Service health status
- Error rates and counts
- Processing times
- Queue sizes (pending approvals, needs action)
- Task completion rates
- Approval workflow metrics
- System resource usage

Usage:
    # Start metrics server
    python scripts/metrics_exporter.py --vault AI_Employee_Vault --port 9090

    # Or use programmatically
    from metrics_exporter import MetricsCollector, start_metrics_server

    collector = MetricsCollector(vault_path)
    collector.record_task_completed(duration_seconds=1.5)
    collector.record_error(service="orchestrator", error_type="timeout")

    # Start HTTP server for Prometheus scraping
    start_metrics_server(port=9090, vault_path=vault_path)
"""

import time
import psutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread


class PrometheusMetrics:
    """Prometheus metrics registry."""

    def __init__(self):
        self.counters = {}
        self.gauges = {}
        self.histograms = {}

    def counter(self, name: str, help_text: str, labels: Optional[Dict[str, str]] = None) -> float:
        """Get or create a counter metric."""
        key = self._make_key(name, labels)
        if key not in self.counters:
            self.counters[key] = {
                'name': name,
                'help': help_text,
                'type': 'counter',
                'value': 0,
                'labels': labels or {}
            }
        return self.counters[key]['value']

    def inc_counter(self, name: str, labels: Optional[Dict[str, str]] = None, value: float = 1):
        """Increment a counter."""
        key = self._make_key(name, labels)
        if key not in self.counters:
            self.counter(name, '', labels)
        self.counters[key]['value'] += value

    def gauge(self, name: str, help_text: str, labels: Optional[Dict[str, str]] = None) -> float:
        """Get or create a gauge metric."""
        key = self._make_key(name, labels)
        if key not in self.gauges:
            self.gauges[key] = {
                'name': name,
                'help': help_text,
                'type': 'gauge',
                'value': 0,
                'labels': labels or {}
            }
        return self.gauges[key]['value']

    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Set a gauge value."""
        key = self._make_key(name, labels)
        if key not in self.gauges:
            self.gauge(name, '', labels)
        self.gauges[key]['value'] = value

    def histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Record a histogram observation."""
        key = self._make_key(name, labels)
        if key not in self.histograms:
            self.histograms[key] = {
                'name': name,
                'type': 'histogram',
                'observations': [],
                'labels': labels or {}
            }
        self.histograms[key]['observations'].append(value)

    def _make_key(self, name: str, labels: Optional[Dict[str, str]]) -> str:
        """Create unique key for metric with labels."""
        if not labels:
            return name
        label_str = ','.join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def export(self) -> str:
        """Export metrics in Prometheus format."""
        lines = []

        # Export counters
        for key, metric in self.counters.items():
            if not lines or lines[-1].startswith('#'):
                lines.append(f"# HELP {metric['name']} {metric.get('help', '')}")
                lines.append(f"# TYPE {metric['name']} counter")

            label_str = self._format_labels(metric['labels'])
            lines.append(f"{metric['name']}{label_str} {metric['value']}")

        # Export gauges
        for key, metric in self.gauges.items():
            if not any(line.startswith(f"# HELP {metric['name']}") for line in lines):
                lines.append(f"# HELP {metric['name']} {metric.get('help', '')}")
                lines.append(f"# TYPE {metric['name']} gauge")

            label_str = self._format_labels(metric['labels'])
            lines.append(f"{metric['name']}{label_str} {metric['value']}")

        # Export histograms (simplified - just count, sum, and buckets)
        for key, metric in self.histograms.items():
            if not any(line.startswith(f"# HELP {metric['name']}") for line in lines):
                lines.append(f"# HELP {metric['name']} Histogram")
                lines.append(f"# TYPE {metric['name']} histogram")

            observations = metric['observations']
            label_str = self._format_labels(metric['labels'])

            # Buckets
            buckets = [0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
            for bucket in buckets:
                count = sum(1 for obs in observations if obs <= bucket)
                lines.append(f"{metric['name']}_bucket{{le=\"{bucket}\"{label_str[1:] if label_str else ''} {count}")

            # +Inf bucket
            lines.append(f"{metric['name']}_bucket{{le=\"+Inf\"{label_str[1:] if label_str else ''} {len(observations)}")

            # Sum and count
            lines.append(f"{metric['name']}_sum{label_str} {sum(observations)}")
            lines.append(f"{metric['name']}_count{label_str} {len(observations)}")

        return '\n'.join(lines) + '\n'

    def _format_labels(self, labels: Dict[str, str]) -> str:
        """Format labels for Prometheus output."""
        if not labels:
            return ''
        label_str = ','.join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{{{label_str}}}"


class MetricsCollector:
    """Collects metrics for AI Employee services."""

    def __init__(self, vault_path: str):
        self.vault = Path(vault_path)
        self.metrics = PrometheusMetrics()

        # Initialize standard metrics
        self._init_metrics()

    def _init_metrics(self):
        """Initialize standard metrics."""
        # Service health
        self.metrics.gauge('ai_employee_service_up', 'Service health status (1=up, 0=down)')

        # Error metrics
        self.metrics.counter('ai_employee_errors_total', 'Total number of errors')

        # Task metrics
        self.metrics.counter('ai_employee_tasks_completed_total', 'Total tasks completed')
        self.metrics.counter('ai_employee_tasks_failed_total', 'Total tasks failed')

        # Approval metrics
        self.metrics.counter('ai_employee_approvals_requested_total', 'Total approval requests')
        self.metrics.counter('ai_employee_approvals_granted_total', 'Total approvals granted')
        self.metrics.counter('ai_employee_approvals_rejected_total', 'Total approvals rejected')
        self.metrics.gauge('ai_employee_approvals_pending', 'Number of pending approvals')

        # Queue metrics
        self.metrics.gauge('ai_employee_queue_size', 'Queue size')

        # Processing time
        self.metrics.gauge('ai_employee_processing_time_seconds', 'Processing time in seconds')

    def update_service_health(self, service: str, is_up: bool):
        """Update service health status."""
        self.metrics.set_gauge(
            'ai_employee_service_up',
            1.0 if is_up else 0.0,
            labels={'service': service}
        )

    def record_error(self, service: str, error_type: str):
        """Record an error."""
        self.metrics.inc_counter(
            'ai_employee_errors_total',
            labels={'service': service, 'type': error_type}
        )

    def record_task_completed(self, task_type: str, duration_seconds: float):
        """Record a completed task."""
        self.metrics.inc_counter(
            'ai_employee_tasks_completed_total',
            labels={'type': task_type}
        )
        self.metrics.histogram(
            'ai_employee_task_duration_seconds',
            duration_seconds,
            labels={'type': task_type}
        )

    def record_task_failed(self, task_type: str):
        """Record a failed task."""
        self.metrics.inc_counter(
            'ai_employee_tasks_failed_total',
            labels={'type': task_type}
        )

    def record_approval_requested(self, action_type: str):
        """Record an approval request."""
        self.metrics.inc_counter(
            'ai_employee_approvals_requested_total',
            labels={'action': action_type}
        )

    def record_approval_granted(self, action_type: str):
        """Record an approval granted."""
        self.metrics.inc_counter(
            'ai_employee_approvals_granted_total',
            labels={'action': action_type}
        )

    def record_approval_rejected(self, action_type: str):
        """Record an approval rejected."""
        self.metrics.inc_counter(
            'ai_employee_approvals_rejected_total',
            labels={'action': action_type}
        )

    def update_queue_size(self, queue_name: str, size: int):
        """Update queue size."""
        self.metrics.set_gauge(
            'ai_employee_queue_size',
            float(size),
            labels={'queue': queue_name}
        )

    def update_processing_time(self, service: str, seconds: float):
        """Update processing time."""
        self.metrics.set_gauge(
            'ai_employee_processing_time_seconds',
            seconds,
            labels={'service': service}
        )

    def collect_system_metrics(self):
        """Collect system resource metrics."""
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        self.metrics.set_gauge('ai_employee_cpu_usage_percent', cpu_percent)

        # Memory usage
        memory = psutil.virtual_memory()
        self.metrics.set_gauge('ai_employee_memory_usage_percent', memory.percent)
        self.metrics.set_gauge('ai_employee_memory_used_bytes', float(memory.used))

        # Disk usage
        disk = psutil.disk_usage(str(self.vault))
        self.metrics.set_gauge('ai_employee_disk_usage_percent', disk.percent)
        self.metrics.set_gauge('ai_employee_disk_used_bytes', float(disk.used))

    def collect_vault_metrics(self):
        """Collect vault-specific metrics."""
        # Count pending approvals
        pending_approval = self.vault / 'Pending_Approval'
        if pending_approval.exists():
            pending_count = len(list(pending_approval.glob('*.md')))
            self.update_queue_size('pending_approval', pending_count)

        # Count needs action
        needs_action = self.vault / 'Needs_Action'
        if needs_action.exists():
            needs_action_count = len(list(needs_action.glob('*.md')))
            self.update_queue_size('needs_action', needs_action_count)

        # Count approved
        approved = self.vault / 'Approved'
        if approved.exists():
            approved_count = len(list(approved.glob('*.md')))
            self.update_queue_size('approved', approved_count)

    def export_metrics(self) -> str:
        """Export all metrics in Prometheus format."""
        # Update system and vault metrics
        self.collect_system_metrics()
        self.collect_vault_metrics()

        return self.metrics.export()


class MetricsHandler(BaseHTTPRequestHandler):
    """HTTP handler for Prometheus metrics endpoint."""

    collector = None

    def do_GET(self):
        """Handle GET request."""
        if self.path == '/metrics':
            try:
                metrics_output = self.collector.export_metrics()
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain; version=0.0.4')
                self.end_headers()
                self.wfile.write(metrics_output.encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(f"Error: {e}".encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


def start_metrics_server(port: int, vault_path: str, daemon: bool = True):
    """
    Start Prometheus metrics HTTP server.

    Args:
        port: Port to listen on
        vault_path: Path to vault
        daemon: Run as daemon thread

    Returns:
        Thread object
    """
    collector = MetricsCollector(vault_path)
    MetricsHandler.collector = collector

    server = HTTPServer(('0.0.0.0', port), MetricsHandler)

    def serve():
        print(f"[OK] Metrics server started on port {port}")
        print(f"[OK] Prometheus endpoint: http://localhost:{port}/metrics")
        server.serve_forever()

    thread = Thread(target=serve, daemon=daemon)
    thread.start()

    return thread


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Prometheus Metrics Exporter')
    parser.add_argument('--vault', default='AI_Employee_Vault', help='Path to vault')
    parser.add_argument('--port', type=int, default=9090, help='Port to listen on')

    args = parser.parse_args()

    # Start server (non-daemon for standalone mode)
    thread = start_metrics_server(args.port, args.vault, daemon=False)
    thread.join()


if __name__ == '__main__':
    main()
