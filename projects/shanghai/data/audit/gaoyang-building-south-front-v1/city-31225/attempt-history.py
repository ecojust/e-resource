"""Authenticate and optionally publish the original evidence for incomplete map sessions."""
from pathlib import Path
from hashlib import sha256
import json, os, shutil

def digest(file):
    return sha256(file.read_bytes()).hexdigest()

def read(file):
    return json.loads(file.read_bytes())

def history(run, public=None):
    result = {}
    dedup = {}
    if public is not None:
        public.mkdir(exist_ok=True)
        for file in public.parent.iterdir():
            if file.is_file():
                dedup[digest(file)] = file
    def record(file, family, name):
        signature = digest(file)
        if public is None:
            return dict(path=str(file), sha256=signature)
        if signature not in dedup:
            dest = public / family / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            if not dest.exists():
                try: os.link(file, dest)
                except OSError: shutil.copyfile(file, dest)
            assert digest(dest) == signature
            dedup[signature] = dest
        return dict(path=os.path.relpath(dedup[signature], public), sha256=signature)
    for group in sorted((run/'segments').glob('failed-*')):
        index = group/'evidence.json'
        original = read(index)
        receipt = Path(original['failed_closed'])
        report = Path(original['retained_report'])
        closed = read(receipt)
        observation = read(report)
        driver = Path(original['checker'])
        assert receipt.parent.samefile(group) and report.parent.parent.samefile(group)
        assert original['closed_sha256'] == digest(receipt)
        assert original['report_sha256'] == closed['report_sha256'] == digest(report)
        assert original['checker_sha256'] == observation['scriptSha256'] == digest(driver)
        assert not observation['completed'] and closed['node_closed'] and closed['chromium_pids']
        assert closed['node_pid'] == original['node_pid'] and closed['chromium_pids'] == original['chromium_pids']
        assert not closed['remaining_chromium'] and original['all_children_exited'] and not original['remaining_children']
        assert original['exit_code'] == closed['exit'] and original['log_sha256'] == digest(group/(original['phase']+'.log'))
        assert {f.name:digest(f) for f in report.parent.glob('*.png')} == original['screenshots']
        for row in observation['screenshots']:
            assert digest(report.parent / row['file']) == row['sha256']
        result[group.name] = dict(exit_code=closed['exit'],completed=False,
            evidence=record(index,group.name,'evidence.json'),
            closed=record(receipt,group.name,receipt.name),report=record(report,group.name,report.name),
            driver=record(driver,'drivers',driver.name),
            log=record(group/(original['phase']+'.log'),group.name,'browser.log'),
            screens={f.name:record(f,group.name,f.name) for f in sorted(report.parent.glob('*.png'))})
    return result
