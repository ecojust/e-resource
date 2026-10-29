"""Independent ray probes of actual delivered main-house geometry."""
import argparse,hashlib,json,math
from pathlib import Path
import numpy as np
import trimesh
p=argparse.ArgumentParser();p.add_argument('--glb',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
s=trimesh.load(a.glb,force='scene',process=False);meshes=list(s.geometry.values());materials=np.concatenate([[m.visual.material.name]*len(m.faces) for m in meshes]);mesh=trimesh.util.concatenate(meshes)
def ray(x,y,z,direction=(0,1,0)):
 origin=np.array([x,z,-y]);d=np.array([direction[0],direction[2],-direction[1]])
 loc,_,faces=mesh.ray.intersects_location([origin],[d],multiple_hits=True);assert len(loc),'No ray hit'
 distances=np.linalg.norm(loc-origin,axis=1);i=np.argmin(distances);return float(distances[i]),str(materials[faces[i]])
checks=[]
def check(name,xyz,lo,hi,mats,direction=(0,1,0)):
 distance,material=ray(*xyz,direction);assert lo<distance<hi and material in mats,(name,distance,material)
 checks.append({'name':name,'origin':xyz,'distance_m':distance,'material':material})
base=7.7+3.3*((3.6/7.6)+.12*math.sin(math.pi*3.6/7.6))+.03
for x in [-3.5,0,3.5]:check('dormer glass; roof cut away',[x+.2,-6,base+.33],2.10,2.14,['glass'])
check('open south veranda to inset glazing',[1,-10,2.0],4.80,4.84,['glass'])
check('upper south glass',[-4.95,-10,4.60],4.80,4.84,['glass'])
check('east wing glass',[9.7,-9,1.2],2.20,2.24,['glass'])
check('north porch to inset door',[.3,11,1.4],4.20,4.24,['glass'],(0,-1,0))
check('curved balcony slab',[1.2,-7.8,4.1],.23,.25,['grey trim'],(0,0,-1))
for x,y in [(6,-6),(4.8,-3),(-6,3),(7,4)]:
 distance,material=ray(x,y,15,(0,0,-1));height=15-distance;t=min(1,(11.6-abs(x))/7.6,(7.6-abs(y))/7.6);expected=7.7+3.3*(t+.12*math.sin(math.pi*t))
 assert expected-.012<height<expected+.11 and material in ['roof underlay','tile0','tile1','tile2','tile3'],('Curved roof profile',x,y,height,expected,material)
 checks.append({'name':'curved roof top','x':x,'y':y,'actual_z':height,'estimated_envelope_z':expected,'material':material})
a.report.write_text(json.dumps({'glb_sha256':hashlib.sha256(a.glb.read_bytes()).hexdigest(),'checks':checks,'scope':'Actual geometry tests, not survey or city acceptance'},indent=2)+'\n');print('PASS',len(checks),'independent structural probes')
