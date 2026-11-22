"""Check original process, browser and capture records from the three retries and the 308 visitor."""
from pathlib import Path
from hashlib import file_digest
import json

def sha(f):
    with f.open('rb') as stream:
        return file_digest(stream,'sha256').hexdigest()

def verify(audit, order, names):
    assert order == 243
    root = Path(audit)
    if not (root/'field-attempts-243').is_dir():
        root = root.parent
    root = root/'field-attempts-243'
    index = json.loads((root/'index.json').read_bytes())
    assert index['order'] == order and len(index['attempts']) == 5
    for rel, info in index['files'].items():
        file = root/rel
        assert file.is_file() and file.stat().st_size == info['bytes'] and sha(file) == info['sha256'], rel
    normal = root.parent/'city-31243/sessions'
    for stage, code in [('closeups',1),('touch',0),('distant',1)]:
        d=root/(stage+'-01')
        report=json.loads((d/'main-browser.json').read_bytes())
        closed=json.loads((d/'closed.json').read_bytes())
        assert not report['completed'] and closed['exit']==code and closed['node_closed'] and closed['chromium_pids'] and not closed['remaining']
        assert closed['report_sha256']==sha(d/'main-browser.json') and closed['driver_sha256']==sha(root/'first-check-243.cjs')
        good=json.loads((normal/stage/'main-browser.json').read_bytes())
        result=json.loads((normal/stage/'closed.json').read_bytes())
        assert good['completed'] and good['screenshots'] and result['exit']==0 and result['report_sha256']==sha(normal/stage/'main-browser.json')
        assert all(sha(normal.parent/p['file'])==p['sha256'] for p in good['screenshots'])
    touch=json.loads((root/'touch-01/main-browser.json').read_bytes())
    assert touch['realBeacon']['pointer']['trusted'] and not touch['screenshots']
    assert 'No space left on device' in (root/'308-native-01/launch.log').read_text()
    visitor=json.loads((root/'308-viewer-01/process-exit.json').read_bytes())
    assert visitor['exit']==1 and not visitor['remaining'] and visitor['observed_processes']
    for filename in ['native-closed.json','viewer-closed.json']:
        result=json.loads((root/'308-return'/filename).read_bytes())
        assert result['passed'] and result['exit_code']==0 and not result['remaining']
    return True
