"""Validate the real map/browser sessions and archive the review of each saved picture."""
from pathlib import Path
import hashlib, json, os, shutil, sys
from guest_result import verify
work=Path('/tmp/shanghai-main-258')
audit=Path('/workspace/e-resource/projects/shanghai/data/audit/ruikang-comprador-residence-v1')
def sha(p):
    with Path(p).open('rb')as source:return hashlib.file_digest(source,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def save(p,j):
    blob=(json.dumps(j,ensure_ascii=False,indent=2)+'\n').encode()
    if p.is_file():assert p.read_bytes()==blob;return
    tmp=p.with_suffix('.writing');tmp.write_bytes(blob);tmp.replace(p)
def cp(src,dst):
    src,dst=Path(src),Path(dst)
    dst.parent.mkdir(parents=True,exist_ok=True)
    if not dst.exists():
        try:os.link(src,dst)
        except OSError:shutil.copy2(src,dst)
    assert sha(src)==sha(dst)
sessions=read(work/'actual-sessions.json')
assert [r['phase']for r in sessions]==['before','phone','desktop']
images={};reports={};ground=None
for physical in sessions:
    phase=physical['phase'];closed=work/'evidence'/phase/'closed.json';report=Path(physical['report'])
    assert read(closed)==physical and physical['node_closed'] and physical['exit_code']==0 and physical['remaining_chromium']==physical['remaining']==[] and physical['chromium_pids']
    assert sha(report)==physical['report_sha256']
    data=read(report);assert data['completed'] and data['section']==phase and data['count']==(292 if phase=='before' else 293)
    assert not data['page_errors'] and not data['http_errors'] and not data['request_failures']
    state=data['states'][0]
    assert state['current_triangles']==0 and not state['current_visible'] and not state['selected_source_cut'] and not state['selected_display_cut']
    if ground is None:ground=state['neighborhood_ground_samples']
    assert state['neighborhood_ground_samples']==ground
    if phase!='before':
        assert state['archive']['closed'] and state['archive']['focus_restored']
        assert state['archive']['title'].endswith('2019年刊载的历史照片，拍摄年份未详') and '中央两层券廊、两侧后退的露廊和深窗' in state['archive']['scope']
    reports[phase]=dict(report=str(report),report_sha256=sha(report),exit=str(closed),exit_sha256=sha(closed))
    for item in data['captures']:
        key=phase+'/'+item['file'];assert key not in images
        file=report.parent/item['file'];assert sha(file)==item['sha256'];images[key]=dict(sha256=sha(file),source=str(file))
desk=read(reports['desktop']['report']);bound=read(work/'bound-inputs.json')
manifest=read(audit/'viewer.json')
downloads={}
for item in desk['saved_downloads']:
    key,= [r for r,x in manifest['downloads'].items()if x['file']==Path(item['file']).name]
    assert key not in downloads and item['sha256']==manifest['downloads'][key]['sha256'] and item['bytes']==manifest['downloads'][key]['bytes']
    downloads[key]=item
assert set(downloads)=={'raw','full','lod','native'} and len(images)==11
if len(sys.argv)==1:print(json.dumps(images,ensure_ascii=False,indent=2));sys.exit(0)
visual=Path(sys.argv[1]);observations=read(visual)['images'];assert set(observations)==set(images)
out=audit/'city-31258'
for key,item in images.items():
    assert observations[key]['sha256']==item['sha256'] and observations[key]['observation'].strip();cp(item['source'],out/key)
for phase,r in reports.items():
    cp(r['report'],out/phase/Path(r['report']).name);cp(r['exit'],out/phase/'closed.json')
for name in ['recheck-port-31258.py','bind-323.py','bind.py','bound-inputs.json','sequence.py','supervisor.json','test-guest.py','window_ticket.py','archive-attempts.py','submit-reviewed.py','check-whole-sites.py','check-historical-map.cjs','guest_result.py','offer-323.py','review.py','257-all-http.json','258-all-http.json','guest-323-recovered.json','offer-323-recovered.py','sequence-recovered.py','supervisor-recovered.json','after-436-recovered.py','review-recovered.py','submit-recovered.py','actual-sessions.json']:
    cp(work/name,out/name)
cp(visual,out/'visual-review.json')
windows={}
for kind,phase in [('native','before'),('viewer','phone')]:
    o,=[f for f in [work/f'323-{kind}-deferred.json',work/f'323-{kind}-returned.json']if f.exists()]
    d=read(o);assert d['host']==258 and d['phase']==kind and d['host_closed_sha256']==reports[phase]['exit_sha256']
    if d.get('actual_receipt'):
        result=Path(d['actual_receipt']);assert sha(result)==d['sha256'];v=verify(kind,Path(d['host_closed']),result)
        assert (v=='complete')==bool(d.get('passed'))
    else:assert d['missing'] and d['deferred'] and not d['native_started'] and not d['viewer_started']
    cp(o,out/o.name);windows[kind]=dict(path=str(o),sha256=sha(o))
release=dict(order=258,passed=True,exit=0,exit_code=0,remaining=[],remaining_chromium=[],after_real_screenshot_review=True,views_reviewed=True,all_captures_visually_reviewed=True,finished=sessions[-1]['finished'],final_closed_at=sessions[-1]['finished'],visual_review_sha256=sha(visual),screenshots=images,reports=reports,receipts=reports,actual_saved_downloads=downloads,real_browser_process_exits={x['phase']:x for x in sessions},guest_323=windows)
guest=Path('/tmp/hujiang433/development-native/258-development-returned.json');witness=read(guest)
assert witness['host_receipt_sha256']==sha(work/'evidence/desktop/closed.json') and witness['previous_sha256']==sha(work/'actual-sessions.json') and witness['all_children_exited'] and witness['remaining_children']==[]
release['guest_433']={'file':str(guest),'sha256':sha(guest),'outcome':witness}
save(out/'results.json',release);save(work/'258-map-slot-released.json',{**release,'results_sha256':sha(out/'results.json')})
