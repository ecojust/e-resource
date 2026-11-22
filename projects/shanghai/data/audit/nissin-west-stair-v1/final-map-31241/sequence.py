"""Run separate Chromium sessions after the archived 240 handoff and lend the two closed sessions to 306."""
from pathlib import Path
import hashlib, fcntl, json, subprocess, os, sys, time, datetime, tempfile, shutil
w = Path(__file__).resolve().parent
e = w / 'evidence'
r = lambda p: json.loads(p.read_bytes())
h = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
now = lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
phases = ('before','phone','desktop','old-west-stair','west-stair','old-roof','roof','old-main-door','main-door','old-corner','corner','walk-return','mouse','touch','neighbors','distant','standalone-desktop','standalone-phone')
prior = Path('/tmp/shanghai-main-240/240-map-slot-released.json')

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
    assert b['phase'] == phase and b['case_sha256'] == h(w / 'bound.json') and (b['driver_sha256'] == h(w / 'map.cjs'))
    for im in b['screenshots']:
        assert h(d / im['file']) == im['sha256']
    return out

def handoff(which, ticket):
    guest=Path('/tmp/daxin306')
    program=guest/'mapping/handoff/admit-window.py'
    parent=Path('/tmp/shi-tongren305')
    waiting=[parent/'native-closed.json',parent/'raw-305-confirmed.json']
    if which=='viewer':
        waiting += [parent/'viewer-closed.json',guest/'native-closed.json',guest/'raw-306-confirmed.json',Path('/tmp/shanghai-yongjia-porch/scenes/306-comparison.json'), Path('/tmp/shanghai-yongjia-porch/scenes/306-all-http.json')]
    missing=[str(path)for path in [program,*waiting] if not path.is_file()]
    host=w/f'306-{which}-gate.json'
    binding=r(w/'guest-and-next.json')
    if program.is_file():
        assert h(program)==binding['admit_sha256'] and h(guest/'mapping/handoff/dispatch-contract.json')==binding['dispatch_sha256']
    if missing:
        deferred=w/f'306-{which}-deferred.json'
        write(deferred,dict(order=306,host=241,kind=which,deferred=True,source=str(ticket),source_sha256=h(ticket),missing=missing,blender_started=False,browser_started=False))
        write(host,dict(order=306,source=str(ticket),source_sha256=h(ticket),action=which,guest_receipt=str(deferred),guest_sha256=h(deferred)))
        return
    proc=subprocess.Popen([sys.executable,'-B',program,which,str(ticket)],start_new_session=True)
    observed={}
    while proc.poll() is None:
        observed.update(process_group(proc.pid))
        time.sleep(.15)
    for i in range(20):
        if not alive(observed):break
        time.sleep(.25)
    remaining=alive(observed);assert not remaining
    process=dict(wrapper_pid=proc.pid,returncode=proc.returncode,closed=True,remaining=remaining,observed={str(pid):state[1] for pid,state in observed.items()},source_sha256=h(ticket))
    write(w/f'306-{which}-admission-process.json',process)
    if proc.returncode:
        raise RuntimeError(f'306 {which} admission returned {proc.returncode}; preserve its completed process evidence before retrying.')
    closed=guest/f'{which}-closed.json'
    forms=[w/f'306-{which}-deferred.json',guest/'mapping/handoff'/f'{which}-deferred.json',guest/'mapping/handoff'/f'241-{which}-deferred.json', guest/f'241-{which}-deferred.json']
    while not closed.is_file() and not any(x.is_file()for x in forms):time.sleep(2)
    if closed.is_file():
        target=closed
        g=r(target);assert g['order']==306 and g.get('passed') and g.get('exit',g.get('exit_code'))==0 and g.get('remaining',g.get('remaining_chromium',[]))==[]
    else:
        target=next(k for k in forms if k.is_file());g=r(target)
        assert g['order']==306 and g['authorized'] is False and g['stage']==which and g['reason'].strip()
        assert Path(g['previous_session']).resolve()==ticket.resolve() and g['previous_report_sha256']==r(ticket)['report_sha256']
        if g['attempted']:
            assert process['closed'] and not process['remaining']
            attempts=[]
            for q in (guest/'mapping/handoff').glob(f'{which}-attempt-*/process-exit.json'):
                act=r(q)
                if act.get('admitted_from')==h(ticket):
                    assert act['wrapper_closed'] and not act['remaining']
                    attempts.append(dict(path=str(q),sha256=h(q)))
            write(w/f'306-{which}-attempted-return.json',dict(observed_admission=process,physical_attempt_exits=attempts,real_graphics_processes=[pid for pid,name in process['observed'].items()if name in ('blender','chromium','chrome')]))
        else:
            assert not any(v in ('blender','chromium','chrome')for v in process['observed'].values())
    write(host,dict(order=306,source=str(ticket),source_sha256=h(ticket),action=which,guest_receipt=str(target),guest_sha256=h(target)))

