"""Ray-test the hospital iron gate, stone loggia, upper terrace and glazed openings."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-sino-german-hospital-courtyard-loggia'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    results=[]
    def ray(label,x,y,z,direction,span,materials,reach=7):
        hit=scene.ray([x,y,z],direction,reach)
        accepted=(hit is None) if not materials else bool(hit and hit['material'] in materials and span[0]<=hit['distance_m']<=span[1])
        results.append(dict(check=label,origin=[x,y,z],direction=direction,range_m=span,materials=materials,hit=hit,passed=accepted))
    def front(label,x,z,span,materials,y=-1.30,reach=7):ray(label,x,y,z,[0,1,0],span,materials,reach)
    for x in [-2.58,2.58]:
        for z in [4.81,5.38,5.89,6.35,6.84,7.43,7.88]:
            front('upper square portico shaft',x,z,[1.99,2.04],['warm render'])
        for z in [.47,.95,1.32,1.79,2.16,2.53,3.15]:
            front('ground square shaft behind the gate',x,z,[.49,.54],['warm render'],.22)
    for z in [5.83,6.32,6.63,7.02,9.96,10.37,10.90,11.12]:
        for x in [-1.34,-.23,.26,1.35]:
            front('setback loggia and terrace glazing',x,z,[5.435,5.453],['glass'])
    for x in [-1.81,-.83,.87,1.82]:
        for z in [5.94,6.48,7.1,10.20,10.75,11.26]:
            front('render between the glazed leaves',x,z,[5.27,5.29],['warm render'])
    for z in [.46,1.25,2.05,2.63]:
        for x in [-2.75,2.75]:front('masonry gatepost',x,z,[.32,.35],['dressed stone'])
    for x in [-2.0,-1.36,-.77,.68,1.37,2.12]:
        for z in [.17,.72,1.16,2.26]:front('pierced double gate horizontal bar',x,z,[.59,.62],['wrought iron'])
    for z in [.40,.94,1.53,2.60,3.18]:
        front('two gate leaves separated on the garden centreline',0,z,[0,0],[],reach=1.30)
    for z in [1.21,1.86,2.57]:
        for x in [-1.53,1.53]:
            front('ground glazed sidelights behind the gate',x,z,[3.60,3.77],['glass'],.46)
    for x in [-2.0,-1.5,-.87,-.32,.52,1.02,1.47,1.87]:
        front('continuous projecting balustrade coping',x,5.32,[2.15,2.19],['light stone'])
        front('upper iron top rail across terrace',x,9.72,[2.28,2.33],['wrought iron'])
    for x in [-1.55,-.62,.73,1.53]:
        for z,y in [(5.32,2.1),(6.15,2.45),(9.36,2.25),(10.36,2.85)]:
            expect=4.44 if z<8.78 else 8.78
            ray('walkable loggia slab behind the railing',x,y,z,[0,0,-1],[z-expect-.008,z-expect+.008],['light stone'])
    for x in [-3.80,3.75]:
        for z in [.9,2.0,5.7,7.5,10.5,12.2]:front('outside the modeled central bay',x,z,[0,0],[])
    return dict(passed=all(v['passed']for v in results),samples=results)

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
            if role!='raw':mesh.unlink()
    result=dict(id=ID,manifest_sha256=digest(args.manifest),checker_sha256=digest(Path(__file__)),
                reader_sha256=digest(READER),decoder_sha256=digest(DECODER),results=rows)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for role,r in rows.items():print(role,'pass' if r['passed'] else [q for q in r['samples'] if not q['passed']])
    return all(r['passed'] for r in rows.values())


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
