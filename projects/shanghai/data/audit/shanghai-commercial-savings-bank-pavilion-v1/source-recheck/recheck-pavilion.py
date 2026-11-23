"""Recompute the three mesh inspections and compare the two aerial eave outlines."""
from hashlib import sha256
from pathlib import Path
import argparse, json, math, subprocess,sys
from shapely.geometry import Polygon

root=next((parent for parent in Path(__file__).resolve().parents if (parent/'assets/models/candidates').is_dir()),Path.cwd())
parser=argparse.ArgumentParser()
parser.add_argument('--project',type=Path,default=root)
parser.add_argument('--out',required=True,type=Path)
p=parser.parse_args()
P=p.project; ID='huangpu-shanghai-commercial-savings-bank-pavilion'
audit=P/'data/audit/shanghai-commercial-savings-bank-pavilion-v1/preflight'
source=P/'source/precise'/ID
read=lambda f:json.loads(f.read_bytes())
digest=lambda f:sha256(f.read_bytes()).hexdigest()
p.out.mkdir(exist_ok=True,parents=True)
fresh=p.out/'actual-mesh-rays.json'
subprocess.run([sys.executable,'-B',source/'source/check_surfaces.py','--out',fresh],check=True)
legacy=read(audit/'real-asset-probes.json'); observed=read(fresh)
assert legacy['results']==observed['results']
assert all(v['passed'] and len(v['samples'])==91 for v in observed['results'].values())
images=[('Esri',[[99,222],[246,172]],[[112,182],[168,161],[177,191],[119,210]]),('satellite',[[137,231],[276,179]],[[172,169],[222,149],[233,177],[178,201]])]
signed=read(audit/'orthophoto-registration.json'); length=signed['cornice_length_reference_m']
results=[]
for i,(name,datum,ring) in enumerate(images):
 (x,y),(x1,y1)=datum
 dx,dy=x1-x,y1-y;factor=length/(dx*dx+dy*dy)
 roof=[(((u-x)*dx+(v-y)*dy)*factor,((u-x)*dy-(v-y)*dx)*factor) for u,v in ring]
 poly=Polygon(roof);center=list(poly.centroid.coords[0]);sx,sy,ex,ey=poly.bounds
 dims=[ex-sx,ey-sy]
 assert math.dist(center,signed['two_image_centres_m'][i])<1e-8
 assert math.dist(dims,signed['two_image_extents_m'][i])<1e-8
 results.append({'source':name,'cornice_pixels':datum,'eave_pixels':ring,'centre_m':center,'eaves_m':dims})
a,b=results
photos=read(source/'reference-review.json')
assert photos['municipal']['items'][0][0]=='4A011'
result={'municipal_id':'4A011','registered_scope':photos['model_scope'],'three_roles':{k:{'sha256':v['sha256'],'passed_rays':sum(r['passed'] for r in v['samples'])}for k,v in observed['results'].items()},'fresh_result_sha256':digest(fresh),'original_result_sha256':digest(audit/'real-asset-probes.json'),'signed_aerial_measurements_sha256':digest(audit/'orthophoto-registration.json'),'cornice_baseline_m':length,'aerial_measurements':results,'between_centres_m':math.dist(a['centre_m'],b['centre_m']),'between_footprint_dimensions_m':[abs(x-y)for x,y in zip(a['eaves_m'],b['eaves_m'])],'source_notes':'两个航片底图均未确定拍摄日期。近代街角照片用于辨认银行主楼，当代屋顶近照与街面照片用于核对亭的窗扇、重檐和脊饰。'}
(p.out/'source-recheck.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
