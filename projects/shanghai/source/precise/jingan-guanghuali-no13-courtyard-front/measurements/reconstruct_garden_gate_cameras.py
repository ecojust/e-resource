"""Recover the gate cameras from their published native-pixel controls and EXIF. No image files required."""
from pathlib import Path
import argparse
import json
import numpy as np

def homography(subject, pixels):
    rows=[]
    for (x,z),(u,v) in zip(subject,pixels):
        rows.extend(([x,z,1,0,0,0,-u*x,-u*z,-u], [0,0,0,x,z,1,-v*x,-v*z,-v]))
    h=np.linalg.svd(rows)[2][-1].reshape(3,3)
    return h/h[2,2]

def reconstruct(camera, leaf_depth):
    controls=camera['controls']
    xz=np.array([p['world_x_y_z'][::2] for p in controls])
    uv=np.array([p['observed_native_px'] for p in controls])
    h=homography(xz,uv);k=np.array(camera['K'])
    basis=np.linalg.solve(k,h)
    a,b=basis[:,0],basis[:,1]
    normal=np.cross(b,a)
    normal*=np.sqrt(np.linalg.norm(a)*np.linalg.norm(b))/np.linalg.norm(normal)
    projection=np.column_stack((h[:,0],k@normal,h[:,1],h[:,2]))
    projection[:,3]-=projection[:,1]*leaf_depth
    return projection

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--survey',type=Path,default=Path(__file__).with_name('no13-garden-gate-cameras.json'))
    args=parser.parse_args();doc=json.loads(args.survey.read_text())
    for name,row in doc['cameras'].items():
        p=reconstruct(row,doc['extent_m']['leaf_face_y'])
        if not np.allclose(p,row['P'],rtol=1e-8,atol=1e-8):
            raise ValueError('Reconstructed matrix differs for '+name)
        eye=-np.linalg.solve(p[:,:3],p[:,3]);print(name,' '.join(f'{v:.4f}'for v in eye))