def run():
    subprocess.run([sys.executable,'-B',w/'complete-inputs.py'],check=True)
    old=r(prior)
    assert old['order'] == 240 and old['passed'] and (old['exit_code'] == 0) and (old['remaining_chromium'] == []) and old['all_captures_visually_reviewed'] and old['real_browser_process_exits'] and (len(old['manual_sha256']) == 64)
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
            with tempfile.TemporaryDirectory(prefix='city-241-' + phase + '-', dir=root) as temporary, (d / 'stdout.log').open('wb') as log:
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
                write(c, dict(order=241, phase=phase, exit=proc.returncode, exit_code=proc.returncode, pid=proc.pid, node_pid=proc.pid, node_closed=proc.pid in seen and proc.pid not in remaining, chromium_pids=sorted(chromes), remaining_chromium=alive(chromes), remaining=remaining, started=start, finished=now(), port=31240 if phase=='before' or phase.startswith('old-') else 31241, report=str(f), report_sha256=h(f) if f.is_file() else None))
        verify_closed(phase)
        if phase == 'mouse':
            guest = Path('/tmp/overseas-chinese530')
            program = guest / 'recheck-after-241.py'
            assert h(program) == '3381c546b702ebc8897754b33a14833ea5f074430b0101d9364edb5b3347ce63'
            subprocess.run([sys.executable, '-Bu', program, c], check=True)
            result = r(guest / '241-native-returned.json')
            assert (result['order'], result['host'], result['phase']) == (530, 241, 'mouse')
            assert result['host_sha256'] == h(c) and result['host_report_sha256'] == h(f)
            assert result['all_children_exited'] and result['remaining_children'] == []
            early = guest / 'early-236-native-returned.json'
            original = r(early)
            assert result['reverified_early'] and result['early_sha256'] == h(early)
            assert original['author_sha256'] == h(guest / 'author-physical.json')
            assert result['phases'] == original['phases'] and result['four_assets'] == original['four_assets']
            assert set(result['four_assets']) == {'native','raw','full','lod'}
            assert result['phases'] and result['exit_code'] == result['phases'][-1]['exit_code']
            assert result['passed'] == (len(result['phases']) == 2 and result['exit_code'] == 0)
            for step in result['phases']:
                assert step['pid'] > 1 and len(step['log_sha256']) == 64
                if step['physical']:
                    assert h(Path(step['physical'])) == step['physical_sha256']
        if phase in ('before', 'phone'):
            which = 'native' if phase == 'before' else 'viewer'
            if not (w / f'306-{which}-gate.json').exists():
                handoff(which, c)
        if phase == 'desktop':
            runner = Path('/workspace/.e-resource-recovery/grace/early-native-after-publication-v9.py')
            assert h(runner) == '9549525f3f893f79274af8f42dfd910fcd1f27cf0ad32213d2c8d42a16c141ed'
            previous = Path('/tmp/jingcun558/early-240-native-returned.json')
            assert h(previous) == '33ded8bd04f5c2158afa4cd142500b5b8ca4186b8bdea4a7444f03e79c1b00b2'
            subprocess.run([sys.executable, '-Bu', runner, '241', c, h(c), f, previous, h(previous), '562', '566'], check=True)
            first = Path('/tmp/songyun562/early-241-native-returned.json')
            last = Path('/tmp/xiangming566/early-241-native-returned.json')
            assert r(first)['previous_sha256'] == h(previous) and r(last)['previous_sha256'] == h(first)
            for completed in (first, last):
                signed = r(completed)
                assert signed['host_sha256'] == h(c) and signed['host_report_sha256'] == h(f)
                assert signed['passed'] and signed['exit_code'] == 0 and signed['all_children_exited'] and not signed['remaining_children']
            entry = Path('/workspace/.e-resource-recovery/history/early-slaughterhouse-after-reboot.py')
            assert h(entry) == 'fedab602bb203a47bcc587b413681323e9f378f66fc1ce675ad006e49e580341'
            returned = Path('/tmp/hongkou-408-study/recovered-development/development-native/early-development-returned.json')
            while not returned.is_file():
                time.sleep(1)
            case = r(returned)
            assert case['order'] == 408 and case['host'] == 241 and case['host_sha256'] == h(c)
            assert case['host_report_sha256'] == h(f) and case['prior_in_this_window_sha256'] == h(last)
            assert case['physical_sha256'] == h(Path(case['physical'])) and case['all_children_exited'] and not case['remaining_children']
            assert case['exit_code'] == r(Path(case['physical']))['exit_code'] and case['passed'] == (case['exit_code'] == 0)
        if phase == 'distant':
            supplement = Path('/workspace/.e-resource-recovery/grace/reboot241/supplement-306.py')
            assert h(supplement) == '2cb77d1dbdb654cf0a23fe365610579663b65693301c0c382aa6d55480c7b474'
            subprocess.run([sys.executable, '-Bu', supplement, c], check=True)
    write(w / 'all-sessions-closed.json', dict(order=241, phases=list(phases), closed_at=now(), pending_visual_review=True))
    development=Path('/tmp/hongkou-420-study/development-native/link-241.py')
    assert h(development)=='dbadd2812f2d441e3284388f91ec4d633af6dd7307475d6f77ae4df790ce46da'
    subprocess.run([sys.executable,'-Bu',development,e/'standalone-phone/closed.json',w/'all-sessions-closed.json'],check=True)
    result=r(development.parent/'241-development-returned.json')
    assert result['order']==420 and result['host']==241 and result['all_children_exited'] and result['remaining_children']==[]
    assert result['host_sha256']==h(e/'standalone-phone/closed.json') and result['previous_sha256']==h(w/'all-sessions-closed.json')
if __name__ == '__main__':
    with (w / 'sequence.lock').open('a') as file:
        fcntl.flock(file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        run()
