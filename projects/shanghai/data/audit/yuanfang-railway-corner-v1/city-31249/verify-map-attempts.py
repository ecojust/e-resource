from hashlib import sha256
from pathlib import Path
import json

def verify(audit,order,names):
    assert order==249
    base=Path(audit).resolve()/'city-31249'
    bucket=base/'renderer-failures'
    def digest(path):
        with path.open('rb') as f:return sha256(f.read()).hexdigest()
    def read(path):return json.loads(path.read_bytes())
    idx=bucket/'index.json'
    assert digest(idx)=='255d8e464daf0e9f4f1e19aea1892709adb58c09998854870bf85af85b2e475c'
    book=read(idx)
    assert set(book)=={'order','failed','success'} and book['order']==249
    assert {p.name for p in bucket.iterdir()}==set(book['failed'])|{'index.json'}
    failed_files=set()
    def session(row,ok):
        for rel,sig in row['files'].items():
            p=base/rel;assert p.resolve().is_relative_to(base) and digest(p)==sig
        close=base/row['receipt']; rp=base/row['report'];source=base/row['source']
        ex,report=read(close),read(rp)
        phase=row['phase'];assert report['id']=='huangpu-yuanfang-lane-railway-corner' and report['section']==phase
        assert report['server']==('http://127.0.0.1:31248/' if phase=='before' else 'http://127.0.0.1:31249/')
        assert report['catalog']['count']==(283 if phase=='before' else 284) and len(report['bindings'])==7
        assert ex['report_sha256']==digest(rp) and ex['driver_sha256']==digest(source)==report['scriptSha256']
        unfinished = not ok and close.parent.name=='details-01'
        no_finish = unfinished or (not ok and close.parent.name=='architecture-02')
        assert ex['exit']==(0 if ok or unfinished else 1) and ex['node']>0 and ex['node_closed'] is True
        assert ex['chromium_pids'] and all(isinstance(pid,int) and pid>0 for pid in ex['chromium_pids'])
        assert ex['remaining']==[] and report['completed'] is ok and (report.get('finished') is None if no_finish else report['finished']>=report['started'])
        for image in report['screenshots']:
            file=close.parent/image['file']
            assert digest(file)==image['sha256'] and file.stat().st_size==image['bytes']
        if ok:
            assert report['views'] and report['screenshots'] and not any(report.get(k) for k in ('failure','errors','failed'))
        else:
            msg=(report.get('failure') or '').split('\n',1)[0].strip()
            if not no_finish:assert msg and msg in (close.parent/'run.log').read_text()
            if unfinished:
                assert digest(rp)=='897c5f0d3e5582ddc5825c1a0a0d051c95d4f6ea159ed5a6ca3a03dd448d237c'
                assert not msg and report['screenshots']==[] and len(report['views'])==1
                view=report['views'][0]; point=report['realBeacon']
                assert view['asset']['visible'] and view['asset']['triangles']==6112 and view['asset']['verifiedAsset']['sha256']=='7dc9f26faf53af0ffd67f8c8a0a0c3ec8b4bc0c9fc731b532ddf8da22e29eba8'
                assert point['pointer']['trusted'] and point['action']=='physical canvas mouse click' and point['landed']==report['id']==view['pick']
                assert (close.parent/'run.log').read_text()=='[map] map-beacon-return\n'
            elif no_finish or msg in ('cdpSession.detach: Target page, context or browser has been closed','cdpSession.send: Target page, context or browser has been closed'):
                assert phase=='architecture' and report.get('browserCrash') is True and report.get('incompleteAtNodeExit') is True
                assert not report['screenshots'] and len(report['views'])==1 and report['views'][0]['view']=='map-street-facade'
                assert report['views'][0]['asset']['visible'] and report['views'][0]['asset']['triangles']==6112
                if no_finish:assert not msg and (close.parent/'run.log').read_text()=='[map] map-street-facade\n'
            elif msg=="TypeError: Cannot read properties of undefined (reading 'file')":
                assert row['phase']=='before' and len(report['screenshots'])==len(report['views'])==1
                view=report['views'][0]
                assert view['view']=='map-before' and view['contextLost'] is False and view['glError']==0
                assert view['labels']==283 and view['route'].startswith('#landmark=huangpu-asia-realty-sichuan-front&mode=overview')
            elif msg=='AssertionError [ERR_ASSERTION]: Expected values to be strictly equal:':
                assert phase=='distant' and report['screenshots']==[] and len(report['views'])==1
                view=report['views'][0]
                assert view['view']=='map-distant' and view['pick'] is None and view['asset']['visible'] and view['asset']['triangles']==2232 and view['asset']['variant']=='distant'
                assert view['route']=='#landmark='+report['id']+'&mode=overview' and ('+ null\n- '+repr(report['id'])) in report['failure']
            elif msg.startswith('AssertionError [ERR_ASSERTION]: Scene never downloaded '):
                assert msg.endswith('assets/city-detail/macros/14-13720-6694/near/3_-3-s1-s1.glb.gz')
                assert row['phase']=='before' and len(report['views'])==len(report['screenshots'])==1
            elif msg=='cdpSession.detach: Protocol error (Target.detachFromTarget): No session with given id':
                assert phase in ('touch','architecture') and report['screenshots']==[]
                if phase=='architecture':
                    diagnosis=read(close.parent/'renderer-diagnostics.json')
                    assert diagnosis['url'].endswith('#landmark='+report['id']+'&mode=overview')
                    attachment=next(e for e in diagnosis['events']if e.get('method')=='Target.attachedToTarget' and e['params']['targetInfo']['targetId']==diagnosis['target'])
                    assert any(e.get('method')=='Inspector.targetCrashed'and e.get('sessionId')==attachment['params']['sessionId']for e in diagnosis['events'])
                    assert report['views'][0]['asset']['visible']and report['views'][0]['view']=='map-street-facade'
                    forced=read(close.parent/'close-after-crash.json')
                    assert forced['request']=={'id':1,'method':'Browser.close'} and diagnosis['at']<forced['at']<report['finished']
                else:
                    assert phase=='touch' and report['browserCrash'] is True and report['incompleteAtNodeExit'] is True
                    point=report['realBeacon'];assert point['pointer']['trusted'] and point['pointer']['type']=='touch' and point['landed']==report['id']
                    assert report['reopenedPointerDestination']['status']==200 and report['reopenedPointerDestination']['pointerId']==report['id'] and not report['screenshots']
                    forced=read(close.parent/'close-after-crash.json')
                    assert forced['request']=={'id':1,'method':'Browser.close'} and forced['driver']==digest(source) and forced['at']<report['finished']
            else:
                assert 'Target crashed' in msg
            files={p.name for p in close.parent.iterdir()}
            if '.gitattributes'in files:
                assert (close.parent/'.gitattributes').read_text().splitlines()==['run.log -whitespace']
                files.remove('.gitattributes')
            assert files=={Path(x).name for x in row['files']}
            failed_files.update((base/x).resolve()for x in row['files'])
        return report
    for attempt,item in book['failed'].items():
        bad=session(item,False)
        assert bad['section'] in book['success']
        good=session(book['success'][bad['section']],True)
        if (bad.get('failure') or '').startswith('AssertionError [ERR_ASSERTION]: Scene never downloaded '):
            matching={v['file']:v for v in good['files']}
            new=matching['assets/city-overrides-v6/14-13720-6694/3_-3-s1-s1.glb.gz']
            old=matching['assets/city-detail/macros/14-13720-6694/near/3_-3-s1-s1.glb.gz']
            assert new['loadedByScene'] and new['sha256']=='1fa4dfadb77963ab1ba1368fc39fd5c4f4170bbd2864435188c5a3c907a5585d'
            assert not old['loadedByScene'] and old['sha256']=='83019a631b04516a73f43ba0c036a5dfa209f9f5ae2fd72ccca13d2e79f79a70'
            assert bad['screenshots']==good['screenshots']
        assert good['catalog']==bad['catalog'] and good['bindings']==bad['bindings'] and good['caseSha256']==bad['caseSha256']
    return failed_files
