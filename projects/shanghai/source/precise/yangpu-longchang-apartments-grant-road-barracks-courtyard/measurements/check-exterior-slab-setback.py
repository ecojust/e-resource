from pathlib import Path
import argparse,sys,json,numpy as np
s=Path(__file__).resolve().parents[1]
prec=s.parent
sys.path.insert(0,str(prec/'xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
from glb_triangles import SerialScene
layout=json.loads((s/'source/courtyard-layout.json').read_bytes());corner=np.array(layout['outer_corners']);ht=layout['storey_pitch']
def inspect(file):
 m=SerialScene(file);out=[]
 triangles=m.tri[np.array([m.materials[i]=='Court | floor concrete' for i in m.mi])]
 zz=triangles[:,:,2]
 for i in range(4):
  lo=corner[i];hi=corner[(i+1)%4];length=np.linalg.norm(hi-lo);t=(hi-lo)/length;normal=np.array([-t[1],t[0]])
  depth=(triangles[:,:,:2]-lo)@normal;u=(triangles[:,:,:2]-lo)@t
  for lev in range(1,6):
   z=lev*ht
   filter=(zz.min(axis=1)>=z-.22)&(zz.max(axis=1)<=z+.012)&(np.ptp(zz,axis=1)>.15)&(u.mean(axis=1)>.2)&(u.mean(axis=1)<length-.2)&(np.ptp(depth,axis=1)<.003)
   d=depth[filter].mean(axis=1)
   out.append({'face':['west','south','east','north'][i],'roof_or_floor':lev,'coplanar_triangles':int((abs(d)<.002).sum()),'nearest_slab_side_m':round(float(d.min()),4)})
 return {'mesh':m.asset,'checks':out}
if __name__=='__main__':
    ap=argparse.ArgumentParser(description='Check for coplanar concrete edges on the exterior brick face.')
    for role in ['original','raw','full','lod','out']:ap.add_argument('--'+role,type=Path,required=True)
    a=ap.parse_args()
    d={'previous':inspect(a.original),'revised':{role:inspect(getattr(a,role)) for role in ['raw','full','lod']}}
    assert all(q['coplanar_triangles']>=2 for q in d['previous']['checks'])
    assert all(q['coplanar_triangles']==0 and .115<q['nearest_slab_side_m']<.125 for chk in d['revised'].values() for q in chk['checks'])
    a.out.write_text(json.dumps(d,indent=2)+'\n')
