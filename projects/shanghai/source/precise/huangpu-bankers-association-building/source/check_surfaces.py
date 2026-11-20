"""Sample the four freestanding shafts, both responds, recessed portal and attic on the actual GLBs."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-bankers-association-building'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']


def test(scene):
    rows=[]
    def shot(label,x,z,mat,y,tolerance=.045):
        hit=scene.ray([x,-3,z],[0,1,0],45)
        passed=hit is None if mat is None else (hit is not None and hit['material']==mat and abs(hit['distance_m']-(3+y))<tolerance)
        rows.append(dict(label=label,origin=[x,-3,z],direction=[0,1,0],expected_material=mat,expected_y_m=y,actual=hit,passed=passed))
    def down(label,x,y,mat,z):
        hit=scene.ray([x,y,20],[0,0,-1],25)
        passed=hit is None if mat is None else (hit is not None and hit['material']==mat and abs(hit['distance_m']-(20-z))<.035)
        rows.append(dict(label=label,origin=[x,y,20],direction=[0,0,-1],expected_material=mat,expected_z_m=z,actual=hit,passed=passed))
    stone='warm artificial stone';pale='raised stone mouldings';glass='smoked window glass'
    for x in [-4.41,-1.47,1.47,4.41]:
        shot('detached fluted round shaft',x,3.10,stone,.208,.08)
        shot('shaft plinth',x,.32,stone,.045,.012)
        shot('column top abacus',x,8.488,pale,-.095,.018)
    for x in [-7.35,7.35]:
        shot('engaged terminal shaft, flat fluted face',x+(.18 if x<0 else -.18),3.10,stone,.16,.035)
        shot('engaged terminal plinth',x,.31,stone,.045,.012)
    for x in [-5.88,-2.94,0,2.94,5.88]:
        shot('second-storey light deep behind the columns',x+.21,5.73,glass,2.99)
        shot('third-storey light above projecting entablature',x+.20,9.90,glass,.32)
    for x in [-9.14,9.14]:
        shot('outer bay barred lower light',x+.13,1.65,glass,.32)
        shot('outer bay upper light',x+.15,6.04,glass,.32)
        shot('terminal garland field',x,5.11,'weathered stone recess',-.10)
        shot('hanging central garland leaves',x,4.60,stone,-.211,.018)
    for x in [-.47,.47]:
        shot('recessed double door glass',x,2.14,glass,3.396)
    shot('outer 59 address panel',.171,3.54,'green address enamel',2.478,.018)
    shot('raised 5 on the plaque',-.094,3.612,'cream numerals',2.469,.018)
    shot('raised 9 on the plaque',.08,3.609,'cream numerals',2.469,.018)
    shot('historical cartouche centre',0,12.35,stone,-.19)
    shot('shield carved rim near crest',0,12.95,pale,-.286,.05)
    shot('rectangular cornice between first and second dentils',0,9.43,pale,-.59)
    for x in [-6.7,0,6.7]:
        down('roof cut in upper street range',x,3.65,'section stone',11.55)
    down('walkable pavement before the portico',0,-.75,None,None)
    down('rear block outside modeled strip',0,5.5,None,None)
    shot('outside the east terminal bay',-11.3,2.43,None,None)
    shot('outside the west terminal bay',11.3,2.43,None,None)
    return dict(triangles=len(scene.tri),samples=rows,passed=all(r['passed']for r in rows))


def digest(p):
    return sha256(p.read_bytes()).hexdigest()


def main():
    ap=ArgumentParser(description=__doc__)
    ap.add_argument('--manifest',type=Path,default=PROJECT/'assets/models/candidates'/ID/'manifest.json')
    ap.add_argument('--out',required=True,type=Path)
    args=ap.parse_args()
    m=json.loads(args.manifest.read_bytes())
    assert m['id']==ID
    rows={}
    with tempfile.TemporaryDirectory() as directory:
        for role in ('raw','full','lod'):
            a=m['assets'][role]
            original=args.manifest.parent/a['file']
            assert original.stat().st_size==a['bytes'] and digest(original)==a['sha256']
            mesh=original
            if role!='raw':
                mesh=Path(directory)/(role+'.glb')
                subprocess.run(['node',UNPACK,original,mesh,DECODER],check=True,stdout=subprocess.DEVNULL)
            rows[role]=dict(sha256=a['sha256'],**test(SerialScene(mesh)))
    result=dict(id=ID,manifest_sha256=digest(args.manifest),checker_sha256=digest(Path(__file__)),
                reader_sha256=digest(READER),decoder_sha256=digest(DECODER),results=rows)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for role,r in rows.items():print(role,'pass' if r['passed'] else [q for q in r['samples'] if not q['passed']])
    return all(r['passed'] for r in rows.values())


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
