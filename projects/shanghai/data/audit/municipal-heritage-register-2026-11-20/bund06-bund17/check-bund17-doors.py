"""Read the V4.4 mesh itself at the two photographed ground-floor doors."""
from pathlib import Path
import runpy,json,hashlib,collections,argparse,subprocess,tempfile
import numpy as np
args=argparse.ArgumentParser(description=__doc__);args.add_argument('--output',required=True,type=Path);options=args.parse_args()
root=Path(__file__).resolve().parents[6]
revision='2de028ea0d545643b95fd5ee1d12db26bb5d7b60'
scratch=tempfile.TemporaryDirectory();base=Path(scratch.name)
for name,original in [('bund17-original.glb','assets/models/bund/bund17.glb'),('news-footprint.json','source/bund/bund_classics/photo-v4.4/news-footprint.json')]:
 (base/name).write_bytes(subprocess.check_output(['git','show',revision+':projects/shanghai/'+original],cwd=root))
resource=root/'projects/shanghai/data/audit/postal-office-v1/independent-glb-review-helpers.py'
scene=runpy.run_path(str(resource))['SerialScene'](base/'bund17-original.glb')
poly=np.array(json.loads((base/'news-footprint.json').read_bytes())['polygon_local_east_north']);a,b=poly[2],poly[3]
t=(b-a)/np.linalg.norm(b-a);n=np.array([t[1],-t[0]]);mid=(a+b)/2;L=np.linalg.norm(b-a);wc=L/2-3.55/2
rows=[]
for side in (-1,1):
 records=[]
 for z in (.72,1.05,1.44,1.82,2.20,2.58):
  for off in (-.77,-.49,-.22,-.045,.045,.22,.49,.77):
   u=side*wc+off;hit=scene.ray([*(mid+t*u+n*1.2),z],[*(-n),0],4.)
   records.append({'u_offset':off,'z_m':z,'material':hit['material']if hit else None,'outward_m':round(1.2-hit['distance_m'],4)if hit else None})
 rows.append({'u_center_m':side*wc,'rays':records,'materials':dict(collections.Counter(r['material'] for r in records))})
out={'id':'bund17','baseline_commit':'2de028ea0d545643b95fd5ee1d12db26bb5d7b60','raw_sha256':hashlib.sha256((base/'bund17-original.glb').read_bytes()).hexdigest(),'triangles':len(scene.tri),'front_segment_index':2,'front_length_m':L,'surface_ray_count':sum(len(r['rays']) for r in rows),'panels':rows,'material_names':scene.materials}
options.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(out['triangles'],out['surface_ray_count'],[(r['u_center_m'],r['materials'])for r in rows]);print('front ax=',t,'outward',n)
