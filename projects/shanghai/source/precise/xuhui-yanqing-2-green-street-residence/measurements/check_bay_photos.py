"""Shoot frozen original-pixel rays at the windows, sills, apron rims and returns in a delivered GLB."""
from pathlib import Path
import argparse
import json
import sys
import numpy as np

from register_front import Camera

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
from glb_triangles import SerialScene


def trace(mesh):
    controls=json.loads((HERE/'street-bay-photo-controls.json').read_text())
    stations=json.loads((HERE/'december-street-geometry.json').read_text())
    scene=SerialScene(mesh)
    methods={'sash':['dark steel bay frames','recessed blue grey glass'],
             'wall':['pale celadon mineral render'],'cream':['ivory stone bay bands']}
    result={'asset':scene.asset,'controls':'street-bay-photo-controls.json','views':{}}
    for view,points in controls['probes'].items():
        if view=='june':
            cam=Camera();eye=cam.c;inverse=cam.inv
        else:
            cam=stations['photos'][view];eye=np.asarray(cam['C'])
            inverse=np.asarray(cam['R']).T@np.linalg.inv(cam['K'])
        checks=[]
        for item in points:
            u,v=item['pixel']
            hit=scene.ray(eye,inverse@[u,v,1.],60)
            material=hit['material'] if hit else None
            ok=bool(material and any(m in material for m in methods[item['expected']]))
            near=0 if ok else None
            if not ok:
                for step in (2,4,8,12,18):
                    for dx,dy in ((-step,0),(step,0),(0,-step),(0,step)):
                        h=scene.ray(eye,inverse@[u+dx,v+dy,1.],60)
                        if h and any(m in h['material'] for m in methods[item['expected']]):
                            near=step
                            break
                    if near is not None:
                        break
            checks.append({**item,'first_hit':material,'matches':ok,'nearest_axial_offset_px':near})
        result['views'][view]={'direct_first_hits':sum(x['matches']for x in checks),'probes':len(checks),'checks':checks}
    return result


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('mesh',type=Path)
    cli.add_argument('report',type=Path)
    args=cli.parse_args()
    report=trace(args.mesh)
    args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print({k:[r['direct_first_hits'],r['probes']]for k,r in report['views'].items()})
