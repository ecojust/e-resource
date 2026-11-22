"""Run separate Chromium sessions after the archived 239 handoff and lend the two closed sessions to 305."""
from pathlib import Path
import hashlib, fcntl, json, subprocess, os, sys, time, datetime, tempfile, shutil
w = Path(__file__).resolve().parent
e = w / 'evidence'
r = lambda p: json.loads(p.read_bytes())
h = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
now = lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
phases = ('before', 'phone', 'desktop', 'old-roof', 'roof', 'old-river', 'river', 'walk-return', 'mouse', 'touch', 'neighbors', 'distant')
prior = Path('/tmp/shanghai-main-239/239-map-slot-released.json')

def write(f, v):
    b = (json.dumps(v, ensure_ascii=False, indent=2) + '\n').encode()
    t = f.with_suffix('.part')
    t.write_bytes(b)
    os.replace(t, f)

def process_group(pid):
    processes = {}
    children = {}
    for f in Path('/proc').glob('[0-9]*/stat'):
        try:
            fields = f.read_text().rsplit(')', 1)[1].split()
            current = int(f.parent.name)
            parent = int(fields[1])
            processes[current] = (fields[19], (f.parent / 'comm').read_text().strip())
            children.setdefault(parent, []).append(current)
        except (OSError, IndexError, ValueError):
            continue
    pending = [pid]
    seen = {}
    while pending:
        current = pending.pop()
        if current in seen or current not in processes:
            continue
        seen[current] = processes[current]
        pending.extend(children.get(current, []))
    return seen

def alive(row):
    result = []
    for pid, (birth, comm) in row.items():
        try:
            sub = Path('/proc', str(pid), 'stat').read_text().rsplit(')', 1)[1].split()
        except OSError:
            continue
        if sub[0] not in ('Z', 'X') and sub[19] == birth:
            result.append(pid)
    return result

def verify_closed(phase):
    d = e / phase
    out = r(d / 'closed.json')
    b = r(d / 'browser.json')
    assert out['exit'] == 0 and out['node_closed'] and out['chromium_pids'] and (not out['remaining']) and (not out['remaining_chromium'])
    assert b['completed'] and (not b['errors']) and (not b['failed']) and b['screenshots'] and (out['report_sha256'] == h(d / 'browser.json'))
    assert b['phase'] == phase and b['case_sha256'] == h(w / 'bound.json') and (b['driver_sha256'] == h(w / ('first-240-roof-diagnostic/map.cjs' if phase in ('before','phone','desktop') else 'map.cjs')))
    for im in b['screenshots']:
        assert h(d / im['file']) == im['sha256']
    return out

def handoff(which, ticket):
    guest = Path('/tmp/shi-tongren305')
    done = guest / f'{which}-closed.json'
    skip = guest / 'handoff' / f'{which}-deferred.json'
    script = guest / 'handoff/admit-window.py'
    assert script.is_file()
    subprocess.run([sys.executable, '-B', script, which, ticket], check=True)
    while not done.is_file() and (not skip.is_file()):
        time.sleep(2)
    if done.is_file():
        g = r(done)
        assert g['order'] == 305 and g['passed'] and (g['exit'] == 0) and (not g['remaining'])
    else:
        g = r(skip)
        assert g['order'] == 305 and g['host'] == 240 and g['kind'] == which and g['deferred'] is True
        assert g['source_sha256'] == h(ticket)
        if g.get('actual_prior_attempt'):
            assert g['attempt_exit_code'] != 0 and g['all_processes_closed'] is True and g['remaining'] == []
            assert g['blender_started'] is (which == 'native') and g['browser_started'] is (which == 'viewer')
            physical = guest / 'handoff' / f'{which}-most-recent-exit.json'
            observed = r(physical)
            assert observed == g['physical_exit'] and observed['remaining'] == [] and observed['wrapper_closed'] is True
        else:
            assert g['blender_started'] is False and g['browser_started'] is False and g['missing']
    write(w / f'305-{which}-gate.json', dict(action=which, source=str(ticket), source_sha256=h(ticket), guest_receipt=str(done if done.is_file() else skip), guest_sha256=h(done if done.is_file() else skip)))

