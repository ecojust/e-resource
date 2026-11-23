"""Re-read original files from a released Nanshi Telephone Exchange field review."""
import hashlib
import json
from pathlib import Path

def sha(p):
    with p.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()

def read(p):
    return json.loads(p.read_bytes())

def verify(audit,order,names):
    audit=Path(audit)
    index_rel='city-31262/independent-field-audit/field-index.json'
    index_path=audit/index_rel
    assert order==262 and index_rel in names and sha(index_path)=='94dd2ccd679bc080988608a955a336832617e310a4dcda442d8d510464812738'
    index=read(index_path)
    assert index['order']==order and index['id']=='huangpu-nanshi-telephone-exchange'
    phases=index['phases']
    assert phases==['control','mobile-card','mobile-pin','desktop-card','desktop-pin','street','roof','clock','central-arch','distant']
    assert not index['final'] or list(index['completed'])==phases
    for name,item in index['files'].items():
        file=audit/name
        assert name in names and file.stat().st_size==item['bytes'] and sha(file)==item['sha256'],name
    for state in ('attempts','completed'):
        for key,attempt in index[state].items():
            folder=audit/attempt['directory']
            phase=attempt['phase']
            c=read(folder/attempt['closure'])
            original=folder/attempt['report']
            assert original.is_file()==attempt['report_present']
            assert c['order']==order and c['phase']==phase and phase in phases
            assert c['node_pid']==attempt['node'] and c['node_closed'] and c['cdp_closed']
            assert not c['remaining_chromium'] and not c['remaining']
            assert c['exit_code']==c['exit']==attempt['exit']
            assert c['observed_chromium_pid_and_starttime']==attempt['observed_chromium']
            assert set(map(str,c['chromium_pids']))==set(attempt['observed_chromium'])
            assert sha(folder/'node.log')==c['stdout_sha256']
            assert sha(audit/attempt['driver'])==c['source_code_sha256']
            assert c['actual_origin']==(31261 if phase=='control' else 31262)
            if not attempt['report_present']:
                assert state=='attempts' and c['exit_code']!=0 and c['report_sha256'] is None
                assert not attempt['screenshot_names'] and not attempt['failure_first_line']
                retained=read(folder/'retained-at-reentry.json')
                assert retained['phase']==phase
                for item in retained['retained']:
                    assert sha(folder/item['name'])==item['sha256']
                continue
            assert sha(original)==c['report_sha256']
            report=read(original)
            assert report['phase']==phase and report['id']==index['id']
            if attempt['report_driver']:
                assert state=='attempts' and c['exit_code']!=0
                assert sha(audit/attempt['report_driver'])==report['scriptSha256']!=c['source_code_sha256']
            else:
                assert report['scriptSha256']==c['source_code_sha256']
            assert report['server']=='http://127.0.0.1:'+str(c['actual_origin'])+'/'
            assert [s['file'] for s in report['screenshots']]==attempt['screenshot_names']
            for shot in report['screenshots']:
                image=folder/shot['file']
                assert sha(image)==shot['sha256'] and image.stat().st_size==shot['bytes']
            if 'viewportCalibration' in report:
                cal=report['viewportCalibration']
                assert sha(folder/cal['image'])==cal['sha256']
            if state=='attempts':
                assert c['exit_code']!=0 and not report['completed']
                assert str(report.get('failure','')).split('\n')[0]==attempt['failure_first_line']
                retained=read(folder/'retained-at-reentry.json')
                assert retained['phase']==phase
                for item in retained['retained']:
                    assert sha(folder/item['name'])==item['sha256']
            else:
                assert c['exit_code']==0 and report['completed'] and not report['failed'] and not report['errors']
                assert len(report['screenshots'])==1
                assert c['frame_check_sha256']==sha(folder/'frame-check.json')
                assert read(folder/'frame-check.json')['report_sha256']==c['report_sha256']
                assert report['realDirectoryEntry']['pointer']['trusted']
    return True
