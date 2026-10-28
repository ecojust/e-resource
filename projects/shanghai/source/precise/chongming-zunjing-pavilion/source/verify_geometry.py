import json
import argparse
from pathlib import Path
import numpy as np
import trimesh

def inspect(path):
 s=trimesh.load(path,force='scene',process=False)
 t=np.concatenate([m.triangles for m in s.geometry.values()]).astype('<f4')
 assert np.isfinite(t).all()
 t[t==0]=0
 area=np.linalg.norm(np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]),axis=1)
 assert (area>0).all()
 # Canonicalize vertices and triangles independently of codec ordering.
 v=t.view([('x','<f4'),('y','<f4'),('z','<f4')]).reshape(-1,3)
 v.sort(axis=1,order=['x','y','z']);canonical=np.sort(v.view('V36').reshape(-1))
 return canonical,{'triangles':len(t),'bounds':[t.min(axis=(0,1)).tolist(),t.max(axis=(0,1)).tolist()],'nondegenerate':True,'finite':True}
parser=argparse.ArgumentParser()
for name in ['raw','decoded_full','lod','decoded_lod','report']: parser.add_argument('--'+name.replace('_','-'),required=True)
args=parser.parse_args()
report={}
for name,raw,decoded in [('full',args.raw,args.decoded_full),('lod',args.lod,args.decoded_lod)]:
 a,r=inspect(raw);b,_=inspect(decoded);assert np.array_equal(a,b),name
 r['meshopt_decoded_triangle_positions_exact']=True;report[name]=r
p=Path(args.report);p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
