"""Lend a physically closed city-map interval to the already running model coordinator."""
import argparse
import datetime
import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

root = Path('/tmp/remi-jinling285')
parent = Path('/tmp/zhongxing284')
handoff = root/'mapping/handoff'
cmd = argparse.ArgumentParser(description=__doc__)
cmd.add_argument('phase', choices=['native', 'viewer'])
cmd.add_argument('physical_exit', type=Path)
parameters = cmd.parse_args()
phase, evidence = parameters.phase, parameters.physical_exit
here = Path(__file__).resolve().parent
read = lambda f: json.loads(f.read_bytes())
digest = lambda f: hashlib.sha256(f.read_bytes()).hexdigest()
now = lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
outcome = here/f'285-{phase}-outcome.json'


def save(result):
    temporary = outcome.with_suffix('.part')
    temporary.write_text(json.dumps(result, indent=2)+'\n')
    temporary.replace(outcome)


def physical(file, order):
    data = read(file)
    assert data.get('order', order) == order
    assert next((data[key] for key in ['exit','exit_code','code','returncode'] if key in data), None) == 0
    assert not any(data.get(key) for key in ('remaining','remaining_chromium','remaining_processes'))
    return data


def snapshot(file, order):
    data = read(file)
    assert data['order'] == order and Path(data['root']).is_dir()
    assert digest(Path(data['snapshot'])) == data['sha256']
    return data


city = physical(evidence, 220)
assert city['tag'] == {'native':'before','viewer':'phone'}[phase] and not (Path('/proc')/str(city['node_pid'])).exists()
report = Path(city['report'])
assert digest(report) == city['sha256'] and read(report)['passed'] and read(report)['browser_closed']
if outcome.exists():
    old = read(outcome)
    assert old['physical_exit_sha256'] == digest(evidence)
    if old.get('decision') in ('deferred','completed'):
        sys.exit(0)
release = root/('native-closed.json' if phase=='native' else 'viewer-closed.json')
parent_raw = parent/'raw-284-confirmed.json'
parents = [parent/'native-closed.json', parent_raw]
if phase == 'viewer':
    parents += [parent/'viewer-closed.json', root/'native-closed.json', root/'raw-285-confirmed.json', Path('/tmp/shanghai-yongjia-porch/scenes/285-comparison.json')]
decision = dict(phase=phase, order=285, host=220, physical_exit=str(evidence),physical_exit_sha256=digest(evidence), checked_utc=now())
if release.exists():
    physical(release,285)
    save({**decision,'decision':'completed','already_closed':True,'release':str(release),'release_sha256':digest(release)})
    sys.exit(0)
missing = [str(file) for file in parents if not file.is_file()]
if missing:
    save({**decision,'decision':'deferred','unavailable_inputs':missing})
    sys.exit(0)
physical(parents[0],284)
snapshot(parent_raw,284)
if phase == 'viewer':
    physical(parent/'viewer-closed.json',284)
    physical(root/'native-closed.json',285)
    snapshot(root/'raw-285-confirmed.json',285)
    assert read(parents[-1])['passed']
dispatch = read(handoff/'dispatch-contract.json')
admit = handoff/'admit-window.py'
assert digest(admit) == dispatch['signed_programs'][admit.name]
command = [sys.executable,'-B',admit,phase,evidence]
if phase == 'native':
    candidates=[Path('/dev/shm'), Path('/tmp')]
    chosen=max(candidates,key=lambda d:shutil.disk_usage(d).free)
    scratch=chosen/'jinling285-window220'
    command += ['--work-directory',scratch]
subprocess.run(command,check=True)
while not release.exists():
    monitor = int((handoff/'monitor.pid').read_text())
    if not (Path('/proc')/str(monitor)).exists():
        raise RuntimeError(f'285 coordinator {monitor} exited before {release}')
    time.sleep(2)
record = physical(release,285)
assert record['passed']
if phase == 'native':
    assert record['wrapper_closed'] and record['blender_pids'] and len(record['assets'])==4 and record['window_sha256']==digest(evidence)
else:
    assert record['chromium_pids'] and record['admitted_from']==digest(evidence)
save({**decision,'decision':'completed','release':str(release),'release_sha256':digest(release),'finished_utc':now()})
