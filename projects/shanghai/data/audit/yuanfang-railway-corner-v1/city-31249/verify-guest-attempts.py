from hashlib import sha256
from pathlib import Path
import json


def verify(audit, order, names):
    assert order == 249
    root = Path(audit) / 'city-31249'
    failed = root / 'guest-attempts/421-first-reopen'
    later = root / 'guest-returns'
    read = lambda p: json.loads(p.read_bytes())
    digest = lambda p: sha256(p.read_bytes()).hexdigest()

    old = read(failed / '249-development-returned.json')
    actual = read(failed / 'physical.json')
    close = read(failed / 'closed.json')
    newer = read(later / '421-249-development-returned.json')
    assert digest(later / '421-249-development-returned.json') == '01d84b6d23a43793f6dcb2678663caff44bf431961c61925d78898985a361ec4'
    for item, success in [(old, False), (newer, True)]:
        assert item['order'] == 421 and item['host'] == 249
        assert item['passed'] is success and item['exit_code'] == (0 if success else 1)
        assert item['host_receipt_sha256'] == digest(root / 'standalone/closed.json')
        assert item['host_report_sha256'] == digest(root / 'standalone/viewer.json')
        assert item['all_children_exited'] and not item['remaining_children']
    assert digest(failed / 'physical.json') == old['physical_sha256']
    assert not actual['passed'] and actual['exit_code'] == 1 and not actual['remaining_children']
    assert not close['passed'] and close['all_children_exited']
    assert [(z['name'],z['exit']) for z in close['events']] == [('render',0),('reopen',1)]
    for event in close['events']:
        assert event['pid'] > 0 and digest(failed / Path(event['log']).name) == event['log_sha256']
    for event in actual['events']:
        assert digest(failed / (event['name']+'.log')) == event['log_sha256']
    assert "Yaxiya Li four-window dormer" in (failed / 'reopen.log').read_text()
    assert "AssertionError" in (failed / 'reopen.log').read_text()
    assert digest(later / '421-physical.json') == newer['physical_sha256']
    corrected = read(later / '421-verified-editable.json')
    assert corrected['match_raw'] and corrected['street_view']['camera'] == 'Yaxiya Li street dormer'
    assert corrected['street_view']['mesh_count'] == 21 and corrected['street_view']['all_group_bounds_in_frame']

    earlier = root / 'guest-attempts/674-native-after-248'
    miss = read(earlier / 'return.json')
    assert miss['host'] == 248 and miss['order'] == 674 and miss['exit_code'] == 1 and not miss['passed']
    assert miss['all_children_exited'] and not miss['remaining_children']
    assert len(miss['phases']) == 1 and miss['phases'][0]['exit_code'] == 1
    assert digest(earlier/'physical.json') == miss['phases'][0]['physical_sha256']
    assert digest(earlier/'run.log') == miss['phases'][0]['log_sha256']
    for n in (674,678):
        result = read(later / f'{n}-returned.json')
        assert result['order'] == n and result['host'] == 249 and result['passed']
        assert not result['remaining_children'] and result['exit_code'] == 0 and result['all_children_exited']
        assert len(result['phases']) == 2 and all(r['exit_code']==0 for r in result['phases'])
    assert read(later/'678-returned.json')['previous_sha256'] == digest(later/'674-returned.json')
    return {failed/'249-development-returned.json',failed/'physical.json',failed/'closed.json',earlier/'return.json',earlier/'physical.json'}
