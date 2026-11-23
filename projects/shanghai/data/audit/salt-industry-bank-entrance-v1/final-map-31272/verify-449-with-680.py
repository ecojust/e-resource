"""Wait for the actual 271 city and 449 development returns before starting the original 272 runner."""
from datetime import datetime, timezone
from hashlib import file_digest
import json, os, sys
from pathlib import Path

def digest(path):
    with path.open('rb') as stream:
        return file_digest(stream, 'sha256').hexdigest()

def read(path):
    return json.loads(path.read_bytes())

q = Path(__file__).parent
host = Path('/tmp/shanghai-main-271')
dev = Path('/tmp/jiangsu796-449/development-native')
city = host / '271-map-slot-released.json'
closed = host / 'viewer-31271/closed.json'
report = closed.with_name('viewer.json')
returned = dev / '271-development-returned.json'
runner = q / 'wait-271-with-680.py'
assert digest(runner) == '4641b3bd13e2d180608bcf5d531eeb9d34889998adccd054d2cce55d9a33eaaf'
assert digest(dev / 'after-271.py') == '3671f3d864ee2813f80c9dff8c56a6019335dddc2d6eb347ea6786b1d7bac340'
r = read(returned)
assert r['host'] == 271 and r['order'] == 449 and r['finished']
assert r['all_children_exited'] and r['remaining_children'] == []
assert r['host_sha256'] == digest(closed) and r['host_report_sha256'] == digest(report)
assert r['previous_sha256'] == digest(city) and read(city)['passed']
for source in r['sources'].values():
    assert digest(Path(source['file'])) == source['sha256']
if r['started']:
    physical = dev / 'physical.json'
    assert r['pid'] > 1 and Path(r['physical']).samefile(physical)
    assert digest(physical) == r['physical_sha256']
    result = read(physical)
    assert result['exit_code'] == r['exit_code'] and result['all_children_exited']
    assert result['remaining_children'] == [] and r['passed'] == (r['exit_code'] == 0)
    if r.get('reused_closed_session'):
        early = dev.parent / 'second-234-development'
        assert r['prior_physical_host'] == 234 and r['started_renderer'] is False
        assert (early / '234-development-returned.json').samefile(r['prior_return'])
        assert digest(early / '234-development-returned.json') == r['prior_return_sha256']
        assert digest(dev / 'recheck-234.py') == r['verification_program_sha256']
        assert physical.samefile(early / 'physical.json')
else:
    assert r['deferred'] and r['missing']
out = q / '449-development-verified-for-272.json'
record = dict(host=272, prior_city=271, guest=449, city_sha256=digest(city),
              return_sha256=digest(returned), started=r['started'], remaining_children=[],
              verified=datetime.now(timezone.utc).isoformat())
if out.exists():
    assert read(out)['return_sha256'] == digest(returned)
else:
    temp=out.with_suffix('.new')
    temp.write_text(json.dumps(record, indent=2)+'\n')
    temp.replace(out)
os.execv(sys.executable, [sys.executable, '-Bu', str(runner)])
