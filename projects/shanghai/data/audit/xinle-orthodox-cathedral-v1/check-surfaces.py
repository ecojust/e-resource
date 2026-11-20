"""Measure visible dome skins, drum recesses, windows and north doors on all three GLBs."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import runpy
import subprocess
import tempfile

AUDIT = Path(__file__).resolve().parent
PROJECT = AUDIT.parents[2]
ID = 'xuhui-xinle-orthodox-cathedral'
SerialScene = runpy.run_path(str(PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
DECODER = PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'


def probes(path):
    mesh = SerialScene(path)
    checks = []

    def cast(label, origin, direction, expected, length=7, distance=None):
        hit = mesh.ray(origin, direction, length)
        passed = (hit is None if expected is None else
                  hit is not None and hit['material'] == expected
                  and (distance is None or abs(hit['distance_m']-distance) <= .065))
        checks.append(dict(label=label, origin=origin, direction=direction, length=length,
                           first_surface=expected, expected_distance_m=distance, hit=hit, passed=passed))

    # Origins and directions below are in the authored Z-up frame converted by SerialScene.
    towers = [('central',0,0,4.65,20.4,28.3,12), ('northeast',6.25,7,2.28,15.85,21.70,8),
              ('northwest',-6.25,7,2.28,15.85,21.70,8),('southeast',6.25,-7,2.28,15.85,21.70,8),
              ('southwest',-6.25,-7,2.28,15.85,21.70,8)]
    for name,x,y,radius,bottom,top,count in towers:
        for i in range(count):
            step = math.tau/count
            direction = ((i+.55)*step)
            dx, dy = math.cos(direction), math.sin(direction)
            origin = [x+(radius+.75)*dx, y+(radius+.75)*dy, bottom+.41*(top-bottom)]
            cast(name+' drum pane '+str(i+1),origin,[-dx,-dy,0],'smoky recessed glazing',1.6)
        height = 6.49 if name=='central' else 3.55
        r = 4.91 if name=='central' else 2.47
        z = top-.02+.16*height
        for i in range(4):
            angle = math.tau*i/4+.115
            dx,dy = math.cos(angle),math.sin(angle)
            cast(name+' copper shoulder '+str(i+1),[x+(r+.65)*dx,y+(r+.65)*dy,z],[-dx,-dy,0],'blue painted copper',1.8)
        cast(name+' metal finial',[x+.004,y+.002,top-.02+height+1.05],[0,0,-1],'weathered finial metal',1.4,.82)

    for sign in [-1,1]:
        cast('north double door '+str(sign),[sign*.77,16,2.10],[0,-1,0],'dark green entrance doors',5,3.625)
        cast('north arched door casing '+str(sign),[sign*1.60,16,2.46],[0,-1,0],'pale moulded plaster',5,3.21)
        cast('north lower slit '+str(sign),[sign*(3.77+.13),16,2.21],[0,-1,0],'smoky recessed glazing',5,3.70)
        cast('north upper slit '+str(sign),[sign*(3.77+.13),16,7.51],[0,-1,0],'smoky recessed glazing',5,3.70)
        cast('east paired lower slit '+str(sign),[16,sign*(2+.13),2.21],[-1,0,0],'smoky recessed glazing',6,4.55)
    cast('vertical bar in the north fanlight',[.014,16,5.88],[0,-1,0],'dark glazing bars',5,3.54)
    cast('middle moulded arch course',[1.78,16,2.35],[0,-1,0],'pale moulded plaster',5,3.268)
    cast('outer moulded arch course',[1.98,16,2.35],[0,-1,0],'pale moulded plaster',5,3.318)
    cast('upper glass of north door',[.45,16,5.19],[0,-1,0],'smoky recessed glazing',5,3.70)
    for side in (-1,1):
        for radius in (.45,.775):
            cast('north leaf raised circle '+str((side,radius)),[side*.7625,16,2.91+radius],[0,-1,0],
                 'dark green entrance doors',5,3.576)
    for u in (2.473,2.627):
        cast('white numeral on address plate '+str(u),[-u,16,3.618],[0,-1,0],'porcelain numerals',5,3.306)
    cast('green enamel behind the numerals',[-2.55,16,3.43],[0,-1,0],'green enamel address plate',5,3.315)
    for i in range(4):
        cast('north stone stair '+str(i+1),[.15,12.62+.11+.22*i,.90],[0,0,-1],
             'grey threshold and plinth',1,.38+.13*i)
    cast('plaster in front of the inset roof edge',[3.08,16,12.47],[0,-1,0],'ivory mineral plaster',5,3.38)
    cast('east central pier between two windows',[16,0,1.85],[-1,0,0],'ivory mineral plaster',6,4.23)
    cast('space above north pavement',[0,15.1,2.4],[0,1,0],None,2)
    cast('space along east pavement',[13.1,0,1.7],[1,0,0],None,2)
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
