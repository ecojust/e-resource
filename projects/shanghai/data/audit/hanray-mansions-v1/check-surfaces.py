"""Verify the Huaihai Road facade against standard sash apertures, central shopfront, flutes and curved rooftop terraces."""
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
ID = 'xuhui-hanray-mansions'
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

    # Compare against the surveyed normal of each of the two distinct projecting
    # bays. Angled glass must be behind its outer steel bars in both LODs.
    street={ 'west':((-18.25,0),(-5.70,0)), 'east':((5.70,0),(17.34,1.60)),
             'axis':((-5.48,2.74),(5.48,2.97)), 'tower':((-5.48,1.13),(5.48,1.36)) }
    def at(name, segment, u, z, expected, distance=None):
        a,b=street[segment];length=hypot(b[0]-a[0],b[1]-a[1]);dx,dy=(b[0]-a[0])/length,(b[1]-a[1])/length
        normal=[dy,-dx];point=[(a[0]+b[0])/2+dx*u,(a[1]+b[1])/2+dy*u]
        cast(name,[point[0]+4*normal[0],point[1]+4*normal[1],z],[-normal[0],-normal[1],0],expected,6,distance)
    for n,floor in enumerate([4.15,7.29,10.43,13.57,16.71],2):
        for wing in ('west','east'):
            a,b=street[wing];width=hypot(b[0]-a[0],b[1]-a[1])
            for band,offset,span,panels in [('outer',-.29,.25,3),('middle',.085,.41,5),('end',.395,.14,2)]:
                x=width*(offset-span/2+span*.50/panels)
                at(f'{wing} {band} pane floor {n}',wing,x,floor+.82,'blue grey window glass',4.32)
                x=width*(offset-span/2+span/panels)
                at(f'{wing} {band} metal bar floor {n}',wing,x,floor+.82,'weathered window metal')
            at(f'{wing} sill floor {n}',wing,width*.085,floor+.335,'pale artificial stone')
        for side in (-1,1):
            at(f'central sash glass {n} {side}','tower',side*3.66+.32,floor+.77,'blue grey window glass',4.32)
            at(f'central vertical fluting {n} {side}','tower',side*.80,floor+.7,'fine grooved ochre tile')
            at(f'central pilaster {n} {side}','tower',side*2.12,floor+.8,'pale artificial stone')
    for n,z in [(7,19.85),(8,22.99)]:
        for side in (-1,1):
            at(f'tower window {n} {side}','tower',side*3.66+.31,z+.77,'blue grey window glass',4.32)
            at(f'continuous outer pier {n} {side}','tower',side*2.12,z+.77,'pale artificial stone')
            at(f'continuous central flutes {n} {side}','tower',side*.80,z+.77,'fine grooved ochre tile')
    for side in (-1,1):
        at(f'paired narrow crown lights {side}','tower',side*.41,24.04,'blue grey window glass',4.32)
    at('rounded central roof crest','tower',0,25.53,'cream glazed brick')
    at('shop glazing left of doorway','axis',-3.98,1.24,'blue grey window glass',4.32)
    at('recessed glazed entrance','axis',.47,1.21,'blue grey window glass',4.32)
    at('entrance joinery','axis',0,1.10,'weathered window metal')
    at('shopfront fascia','axis',-.41,3.39,'pale artificial stone')
    for x,label in [(-18.9,'west'),(18.2,'east')]:
        cast(label+' rounded seventh floor parapet',[x,-4,20.90],[0,1,0],'cream glazed brick',12)
    for x,label in [(-15.0,'west'),(14.9,'east')]:
        cast(label+' rounded eighth floor parapet',[x,-4,23.84],[0,1,0],'cream glazed brick',14)
    for x,y,z,text in [(18.52,3.7,30,'seventh floor open terrace'),(14.5,5.4,30,'eighth floor open terrace'),(0,6.22,30,'top roof')]:
        cast(text,[x,y,z],[0,0,-1],'terrace paving',15)
    cast('open sky above cornice',[0,-4,27],[0,1,0],None,17)
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
