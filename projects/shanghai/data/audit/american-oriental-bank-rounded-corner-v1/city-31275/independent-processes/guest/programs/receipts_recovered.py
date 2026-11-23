"""Verify both actual 275 map exits and the 339/340 physical author and distribution records."""
from pathlib import Path
from hashlib import file_digest
import os,json
HERE=Path('/tmp/liuyazi340/mapping/handoff'); WORK=HERE.parents[1]; PROJECT=Path('/workspace/e-resource/projects/shanghai'); FAMILY=Path('/tmp/shanghai-yongjia-porch')
ID='huangpu-liu-yazi-residence-fuxing-517';PRIOR_ID='huangpu-fuxing-garden-north-house-east-portico';TAG='liu-yazi-residence-fuxing-517-v1';PRIOR=Path('/tmp/fuxing-garden339');SLOTS=Path('/tmp/shanghai-main-275/evidence');ASSETS=PROJECT/'assets/models/candidates'/ID;AUDIT=PROJECT/'data/audit'/TAG
ROLES={'native','raw','full','lod'}
def read(path):return json.loads(Path(path).read_bytes())
def digest(path):
    with Path(path).open('rb') as f:return file_digest(f,'sha256').hexdigest()
def write(path,document):
    data=(json.dumps(document,ensure_ascii=False,indent=2)+'\n').encode();p=Path(path)
    if p.exists():assert p.read_bytes()==data,p;return
    temp=p.with_suffix(p.suffix+'.'+str(os.getpid())+'.new');temp.write_bytes(data);os.replace(temp,p)
def frozen():
    contract=read(HERE/'dispatch-recovered.json');assert contract['order']==340 and contract['id']==ID and contract['physical_map_order']==275
    historical=read(contract['recovery_evidence'])
    assert historical['original_files_unavailable']==contract['historical_inputs_unavailable']
    assert historical['original_dispatch_sha256']==digest(HERE/'dispatch-contract.json')
    for p,sig in contract['programs_and_inputs'].items():
        assert digest(p)==sig,p
    return contract

def finished(path,order):
    r=read(path);assert r['order']==order and r['passed'] and r['exit']==r.get('exit_code',0)==0 and r['all_processes_closed'] and r['wrapper_closed'];assert r['remaining']==[]
    return r

def verify_assets(order,asset_rows):
    model=PRIOR_ID if order==339 else ID;root=PROJECT/'assets/models/candidates'/model
    manifest=root/'manifest.json';doc=read(manifest)
    assert doc['id']==model and set(doc['assets'])==set(asset_rows)==ROLES
    for k,r in doc['assets'].items():
        p=root/r['file'];source=asset_rows[k]
        assert all(source[t]==r[t] for t in ('sha256','file','bytes')) and digest(p)==r['sha256'] and p.stat().st_size==r['bytes'],k
    return manifest,doc

def native(path,order):
    r=finished(path,order);assert r['remaining_blender']==r['remaining_oidn']==[] and len(set(r['blender_pids']))>=2
    manifest,doc=verify_assets(order,r['assets']);assert digest(manifest)==r['manifest_sha256']
    if order==340:
        stages=r['native_stages']
        expected=(['reopen-geometry','reopen-materials-cameras'] if frozen().get('accepted_development') else ['render','reopen','denoise'])
        assert [stage['stage'] for stage in stages]==expected and all(x['pid']>0 and x['exit']==0 and x['finished']>=x['started'] for x in stages)
    audit=PROJECT/'data/audit'/('fuxing-garden-east-portico-v1' if order==339 else TAG)
    assert r['geometry_native_sha256']==digest(audit/'geometry-native.json')
    scanned=read(audit/'geometry-native.json');assert scanned['meshopt_decoded_oriented_surfaces_match'] and scanned['native_reopened_and_compared']['match_raw'] and scanned['native_reopened_and_compared']['mesh_count']==r['group_count']
    return r

def raw(path,order):
    r=read(path);snapshot=Path(r['snapshot']);assert r['order']==order and r.get('passed',True) and digest(snapshot)==r['sha256'];s=read(snapshot)
    cat='data/candidate-city-integrations.json';p=Path(r['root'])/'projects/shanghai'/cat
    assert digest(p)==r['catalog_sha256']==s['files'][cat];c=read(p)
    assert c['models'][-1]['id']==(PRIOR_ID if order==339 else ID) and c['resulting_city_count']==s['resulting_count']==r['count']==order+35
    assert len(s['files'])==r['input_count'];return r

def completed_viewer(path,order):
    r=finished(path,order);assert r['node']>0 and r['chromium_pids'] and r['remaining_chromium']==[]
    report=Path(r['report']);assert digest(report)==r['receipt_sha256'] and r.get('report_sha256',r['receipt_sha256'])==r['receipt_sha256'];v=read(report)
    assert v['passed'] and v['base'].rstrip('/')==f'http://127.0.0.1:{31000+order}' and not v['pageErrors']
    assert len(v['views'])==r['views']==6 and len(v['downloads'])==r['downloads']==4
    if order==340:
        expected={(770,'full',mode) for mode in ('front','oblique','above')}
        expected|={(770,'lod','front'),(390,'full','front'),(390,'lod','front')}
        assert {(x['viewport']['width'],x['role'],x['mode']) for x in v['views']}==expected
        assert len({x['filename'] for x in v['views']})==6
    for view in v['views']:
        assert digest(report.parent/view['filename'])==view['sha256']
    manifest,doc=verify_assets(order,v['downloads']);assert v['manifestSHA256']==digest(manifest)
    return r

