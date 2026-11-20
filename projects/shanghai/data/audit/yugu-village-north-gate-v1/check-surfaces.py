"""Check actual first surfaces of the gate posts, enamel lettering, iron leaves and gaps."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

AUDIT = Path(__file__).resolve().parent
PROJECT = AUDIT.parents[2]
ID = 'jingan-yugu-village-north-gate'
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

    for x, z in [(-1.62728,1.68808), (-1.63298,1.41037), (-1.55907,1.22750),
                 (1.54272,1.68808), (1.53702,1.41037), (1.61093,1.22750)]:
        front('raised strokes on vertical name tablets', x, z, 'black calligraphic lettering', .977)
    for x, z in [(1.45465,2.35433), (1.57173,2.36492), (1.69948,2.36810),
                 (1.82905,2.36207), (1.66332,2.27037)]:
        front('painted address lettering', x, z, 'pale enamel letters', .962)
    for side in (-1, 1):
        x = side * 1.585
        front('bare ivory field beside lettering', x+.116, 1.58, 'ivory name tablet', .980)
        front('outer moulded name-tablet rim', x+.137, 1.65, 'lighter dressed stone', .975)
        front('raised centre of post crown', x, 2.79, 'gray cast stone', .996)
        front('space above cut crown shoulder', x+.148, 2.76, None)
        front('unadorned lower post', x, .64, 'gray cast stone', .996)
        for n in range(3):
            u = side * (2.375+n*.072)
            front('stepped outer return fin', u, 2.41+n*.071,
                  'lighter dressed stone' if n==1 else 'gray cast stone')
        for z in (.327,1.84):
            front('two external hinge barrels', side*1.3752, z, 'weathered iron edges')
    front('bronze panel face', -2.07, 1.42, 'dark commemorative plaque', 1.004)
    front('narrow bronze perimeter', -2.304, 1.41, 'aged metal rim', .996)
    front('blank green strip behind address letters', 1.64, 2.415, 'green enamel address sign', .965)
    for panel, cx in enumerate((-1.05,-.35,.35,1.05), 1):
        for i in range(1,7):
            x = cx-.34+.68*i/7
            front(f'panel {panel} picket {i}', x, .62, 'dark ironwork', 1.203)
            front(f'panel {panel} spear {i}', x, 2.337, 'weathered iron edges', 1.204)
        front(f'panel {panel} central diamond tip', cx, 1.428, 'weathered iron edges')
        front(f'panel {panel} through lower grille', cx, .73, None)
        front(f'panel {panel} horizontal rail', cx, .278, 'dark ironwork')
    front('clear sky over centre of gate', .02, 2.51, None)
    front('open pavement past east side', -2.69, 1.12, None)
    front('open pavement past west side', 2.69, 1.12, None)
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
