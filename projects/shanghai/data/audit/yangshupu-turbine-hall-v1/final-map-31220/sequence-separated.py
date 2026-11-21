"""Close each physical Chromium between the old scene, desktop and touchscreen scenes."""
from pathlib import Path
import datetime,hashlib,os,subprocess,fcntl,shutil,json,sys,time,runpy
w=Path(__file__).parent
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def save(f,j):v=f.with_suffix('.part');v.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n');v.replace(f)
def rest(prefix):
    out=[]
    for f in Path('/proc').glob('[0-9]*/cmdline'):
        try:
            argv=f.read_bytes().split(b'\0');live=(f.parent/'stat').read_text().rsplit(')',1)[1].split()[0]!='Z'
            if live and b'chrom' in argv[0] and any(os.fsencode(prefix)in item for item in argv):out.append(int(f.parent.name))
        except OSError:pass
    return out
def offer_284(tag,receipt,report):
    program=Path('/dev/shm/284-offer-after-220.py')
    assert sha(program)=='776567db523ddea7dcfc8a0f5c5b82237c04ccfbe08f204400209d3e92625ebe'
    subprocess.run([sys.executable,'-Bu',program,tag,receipt],check=True)
    returned=Path('/tmp/zhongxing284')/f'220-{tag}-viewer-returned.json'
    outcome=json.loads(returned.read_bytes())
    assert outcome['phase']==tag and outcome['order']==284 and outcome['host']==220
    assert outcome['host_receipt_sha256']==sha(receipt) and outcome['host_report_sha256']==sha(report)
    assert outcome['remaining']==[]
    if outcome.get('passed'):
        assert sha(Path(outcome['receipt']))==outcome['receipt_sha256']
    elif outcome.get('deferred'):
        assert outcome['missing'] and not outcome['attempted'] and not outcome['started']
    else:
        assert outcome['failed'] and outcome['attempted'] and outcome['exit_code']!=0
