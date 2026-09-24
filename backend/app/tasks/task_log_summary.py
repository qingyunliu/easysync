"""Build a structured, UI-friendly summary from task logs."""
from datetime import datetime
from typing import Any, Dict, Iterable, Optional
import re

_PROGRESS_PATTERN = re.compile(r"(?:同步进度|progress)\s*[:：]?\s*(\d+(?:\.\d+)?)%", re.I)


def _is_progress(log: Any) -> bool:
    status = str(getattr(log, 'status', '') or '').lower()
    details = getattr(log, 'details', None) or {}
    phase = str(details.get('phase', '') or '').lower()
    message = str(getattr(log, 'message', '') or '')
    return status == 'progress' or phase == 'sync_progress' or bool(_PROGRESS_PATTERN.search(message))


def _phase(task: Any, latest_log: Optional[Any]) -> str:
    status = str(getattr(task, 'status', '') or '').lower()
    if status == 'failed':
        return 'task_failed'
    if status == 'completed':
        return 'task_completed'
    if status in {'pending', 'assigned'}:
        return 'initializing'
    if not latest_log:
        return 'sync_progress' if status == 'running' else status or 'initializing'

    details = getattr(latest_log, 'details', None) or {}
    explicit = details.get('phase') or details.get('current_step')
    if explicit:
        return str(explicit)
    return 'sync_progress' if _is_progress(latest_log) else status or 'initializing'


def build_execution_summary(task: Any, logs: Iterable[Any], now: Optional[datetime] = None) -> Dict[str, Any]:
    """Return task status, latest structured progress, and log counts."""
    logs = list(logs)
    now = now or datetime.utcnow()
    progress_logs = [log for log in logs if _is_progress(log)]
    error_logs = [log for log in logs if str(getattr(log, 'status', '')).lower() in {'error', 'failed'}]
    step_logs = [log for log in logs if str(getattr(log, 'status', '')).startswith('step_')]
    latest_log = max(logs, key=lambda log: getattr(log, 'created_at', datetime.min), default=None)
    latest_progress_log = max(progress_logs, key=lambda log: getattr(log, 'created_at', datetime.min), default=None)

    progress_details = dict(getattr(latest_progress_log, 'details', None) or {})
    if 'progress' not in progress_details and latest_progress_log:
        match = _PROGRESS_PATTERN.search(str(getattr(latest_progress_log, 'message', '') or ''))
        if match:
            progress_details['progress'] = float(match.group(1))
    progress_details.setdefault('progress', getattr(task, 'progress', 0) or 0)

    status_counts: Dict[str, int] = {}
    for log in logs:
        status = str(getattr(log, 'status', '') or 'unknown')
        status_counts[status] = status_counts.get(status, 0) + 1

    started_at = getattr(task, 'started_at', None)
    completed_at = getattr(task, 'completed_at', None)
    execution_time = None
    if started_at:
        execution_time = max(0, ((completed_at or now) - started_at).total_seconds())

    return {
        'task_id': task.id,
        'task_name': task.name,
        'task_type': task.type,
        'status': task.status,
        'progress': progress_details['progress'],
        'current_phase': _phase(task, latest_log),
        'latest_progress': progress_details,
        'error': getattr(task, 'error', None),
        'execution_time': execution_time,
        'created_at': task.created_at.isoformat(),
        'started_at': started_at.isoformat() if started_at else None,
        'completed_at': completed_at.isoformat() if completed_at else None,
        'log_summary': {
            'total_logs': len(logs),
            'status_counts': status_counts,
            'error_count': len(error_logs),
            'progress_count': len(progress_logs),
            'step_count': len(step_logs),
        },
        'latest_logs': [log.to_dict() for log in sorted(logs, key=lambda item: getattr(item, 'created_at', datetime.min))[-5:]],
    }
