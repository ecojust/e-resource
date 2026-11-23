"""Shoot independently picked pixels of the photographed No. 7 terrace at an actual GLB."""
from pathlib import Path
import argparse
import json
import sys

from register_court import Camera

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
from glb_triangles import SerialScene


def trace(mesh):
    scene=SerialScene(mesh)
    obs=json.loads((HERE/'no7-enclosure-photo-controls.json').read_text())
    camera=Camera(18)
    checks=[]
    for name,uv,target in obs['probes']:
        hit=scene.ray(camera.c,camera.ray(uv),60)
        mat=hit['material'] if hit else None
        match=mat==obs['materials'][target]
        offset=0 if match else None
        if not match:
            for step in (1,2,3,4,6,8,12):
                for dx,dy in ((-step,0),(step,0),(0,-step),(0,step)):
                    nearby=scene.ray(camera.c,camera.ray((uv[0]+dx,uv[1]+dy)),60)
                    if nearby and nearby['material']==obs['materials'][target]:
                        offset=step
                        break
                if offset is not None:
                    break
        checks.append(dict(feature=name,pixel=uv,expected=target,first_hit=mat,match=match,nearest_axial_px=offset))
    return {'asset':scene.asset,'controls':'no7-enclosure-photo-controls.json','n':len(checks),
            'direct_first_hits':sum(r['match'] for r in checks),'results':checks}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mesh',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args();result=trace(args.mesh)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(result['direct_first_hits'],result['n'])