def run():
    old = r(prior)
    assert old['order'] == 239 and old['passed'] and (old['exit_code'] == 0) and (old['remaining_chromium'] == []) and old['all_captures_visually_reviewed'] and old['real_browser_process_exits'] and (len(old['manual_sha256']) == 64)
    write(w / 'prior-release.json', dict(path=str(prior), sha256=h(prior), receipt=old))
    e.mkdir(exist_ok=True)
    for phase in phases:
        d = e / phase
        d.mkdir(exist_ok=True)
        c = d / 'closed.json'
        f = d / 'browser.json'
        if not c.exists():
            assert not f.exists(), 'Archive physically ended partial attempts before retrying.'
            root = max([Path('/run/codex-docker/user'), Path('/dev/shm')], key=lambda q: shutil.disk_usage(q).free)
            with tempfile.TemporaryDirectory(prefix='city-240-' + phase + '-', dir=root) as temporary, (d / 'stdout.log').open('wb') as log:
                env = dict(os.environ, TMPDIR=temporary, NODE_PATH='/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules')
                start = now()
                proc = subprocess.Popen(['node', w / 'map.cjs', phase], cwd=w, env=env, start_new_session=True, stdout=log, stderr=subprocess.STDOUT)
                seen = {}
                while proc.poll() is None:
                    seen.update(process_group(proc.pid))
                    time.sleep(0.4)
                for i in range(35):
                    if not alive(seen):
                        break
                    time.sleep(0.5)
                remaining = alive(seen)
                chromes = {k: v for k, v in seen.items() if v[1] in ('chrome', 'chromium')}
                write(c, dict(order=240, phase=phase, exit=proc.returncode, exit_code=proc.returncode, pid=proc.pid, node_pid=proc.pid, node_closed=proc.pid in seen and proc.pid not in remaining, chromium_pids=sorted(chromes), remaining_chromium=alive(chromes), remaining=remaining, started=start, finished=now(), port=31239 if phase in ('before', 'old-roof', 'old-river') else 31240, report=str(f), report_sha256=h(f) if f.is_file() else None))
        verify_closed(phase)
        if phase == 'mouse':
            guest = Path('/tmp/meilun526')
            program = guest / 'recheck-after-240.py'
            assert h(program) == '23e70b0637d923bfab3e8f27e8115f20980ef0eeafa088f702889f907b2c4932'
            subprocess.run([sys.executable, '-Bu', program, c], check=True)
            result = r(guest / '240-native-returned.json')
            assert (result['order'], result['host'], result['phase']) == (526, 240, 'mouse')
            assert result['host_sha256'] == h(c) and result['host_report_sha256'] == h(f)
            assert result['all_children_exited'] and result['remaining_children'] == []
            assert result['author_sha256'] == h(guest / 'author-physical.json')
            assert result['phases'] and result['exit_code'] == result['phases'][-1]['exit_code']
            assert result['passed'] == (len(result['phases']) == 2 and result['exit_code'] == 0)
            for step in result['phases']:
                assert step['pid'] > 1 and len(step['log_sha256']) == 64
                if step['physical']:
                    assert h(Path(step['physical'])) == step['physical_sha256']
        if phase in ('before', 'phone'):
            which = 'native' if phase == 'before' else 'viewer'
            if not (w / f'305-{which}-gate.json').exists():
                handoff(which, c)
        if phase not in ('before','phone') and not (Path('/tmp/shi-tongren305/viewer-closed.json')).is_file():
            score=Path('/tmp/shanghai-yongjia-porch/scenes/305-comparison.json')
            if score.is_file() and r(score).get('passed'):
                handoff('viewer',e/'phone'/'closed.json')
    write(w / 'all-sessions-closed.json', dict(order=240, phases=list(phases), closed_at=now(), pending_visual_review=True))
if __name__ == '__main__':
    with (w / 'sequence.lock').open('a') as file:
        fcntl.flock(file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        run()