with(w/'whole-map.lock').open('a')as g:
    fcntl.flock(g,fcntl.LOCK_EX|fcntl.LOCK_NB)
    parent=Path('/tmp/jiangnan219/219-map-slot-released.json')
    while not parent.is_file():time.sleep(3)
    predecessor=json.loads(parent.read_bytes())
    assert predecessor['order']==219 and predecessor['passed'] and predecessor['after_real_screenshot_review'] and predecessor['final_closed_at'] and not predecessor['remaining_chromium']
    stages=('control','phone','desktop','return','placement','distant')
    assert set(predecessor['receipts'])=={*stages,'standalone'}
    captured=[]
    for stage,old in predecessor['receipts'].items():
        old_file=Path(old['closed']);doc=Path(old['report'])
        assert old['exit']==0 and sha(old_file)==old['sha256'] and sha(doc)==old['report_sha256']
        prev=json.loads(old_file.read_bytes());seen=json.loads(doc.read_bytes())
        assert prev['exit']==0 and prev['node_closed'] and prev['chromium_pids'] and prev['report_sha256']==sha(doc)
        if stage=='standalone':
            assert old_file==Path('/tmp/jiangnan219/standalone-closed.json') and prev['chromium_remaining']==[]
            assert prev['passed'] and prev['views']==6 and len(prev['downloads'])==4
        else:
            assert old_file.samefile(Path('/dev/shm/jiangnan219-final/segments')/(stage+'-closed.json'))
            assert prev['remaining_chromium']==[] and seen['completed']
            for shot in seen['screenshots']:
                assert sha(doc.parent/shot['file'])==shot['sha256']
                captured.append(shot['sha256'])
    assert len(captured)==predecessor['screenshots']==10
    sessions=[]
    for tag,mode,device in [('before','before','desktop'),('phone','after','mobile'),('desktop','after','desktop')]:
        out=w/tag;out.mkdir(exist_ok=True);profile=Path(max(['/dev/shm','/tmp'],key=lambda d:shutil.disk_usage(d).free))/('map220-profile-'+tag);profile.mkdir(exist_ok=True)
        receipt=out/'physical-exit.json';report=out/(mode+'.json')
        if not receipt.exists():
            env={**os.environ,'TMPDIR':str(profile),'NODE_PATH':'/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules'}
            command=['node',w/'check-historical-map.cjs',mode,w/'bound-inputs.json',out,w/'before/before.json',device]
            physical=runpy.run_path(str(w/'physical-session.py'))['check']
            data=physical(profile,command,env,report,out/'process.log',tag)
            save(receipt,data)
        j=json.loads(receipt.read_bytes());assert j['exit_code']==0 and j['remaining_chromium']==[] and j['sha256']==sha(report),j
        assert j['node_closed'] and j['chromium_pids'] and not j['remaining_children'] and j['cdp_closed']
        assert j['sha256']==sha(report)

        r=json.loads(report.read_bytes());assert r['passed'] and r['browser_closed'] and len(r['captures'])==(1 if mode=='before'else 3)
        assert len(r['trusted_inputs'])==1 and all(f['trusted'] for f in r['trusted_inputs'])
        sessions.append(j)
        if tag=='desktop':
            follow=Path('/tmp/wanyi343/mapping/220-after-desktop.py')
            assert sha(follow)=='bd1c99e662d2787a1e7d54a43a46dd4a52644bfe9d2c997160e150826daadabd'
            subprocess.run([sys.executable,'-B',follow,receipt],check=True)
            returned=Path('/tmp/wanyi343/mapping/220-city-cpu-closed.json')
            action=json.loads(returned.read_bytes())
            assert action['host_sha256']==sha(receipt) and action['host_report_sha256']==sha(report) and action['remaining']==[]
            if action['attempted']:
                assert all(not phase.get('remaining',[]) for phase in action['phases'])
                assert action['log_sha256']==sha(Path(action['log']))
            shaoxing=Path('/tmp/shaoxing9-347/mapping/test-model-at-host.py')
            assert sha(shaoxing)=='62ce92140eab1084b91b089b48961645738ee3ae8d53de02f643563e6b002b49'
            subprocess.run([sys.executable,'-B',shaoxing,'220',receipt,returned],check=True)
            finished=shaoxing.parent/'220-model-closed.json';verified=json.loads(finished.read_bytes())
            assert verified['order']==347 and verified['host_sha256']==sha(receipt) and verified['previous_return_sha256']==sha(returned)
            assert verified['attempted'] and verified['phases'] and verified['exit'] is not None and verified['remaining']==[]
            assert verified['log_sha256']==sha(Path(verified['log']))
            garden=Path('/tmp/jiangvilla349/host-cpu.py')
            assert sha(garden)=='ceb24e2ca186a9ba96c176117adc281b3d548eb073b9731d5b0034c33294b96f'
            subprocess.run([sys.executable,'-B',garden,'220',receipt,finished],check=True)
            garden_ticket=garden.parent/'220-cpu-closed.json'
            complete=json.loads(garden_ticket.read_bytes())
            assert complete['order']==349 and complete['host']==220 and complete['host_receipt_sha256']==sha(receipt)
            assert complete['receipts']=={'desktop':sha(report),'343':sha(returned),'347':sha(finished)} and complete['remaining']==[]
            if complete['attempted']:
                assert complete['exit_code'] is not None and complete['phases'] and all(row['pid']>0 and sha(Path(row['log']))==row['log_sha256'] for row in complete['phases'])
            else:
                assert complete['deferred'] and not complete['phases']
            last=Path('/tmp/anhe345/220-runtime-window.py')
            assert sha(last)=='45c2431a258a80a7cd6be78e02e9fb830b131ba616a60c69ba7a8f7161e75295'
            subprocess.run([sys.executable,'-B',last,receipt,garden_ticket],check=True)
            outcome=json.loads((last.parent/'220-cpu-closed.json').read_bytes())
            assert outcome['host']==220 and outcome['order']==345 and not outcome['remaining']
            assert outcome['host_receipt_sha256']==sha(receipt) and outcome['host_report_sha256']==sha(report)
            assert outcome['previous_sha256']==sha(garden_ticket)
            if outcome['stages']:
                assert all(i['pid']>0 and sha(Path(i['log']))==i['log_sha256'] for i in outcome['stages'])
            else:assert outcome['deferred']
        if tag in ('before','phone'):
            phase={'before':'native','phone':'viewer'}[tag]
            if tag=='phone':offer_284(tag,receipt,report)
            subprocess.run([sys.executable,'-B',w/'offer-285.py',phase,receipt],check=True)
            if tag=='before':offer_284(tag,receipt,report)
            if tag=='before':
                study=Path('/tmp/park-fuxing338/design/after-220-control.py')
                assert sha(study)=='d9e1a5eb8fd736aac1c3cee9534d75efecbe2a9e63b19b27eea5788bf6ee4d4c'
                earlier=w/'285-native-outcome.json'
                subprocess.run([sys.executable,'-B',study,receipt,earlier],check=True)
                returned=study.parent.parent/'220-map-cpu-closed.json'
                visited=json.loads(returned.read_bytes())
                assert visited['order']==338 and visited['host']==220 and visited['host_sha256']==sha(receipt)
                assert visited['previous_sha256']==sha(earlier) and visited['pid']>1 and visited['remaining']==[]
                assert isinstance(visited['exit_code'],int) and sha(Path(visited['log']))==visited['log_sha256']

                retry=Path('/tmp/wanyi343/mapping/220-before-model.py')
                assert sha(retry)=='441e0210d39eeceb9fbbd21df1213af4cf2522485e55fdb06286c58de23a16ba'
                subprocess.run([sys.executable,'-B',retry,receipt],check=True)
                model=json.loads((retry.parent/'220-before-model-closed.json').read_bytes())
                assert model['host']==220 and model['order']==343 and model['source_sha256']==sha(receipt)
                assert model['host_report_sha256']==sha(report) and model['previous_sha256']==sha(returned)
                assert model['remaining']==[] and sha(Path(model['log']))==model['log_sha256']

            if tag=='phone':
                trial=Path('/tmp/huaihai1897-356/development-native/after-220.py')
                assert sha(trial)=='1b748276efc9b1397ce759470d14b0e4ff569a559660d253dfd1edf9843f92ad'
                previous=w/'285-viewer-outcome.json'
                subprocess.run([sys.executable,'-B',trial,receipt,previous],check=True)
                then=trial.parent/'220-development-returned.json';completed=json.loads(then.read_bytes())
                assert completed['order']==356 and completed['host']==220 and completed['host_sha256']==sha(receipt)
                assert completed['host_report_sha256']==sha(report) and completed['previous_sha256']==sha(previous)
                assert completed['all_children_exited'] and completed['remaining_children']==[]
                if completed['started']:
                    assert completed['wrapper_pid']>0 and isinstance(completed['exit_code'],int)
                    assert sha(Path(completed['log']))==completed['log_sha256']
                    if completed['exit_code']==0:
                        assert completed['passed'] and sha(Path(completed['physical']))==completed['physical_sha256']
                else:
                    assert completed['deferred'] and completed['missing']
    save(w/'three-scene-outcomes.json',sessions)
