"""Read the rendered GLB triangles and record the nearest material at 17 photograph marks."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy

import numpy as np

HERE=Path(__file__).resolve().parent
scene=runpy.run_path(str(HERE/'render-villa-stations.py'))


def cast(path,marks):
    _,P,_,_=next(scene['stations']())
    A=P[:,:3];origin=np.linalg.solve(A,-P[:,3]);inv=np.linalg.inv(A)
    parts,materials,_=scene['renderer'].read_glb(path)
    triangles=[];labels=[]
    for pos,_,_,indices,material,_ in parts:
        triangles.append(pos[indices.reshape(-1,3)])
        labels.extend([materials[material]['name']]*(len(indices)//3))
    faces=np.vstack(triangles).astype('float64');e1=faces[:,1]-faces[:,0];e2=faces[:,2]-faces[:,0]
    off=origin-faces[:,0];Q=np.cross(off,e1);dv=np.einsum('ij,ij->i',e2,Q)
    def hit(u,v):
        direction=inv@[u,v,1.]
        normal=np.cross(direction,e2);det=(e1*normal).sum(axis=1)
        valid=np.abs(det)>1.e-12
        prop=np.divide(1.,det,where=valid,out=np.zeros_like(det))
        a=prop*(off*normal).sum(1);b=prop*(Q@direction);t=prop*dv
        candidates=np.flatnonzero(valid&(a>=0)&(b>=0)&(a+b<=1)&(t>.001))
        if not len(candidates):return [None,None]
        index=candidates[np.argmin(t[candidates])]
        return [labels[index],(origin+t[index]*direction).round(4).tolist()]
    result=[]
    for row in marks:
        mat,xyz=hit(*row['pixel'])
        result.append({**row,'first_material':mat,'first_position_m':xyz,'matches':mat==row['material']})
    return {'sha256':hashlib.file_digest(path.open('rb'),'sha256').hexdigest(),
            'matched':sum(r['matches']for r in result),'count':len(result),'samples':result}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('exports',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args()
    marks=json.loads((HERE/'street-material-landmarks.json').read_bytes())
    result={k:cast(a.exports/name,marks['points'])for k,name in [('raw','full-source.glb'),('full','decoded-full.glb'),('lod','decoded-lod.glb')]}
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=1)+'\n')
    print({k:v['matched']for k,v in result.items()})
