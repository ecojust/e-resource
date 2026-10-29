"""Independent ray tests of exported geometry, including intentional bad meshes."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import trimesh

ROOT=Path(__file__).resolve().parent.parent
g=json.loads((ROOT/'geometry-input.json').read_text());x=g['architecture_X_EN'];y=g['architecture_Y_EN']
ROT=np.array([[x[0],y[0],0],[0,0,1],[-x[1],-y[1],0]])


def probes(mesh,materials):
 rows=[]
 def hit(label,point,direction,minimum,maximum,allowed):
  origin=np.array(point)@ROT.T;direction=np.array(direction)@ROT.T
  locations,_,faces=mesh.ray.intersects_location([origin],[direction],multiple_hits=True)
  assert len(locations),(label,'no hit')
  distances=np.linalg.norm(locations-origin,axis=1);i=np.argmin(distances)
  distance=float(distances[i]);material=str(materials[faces[i]])
  assert minimum<distance<maximum and material in allowed,(label,distance,material)
  rows.append({'id':label,'point_source_axes_m':point,'direction_glb':direction.tolist(),
               'first_hit_distance_m':distance,'material':material})
 for level,base in enumerate([.45,4.2,7.95]):
  for bay,cx in enumerate([-9.36,-4.68,0,4.68,9.36]):
   hit(f'veranda-{level}-{bay}',[cx+.40,-14,base+2.0],[0,1,0],4.70,4.94,{'shutter wood','shutter edge'})
 for cx in [-4.8,4.8]:
  hit(f'dormer-inset-glass-{cx}',[cx+.40,-10,13.75],[0,1,0],3.0699,3.0701,{'glass'})
 for origin,top in [(7.5,4.2),(10.,7.95),(11.95,11.85)]:
  hit(f'veranda-floor-{top}',[0,-11,origin],[0,0,-1],origin-top-.0001,origin-top+.0001,{'pale trim','shutter edge'})
 hit('main-roof-hip',[8,0,20],[0,0,-1],4.70,4.82,{'roof underlay','clay tile 0','clay tile 1','clay tile 2','clay tile 3'})
 hit('estimated-rear-wing-roof',[-5.15,22,20],[0,0,-1],6.33,6.45,{'roof underlay','clay tile 0','clay tile 1','clay tile 2','clay tile 3'})
 return rows


def main():
 p=argparse.ArgumentParser();p.add_argument('--glb',type=Path,required=True);p.add_argument('--report',type=Path,required=True);p.add_argument('--negative-regressions',action='store_true');a=p.parse_args()
 scene=trimesh.load(a.glb,force='scene',process=False);parts=list(scene.geometry.values())
 materials=np.concatenate([[part.visual.material.name]*len(part.faces) for part in parts]);mesh=trimesh.util.concatenate(parts)
 report={'file':a.glb.name,'sha256':hashlib.sha256(a.glb.read_bytes()).hexdigest(),'probes':probes(mesh,materials),
         'scope':'Exterior opening/recess, floor and roof geometry probes only; not city collision or walk acceptance'}
 if a.negative_regressions:
  failures=[]
  for name,center,size in [('filled-veranda',(0,-12,6),(23.4,.20,11.5)),('covered-dormer',(-4.8,-7.20,13.9),(1.7,.16,.7))]:
   bad=trimesh.creation.box(size);bad.apply_translation(center);transform=np.eye(4);transform[:3,:3]=ROT;bad.apply_transform(transform)
   combined=trimesh.util.concatenate([mesh,bad]);labels=np.concatenate([materials,np.array(['regression blocker']*len(bad.faces))])
   try:probes(combined,labels)
   except AssertionError as error:failures.append({'case':name,'rejected':True,'reason':str(error)})
   else:raise AssertionError('Bad geometry was accepted: '+name)
  report['negative_regressions']=failures
 a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({'probes_passed':len(report['probes']),'negative_cases_rejected':len(report.get('negative_regressions',[]))}))


if __name__=='__main__':main()
