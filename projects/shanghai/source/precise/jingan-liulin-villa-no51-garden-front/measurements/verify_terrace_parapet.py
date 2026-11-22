"""Measure the first surfaces of the bowed Flemish-bond parapet in an actual GLB, including native photographic checks."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from scipy.optimize import brentq
from scipy.integrate import quad

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'source'), str(HERE.parents[1] / 'xuhui-pathe-records-office/measurements/city-contact')]
from glb_triangles import SerialScene
from terrace_parapet import BRICK, MORTAR, CAP

def check(path, component=False):
    mesh = SerialScene(path)
    evidence = json.loads((HERE / 'terrace-parapet-photo.json').read_text())
    camera = np.asarray(json.loads((HERE / 'no51-house-cameras.json').read_text())['source_poses']['gao06']['P'])
    eye = -np.linalg.solve(camera[:, :3], camera[:, 3])
    a,b,c = evidence['curve_y_coefficients']
    def front(x):
        return a + b*x + c*x*x
    def arc(x):
        return quad(lambda u: np.hypot(1, 2*c*u+b), 0, x)[0]
    def xpos(s):
        return brentq(lambda x: arc(x) - s, -5, 5)
    rows = []
    def cast(kind, start, direction, maximum, wanted, **fields):
        first = mesh.ray(start, direction, maximum)
        actual = first['material'] if first else None
        rows.append(dict(test=kind, passed=actual in wanted, expected=list(wanted),
                         actual=actual, first_xyz_m=first['point_enu_m'] if first else None, **fields))
    def face(kind, x, z, wanted):
        cast(kind, [x, front(x)-.060, z], [0,1,0], .14, wanted, xz_m=[round(x,5),round(z,5)])
    for obs in evidence['independent_centres']:
        u,v = obs['native_uv']
        direction = np.linalg.solve(camera[:,:3], [u,v,1.])
        cast('2014 source '+obs['kind'], eye, direction, 40, BRICK, native_uv=[u,v],
             measured_span_m=obs['measured_span_m'])
    joint = .385
    for row in range(15):
        # The first exposed run is cut off at the cornice. Inspect the middle of each run.
        z = 8.764 + row*.0653
        phase = arc(.15) - (row%2)*.1925
        for repeat in [-9,-4,0,4,8]:
            start = phase + joint * repeat
            for offset, name, wanted in [(0.,'Mortar before header',[MORTAR]),(.064,'Header face',BRICK),
                                         (.128,'Mortar before stretcher',[MORTAR]),(.255,'Stretcher face',BRICK)]:
                face(name, xpos(start+offset), z, wanted)
        if row < 14:
            for x in [-2.6,.73,2.85]:
                face('Horizontal mortar bed',x,8.794 + row*.0653,[MORTAR])
    for x in [-4.27,-3.8,-2.6,-1.2,0,1.2,2.6,3.8,4.19]:
        face('Coping front', x, 9.761, [CAP])
        cast('Top of coping',[x,front(x)+.09,9.84],[0,0,-1], .07,[CAP],x_m=x)
        if x == 4.19 and not component:
            # The curved parapet terminates against the villa's pale window reveal.
            # Gao 05 (2439.62,744.92) and 06 (2992.79,592.06) show the same return.
            cast('Photographed right wing reveal above the parapet end',
                 [x, front(x)-.060, 9.875], [0,1,0], .14, ['Villa | pale rendered surrounds'],
                 gao05_px=[2439.62,744.92], gao06_px=[2992.79,592.06])
        else:
            face('Unfilled area above coping',x,9.875,[None])
    with path.open('rb') as f:
        sha = hashlib.file_digest(f,'sha256').hexdigest()
    return dict(mesh_sha256=sha, passed=all(r['passed'] for r in rows),
                count=len(rows), samples=rows, source_numeric_evidence='terrace-parapet-photo.json')

if __name__ == '__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('mesh',type=Path);ap.add_argument('output',type=Path)
    ap.add_argument('--component',action='store_true',help='Check the isolated parapet, without the villa wing at the right end.')
    args=ap.parse_args()
    result=check(args.mesh,args.component); args.output.parent.mkdir(exist_ok=True,parents=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=1)+'\n')
    failed=[r for r in result['samples']if not r['passed']]
    print(result['count'], 'probes,', len(failed),'failed',result['mesh_sha256'])
    if failed:print(failed[:3])
    sys.exit(0 if result['passed'] else 1)
