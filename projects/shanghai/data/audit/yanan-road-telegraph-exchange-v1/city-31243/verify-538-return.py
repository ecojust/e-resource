"""Verify the real 538 handback after the signed 243 viewer and 409 guest."""
from pathlib import Path
import hashlib
import json
import runpy

def digest(path):
    with Path(path).open('rb') as data:
        return hashlib.file_digest(data, 'sha256').hexdigest()

def verify():
    work = Path('/tmp/fair-building538')
    host = Path('/tmp/shanghai-main-243/viewer-31243/closed.json')
    report = host.with_name('viewer.json')
    predecessor = Path('/tmp/linong409/development-native/243-development-returned.json')
    returned = work / '243-native-returned.json'
    prior = json.loads(predecessor.read_bytes())
    result = json.loads(returned.read_bytes())
    assert prior['order'] == 409 and prior['host'] == 243
    assert prior['all_children_exited'] and not prior['remaining_children']
    assert (prior['host_receipt_sha256'], prior['host_report_sha256']) == (digest(host), digest(report))
    assert (result['order'], result['host'], result['phase']) == (538, 243, 'independent')
    assert (result['previous_sha256'], result['host_sha256'], result['host_report_sha256']) == (digest(predecessor), digest(host), digest(report))
    assert result['all_children_exited'] and result['remaining_children'] == []
    if result.get('already_completed'):
        check = Path('/workspace/.e-resource-recovery/grace/verified-native-prior.py')
        assert digest(check) == 'bc59e775b80a6a5d4328347304126f7ac5be1a5645a3b2c9abb5b7ec5058abe4'
        path, earlier = runpy.run_path(str(check))['inspect'](work, 538)
        assert str(path) == result['earlier'] and digest(path) == result['earlier_sha256']
        assert result['passed'] and result['exit_code'] is None and result['previous_completed_exit'] == 0
        assert result['four_assets'] == earlier['four_assets'] and result['phases'] == earlier['phases']
    else:
        phases = result['phases']
        assert phases and all(phase['pid'] > 1 and isinstance(phase['exit_code'], int) for phase in phases)
        assert result['exit_code'] == phases[-1]['exit_code']
        assert result['passed'] == (len(phases) == 2 and all(phase['exit_code'] == 0 for phase in phases))
        for phase in phases:
            if phase['physical']:
                assert digest(phase['physical']) == phase['physical_sha256']
            else:
                assert phase['exit_code'] != 0
    return digest(returned)

if __name__ == '__main__':
    print(verify())
