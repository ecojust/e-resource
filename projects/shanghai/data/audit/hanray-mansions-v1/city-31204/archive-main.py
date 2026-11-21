"""Archive the reviewed entrance, facade and roof views after every browser has exited."""
import json,hashlib,os,shutil,sys
from pathlib import Path
from datetime import datetime,timezone
number=int(sys.argv[1]);cfg={204:('henri204','hanray-mansions-v1','map-main-recessed-entrance',25)}
name,tag,special,num_ground=cfg[number];token=31000+number;q=Path('/tmp')/name/f'final{token}';a=Path('/workspace/e-resource/projects/shanghai/data/audit')/tag/f'city-{token}'
processes=json.loads((q/'all-main-outcomes.json').read_bytes());assert len(processes)==11
a.mkdir(exist_ok=True)
final=[]
for proc in processes:
 assert proc['exit_code']==0 and not proc['remaining_chromium']
 assert not (Path('/proc')/str(proc['pid'])).exists()
 f=Path(proc['report']);j=json.loads(f.read_bytes());assert j['completed'] and not j['failed'] and not j['errors']
 out=a/proc['name'];out.mkdir(exist_ok=True)
 assert j['views'] and len(j['views'])==len(j['screenshots'])
 for s in j['screenshots']:
  img=f.parent/s['file'];assert img.stat().st_size==s['bytes'] and hashlib.file_digest(img.open('rb'),'sha256').hexdigest()==s['sha256']
  target=out/img.name
  if not target.exists():os.link(img,target) if img.stat().st_dev==target.parent.stat().st_dev else shutil.copy2(img,target)
  assert hashlib.file_digest(target.open('rb'),'sha256').hexdigest()==s['sha256']
 assert all(v['glError']==0 and not v['contextLost']for v in j['views'])
 stages={'before':['map-before'],'phone':['map-mobile'],'phone-zoom':['map-mobile-zoom'],'desktop':['map-desktop','map-street-facade',special,'map-stepped-curved-terraces','map-roof','map-distant']}
 original=stages['desktop']
 stages.update(desktop=['map-desktop'],street=['map-street-facade'],paired=['map-street-paired-440'],architecture=[special],terraces=[original[3]],threshold=['map-entrance-and-door-threshold'],roof=['map-roof'],distant=['map-distant'])
 assert [v['view']for v in j['views']]==stages[proc['name']]
 if proc['name']=='distant':
  assert {r['role'] for r in j['savedDownloads']}=={'raw','full','lod','native'}
  assert sum(x['file'].startswith('assets/models/candidates/'+j['id']+'/') for x in j['files'])==4
 if proc['name']=='street':
  assert len(j['ground'])==num_ground and all(v['found']==v['expected']for v in j['ground'])
 target=out/f.name
 if not target.exists():shutil.copy2(f,target)
 assert target.read_bytes()==f.read_bytes()
 final.append({**proc,'report':str(target.relative_to(a)),'sha256':hashlib.file_digest(target.open('rb'),'sha256').hexdigest()})
# The same angular camera and physical viewport document the change from the preceding edition.
from PIL import Image,ImageChops,ImageStat
left_report,= [v for v in final if v['name']=='before'];right_report,=[v for v in final if v['name']=='paired']
left_data=json.loads((a/left_report['report']).read_bytes());right_data=json.loads((a/right_report['report']).read_bytes())
left=next(v for v in left_data['views'] if v['view']=='map-before');right=next(v for v in right_data['views'] if v['view']=='map-street-paired-440')
assert left['viewport']==right['viewport']==[440,380]
for key in ('zoom','pitch','bearing','elevation'):
 assert abs(left['camera'][key]-right['camera'][key])<1e-5,(key,left['camera'],right['camera'])
for coordinate in ('lng','lat'):
 assert abs(left['camera']['center'][coordinate]-right['camera']['center'][coordinate])<1e-8,coordinate
before_image=a/'before'/'map-before.png';after_image=a/'paired'/'map-street-paired-440.png'
with Image.open(before_image)as b,Image.open(after_image)as c:
 assert b.size==c.size==(440,380)
 interior=(66,114,374,266);d=ImageChops.difference(b.convert('RGB').crop(interior),c.convert('RGB').crop(interior))
 mean=ImageStat.Stat(d).mean
 assert max(mean)>0
