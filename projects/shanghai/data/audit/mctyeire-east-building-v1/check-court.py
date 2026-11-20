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
    # The center of an arcade opening sees the garden-facing inner casement,
    # whereas the small spaces between neighbouring openings see solid piers.
    for x0,x1,y in [(-34.20,-10.16,4.00),(10.16,36.49,3.76)]:
        mid=(x0+x1)/2; width=x1-x0; arcade=y-1.83
        for i in range(6):
            x=x0+(i+.5)*width/6
            ray('recessed window beyond open arcade',[x+.18,arcade-.75,1.82],[0,1,0],{'casement glass'},(4.24,4.30))
            ray('Tudor crown solid above the opening',[x+.13,arcade-.75,3.64],[0,1,0],{'court ashlar','cream dressings'},(.64,.77))
        for i in range(1,6):
            ray('arcade stone pier',[x0+i*width/6,arcade-.75,1.83],[0,1,0],{'court ashlar'},(.74,.76))
        for i in range(8):
            x=x0+(i+.5)*width/8
            for level in (6.75,11.02):
                ray('two separate floors of recessed paired casements',[x+.30,y-.6,level],[0,1,0],{'casement glass'},(.91,.945))
        for i in range(4):
            x=mid+(i-1.5)*width/4+.24
            yy=y+1.51;zz=13.57+.46*(yy-y+.30)
            ray('gable dormer paired glazing',[x,y+.46,zz+.56],[0,1,0],{'casement glass'},(1.36,1.40))
    for x in (-6.95,6.95):
        ray('ground floor diamond glazing',[x+.23,-1.16,2.21],[0,1,0],{'amber leaded glass','dark lead'},(1.88,1.95))
        ray('middle stone-mullioned window',[x,-1.16,7.39],[0,1,0],{'casement glass','cream dressings','dark casement'},(1.70,1.96))
    for x in (-2.64,2.64):
        ray('porch front stone piers',[x,-5.21,2.2],[0,1,0],{'porch stone'},(1.68,1.72))
    ray('central recessed timber door',[.44,-5.21,1.05],[0,1,0],{'old mahogany'},(5.43,5.48))
    ray('deep porch ceiling',[.13,-2.48,.85],[0,0,1],{'cream dressings'},(4.15,4.22))
    ray('central gable attic light',[.17,-1.82,15.48],[0,1,0],{'casement glass'},(1.77,1.81))
    ray('central raised roof ridge',[5.86,7.08,26],[0,0,-1],{'burnt clay tiles','sunlit tile lips'},(6.55,6.78))
    for x in (-14.1,25.11):
        ray('flanking clay field below the center ridge',[x,10.92,26],[0,0,-1],{'burnt clay tiles','sunlit tile lips'},(8.90,9.52))
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
