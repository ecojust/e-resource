"""Verify what happened in either of 324's borrowed city windows."""
from pathlib import Path
from hashlib import file_digest
import json

import psutil


def digest(path):
    with Path(path).open('rb') as handle:
        return file_digest(handle, 'sha256').hexdigest()


def load(path):
    return json.loads(Path(path).read_bytes())


def require_closed(pid, birth):
    assert isinstance(pid, int) and pid > 0 and birth > 0
    try:
        current = psutil.Process(pid)
        assert current.create_time() != birth or current.status() in (psutil.STATUS_ZOMBIE, psutil.STATUS_DEAD), pid
    except psutil.NoSuchProcess:
        pass


def verify(kind, host_path, result_path):
    host, result = load(host_path), load(result_path)
    assert host['order'] == 259 and host['phase'] == {'native': 'before', 'viewer': 'phone'}[kind]
    assert host['exit_code'] == 0 and host['node_closed'] and host['remaining_chromium'] == host['remaining'] == []
    assert host['report_sha256'] == digest(host['report'])
    assert result['order'] == 324
    assert host['report_sha256'] == result['host_report_sha256']
    source_sha = digest(host_path)
    if result.get('passed') is True:
        assert result['exit'] == 0 and result['host_receipt_sha256'] == source_sha
        if kind == 'native':
            assert result['remaining_blender'] == result['remaining_oidn'] == []
        else:
            assert result['remaining_chromium'] == []
        return 'complete'


    assert result['kind'] == kind and type(result['started']) is bool
    assert result['attempted'] == result['started'] and result['host_receipt_sha256'] == source_sha
    if not result['started']:
        assert result['host'] == 259 and result['deferred'] and result['missing']
        assert result.get('blender_started') is False and result.get('browser_started') is False and not result.get('chromium_started',False)
        assert Path(result['source']).resolve(strict=True) == Path(host_path).resolve(strict=True)
        assert result['source_sha256'] == source_sha
        assert not any(key in result for key in ('launch_log','launch_process','exit'))
        return 'deferred-before-launch'
    assert result['passed'] is False and result['exit'] != 0
    assert result['wrapper_closed'] is True and result['remaining'] == result['remaining_children'] == []
    for key in ('launch_process','launch_log'):
        assert digest(result[key]) == result[key+'_sha256']
    physical=load(result['launch_process'])
    assert all(physical[key] == result[key] for key in ('pid','exit','started','finished','remaining','wrapper_closed','observed_children','host_receipt_sha256','host_report_sha256') if key != 'started')
    assert physical['started'] and physical['finished'] and physical['wrapper_closed']
    for pid,birth in physical['observed_children'].items():
        require_closed(int(pid),birth)
    return 'deferred-after-physical-exit'