paired={'before_report_sha256':left_report['sha256'],'after_report_sha256':right_report['sha256'],'before_image_sha256':hashlib.sha256(before_image.read_bytes()).hexdigest(),'after_image_sha256':hashlib.sha256(after_image.read_bytes()).hexdigest(),'viewport':[440,380],'before_camera':left['camera'],'after_camera':right['camera'],'central_image_rectangle':interior,'mean_absolute_rgb_difference_per_channel':mean}
(a/'paired-street-view.json').write_text(json.dumps(paired,indent=2)+'\n')
extra=[]
for mode in ('mouse','touch'):
 folder=q/('physical-'+mode);proc=json.loads((folder/'physical-exit.json').read_bytes());assert proc['exit_code']==0 and not proc['remaining_chromium'] and not (Path('/proc')/str(proc['pid'])).exists()
 r=folder/'main-browser.json';report=json.loads(r.read_bytes());assert report['completed'] and not report['failed'] and not report['errors'] and hashlib.sha256(r.read_bytes()).hexdigest()==proc['sha256']
 choice,=report['physicalSelections'];assert choice['input']==mode and choice['selected']=='xuhui-hanray-mansions'
 dest=a/('physical-'+mode);dest.mkdir(exist_ok=True)
 for f in (r,folder/'physical-exit.json'):
  if not(dest/f.name).exists():shutil.copyfile(f,dest/f.name)
  assert f.read_bytes()==(dest/f.name).read_bytes()
 extra.append({**proc,'name':'physical-'+mode,'report':str((dest/r.name).relative_to(a))})
for local in ('check-hanray-map.cjs','check-map-beacon.cjs','physical-beacon.py','district-and-original-http.json','check-map-inputs.py','confirmed-architectural-ray-views.json','actual-camera-city-triangles.json','special-camera-sightlines.json'):
 f=q/local
 if not (a/local).is_file():shutil.copyfile(f,a/local)
 assert f.read_bytes()==(a/local).read_bytes()
final+=extra
viewer=Path((q/'evidence-root.txt').read_text().strip())/'independent'
vc=json.loads((viewer/'closed.json').read_bytes());vr=json.loads((viewer/'viewer.json').read_bytes());assert vc['passed'] and vc['exit_code']==0 and not vc['remaining_chromium'] and vc['observed_chromium_pid_and_starttime']
assert hashlib.sha256((viewer/'viewer.json').read_bytes()).hexdigest()==vc['report_sha256'] and vr['passed'] and len(vr['views'])==4 and len(vr['downloads'])==4
vd=a/'standalone';vd.mkdir(exist_ok=True)
for item in [viewer/'viewer.json',viewer/'closed.json',*(viewer/v['filename'] for v in vr['views'])]:
 t=vd/item.name
 if not t.exists():
  try:os.link(item,t)
  except OSError:shutil.copyfile(item,t)
 assert item.read_bytes()==t.read_bytes()
for v in vr['views']:assert hashlib.sha256((vd/v['filename']).read_bytes()).hexdigest()==v['sha256']
final.append(dict(name='standalone',pid=vc['node_pid'],exit_code=0,remaining_chromium=[],started_utc=vc['started'],finished_utc=vc['finished'],report='standalone/viewer.json',sha256=vc['report_sha256']))
for name in ['check-final-standalone.py','run-main.py','archive-main.py','isolated-camera-programs.json']:
 f=q/name
 if not(a/name).is_file():shutil.copy2(f,a/name)
 assert f.read_bytes()==(a/name).read_bytes()
done={'order':number,'finished_utc':max(v['finished_utc']for v in final),'checked_utc':datetime.now(timezone.utc).isoformat(),'code':0,'sessions':final}
(a/'map-process-outcomes.json').write_text(json.dumps(done,indent=2)+'\n');print(done['finished_utc'])

release={'order':number,'exit_code':0,'passed':True,'all_captures_visually_reviewed':True,'remaining_chromium':[],'actual_closed_utc':done['finished_utc'],'verified_utc':done['checked_utc'],'normal_directory_origins':[31203,31204],'counts':[240,241],'returned_to':'205','reports':str(a/'map-process-outcomes.json'),'sessions':[{k:item[k] for k in ['name','pid','exit_code','remaining_chromium','finished_utc','sha256']} for item in final]}
target=q.parent/'204-map-slot-released.json'
part=target.with_suffix('.part')
part.write_text(json.dumps(release,indent=2)+'\n')
part.replace(target)
