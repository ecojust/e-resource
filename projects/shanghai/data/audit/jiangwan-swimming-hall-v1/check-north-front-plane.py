from pathlib import Path
import json,hashlib,numpy as np
from shapely.geometry import Polygon,box,mapping
from shapely.ops import unary_union
from shapely.strtree import STRtree
p=Path('/workspace/jiangwan-swimming-review/actual-triangles/raw-triangles-enu.f64');t=np.frombuffer(p.read_bytes(),dtype='<f8').reshape(-1,3,3);front_y=48.05083801269531;ids=np.flatnonzero(np.max(abs(t[:,:,1]-front_y),axis=1)<1e-6);polys=[];indices=[]
for i in ids:
 g=Polygon(t[i][:,[0,2]])
 if g.area>1e-12:polys.append(g);indices.append(int(i))
u=unary_union(polys);tree=STRtree(polys);pairs=[]
for i,g in enumerate(polys):
 for j in tree.query(g):
  j=int(j)
  if j<=i:continue
  overlap=g.intersection(polys[j])
  if overlap.area>1e-8:pairs.append({'triangles':[indices[i],indices[j]],'area_m2':overlap.area,'bounds_xz':list(overlap.bounds)})
controls={'below_upper_slots_above_arch':box(-6.0,4.8,4.0,8.4),'right_of_arch_wall':box(1.0,1.0,4.0,8.4),'left_of_arch_wall':box(-6.0,1.0,-3.0,8.4)}
checks=[]
for name,g in controls.items():
 missing=g.difference(u);overlap=sum(Polygon(t[row['triangles'][0]][:,[0,2]]).intersection(Polygon(t[row['triangles'][1]][:,[0,2]])).intersection(g).area for row in pairs)
 checks.append({'region':name,'bounds_xz':list(g.bounds),'missing_face_area_m2':missing.area,'coplanar_overlap_pair_area_m2':overlap})
out={'schema':'swimming-independent-north-front-plane-investigation','raw_sha256':'fdabd4072e7af304c0f3367e4c94cbd855a311e838d0bc3c3967753702d122ba','triangle_payload_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'method':'Read previously reviewer-decoded actual ENU triangle payload, select planar north-front triangles by actual vertex coordinates, perform direct XZ union and pair overlap; no model rebuild, original-city rerun or browser.','plane_y_m':front_y,'planar_triangles':len(polys),'union_area_m2':u.area,'sum_area_m2':sum(g.area for g in polys),'controls':checks,'coplanar_overlap_pairs':pairs,'scope':'Geometric evidence only. Does not alone identify a WebGL pixel artifact, source clipping behavior, shadow bias or GPU depth precision.'};Path('/workspace/jiangwan-swimming-review/north-front-plane-investigation.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'planar_triangles':len(polys),'overlap_pairs':len(pairs),'controls':checks,'overlap_bounds':[r['bounds_xz']for r in pairs[:12]]},indent=2))
