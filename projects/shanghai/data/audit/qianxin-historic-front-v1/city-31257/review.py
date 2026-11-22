"""Validate the real map/browser sessions and archive the review of each saved picture."""
from pathlib import Path
import hashlib, json, os, shutil, sys
work=Path('/tmp/shanghai-main-257')
audit=Path('/workspace/e-resource/projects/shanghai/data/audit/qianxin-historic-front-v1')
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
    data=read(report);assert data['completed'] and data['section']==phase and data['count']==(291 if phase=='before' else 292)
    assert not data['page_errors'] and not data['http_errors'] and not data['request_failures']
    state=data['states'][0]
    assert state['current_triangles']==0 and not state['current_visible'] and not state['selected_source_cut'] and not state['selected_display_cut']
    if ground is None:ground=state['neighborhood_ground_samples']
    assert state['neighborhood_ground_samples']==ground
    if phase!='before':
        assert state['archive']['closed'] and state['archive']['focus_restored']
        assert state['archive']['title']==state['selected_name']+' · 2015年照片' and '上下两排各三券，下排有三段透空石栏' in state['archive']['scope']
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
    assert item['saveAsVerified'] and Path(item['saved'])==Path('saved')/Path(item['file']).name
    saved=Path(reports['desktop']['report']).parent/item['saved']
    assert saved.stat().st_size==item['bytes'] and sha(saved)==item['sha256']
    downloads[key]=item
assert set(downloads)=={'raw','full','lod','native'} and len(images)==11
if len(sys.argv)==1:print(json.dumps(images,ensure_ascii=False,indent=2));sys.exit(0)
visual=Path(sys.argv[1]);observations=read(visual)['images'];assert set(observations)==set(images)
out=audit/'city-31257'
for key,item in images.items():
    assert observations[key]['sha256']==item['sha256'] and observations[key]['observation'].strip();cp(item['source'],out/key)
for phase,r in reports.items():
    assert sha(Path(r['report']).parent/'actual-driver.cjs')==read(r['report'])['script_sha256']
    cp(Path(r['report']).parent/'actual-driver.cjs',out/phase/'actual-driver.cjs')
    report_path=Path(r['report']);document=read(report_path)
    if document.get('displayCaptures'):
        from PIL import Image,ImageChops
        calibration=document['viewportCalibration'];source=report_path.parent/calibration['file']
        assert sha(source)==calibration['sha256'];cp(source,out/phase/source.name)
        assert len(document['displayCaptures'])==len(document['captures'])
        for display,capture in zip(document['displayCaptures'],document['captures'],strict=True):
            assert display['file']==capture['file'] and display['sha256']==capture['sha256']
            x,y,width,height=display['rect'];assert [x,y,width,height]==[calibration[k] for k in ('x','y','width','height')]
            parent=report_path.parent/display['root'];child=report_path.parent/capture['file'];assert sha(parent)==display['root_sha256']
            with Image.open(parent) as large,Image.open(child) as small:
                assert small.size==(width,height) and not ImageChops.difference(large.crop((x,y,x+width,y+height)).convert('RGB'),small.convert('RGB')).getbbox()
            cp(parent,out/phase/parent.name)
    cp(r['report'],out/phase/Path(r['report']).name);cp(r['exit'],out/phase/'closed.json')
for name in ('bind.py','bound-inputs.json','sequence.py','run-322.py','check-whole-sites.py','check-historical-map.cjs','review.py','archive-attempts.py','submit-reviewed.py','256-all-http.json','257-all-http.json','actual-sessions.json'):
    cp(work/name,out/name)
cp(visual,out/'visual-review.json')
windows={}
for kind,phase in [('native','before'),('viewer','phone')]:
    o=Path('/tmp/changshu322')/(kind+'-closed.json')
    row=read(o);assert row['host']==257 and row['order']==322 and row['host_receipt_sha256']==reports[phase]['exit_sha256'] and row['host_report_sha256']==reports[phase]['report_sha256']
    assert row['passed'] and row['wrapper_closed'] and row['exit']==0 and not row['remaining']
    cp(o,out/'guest-322'/o.name);windows[kind]=dict(path=str(o),sha256=sha(o))
release=dict(order=257,passed=True,exit=0,exit_code=0,remaining=[],remaining_chromium=[],after_real_screenshot_review=True,views_reviewed=True,all_captures_visually_reviewed=True,finished=sessions[-1]['finished'],final_closed_at=sessions[-1]['finished'],visual_review_sha256=sha(visual),screenshots=images,reports=reports,receipts=reports,actual_saved_downloads=downloads,real_browser_process_exits={x['phase']:x for x in sessions},guest_322=windows)
save(out/'results.json',release);save(work/'257-map-slot-released.json',{**release,'results_sha256':sha(out/'results.json')})
