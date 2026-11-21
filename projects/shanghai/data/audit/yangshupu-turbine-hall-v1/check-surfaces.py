"""Measure the depth of actual glass, masonry, arch frames and flue mouths in all three GLBs."""
from pathlib import Path
import argparse
import hashlib
import json
import math
import subprocess
import tempfile

import numpy as np
import trimesh

PROJECT = Path(__file__).resolve().parents[3]
AUDIT = Path(__file__).resolve().parent
MODEL = 'yangpu-yangshupu-power-turbine-hall'
ANGLE = math.radians(-22.0)


def samples():
    points = []
    for title, x0, x1, y, count, z in [('long', -35, 3.1, -2, 8, 8.19), ('raised', 3.1, 20.3, -3.2, 4, 10.61)]:
        spacing = (x1 - x0) / count
        for n in range(count):
            center = x0 + (n + .5) * spacing
            for dx in (-.35,.35):
                points.append((f'{title} sash {n+1} glazing {dx}', 'front', center+dx, z, y+.30, y+.34))
        for n in range(1,count):
            points.append((f'{title} concrete pier {n}', 'front', x0+n*spacing, z, y-.26, y-.16))
    for n in range(5):
        center = 5.72 + (n+.5)*(21.3-5.72)/5
        for d in (-.20,.20):
            points.append((f'high end glazing {n+1} {d}', 'end', center+d, 10.41, 26.15, 26.21))
    for x in (.65,7.2,15.4,23.3):
        points.append((f'round roof frame {x}', 'above', x,11.7,26.81,27.13))
        points.append((f'open beside frame {x}', 'above', x+.70,11.7,23.96,24.15))
    for x,y,high,r in [(-18.6,3,18.7,.68),(-8.1,3,21.3,.80),(13.6,9.4,33.7,.93),(24.2,18.4,29.1,.8)]:
        points.append((f'flue lip {x}', 'above', x+.89*r,y,high-.055,high+.04))
        points.append((f'recessed mouth {x}', 'above', x,y,high-1.04,high-.95))
    return points


def model_space(path):
    scene = trimesh.load(path,force='mesh',process=False)
    t = scene.triangles
    gx, gy, gz = t[:,:,0], -t[:,:,2], t[:,:,1]
    return np.stack((math.cos(ANGLE)*gx+math.sin(ANGLE)*gy,
        -math.sin(ANGLE)*gx+math.cos(ANGLE)*gy+5,gz),axis=2)


def measure(mesh, probes):
    t = model_space(mesh)
    rows = []
    for name, orientation, a, b, low, high in probes:
        uaxis,vaxis,depth = {'front':(0,2,1),'end':(1,2,0),'above':(0,1,2)}[orientation]
        uv = t[:,:,[uaxis,vaxis]]
        v0 = uv[:,0]
        v1,v2 = uv[:,1]-v0,uv[:,2]-v0
        det = v1[:,0]*v2[:,1]-v1[:,1]*v2[:,0]
        valid = abs(det)>1.e-9
        det = np.where(valid,det,1)
        p = [a,b]-v0
        s = (p[:,0]*v2[:,1]-p[:,1]*v2[:,0])/det
        q = (v1[:,0]*p[:,1]-v1[:,1]*p[:,0])/det
        mask = valid & (s>=-1.e-8) & (q>=-1.e-8) & (s+q<=1+1.e-8)
        hits = (t[:,0,depth]+s*(t[:,1,depth]-t[:,0,depth])+q*(t[:,2,depth]-t[:,0,depth]))[mask]
        actual = float((np.min if orientation=='front' else np.max)(hits)) if len(hits) else None
        rows.append({'feature':name,'orientation':orientation,'coordinates':[a,b],'expected_m':[low,high],
                     'observed_m':actual,'passed':actual is not None and low<=actual<=high})
    return rows


def run():
    arg=argparse.ArgumentParser()
    arg.add_argument('--assets',type=Path,default=PROJECT/'assets/models/candidates'/MODEL)
    arg.add_argument('--out',type=Path,default=AUDIT/'surface-checks.json')
    args=arg.parse_args()
    manifest=json.loads((args.assets/'manifest.json').read_bytes())
    decoder=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
    with tempfile.TemporaryDirectory() as tmp:
        result={}
        for role in ('raw','full','lod'):
            rec=manifest['assets'][role]
            path=args.assets/rec['file']
            digest=hashlib.sha256(path.read_bytes()).hexdigest()
            assert digest==rec['sha256']
            mesh=path
            if role!='raw':
                mesh=Path(tmp)/(role+'.glb')
                subprocess.run(['node',decoder,path,mesh,PROJECT/'vendor/meshopt_decoder.module.js'],check=True)
            rows=measure(mesh,samples())
            result[role]={'sha256':digest,'samples':rows}
            bad=[p for p in rows if not p['passed']]
            if bad:
                raise ValueError(f'{role}: {bad}')
        args.out.write_text(json.dumps({'id':MODEL,'checks':len(samples())*3,'variants':result,
                          'checker_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},indent=2)+'\n')
        print('Verified',len(samples())*3,'first-surface measurements')


if __name__=='__main__':
    run()
