"""Probe actual delivered triangle geometry, independent of builder metadata."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
import trimesh
p=argparse.ArgumentParser();p.add_argument('--glb',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
s=trimesh.load(a.glb,force='scene',process=False);meshes=list(s.geometry.values())
materials=np.concatenate([[m.visual.material.name]*len(m.faces) for m in meshes]);mesh=trimesh.util.concatenate(meshes)
def ray(x,y,z,axis=(0,1,0)):
 origin=np.array([x,z,-y]);d=np.array([axis[0],axis[2],-axis[1]])
 loc,_,faces=mesh.ray.intersects_location([origin],[d],multiple_hits=True)
 assert len(loc),'No hit';dist=np.linalg.norm(loc-origin,axis=1);i=np.argmin(dist)
 return float(dist[i]),str(materials[faces[i]])
checks=[]
def check(name,xyz,lo,hi,material,axis=(0,1,0)):
 d,m=ray(*xyz,axis);assert lo<d<hi and m in material,(name,d,m)
 checks.append({'name':name,'origin':xyz,'first_hit_distance_m':d,'material':m})
# Start behind the separate fence so the actual entry recess is tested.
check('arch to recessed glass',[.50,-1,1.75],1.48,1.51,['glass'])
check('solid brick pier',[2.60,-1,5.81],.98,1.02,['mortar','brick0','brick1','brick2','brick3','brick4','brick5'])
check('lower closed sash glazing',[-1.63,-1,5.15],1.14,1.18,['glass'])
check('upper right glass',[1.32,-1,8.35],1.14,1.18,['glass'])
# Gatepost grooves must be recessed by 5cm relative to the front skin.
check('gatepost flute',[-.25,-4,1.0],1.32,1.34,['stone'])
check('gatepost face',[-.19,-4,1.0],1.27,1.29,['stone'])
check('balcony slab top',[.42,-.70,9],1.43,1.45,['stone'],(0,0,-1))
check('entry fanlight',[.55,-1,2.80],1.53,1.56,['glass'])
# The right pair of lower sashes must not leave glass in their closed positions.
for x in [1.00,1.58]:
 origin=np.array([x,5.1,1.]);loc,_,_=mesh.ray.intersects_location([origin],[[0,0,-1]],multiple_hits=True)
 distances=np.linalg.norm(loc-origin,axis=1) if len(loc) else np.array([])
 assert not np.any((distances>1.13)&(distances<1.18)),('Open sash still fills wall opening',x)
 checks.append({'name':'open lower sash','x':x,'no_glass_at_closed_depth':True})
a.report.write_text(json.dumps({'glb_sha256':hashlib.sha256(a.glb.read_bytes()).hexdigest(),'checks':checks,'scope':'Component geometry only; not a measured building or city integration acceptance'},indent=2)+'\n');print('PASS',len(checks),'independent geometry probes')
