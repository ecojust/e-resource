"""Read the pointed garage, round gate, south arcade and square garden tower from all three delivered meshes."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

AUDIT = Path(__file__).resolve().parent
PROJECT = AUDIT.parents[2]
ID = 'changning-xinhua-lane-329-no17'
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

    for i in range(4):
        left=-.73-3.63/2+3.63*i/4
        normal('folding door raised panel',left+.35,1.45,'oxblood joinery')
        normal('folding door stile',left+.048,.81,'oxblood joinery')
    for x in (-2.61,1.14):
        normal('masonry garage jamb',x,1.62,'fired arch brick')
    for x in (-1.82,.31):
        z=2.78+.4*(1-abs((x+.73)/(3.63/2))**.76)+.11
        normal('pointed garage brick head',x,z,'fired arch brick')
    normal('radial joint at the two-centred crown',-.73,3.29,'lime mortar')
    normal('left side door stile',-4.81,1.87,'dark shutter')
    for x in (-4.56,-3.74):normal('small red lane door',x,1.87,'oxblood joinery')
    normal('main door grille',2.89+.40,1.70,'black iron')
    normal('main door glass through round porch',2.89+.28,1.70,'smoked window glass')
    normal('porch right brick jamb',3.86,1.27,'fired arch brick')
    normal('porch left brick jamb',1.92,1.27,'fired arch brick')
    normal('porch white side pier',4.12,2.04,'pale porch render')
    normal('small lane light',4.72,1.78,'smoked window glass')
    for x in (-3.79,-.89,1.68):
        normal('upper lane window',x,5.14,'smoked window glass')
    for x in (-4.21,-2.03,.13):
        cast('low garage and door roofs',[x,.37,5.66],[0,0,-1],('weathered barrel tile','raised tile roll'),3)
    for y in (2.045,5.115,8.365,11.475):
        cast('arcade open to inner casements',[7,y+.24,1.34],[-1,0,0],'smoked window glass',4)
        cast('garden arcade curved plaster crown',[7,y,3.42],[-1,0,0],'warm roughcast',3)
    for y in (3.55,6.79,10.07):
        cast('garden pier at ground level',[7,y,1.16],[-1,0,0],'warm roughcast',2)
    for y in (2.91,6.81,9.17,12.08):
        cast('iron upper garden rail',[7,y,4.52],[-1,0,0],'black iron',3)
    for y in (9.42,10.82,11.99):
        cast('third storey tower casement',[7,y,8.08],[-1,0,0],'smoked window glass',4)
    for y in (8.898,12.48):
        cast('shutter beside tower window',[7,y,8.14],[-1,0,0],('dark shutter','oxblood joinery'),4)
    for y in (9.66,10.55,11.64):
        cast('upper door onto garden terrace',[7,y,5.44],[-1,0,0],'smoked window glass',4)
    for x,y in ((-.68,4.02),(-3.70,3.13),(2.11,10.47)):
        cast('clay hipped roof',[x,y,12],[0,0,-1],('weathered barrel tile','raised tile roll'),6)
    normal('green enamel number plate beside porch',4.11,2.177,'green enamel')
    normal('ivory numeral one',4.10-.073,2.18,'ivory enamel')
    normal('top stroke of numeral seven',4.10+.062,2.255,'ivory enamel')
    for x in (2.91,3.57):
        cast('porch roof at low/front and high/back points',[x,-.83,5.50],[0,0,-1],('weathered barrel tile','raised tile roll'),3)
    for x in (-4.23,4.83):
        cast('small lane red awnings',[x,-.43,3.33],[0,0,-1],'oxblood joinery',1)
    for x in (1.62,4.16):normal('shaped canopy corbel',x,3.59,'pale porch render')
    for y in (9.655,10.685,11.717):
        cast('three separate upper casement mullions',[7,y,8.31],[-1,0,0],'dark shutter',4)
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
