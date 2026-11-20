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
    brick={'tower face brick','burnt header','warm stretcher','dark mortar'}
    # Local +Y enters the building. The tall street-facing opening and its
    # contemporary south return can both be traced to their inset glass, solid white
    # spandrel, and ventilation blades at the upper level.
    for z,materials,depth in [(6.65,{'dark glazing'},(.62,.68)),(8.58,{'white painted plaster'},(.53,.58)),
                              (10.15,{'window steel','inner dark timber'},(.50,.74))]:
        ray('street tower opening',[-3.02,-2,z],[0,1,0],materials,(2+depth[0],2+depth[1]))
        ray('southeast tower return',[-7.0,2.03,z],[1,0,0],materials,(2.43,2.88))
    for z in (5.86,7.55,9.42,11.30):
        ray('brick tower beside recessed shaft',[-4.15,-2,z],[0,1,0],brick,(2.31,2.38))
    for x in (-.825,.775):
        ray('two deep visible entrance doors',[x+.048,-2,1.12],[0,1,0],{'inner dark timber'},(2.46,2.55))
        ray('entry door head',[x,-2,2.25],[0,1,0],{'white painted plaster'},(1.85,1.91))
    for x in (-.825,.775,2.375):
        ray('three separate lobby window apertures',[x+.18,-2,3.60],[0,1,0],{'dark glazing'},(2.21,2.27))
        ray('moulded pale arched window trim',[x+.59,-2,4.40],[0,1,0],{'white painted plaster'},(1.85,1.91))
    for z in (5.37,6.69):
        ray('continuous vestibule cornice',[.39,-2,z],[0,1,0],{'white painted plaster','cream coping'},(1.67,1.88))
    ray('gable above the entrance',[.29,-2,7.75],[0,1,0],brick,(2.66,2.72))
    for x in (-3.82,-2.62):
        ray('separate arms of red cross',[x,-2,13.96],[0,1,0],{'cross vermilion'},(3.74,3.83))
    ray('top of the red cross',[-3.20,1.88,17],[0,0,-1],{'cross vermilion'},(2.34,2.38))
    ray('crown beside the cross',[-4.12,2.15,17],[0,0,-1],{'white painted plaster'},(4.52,4.56))
    ray('east shoulder window',[4.87,-2,2.34],[0,1,0],{'dark glazing'},(2.95,3.02))
    for x,z in [(-5.55,2.3),(.32,7.91),(5.36,3.54)]:
        ray('closed neutral section behind gabled roof',[x,8,z],[0,-1,0],{'neutral section'},(3.75,3.80))
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
