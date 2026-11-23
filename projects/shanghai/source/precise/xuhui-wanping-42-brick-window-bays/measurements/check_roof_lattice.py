"""Cast calibrated 2019 photographic rays into a source or decoded delivery."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'source'),str(HERE.parents[1]/'xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact')]
from glb_triangles import SerialScene
from register_street import Camera
from roof_lattice import CAP, GLASS, LATTICE, plan, height

# Independent readings on the high-resolution plane rectification. Retain
# foliage, oblique cable runs, the dark terminal crop and reconstructed edges.
GLASS_POINTS = [(240,179),(510,178),(688,193),(1175,185),(1301,182),
                (1436,186),(1474,187),(1606,186),(1736,182)]
LATTICE_POINTS = [(201,137),(471,142),(651,142),(1135,144),(1265,146),
                  (1394,146),(1568,146),(1693,147),(120,136),(1813,139)]
CROWN_POINTS = [(241,101),(511,101),(551,101),(690,102),(1175,104),
                (1303,105),(1434,105),(1473,106),(1608,106),(1734,106)]
# Sample the middle of the actual projecting stems, away from roof silhouette.
RAFTER_POINTS = [(50,56),(132,59),(268,61),(398,62),(495,63),(589,63),
                 (719,64),(866,66),(1078,63),(1206,62),(1343,64),(1431,64),
                 (1523,65),(1644,67),(1783,70),(1863,75)]


def inspect(mesh,scale):
    scale=np.broadcast_to(np.asarray(scale,dtype=float),(3,));assert np.all(scale>0)
    c=Camera(22.);eye=c.C*scale
    scene=SerialScene(mesh);checks=[]
    for kind,marks,material in [('glazing',GLASS_POINTS,GLASS),('side lattice',LATTICE_POINTS,LATTICE),
                                ('arched head',CROWN_POINTS,LATTICE),('rafter',RAFTER_POINTS,CAP)]:
        for n,(u,v) in enumerate(marks,1):
            on_plane=np.array([plan(u),0.,height(v)])
            hit=scene.ray(eye,on_plane*scale-eye,150.)
            checks.append({'feature':kind,'member':n,'rectified_pixel':[u,v],
                           'original_3968_pixel':(c.pixel(on_plane)*3968/1050).round(2).tolist(),
                           'expected':material,'first_surface':hit,
                           'matches':bool(hit and hit['material']==material)})
    return {'mesh':mesh.name,'sha256':hashlib.sha256(mesh.read_bytes()).hexdigest(),'scale':scale.tolist(),
            'station':[float(v) for v in eye], 'tests':len(checks),
            'matched':sum(row['matches'] for row in checks),'measurements':checks}


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('mesh',type=Path);ap.add_argument('output',type=Path);ap.add_argument('--scale',type=float,nargs='+',default=[1.])
    args=ap.parse_args();data=inspect(args.mesh,args.scale)
    args.output.write_text(json.dumps(data,indent=2)+'\n')
    print(data['matched'],data['tests'])
    for r in data['measurements']:
        if not r['matches']:
            print(r['feature'],r['member'],r['rectified_pixel'],r['first_surface'] and r['first_surface']['material'])
