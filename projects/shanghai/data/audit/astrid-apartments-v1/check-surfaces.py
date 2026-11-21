"""Verify the original and decoded street-corner meshes against the photographed gate, paired openings, projecting bays and crown."""
import argparse
from math import cos, sin, pi, hypot
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

AUDIT = Path(__file__).resolve().parent
PROJECT = AUDIT.parents[2]
ID = 'huangpu-astrid-apartments-corner'
SerialScene = runpy.run_path(str(PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
DECODER = PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'


def probes(path, simplified=False):
    mesh = SerialScene(path)
    checks = []

    def cast(label, origin, direction, expected, length=7, distance=None):
        hit = mesh.ray(origin, direction, length)
        passed = (hit is None if expected is None else
                  hit is not None and (hit['material'] in expected if isinstance(expected,tuple) else hit['material']==expected)
                  and (distance is None or abs(hit['distance_m']-distance) <= .008))
        checks.append(dict(label=label, origin=origin, direction=direction, length=length,
                           first_surface=expected, expected_distance_m=distance, hit=hit, passed=passed))

    def normal(label,x,z,material,depth=None,length=7):
        cast(label,[x,-4,z],[0,1,0],material,length,depth)

    for sign in (-1,1):
        for n,z in enumerate((4.36,7.60,10.84,14.08,17.32,20.56,23.80),1):
            normal(f'paired street sash {sign}, level {n}',sign*2.66,z+.81,'smoky window glass',3.97)
            normal(f'steel mullion {sign}, level {n}',sign*2.89,z+.81,'dark painted steel',3.81)
        normal('outer jamb of entrance',sign*2.22,1.5,'pale artificial stone',3.29)
        normal('inner tiled jamb',sign*2.049,1.50,'yellow ochre brick',3.44)
        normal('street-level side light',sign*3.29,1.02,'smoky window glass',3.97)
    for x in (-1.52,-.51,.51,1.52):
        normal('pressed metal in waist band',x+.16,.97,'patinated entrance metal',4.50)
    for x in (-1.61,-.805,.805,1.61):
        for z in (.44,1.50):normal('upright iron grille',x,z,'patinated entrance metal',4.4725)
        normal('dark backing between iron uprights',x+.057,1.50,'smoky window glass',4.80)
    for z in (1.79,1.99,2.09):
        normal('continuous rails below fanlight',.65,z,'patinated entrance metal',4.44)
    for index in (3,5,7,9,11,13):
        angle=pi*index/16
        normal('radial transom spoke',1.1275*cos(angle),2.11+.285*sin(angle),'patinated entrance metal',4.47)
    normal('upper round of fanlight',.0,2.534,'patinated entrance metal',4.458)
    normal('rectangular stone lintel',.33,3.40,'pale artificial stone',3.24)
    normal('raised shallow arch',.0,2.592,'sandstone geometry',3.54)
    for sign in (-1,1):
        for i in (0,2,4):
            x=.14+i*.289+.18
            z=(2.67+i*.018+2.95+i*.032)/2
            normal('relief on masonry fan',sign*x,z,'sandstone geometry',3.542)
    for x in (-.50,-.17,.17,.50):
        normal('vertical reeding on upper crown',x,24.72,'honey glazed tile',3.336)
    for sign in (-1,1):
        normal('outer shoulder moulding',sign*.962,22.43,'honey glazed tile',3.437)
        normal('inner crown rib',sign*.74,25.1,'sandstone geometry',3.387)
        normal('buff flanking strip below bracket',sign*.79,10.01,'honey glazed tile',3.415)
    for n in range(3):
        # Shelf edges step further over the entrance as they rise.
        normal('projecting corbel course',.79 if n==2 else .07,20.75+n*.23,'sandstone geometry',3.65-(.23+n*.02+(.28+n*.1)/2))
    for x in (-.604,-.302,.302,.604):
        normal('faceted hanging corbel',x,21.14,'honey glazed tile',3.065)
    for z in (22.61,22.79):
        normal('arched crown bas-relief',0,z,'honey glazed tile',3.324)
    normal('high diagonal crown fold',.07,27.05,'yellow ochre brick',3.329)
    normal('flat crest cap',0,31.12,'pale artificial stone',3.405)
    normal('metal mast',.004,32.29,'patinated entrance metal')
    for side,(a,b) in {'west':((-9.71,9.21),(-6.05,1.63)),'east':((5.25,2.41),(8.49,9.21))}.items():
        dx,dy=b[0]-a[0],b[1]-a[1]
        span=hypot(dx,dy)
        tx,ty=dx/span,dy/span
        nx,ny=ty,-tx
        def wing(label,u,z,material,depth):
            origin=[(a[0]+b[0])/2+tx*u+nx*3,(a[1]+b[1])/2+ty*u+ny*3,z]
            cast(side+' '+label,origin,[-nx,-ny,0],material,5,depth)
        for n,z in enumerate((4.36,7.60,10.84,14.08,17.32,20.56,23.80),1):
            wing(f'projecting bay glazing {n}',.30,z+.85,'smoky window glass',2.76)
            wing(f'projecting bay mullion {n}',0,z+.85,'dark painted steel',2.60)
            wing(f'projecting bay head {n}',.70,z+2.50,'honey glazed tile',2.37)
    cast('retained-side junction',[0,12,15],[0,-1,0],'section plane',5)
    cast('limited solid roof',[0,3.5,29],[0,0,-1],'grey roof felt',3)
    cast('pale entrance step',[.7,-.58,1],[0,0,-1],'pale artificial stone',2,.917)
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
