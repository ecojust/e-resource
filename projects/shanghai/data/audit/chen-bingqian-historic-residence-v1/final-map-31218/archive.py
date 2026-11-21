"""Verify camera captures, original archive assets and physical exits before issuing the release handoff."""
import argparse,hashlib,json,os,shutil,subprocess
from datetime import datetime,timezone
from pathlib import Path

here=Path(__file__).resolve().parent
audit=Path('/workspace/e-resource/projects/shanghai/data/audit/chen-bingqian-historic-residence-v1')
dest=audit/'final-map-31218'
p=argparse.ArgumentParser();p.add_argument('--reviewed',action='store_true');p.add_argument('--submit',action='store_true');args=p.parse_args()
def read(f):return json.loads(f.read_bytes())
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def copy(f,path=None):
    to=dest/(path or f.name);to.parent.mkdir(parents=True,exist_ok=True)
    if not to.exists():
        try:os.link(f,to)
        except OSError:shutil.copyfile(f,to)
    assert sha(to)==sha(f)
def write(f,row):
    if f.exists():assert read(f)==row;return
    temp=f.with_suffix('.pending');temp.write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n');temp.replace(f)
b=read(here/'bound-inputs.json');pin=read(here/'frozen-inputs.json')
for name,digest in pin['files'].items():assert sha(here/name)==digest;copy(here/name)
copy(here/'frozen-inputs.json');copy(here/'three-scene-outcomes.json')
offer=read(here/'341-completed-offer.json');guest_return=Path(offer['physical_return'])
assert sha(guest_return)==offer['return_sha256'] and read(guest_return)['source_sha256']==sha(here/'three-scene-outcomes.json') and not read(guest_return)['remaining']
copy(here/'341-completed-offer.json');copy(guest_return,'341-offline-actual-return.json')
for previous in sorted((here/'earlier-attempts').glob('desktop-*/failed-exit.json')):
    d=read(previous);assert d['exit_code']!=0 and d['node_closed'] and not d['remaining_chromium']
    for name in ('failed-exit.json','after.json','stdout.log','desktop-location.png'):
        f=previous.parent/name
        if f.is_file():copy(f,'earlier-attempts/'+previous.parent.name+'/'+name)
for name in ('217','218'):
    for f in ('comparison','all-http'):
        copy(Path('/tmp/shanghai-yongjia-porch/scenes')/f'{name}-{f}.json')
rows=read(here/'three-scene-outcomes.json')
assert [v['tag'] for v in rows]==['before','phone','desktop']
sets=[];artifacts=[];prev=Path('/tmp/shanghai-main-217/217-map-slot-released.json')
for row in rows:
    n=217 if row['tag']=='before'else 218;folder=here/'sessions'/row['tag'];done=folder/'closed.json';report=Path(row['report']);body=read(report);sig=b['origins'][str(n)]
    assert read(done)==row and sha(report)==row['report_sha256'] and sha(prev)==row['previous_session_sha256']
    assert row['exit_code']==0 and not row['remaining_chromium'] and row['observed_chromium'] and row['cdp_closed']
    assert body['passed'] and body['browser_closed'] and body['base']==sig['url'] and body['catalog']==sig['catalog_sha256'] and body['count']==sig['count']
    assert all(sig['files'][f]['sha256']==h for f,h in body['signed_responses'].items())
    assert body['script_sha256']==row['script_sha256']==pin['files']['check-historical-desktop.cjs' if row['tag']=='desktop' else 'check-historical-map.cjs']
    assert body['signed_input_sha256']==pin['files']['bound-inputs.json']
    assert not(body['page_errors'] or body['request_failures'] or body['http_errors'])
    assert len(body['states'])==1 and body['trusted_inputs'][0]['trusted']
    state=body['states'][0];sets.append(state['ground_witnesses']);assert len(sets[-1])==8 and not(state['current_triangles'] or state['selected_source_cut']or state['selected_display_cut']or state['selected_current_entry'])
    if n==218:assert state['archive']['closed'] and state['archive']['ground_after_return']==sets[0] and state['walk_disabled']
    for f in (report,done):copy(f,row['tag']+'/'+f.name)
    for item in body['captures']:
        pic=folder/item['file'];assert sha(pic)==item['sha256'] and pic.stat().st_size==item['bytes'] and not item['gl']['lost'] and item['gl']['error']==0
        copy(pic,row['tag']+'/'+pic.name);artifacts.append({'file':row['tag']+'/'+pic.name,'sha256':sha(pic)})
    if row['tag']=='desktop':
        four=body['saved_downloads'];assert len({k['sha256']for k in four})==4 and {k['sha256']for k in four}=={v['sha256']for v in read(audit/'viewer.json')['downloads'].values()}
    prev=done
assert len(artifacts)==7 and sets[0]==sets[1]==sets[2]
summary={'order':218,'passed':True,'origins':[31217,31218],'directory_counts':[254,255],'images':artifacts,'existing_ground':sets[0],'archive_source':b['archive'],'downloads':four,'physical_exits':rows,'last_closed_at':rows[-1]['end']}
write(dest/'results.json',summary)
if args.reviewed:
    note=here/'observations.md';assert note.is_file() and note.read_text().strip()
    copy(note);receipt=here/'218-map-slot-released.json'
    if not receipt.exists():write(receipt,{'order':218,'passed':True,'exit_code':0,'all_processes_closed':True,'all_captures_visually_reviewed':True,'remaining_chromium':[],'actual_closed_utc':rows[-1]['end'],'captured':len(artifacts),'physical_exits':rows,'report':str(dest/'results.json'),'report_sha256':sha(dest/'results.json'),'review_sha256':sha(note),'issued':datetime.now(timezone.utc).isoformat()})
    else:assert read(receipt)['report_sha256']==sha(dest/'results.json')
if args.submit:
    assert args.reviewed
    doc=audit/'README.md';s=doc.read_text().rstrip();section='## 正式地图入口与历史影像\n\n'+note.read_text().strip()+'\n\n[前后两站、触屏和桌面的实际记录](final-map-31218/results.json) · [街区及七栋现存建筑](final-map-31218/existing-city-geometry.json) · [桌面近景](final-map-31218/desktop/desktop-archive-near.png) · [手机远景](final-map-31218/phone/mobile-archive-lod.png)'
    if '## 正式地图入口与历史影像' not in s:
        tmp=doc.with_name('.README.218.pending');tmp.write_text(s+'\n\n'+section+'\n');tmp.chmod(doc.stat().st_mode);tmp.replace(doc)
    else:assert section in s
    subprocess.run(['python','-B','/tmp/shanghai-signed-release-inbox/submit.py','218','README.md','viewer.json','final-map-31218',*[x['filename']for x in read(audit/'viewer.json')['views']]],check=True)
