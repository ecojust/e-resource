"""Probe exported mesh, independently of builder objects: open lattice and stairs."""
import argparse,json
from pathlib import Path
import numpy as np
import trimesh
p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--report',required=True);a=p.parse_args()
s=trimesh.load(a.model,force='scene',process=False);m=trimesh.util.concatenate(tuple(s.geometry.values()))
# One clear lattice cell in each of 20 leaves; ray stops before inset backing.
origins=[]
for center in [-6.68,-3.34,0,3.34,6.68]:
 for j in range(4):origins.append([center+(j-1.5)*.79-(.75-.14)/2+(.75-.14)/12,2.40+.07+(2.65-.14)/32,6.95])
origins=np.asarray(origins);directions=np.tile([0,0,-1],(len(origins),1))
hits,idx,_=m.ray.intersects_location(origins,directions,multiple_hits=True)
depths=np.array([np.min(6.95-hits[idx==i,2]) for i in range(len(origins))]);assert np.allclose(depths,.3375,atol=1e-5),depths
# Top surface of each tread, outside central decorative ramp.
origins=np.array([[1.1,3,20.32-(i+.5)*.30] for i in range(7)])
hits,idx,_=m.ray.intersects_location(origins,np.tile([0,-1,0],(7,1)),multiple_hits=True)
heights=[max(hits[idx==i,1]) for i in range(7)];assert np.allclose(heights,np.arange(1,8)/7,atol=1e-5)
# At the rear intertier band, exactly one material may occupy the outer plane.
# This catches the white-wall/timber coplanar overlap seen in the browser.
counts=[]
for x in [-4.,0.,4.]:
 count=0
 for mesh in s.geometry.values():
  hits,_,_=mesh.ray.intersects_location(np.array([[x,8.4,-7.5]]),np.array([[0,0,1]]),multiple_hits=True)
  count+=int(any(abs(p[2]+6.7)<1e-5 for p in hits))
 counts.append(count)
assert counts==[1,1,1],('Overlapping rear band materials',counts)
r={'rear_intertier_material_surfaces_per_probe':counts,'lattice_cells_checked' :20,'ray_start_to_inset_backing_m':depths.tolist(),'step_treads_checked':7,'tread_heights_m':heights,'scope':'Actual mesh probes only; does not validate estimated dimensions or provide collision integration.'}
Path(a.report).write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
