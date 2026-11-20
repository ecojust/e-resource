"""Check actual first surfaces of the paired arches, tile caps, enamel lettering, perforated wall and ironwork."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

AUDIT = Path(__file__).resolve().parent
PROJECT = AUDIT.parents[2]
ID = 'xuhui-yiyuan-jianguo-road-gate'
SerialScene = runpy.run_path(str(PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
DECODER = PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'


def probes(path):
    mesh = SerialScene(path)
    checks = []

    def cast(label, origin, direction, expected, length=7, distance=None):
        hit = mesh.ray(origin, direction, length)
        passed = (hit is None if expected is None else
                  hit is not None and hit['material'] == expected
                  and (distance is None or abs(hit['distance_m']-distance) <= .008))
        checks.append(dict(label=label, origin=origin, direction=direction, length=length,
                           first_surface=expected, expected_distance_m=distance, hit=hit, passed=passed))

    def front(label, x, z, material, distance=None):
        cast(label, [x, -1, z], [0, 1, 0], material, 2, distance)

    # The enamel and name probes were read from visible strokes in the original geometry.
    for material, x, z in [['black raised lane name', 1.93092, 2.38015], ['black raised lane name', 1.98907, 1.89577], ['ivory sign lettering', 1.79233, 2.76848], ['ivory sign lettering', 1.85417, 2.74595], ['ivory sign lettering', 1.94243, 2.75282], ['ivory sign lettering', 2.0025, 2.75497], ['ivory sign lettering', 2.0855, 2.76848], ['ivory sign lettering', 2.1307, 2.73805], ['ivory sign lettering', 2.1717, 2.76308], ['ivory sign lettering', 1.95915, 2.67687], ['ivory sign lettering', 1.95915, 2.67687], ['ivory sign lettering', 2.00893, 2.67585], ['ivory sign lettering', 2.04397, 2.67558], ['gilt iron ornament', -0.22212, 1.37058], ['gilt iron ornament', -0.53512, 1.37058], ['gilt iron ornament', -0.84812, 1.37058], ['gilt iron ornament', -1.16112, 1.37058], ['gilt iron ornament', -1.47412, 1.37058], ['gilt iron ornament', 0.05788, 1.37058], ['gilt iron ornament', 0.37088, 1.37058], ['gilt iron ornament', 0.68388, 1.37058], ['gilt iron ornament', 0.99688, 1.37058], ['gilt iron ornament', 1.30988, 1.37058]]:
        front('raised lettering' if 'ornament' not in material else 'gilt scroll on each sash', x,z,material)
    for x in (2.90,3.32,3.74,4.16,4.58):
        front('unobstructed square vent',x,2.11,None)
        front('wall between vents',x-.158,2.11,'warm pebble-dash plaster',1.0)
        front('wall below true vent',x,1.97,'warm pebble-dash plaster',1.0)
    for x in (-1.39,-.75,0,.75,1.39):
        spring=3.45+.60*(1-(x/1.65)**2)
        front('clear aperture under main arch', x,spring-.04,None)
        front('pale front arris',x,spring+.014,'cream painted arch soffit',.998)
        front('plaster over main arch',x,spring+.11,'warm pebble-dash plaster',1.)
    for x in (-2.76,-2.52,-3.0):
        h=2.34+.28*(1-((x+2.76)/.49)**2)
        front('open side passage under small arch',x,h-.08,None)
        front('pale arris on small arch',x,h+.015,'cream painted arch soffit',.998)
        front('small arch plaster band',x,h+.12,'warm pebble-dash plaster',1.)
        front('passage at shoulder height',x,1.37,None)
    for side in (-1,1):
        for i in range(1,10):
            x=side*1.615*i/10
            front('individual picket',x,.90,'painted black iron',1.2405)
            if i>1:front('gap between pickets',x-side*.053,.78,None)
        for z in (.085,1.19,2.02):
            front('continuous sash rail',side*.773,z,'painted black iron')
        for x in (.14,.766,1.392):
            h=2.19+.53*(1-(x/1.615)**2)
            front('gilded spearhead',side*x,h+.077,'gilt iron ornament')
    for x,z in ((-1.855,1.85),(2.22,2.78),(-3.38,.19),(3.57,.24)):
        mat={( -1.855,1.85):'brass plaque',(2.22,2.78):'green enamel address',(-3.38,.19):'gray brown base brick',(3.57,.24):'gray mortar'}[x,z]
        front('mounted plaque or masonry base',x,z,mat)
    for i in (0,5,10,18,25,32,36):
        x=-1.97+3.94*i/36
        h=3.64+.66*(1-(x/1.97)**2)
        front('charcoal barrel tile end',x,h+.047,'weathered charcoal barrel tile')
    for i in (0,4,7,13,19):
        front('red clay coping tile end',2.58+.116*i,2.668,'red clay barrel tile')
    front('sky over ridge',0,4.54,None)
    front('past east end',5.29,2.22,None)
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
            trial=probes(path)
            assert trial['triangles']==entry['triangles']
            results[role]=dict(sha256=sha,**trial)
    ok=all(row['passed'] for row in results.values())
    args.out.write_text(json.dumps(dict(id=ID,passed=ok,variants=results),ensure_ascii=False,indent=2)+'\n')
    assert ok,{k:[r['label']for r in v['probes']if not r['passed']]for k,v in results.items()}


if __name__=='__main__':
    main()
