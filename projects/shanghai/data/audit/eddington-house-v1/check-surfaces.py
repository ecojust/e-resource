"""Check the as-built street elevation, curved balconies, glazing and entrance in all three emitted meshes."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

AUDIT = Path(__file__).resolve().parent
PROJECT = AUDIT.parents[2]
ID = 'jingan-eddington-house'
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

    # The two storeys at road level precede the six balcony levels.
    for side in (-1,1):
        x=side*14.50
        normal('shop glazing',x,.88,'blue grey glazing')
        normal('mezzanine glazing',x,4.11,'blue grey glazing')
        for level,(z,outer) in enumerate(zip([5.82,9.23,12.64,16.05,19.46,22.87],
                                             [20.65,20.65,20.65,20.65,17.76,15.58])):
            normal('long balcony parapet',side*(outer-2.4),z+.44,'ivory balcony render')
            normal('projecting stone drip',side*(outer-2.4),z-.13,'grey threshold')
            cast('rounded parapet end',[side*24,1.56,z+.55],[-side,0,0],'ivory balcony render',11)
            normal('glazed room behind balcony',side*(11.25 if level<5 else 10.12),z+1.47,'blue grey glazing',length=11)
        for x0 in (3.48,5.34):
            for z in (5.82,12.64,19.46,22.87):
                normal('brick spandrel',side*x0,z+.18,'umber spandrel brick')
                normal('tall casement glass',side*(x0+.23),z+1.12,'blue grey glazing')
        for z in (1.15,1.58,2.01):
            normal('striped jamb dark band',side*2.28,z,'charcoal masonry band')
            normal('striped jamb light band',side*2.28,z+.21,'ivory balcony render')
    for z in (5.82,9.23,12.64,16.05):normal('centre balcony',.42,z+.44,'warm roughcast')
    for z in (19.46,22.87):
        normal('uninterrupted pale pier over the four central balconies',.25,z+1.42,'warm roughcast')
        for u in (-5.34,-3.48,3.48,5.34):
            normal('continuous brick surround beside upper casement',u+.71,z+1.36,'umber spandrel brick')
    for z in (27.66,28.01,28.28,28.63):normal('four stepped tiers at the parapet',0,z,'ivory balcony render')
    for side in (-1,1):
        for z in (20.15,24.22):
            cast('upper rear return behind stepped wing',[side*10.30,15,z],[0,-1,0],'warm roughcast',6)

    for i in range(3):normal('independent entrance canopy blade',.79,3.61+i*.185,'ivory balcony render')
    normal('recessed door glazing',.53,1.08,'blue grey glazing',depth=5.49)
    normal('green address plate',2.49,2.59,'green number plate')
    strokes=[('常',-1.867,4.49237),('常',-1.88643,4.477),('德',-.60927,4.51282),('德',-.64943,4.51282),
             ('公',.59242,4.52017),('公',.5778,4.49152),('寓',1.87797,4.49127),('寓',1.86108,4.49138),
             ('1',2.16813,2.55135),('1',2.16242,2.57785),('9',2.28298,2.54875),('9',2.26532,2.54728),
             ('5',2.378,2.5635),('5',2.39467,2.56482)]
    for glyph,x,z in strokes:normal('entrance inscription '+glyph,x,z,'pale metal letters')
    for x in (-1.87,-.62,.62,1.87):normal('letter support above canopy',x,4.14,'bronze rails')
    cast('roof at upper south setback',[-16.1,6.70,28],[0,0,-1],'flat roof membrane',8)
    cast('roof at south lower setback',[-18.90,6.70,28],[0,0,-1],'flat roof membrane',11)
    cast('central roof',[0,5.40,30],[0,0,-1],'flat roof membrane',4)
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
