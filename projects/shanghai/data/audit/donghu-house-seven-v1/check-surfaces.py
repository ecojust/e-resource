"""Read the canopy, Ionic order, projecting wings and tiled hip from all three delivered meshes."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

AUDIT = Path(__file__).resolve().parent
PROJECT = AUDIT.parents[2]
ID = 'xuhui-donghu-hotel-house-seven'
SerialScene = runpy.run_path(str(PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
DECODER = PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'


def probes(path, simplified=False):
    mesh = SerialScene(path)
    checks = []

    def cast(label, origin, direction, expected, length=7, distance=None):
        hit = mesh.ray(origin, direction, length)
        passed = (hit is None if expected is None else
                  hit is not None and hit['material'] == expected
                  and (distance is None or abs(hit['distance_m']-distance) <= .008))
        checks.append(dict(label=label, origin=origin, direction=direction, length=length,
                           first_surface=expected, expected_distance_m=distance, hit=hit, passed=passed))

    def normal(label,x,z,material,depth=None,length=7):
        cast(label,[x,-4,z],[0,1,0],material,length,depth)

    for sign in (-1,1):
        x=sign*7.43
        normal('arched window pane',x+.19,6.36,'garden window glass')
        normal('arch steel centre mullion',x,6.36,'dark steel')
        normal('carved flower garland beside arch',x+.98,7.76,'pale carved granite')
        normal('ashlar beside floral relief',x+1.76,7.76,'light granite')
        normal('floral central keystone',x,7.83,'pale carved granite')
        normal('festoon terminal',x+1.44,7.64,'pale carved granite')
        normal('stepped wing parapet',x,9.24,'light granite')
        normal('matching upper parapet cap',x,9.50,'pale carved granite')
        normal('window iron horizontal rail',x+.40,5.47,'dark steel')
        cast('stone planter bowl',[sign*2.21,-5.38,1.5],[0,0,-1],'garden steps',2,.68)
        cast('door post',[sign*1.99,-6.0,2.1],[0,1,0],'brown canopy frame',3)
        cast('projecting wing wall behind canopy',[x+1.78,-2.50,2.28],[0,1,0],'light granite',4)
    for x in (-.83,.83):
        cast('glass entrance leaf behind the stairs',[x,-4.92,2.13],[0,1,0],'garden window glass',3)
        pull=x+(.65 if x<0 else -.65)
        cast('steel pull',[pull,-4.9,1.67],[0,1,0],'dark steel',3)
    for x in (-3.53,0,3.53):
        normal('upper central loggia glass',x+.30,6.12,'garden window glass')
        normal('upper central steel transom',x+.29,7.01,'dark steel')
        cast('ground door pane behind sunroom',[x+.27,-2,1.82],[0,1,0],'garden window glass',4)
    for axis in (-4.90,-1.77,1.77,4.90):
        for off in (-.19,.19):
            normal('capital cap in pair',axis+off,7.80,'pale carved granite')
            normal('shaft behind capitals',axis+off+.117,6.03,'light granite')
            cast('ground-floor round Tuscan column',[axis+off,-2.03,2.17],[0,1,0],'pale carved granite',3)
    for i in range(5):
        y=-5.87+i*.36+.09
        cast('individual stone stair',[-.36,y,1.45],[0,0,-1],'garden steps',2,1.45-(i+1)*.132)
    for x in (-5.89,4.64,7.22):
        cast('glazed roof between glazing bars',[x,-2.86,6],[0,0,-1],'reflective canopy glass',4)
    for i in (2,4,7,10):
        x=-9.44+i*2*9.44/12
        cast('roof glazing bar',[x,-2.86,6],[0,0,-1],'brown canopy frame',4)
    for x in (-2.38,0,2.38):
        cast('dormer pane in continuous window',[x+.17,.97,10.08],[0,1,0],'garden window glass',3)
    for x in (-1.01,.55,1.38):
        cast('sloping glazed entrance roof',[x,-4.80,6],[0,0,-1],'reflective canopy glass',3)
    for sign in (-1,1):
        cast('upper parapet ledge',[sign*7.43,-.52,11],[0,0,-1],'pale carved granite',3)
    for x in (5.8,6.6):
        cast('front reddish hipped roof',[x,1.15,11],[0,0,-1],'terracotta',3)
    return dict(triangles=len(mesh.tri),passed=all(r['passed']for r in checks),probes=checks)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,default=PROJECT/'assets/models/candidates'/ID/'manifest.json')
    parser.add_argument('--out',type=Path,default=AUDIT/'surface-checks.json')
    args=parser.parse_args()
    bundle=json.loads(args.manifest.read_bytes())
    results={}
    with tempfile.TemporaryDirectory() as tmp:
        for role in ('raw','full','lod'):
            entry=bundle['assets'][role]
            actual=args.manifest.parent/entry['file']
            sha=hashlib.sha256(actual.read_bytes()).hexdigest()
            assert actual.stat().st_size==entry['bytes'] and sha==entry['sha256']
            path=actual
            if role!='raw':
                path=Path(tmp)/(role+'.glb')
                subprocess.run(['node',DECODER,actual,path,PROJECT/'vendor/meshopt_decoder.module.js'],check=True)
            trial=probes(path,role=="lod")
            assert trial['triangles']==entry['triangles']
            results[role]=dict(sha256=sha,**trial)
    ok=all(row['passed'] for row in results.values())
    args.out.write_text(json.dumps(dict(id=ID,passed=ok,variants=results),ensure_ascii=False,indent=2)+'\n')
    assert ok,{k:[r['label']for r in v['probes']if not r['passed']]for k,v in results.items()}


if __name__=='__main__':
    main()