def real_city_exit(kind,source,slots=None):
    assert kind in ('native','viewer')
    slots=Path(slots or SLOTS)
    phase='before' if kind=='native' else 'phone'
    number=274 if phase=='before' else 275
    assert os.path.samefile(source,slots/phase/'closed.json')
    ticket=read(source)
    assert ticket['order']==275 and ticket['phase']==phase and ticket['exit']==ticket['exit_code']==0
    assert ticket['node_closed'] and type(ticket['node']) is int and ticket['node']>0
    assert ticket['chromium_pids'] and all(type(n)is int and n>0 for n in ticket['chromium_pids'])
    assert ticket['remaining']==ticket['remaining_chromium']==[]
    folder=slots/'275'/('before' if phase=='before' else 'separate/phone')
    rp=folder/('control-browser.json' if phase=='before' else 'main-browser.json')
    assert os.path.samefile(ticket['report'],rp) and digest(rp)==ticket['report_sha256']
    assert digest(folder/'closed.json')==digest(source)
    driver=Path('/workspace/shanghai-publisher-preservation/city-275/340-host-drivers')/ticket['driver_sha256']
    assert driver.name in frozen()['approved_host_drivers']
    physical_driver=folder/'actual-driver.cjs'
    if physical_driver.is_file():assert digest(physical_driver)==digest(driver)
    spec=slots.parent/'case275.json'
    program=read(slots.parent/(str(number)+'-production.json'))
    v=read(rp)
    assert v['id']=='huangpu-american-oriental-bank-rounded-corner' and v['completed'] and v['section']==phase and not v.get('failure')
    assert v['mode']==('frozen-before' if phase=='before' else 'delivered')
    assert v['server'].rstrip('/')==f'http://127.0.0.1:{31000+number}' and not v['errors'] and not v['failed']
    assert v['catalog']=={'sha256':program['files']['data/candidate-city-integrations.json'],'count':program['resulting_count']}
    assert v['caseSha256']==digest(spec) and v['scriptSha256']==ticket['driver_sha256']==digest(driver)
    assert [row['file'] for row in v['screenshots']]==(['map-before.png'] if phase=='before' else ['map-mobile.png'])
    case=read(spec)
    assert len(v['views'])==1
    state=v['views'][0]
    assert state['view']==('map-before' if kind=='native' else 'map-mobile')
    assert state['glError']==0 and state['contextLost'] is False and state['labels']==v['catalog']['count']
    peers=[owner for entry in case['existing_group_sources'] for owner in entry['sources']]
    expected=peers+([] if kind=='native' else [case['owner']])
    assert sorted(state['group']['clip_feature_local_ids'])==sorted(expected)
    assert all(item['state'].get('candidateModel') is not True for item in state['neighbors'] if item['local_id'] not in peers)
    if kind=='native':
        assert state['clip'] is None and state['sections']==state['bands']==[]
    else:
        assert state['clip']['owner']=={'macro_id':'14-13720-6693','feature_local_id':case['owner']}
        assert state['asset']['id']==state['pick']==case['id'] and state['asset']['variant']=='full'
        assert v['directoryPointer']['trusted'] and v['directoryPointer']['type']=='touch' and v['directoryPointer']['id']==case['id']
    for row in v['screenshots']:
        f=folder/row['file']
        assert f.stat().st_size==row['bytes'] and digest(f)==row['sha256']
    return ticket

def prereqs(kind,source):
    cfg=frozen();host=real_city_exit(kind,source);parent=raw(PRIOR/'raw-339-confirmed.json',339);native(PRIOR/'native-closed.json',339)
    parent_ticket=Path(cfg['previous_host_ticket'])
    predecessor=read(parent_ticket)
    assert predecessor['order']==339 and predecessor['host']==274
    for part in ('author','admit','dispatch'):
        assert digest(predecessor[part])==predecessor[part+'_sha256']
    assert digest(parent_ticket)==cfg['previous_host_receipt_sha256']
    parent_author=read(predecessor['author'])
    assert parent_author['order']==339 and parent_author['id']==PRIOR_ID

    grant=dict(order=340,host=275,physical_map_order=275,kind=kind,receipt=str(source),sha256=digest(source),report_sha256=host['report_sha256'],previous_native_sha256=digest(PRIOR/'native-closed.json'),parent_snapshot_sha256=parent['sha256'],author_review_sha256=cfg['author_review_sha256'])
    grant['previous_host_binding_sha256']=digest(parent_ticket)
    if kind=='viewer':
        completed_viewer(PRIOR/'viewer-closed.json',339);native(WORK/'native-closed.json',340);child=raw(WORK/'raw-340-confirmed.json',340)
        import sys
        sys.path.insert(0,str(FAMILY));from common import canon,full,sha
        comp=read(FAMILY/'scenes/340-comparison.json');assert comp['passed'] and comp['order']==340 and comp['production_receipt_sha256']==sha(canon(full(340)))
        grant.update(previous_viewer_sha256=digest(PRIOR/'viewer-closed.json'),own_snapshot_sha256=child['sha256'],highest_stage=comp['production_receipt_sha256'])
    return grant
