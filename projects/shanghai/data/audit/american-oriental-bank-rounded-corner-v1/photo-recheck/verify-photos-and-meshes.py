from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
import json,hashlib,subprocess,requests,io,sys,math,os
import numpy as np
root=Path(__file__).resolve().parents[4]
model='huangpu-american-oriental-bank-rounded-corner'
audit=root/'data/audit/american-oriental-bank-rounded-corner-v1'
source=root/'source/precise'/model
assets=root/'assets/models/candidates'/model
if len(sys.argv)!=2:
 raise SystemExit('Give an output directory for the decoded meshes and the two reports.')
work=Path(sys.argv[1]).resolve()
work.mkdir(parents=True,exist_ok=True)
read=lambda f:json.loads(f.read_bytes());sha=lambda b:hashlib.sha256(b).hexdigest()
m=read(assets/'manifest.json');photos=read(source/'photographic-sources.json')
columns=read(source/'source/window-registration.json')
def load_image(row):
 r=requests.get(row['url'],timeout=40,headers={'User-Agent':'Mozilla/5.0'});r.raise_for_status();b=r.content
 assert sha(b)==row['sha256'];im=Image.open(io.BytesIO(b));assert list(im.size)==row.get('original',row.get('dimensions'))
 return b,{'url':row['url'],'sha256':sha(b),'width':im.width,'height':im.height}
items=[photos['independent'],photos['photos'][0],next(r for r in photos['photos']if r['source']=='bank2025')]
with ThreadPoolExecutor(max_workers=3) as pool: images=list(pool.map(load_image,items))
pa,pb=[np.asarray(Image.open(io.BytesIO(b)).convert('RGB').resize((270,202)),dtype=float)for b,row in images[1:]]
corr=float(np.corrcoef(pa.ravel(),pb.ravel())[0,1]);assert corr>.99
rows=columns['two_image_station_estimates_m'];deviations=np.abs(np.array(rows['2015'])-np.array(rows['2023']))
assert len(deviations)==7
corner=read(source/'source/frontage-registration.json');foot=read(source/'footprint-review.json')
for role in ['full','lod']:
 a=m['assets'][role];f=work/('decoded-'+role+'.glb');subprocess.run(['node',root/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs',assets/a['file'],f,root/'vendor/meshopt_decoder.module.js'],check=True)
raw=assets/m['assets']['raw']['file']
res=work/'actual-traced-surfaces.json';subprocess.run([sys.executable,'-B',audit/'verify-export.py','--raw',raw,'--full',work/'decoded-full.glb','--lod',work/'decoded-lod.glb','--manifest',assets/'manifest.json','--out',res],check=True)
real=read(res);orig=read(audit/'preflight/rays.json')
assert real['passed'] and real['raw_and_full_first_hits_equal']
for role,rr in real['results'].items():
 prior=orig['results'][role];assert rr['passed'] and rr['ray_count']==prior['ray_count']==282 and rr['atlas_sha256']==prior['atlas_sha256'] and rr['rays']==prior['rays']
report={'model':model,'model_scope':'弧形转角及两端紧邻街面','source_way':corner['source_way'],'arc_radius_m':corner['arc_radius_m'],'arc_length_m':columns['arc_length_m'],'photos_reread':[v for b,v in images],'2023_2025_thumbnail_rgb_correlation':corr,'2015_2023_absolute_window_station_differences_m':deviations.tolist(),'window_station_median_difference_m':float(np.median(deviations)),'window_station_max_difference_m':max(deviations),'surface_rays':{k:v['ray_count']for k,v in real['results'].items()},'mesh_digests':{k:{'source':v['packed_sha256'],'decoded':v['sha256'],'triangles':v['triangles']}for k,v in real['results'].items()},'full_trace_sha256':sha(res.read_bytes()),'prior_trace_sha256':sha((audit/'preflight/rays.json').read_bytes())}
(work/'photo-and-mesh-recheck.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if 'difference' in k or k=='surface_rays'}))
