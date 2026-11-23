"""Verify glass, the open balcony, the short vent recesses and both roof finishes by depth."""
import argparse,hashlib,json,runpy
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
Scene=runpy.run_path(str(PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
R=json.loads((HERE/'garden-front-registration.json').read_bytes())['fields']
C=json.loads((HERE/'garden-bay-two-stations.json').read_bytes());xy=np.array(C['bay_centre']);radius=C['radius']
def test(p):
 s=Scene(p);rows=[]
 def check(feature,origin,d,length,mat,dist):
  direction=np.array(d,dtype=float);direction/=np.linalg.norm(direction);h=s.ray(np.asarray(origin,dtype=float),direction,length)
  name='air'if h is None else h['material'].split(' | ')[1];delta=None if h is None else h['distance_m']
  ok=name in mat and (dist is None or (delta is not None and dist[0]-1e-5<=delta<=dist[1]+1e-5))
  rows.append(dict(feature=feature,origin_xyz=list(origin),direction=direction.tolist(),expected=mat,first=name,distance_m=delta,expected_distance_m=dist,passed=ok))
 pane=['reflected grey blue glazing','shaded olive glazing']
 for section,z in [('ground',1.64),('upper',5.99)]:
  edges=np.mean([[x[0]for x in C['bands'][section+'-'+k]['jamb_angles_and_error']]for k in ['head','sill']],axis=0)
  for j,(left,right) in enumerate(zip(edges[::2],edges[1::2])):
   ang=left+(right-left)*.29;normal=np.array([np.sin(ang),-np.cos(ang)]);exterior=xy+(radius+1.)*normal
   check(f'{section} bay frame {j+1}: glazed return', [*exterior,z],[*-normal,0],2,pane,[1.07,1.33])
 for z in [.37,3.85,7.38]:
  normal=np.array([0.,-1.]);pos=xy+(radius+1.)*normal
  check('curved solid spandrel', [*pos,z],[0,1,0],2,['yellow roughcast'],[.98,1.03])
 # A ray dropped into the deck should reach the floor several decimetres below the coping.
 check('inside cantilever deck',[1.25,(R['bal_y']+.14)/2,R['bal_top']+.4],[0,0,-1],2.5,['yellow roughcast'],[R['bal_top']+.4-R['bal_under']-.135,R['bal_top']+.4-R['bal_under']-.125])
 for i,(u,v) in enumerate([(.68,1.52),(2.12,2.97)]):
  x=R['left_wall']+u+.1*(v-u)
  check('vent recess '+str(i+1),[x,R['wing_y']-.3,R['wing_top']-.42],[0,1,0],1,['recessed vent'],[.60,.65])
 check('free space below cantilever outer lip',[.40,R['bal_y']-.48,R['bal_under']-.18],[0,1,0],.54,['air'],None)
 return dict(file=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),passed=sum(x['passed']for x in rows),total=len(rows),results=rows)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('roles',nargs='+',type=Path);ap.add_argument('--out',type=Path,required=True);v=ap.parse_args()
 d=[test(p)for p in v.roles];v.out.write_text(json.dumps(d,indent=2)+'\n')
 for t in d:print(t['file'],t['passed'],t['total'],[(r['feature'],r['first'],r['distance_m'])for r in t['results']if not r['passed']])
