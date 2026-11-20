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
    glass={'grey blue glass','high lights','lacquered red timber'}
    red={'lacquered red timber'}
    for i,x in enumerate(np.linspace(-11.35,11.35,7)):
        if i in (2,5):
            ray('inset double door behind the south loggia',[x+.08,-.71,1.55],[0,1,0],{'door wood'},(3.85,3.97))
        else:
            ray('inset ground window beyond the three-metre open gallery',[x+(.19 if i!=6 else -.24),-.71,1.59],[0,1,0],glass,(3.73,3.92))
    posts=[-13.05,-9.78,-6.51,-3.24,.03,3.30,6.57,9.84,13.11]
    for x in (v for v in posts[1:-1] if v!=6.57):
        ray('red portico post',[x,-1.0,2.07],[0,1,0],red,(.94,1.06))
    for (left,right)in zip(posts,posts[1:]):
        x=(left+right)/2+.093
        ray('sash of upper enclosed gallery',[x,-.68,6.33],[0,1,0],glass,(.61,.85))
        ray('rail base with real red timber',[x,-.68,4.564],[0,1,0],red,(.55,.63))
        ray('open meander pattern revealing the shaded room behind',[x,-.68,5.145],[0,1,0],{'shadowed opening'},(3.77,3.90))
    for x in [6.58,11.66]:
        ray('front carriage post',[x,-6.8,2.08],[0,1,0],red,(1.32,1.44))
    for dx in [-2.13,-.67,.65,2.14]:
        ray('arched metal carriage canopy above the empty drive',[9.12+dx,-2.63,.54],[0,0,1],{'black sheet iron','folded iron seams'},(3.57,4.20))
    for x in [-1.60,-.66,.20]:
        ray('glazing on the near face of the lookout',[x,1.4,10.23],[0,1,0],glass,(3.35,3.55))
    ray('metal cap of glazed lookout',[-.79,6.05,16],[0,0,-1],{'black sheet iron'},(4.36,4.50))
    for x,y,z in [(-8.75,6.8,10.18),(4.25,7.36,11.20),(10.52,5.84,10.32)]:
        ray('capped white stack',[x,y,16],[0,0,-1],{'light plaster'},(16-z-.28,16-z-.20))
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
