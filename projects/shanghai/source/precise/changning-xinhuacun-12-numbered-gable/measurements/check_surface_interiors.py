"""Compare first opaque mesh hits to the independent photographic surface interiors."""
import argparse,hashlib,json,math
from pathlib import Path
from photo_ray_mesh import ProjectedMesh,load_triangles
import numpy as np
here=Path(__file__).parent
q=argparse.ArgumentParser()
q.add_argument('mesh',type=Path);q.add_argument('cameras',type=Path);q.add_argument('output',type=Path);q.add_argument('--geometry',type=Path);q.add_argument('--pixels',type=Path,default=here/'independent-surface-interiors.json')
args=q.parse_args()
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
pixels=json.loads(args.pixels.read_bytes());stations=json.loads(args.cameras.read_bytes())
material_groups={'rough':('pebble','roughcast','rough render'),'brick':('brick',),'window':('joinery','glass','casement','green frame'),'trim':('cement','precast','rendered stone'),'pipe':('rainwater','cast iron'),'digit':('numeral','digit'),'roof':('roof','terracotta','tile')}
if args.geometry:
 mesh=ProjectedMesh(args.mesh,json.loads(args.geometry.read_bytes()))
else:
 mesh=ProjectedMesh.__new__(ProjectedMesh);mesh.tri,idx,names,mesh.asset=load_triangles(args.mesh);mesh.labels=idx;mesh.parts=[{'material':m,'label':None} for m in names]
offsets=sorted([(math.hypot(x,y),x,y)for x in range(-12,13)for y in range(-12,13)if x*x+y*y<=144])
out={'mesh':mesh.asset,'camera_sha256':sha(args.cameras),'points_sha256':sha(args.pixels),'geometry_sha256':sha(args.geometry) if args.geometry else None,'stations':{}}
for name,group in pixels['photographs'].items():
 mesh.station(stations[name]);points=[]
 def expect(h,k):return h and any(m in h['material'].lower() for m in material_groups[k])
 for p in group['points']:
  u,v=p['uv'];k=p['expected'];center=mesh.hit(u,v);match=None
  for d,dx,dy in offsets:
   hit=center if not d else mesh.hit(u+dx,v+dy)
   if expect(hit,k):match={'distance_px':round(d,3),'offset':[dx,dy],'hit':hit};break
  points.append({**p,'direct':bool(expect(center,k)),'center':center,'nearest_within_12':match})
 def total(r):return sum(m['nearest_within_12'] is not None and m['nearest_within_12']['distance_px']<=r for m in points)
 out['stations'][name]={'photo_sha256':group['source_sha256'],'count':len(points),'direct':total(0),'within4':total(4),'within12':total(12),'results':points}
print(args.mesh.name,[(k,v['count'],v['direct'],v['within4'],v['within12'])for k,v in out['stations'].items()],flush=True)
args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
