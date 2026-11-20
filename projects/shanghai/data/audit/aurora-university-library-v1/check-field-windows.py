"""Shoot independently defined rays through all three serialised deliveries."""
import argparse,hashlib,json,runpy
from pathlib import Path
import numpy as np

def trace(scene):
    rows=[]
    def ray(name,origin,direction,materials,limits):
        h=scene.ray(origin,direction,36)
        assert h and h['material']in materials and limits[0]<h['distance_m']<limits[1],(name,h,limits)
        rows.append(dict(part=name,origin=origin,direction=direction,material=h['material'],distance_m=h['distance_m']))
    pane = {'window glass'}
    tiles = {'red face tile', 'fired brick red', 'weathered red tile', 'brick bedding'}
    for side in (-1, 1):
        for bay in (4.79, 8.20, 11.59, 15.17, 18.60):
            x = side * bay
            for z in (6.07, 10.57, 15.07):
                ray('upper field-facing window glass', [x+.13,-1,z],[0,1,0],pane,(1.69,1.73))
            ray('rounded ground-floor window', [x+.11,-1,1.43],[0,1,0],pane,(1.69,1.73))
            ray('solid shoulder outside curved window head',[x+.86,-1,3.91],[0,1,0],{'red face tile','grey cement dressings'},(1.32,1.42))
            ray('light spandrel above first floor',[x,-1,9.15],[0,1,0],{'pale window spandrels'},(1.35,1.38))
        for x in (6.49, 9.90, 13.38, 16.89):
            ray('red upright pier between bay groups',[side*x,-1,8.33],[0,1,0],tiles,(1.36,1.41))
    for middle in (-25.1545,25.4545):
        # Two broad end panels each have three distinct upper sashes per floor.
        for delta in (-1.56,0,1.56):
            for z in (6.07,10.57,15.07):
                ray('end panel three-light window',[middle+delta+.14,-1,z],[0,1,0],pane,(1.29,1.33))
        ray('wide basket arch glazing',[middle+.12,-1,1.43],[0,1,0],pane,(1.29,1.33))
        ray('end parapet rises above the connecting wings',[middle,-1,19.91],[0,1,0],{'pale window spandrels'},(.95,1.03))
    for z in (2.00,6.17,12.14):
        ray('continuous recessed central window',[.11,-1,z],[0,1,0],pane,(1.45,1.49))
    # The two resolutions group upper transoms differently. The highest light
    # is a glazed surface in both and sits within 1 cm of the same window plane.
    ray('top light of central window',[.11,-1,16.45],[0,1,0],{'window glass','upper pale reflection'},(1.44,1.49))
    for x,y in [(-25,0),(-13,.40),(0,.16),(13,.40),(25,0)]:
        top=20.88 if abs(x)>22 else 20.10
        ray('slab behind stepped front parapet',[x,y+2.4,25],[0,0,-1],{'flat roof'},(25-top+.27,25-top+.30))
    return rows

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ['project','decoded','manifest','out']:p.add_argument('--'+arg,type=Path,required=True)
    a=p.parse_args();doc=json.loads(a.manifest.read_bytes())
    scene=runpy.run_path(str(a.project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
    sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();cases=[]
    for role in ('raw','full','lod'):
        f=a.manifest.parent/doc['assets'][role]['file'];assert sha(f)==doc['assets'][role]['sha256']
        dec=f if role=='raw' else a.decoded/(role+'.glb');s=scene(dec);tests=trace(s)
        cases.append(dict(variant=role,sha256=sha(f),decoded_sha256=sha(dec),triangles=len(s.tri),checks=tests))
    a.out.parent.mkdir(exist_ok=True,parents=True)
    a.out.write_text(json.dumps(dict(id=doc['id'],passed=True,manifest_sha256=sha(a.manifest),script_sha256=sha(Path(__file__)),count=sum(len(i['checks'])for i in cases),variants=cases),indent=2,ensure_ascii=False)+'\n')
    print(sum(len(i['checks'])for i in cases))
if __name__=='__main__':main()
