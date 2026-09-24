from types import SimpleNamespace
from datetime import datetime, timedelta

from backend.app.tasks.task_log_summary import build_execution_summary


def test_summary_uses_structured_progress_details():
    started = datetime(2026, 9, 24, 8, 0, 0)
    task = SimpleNamespace(
        id='task-1', name='sync', type='sync', status='running', progress=40,
        error=None, created_at=started, started_at=started, completed_at=None,
    )
    logs = [SimpleNamespace(
        status='progress', message='Progress: 42%',
        details={'phase': 'sync_progress', 'progress': 42.6, 'transferred_files': 12, 'total_files': 30},
        created_at=started + timedelta(minutes=1),
        to_dict=lambda: {'status': 'progress'}
    )]

    summary = build_execution_summary(task, logs, now=started + timedelta(minutes=10))

    assert summary['current_phase'] == 'sync_progress'
    assert summary['latest_progress']['progress'] == 42.6
    assert summary['latest_progress']['transferred_files'] == 12
    assert summary['execution_time'] == 600


def test_summary_recognizes_progress_by_status_not_message_language():
    started = datetime(2026, 9, 24, 8, 0, 0)
    task = SimpleNamespace(
        id='task-2', name='sync', type='sync', status='running', progress=5,
        error=None, created_at=started, started_at=started, completed_at=None,
    )
    logs = [SimpleNamespace(
        status='progress', message='Transferred files', details={'progress': 5},
        created_at=started, to_dict=lambda: {'status': 'progress'}
    )]

    summary = build_execution_summary(task, logs, now=started)

    assert summary['log_summary']['progress_count'] == 1
    assert summary['latest_progress']['progress'] == 5
