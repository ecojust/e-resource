"""Verify the two measured views from the live Qiuxin map and every preceding attempt."""
from pathlib import Path
from hashlib import file_digest
import json
import re
from PIL import Image, ImageChops

def verify(audit, order, names):
    assert order == 261
    target = Path(audit) / 'final-map-31261/supplement-architecture'
    index = target / 'independent-session-index.json'
    def digest(path):
        with path.open('rb') as stream:
            return file_digest(stream, 'sha256').hexdigest()
    assert digest(index) == 'dfdb9b5bf87c14b3f0989246302a5483abfc4374bb1f0cda71aa884e0077d198'
    record = json.loads(index.read_bytes())
    assert record['order'] == order
    verified = set()
    photos = {}
    seen_failure = []
    for attempt in record['sessions']:
        folder = target / attempt['directory']
        for name, entry in attempt['files'].items():
            source = folder / name
            assert source.stat().st_size == entry['bytes']
            assert digest(source) == entry['sha256']
            verified.add(source.relative_to(Path(audit)).as_posix())
        report = folder / 'main-browser.json'
        driver = folder / 'actual-driver.cjs'
        closure = folder / 'closed.json'
        if closure.exists():
            close = json.loads(closure.read_bytes())
            assert close['host'] == order and close['phase'] == 'two-veranda-details'
            assert close['remaining_children'] == close['remaining_chromium'] == []
            assert close['driver_sha256'] == digest(driver)
            assert close['predecessor_sha256'] == record['preceding_437_receipt']
            assert close['passed'] == attempt['completed']
            assert close['exit_code'] == attempt['observer_exit']
            assert close['report_sha256'] == (digest(report) if report.exists() else None)
        else:
            assert attempt['directory'].startswith('attempt-02-')
            assert 'JSONDecodeError' in (folder/'observer-stderr.log').read_text()
        if not attempt['completed']:
            seen_failure.append(attempt['directory'])
        assert int((folder/'exit-code').read_text()) == attempt['node_exit']
        if not report.exists():
            assert attempt['directory'].startswith('attempt-01-')
            assert 'ENOENT: no such file or directory, lstat' in (folder/'run.log').read_text()
            continue
        if attempt['invalid_json']:
            try: json.loads(report.read_bytes())
            except (json.JSONDecodeError, UnicodeError): continue
            raise AssertionError('Expected the original malformed report')
        r = json.loads(report.read_bytes())
        assert r['id'] == 'huangpu-qiuxin-shipyard-office-south-veranda'
        assert r['scriptSha256'] == digest(driver)
        assert r['server'] == 'http://127.0.0.1:31261/'
        assert r['completed'] is attempt['completed']
        if attempt['completed']:
            assert close['node_pids'] and close['chromium_pids'] and close['exit_code'] == 0
            assert len(r['ground']) == 54 and all(v['found'] == v['expected'] for v in r['ground'])
        captures=[r.get(k,[]) for k in ('screenshots','webglCaptures','displayCaptures','detailSurvey')]
        assert len({len(values) for values in captures}) == 1
        for shot, web, display, detail in zip(*captures):
            f = folder/shot['file']
            assert digest(f) == shot['sha256'] and f.stat().st_size == shot['bytes']
            assert digest(folder/web['file']) == web['sha256']
            assert digest(folder/display['displayImage']) == display['displayImageSha256']
            w,h,x,y = map(int,re.fullmatch(r'(\d+)x(\d+)\+(\d+)\+(\d+)',display['rectangle']).groups())
            with Image.open(f) as view, Image.open(folder/display['displayImage']) as screen, Image.open(folder/web['file']) as canvas:
                assert canvas.size == (web['width'],web['height']) and view.size == (w,h)
                assert ImageChops.difference(view.convert('RGB'),screen.crop((x,y,x+w,y+h)).convert('RGB')).getbbox() is None
            selected = detail['selected']
            assert selected['clear'] == sum(s['clear'] for s in selected['trace'])
            assert len(detail['samples']) == len(selected['trace']) == 6
            photos[detail['kind']] = [selected['clear'],selected['hit']]
    assert sorted(seen_failure)==sorted(record['failed_attempts'])
    assert photos == {'iron':[6,6],'glass':[3,3]}
    assert all(name in names for name in verified)
    return verified
