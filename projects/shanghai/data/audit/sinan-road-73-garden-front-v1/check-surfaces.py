"""Check porch depth, both glazed galleries, side shutters, stairs and clay roofs."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

AUDIT = Path(__file__).resolve().parent
PROJECT = AUDIT.parents[2]
ID = 'huangpu-sinan-road-73-garden-front'
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

    def front(label,x,z,material,distance=None):
        cast(label,[x,-1,z],[0,1,0],material,5,distance)

    for x in (-2.65,-2.35,2.35,2.65):
        front('porch abutment',x,1.45,'grey pebble dash',1)
    for x in (-1.90,-1.35,1.35,1.90):
        front('through the arch to the recessed wall',x,1.53,'grey pebble dash',3.43)
    for x in (-.78,.28,.78):
        front('glazed door at the back of the porch',x,1.58,'dark recess glazing',3.49)
    front('inner door meeting stile',0,1.39,'red brown window timber',3.425)
    for x in (-1.75,-.85,0,.85,1.75):
        threshold=1.81+.46*(1-(x/2.25)**2)**.5
        front('arch masonry just above its crown',x,threshold+.045,'grey pebble dash',1)
        cast('clear immediately under the front arch',[x,-1,threshold-.045],[0,1,0],None,1.44)
    for sill in (3.25,6.61):
        for x in (-2.55,-1.34,.15,1.36,2.56):
            front('veranda handrail',x,sill+.93,'painted veranda timber')
        for i in (0,5,11,17,23):
            x=-2.86+.16+i*(5.72-.32)/23
            front('individual baluster',x,sill+.54,'painted veranda timber')
            if i < 23:
                behind='red brown window timber' if i in (5,11,17) else 'blue grey casement glass'
                front('casement visible between balusters',x+.123,sill+.54,behind)
        for x in (-1.43,0,1.43):
            front('meeting stiles of four casement groups',x,sill+1.46,'red brown window timber')
        for x in (-2.58,-1.16,.25,1.68):
            front('glazing above handrail',x,sill+1.55,'blue grey casement glass')
    for x in (-3.24,3.24):
        front('upper veranda masonry pier',x,8.55,'grey pebble dash')
    for x in (-2.78,2.78):
        front('masonry at curved upper shoulder',x,9.20,'grey pebble dash')
    for x in (-5.705,4.705):
        front('wing window shutter',x,4.18,'painted veranda timber')
    for x in (-6.035,-4.455,4.375,5.955):
        front('side clerestory',(x),7.1,'dark recess glazing')
    for label,x,y,material in [('cross gable crown',0,4,'terracotta ridge'),
                               ('western main roof',-4.27,5.41,'red clay roof tile'),
                               ('eastern main roof',4.18,6.41,'red clay roof tile'),
                               ('rear hip slope',2.15,13.37,'red clay roof tile'),
                               ('garden bay roof',1.40,3.41,'red clay roof tile'),
                               ('chimney pots',1.46-.1175,7.65,'terracotta ridge')]:
        cast(label,[x,y,16],[0,0,-1],material,10)
    for course in (19,20,21,22):
        for col in (21,24):
            x=col*.208+(course%2)*.104
            y=(course+.49)*.265
            material='red clay roof tile' if simplified else 'recessed clay tile joints'
            cast('tile end joint or continuous distant slope',[x,y,16],[0,0,-1],material,10)
    cast('sky beyond the eave',[7.80,4,16],[0,0,-1],None,18)
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
