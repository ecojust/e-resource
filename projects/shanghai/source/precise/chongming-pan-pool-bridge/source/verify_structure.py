"""Probe actual exported mesh: arch through-opening, every tread, pool water."""
import argparse,json
from pathlib import Path
import numpy as np
import trimesh
p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--report',required=True);a=p.parse_args()
s=trimesh.load(a.model,force='scene',process=False);m=trimesh.util.concatenate(tuple(s.geometry.values()))
assert np.isfinite(m.vertices).all() and (m.area_faces>0).all()
origins=[]
for north in np.linspace(-2.7,2.7,19):
 crown=-.85+2.06*np.sqrt(1-(north/3.08)**2)
 for up in np.linspace(.15,crown-.07,6):
  if up<crown-.04:origins.append([-1.4,up,-north])
arch_ray_count=len(origins)
origins=np.asarray(origins);dirs=np.tile([1,0,0],(len(origins),1))
hits,idx,_=m.ray.intersects_location(origins,dirs,multiple_hits=True)
assert not any(0<=np.dot(hits[k]-origins[i],dirs[i])<=2.8 for k,i in enumerate(idx)), 'Arch opening blocked'
# Central stepping strip: each documented step has a physical horizontal tread.
origins=[];expected=[]
run=(10.1-3.38)/24
for sign in [-1,1]:
 for i in range(12):origins.append([.3,5,-sign*(5.05-i*run-run/2)]);expected.append((i+1)*.14+.024)
origins=np.asarray(origins);dirs=np.tile([0,-1,0],(24,1));hits,idx,_=m.ray.intersects_location(origins,dirs,multiple_hits=True)
actual=[max(hits[idx==i,1]) for i in range(24)];assert np.allclose(actual,expected,atol=1e-5),(actual,expected)
# Visible basin plane away from bridge and coping.
hits,idx,_=m.ray.intersects_location(np.array([[3.,5,0],[-3.,5,0]]),np.array([[0,-1,0],[0,-1,0]]),multiple_hits=True)
water=[max(hits[idx==i,1]) for i in range(2)];assert np.allclose(water,[-.8,-.8],atol=1e-5)
r={'finite':True,'nondegenerate':True,'arch_clear_rays':arch_ray_count,'step_treads_checked':24,'actual_tread_heights_m':actual,'water_surface_y_m':water,'scope':'Checks exported geometry, not architectural dimensions or walk collision'}
Path(a.report).write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
