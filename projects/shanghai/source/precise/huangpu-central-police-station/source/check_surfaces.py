"""Verify the historic street wall, paired half-rounds, window spacing and three parapet levels."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-central-police-station'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']


def test(scene):
    rows=[]
    def sample(label,origin,direction,mat,distance,tol=.035):
        hit=scene.ray(origin,direction,55)
        passed=hit is None if mat is None else hit is not None and hit['material']==mat and abs(hit['distance_m']-distance)<tol
        rows.append(dict(label=label,origin=origin,direction=direction,expected_material=mat,expected_distance=distance,actual=hit,passed=passed))
    def front(label,x,z,mat,y):
        sample(label,[x,-3,z],[0,1,0],mat,3+y if y is not None else None)
    for x in [-20.95,-18.54,-16.13,-13.8,-6.38,-3.83,-1.28,1.28,3.83,6.38,13.8,16.13,18.54,20.95]:
        y=.09 if abs(x)<7 else .17
        for z in [5.99,12.14,21.66]:
            front('historical narrow glazed row',x+.19,z,'period window glass',y+.27)
        front('attic horizontal window group',x+.14,25.82,'period window glass',y+.27)
    for sign in [-1,1]:
        x=sign*10.12
        front('half-round upper recess',x,25.97,'dark historical infill',.04)
        front('coping above the raised band',x,28.82,'limestone sill',-.222)
        sample('raised band top',[x,1.05,32],[0,0,-1],'neutral section',32-28.89)
        sample('lower wing top',[sign*17,1.05,32],[0,0,-1],'neutral section',32-27.39)
    sample('central roof height',[0,1.05,32],[0,0,-1],'neutral section',32-27.87)
    front('beyond western cut',22.4,13.2,None,None)
    front('beyond eastern cut',-22.4,13.2,None,None)
    sample('beyond the modelled street relief',[0,2.2,32],[0,0,-1],None,None)
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
