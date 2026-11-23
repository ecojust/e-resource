"""Intersect the held photo locations at the ground-floor court door with a delivered GLB."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from register_court import Camera

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
from glb_triangles import SerialScene

def check(model):
    cam=Camera()
    scene=SerialScene(model)
    source=json.loads((HERE/'lower-court-control.json').read_text())
    readings=[]
    for name,u,v,expected in source['direct_observations']:
        hit=scene.ray(cam.c,cam.ray((u,v)),50.)
        actual=hit and hit['material']
        readings.append(dict(name=name,native_pixel=[u,v],expected=expected,hit=hit,passed=actual==expected))
    return dict(mesh=model.name,sha256=hashlib.sha256(model.read_bytes()).hexdigest(),samples=readings,
                exact=sum(r['passed'] for r in readings),total=len(readings))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mesh',type=Path);p.add_argument('out',type=Path)
    a=p.parse_args()
    result=check(a.mesh)
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(result['exact'],result['total'])
