"""Read the actual packed facade and test individual flutes, portals and upper windows."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='hongkou-unrra-gray-building-north-front'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    samples = []
    def probe(label, origin, direction, material, minimum, maximum, length=30):
        hit = scene.ray(origin,direction,length)
        valid = hit is None if material is None else (hit is not None and
                hit['material'] in material and minimum <= hit['distance_m'] <= maximum)
        samples.append(dict(label=label,origin=origin,direction=direction,allowed=material,
                            expected_distance_m=[minimum,maximum],hit=hit,passed=valid))
    stone='light grey fluted stone';glass='smoky blue glass';base='dark grey base stone';cornice='grey cornice stone'
    def front(label,x,z,material,a,b):probe(label,[x,-5,z],[0,1,0],[material],a,b)
    for i,x in enumerate([-12,-7.2,-2.4,2.4,7.2,12],1):
        tag=f'pilaster {i}'
        front(tag+' raised ridge',x,10.51,stone,5.79,5.83)
        for j in range(6):
            front(tag+f' flute {j+1}',x+(j-2.5)*.228,10.51,stone,5.895,5.923)
        front(tag+' topmost shaft',x,19.13,stone,5.79,5.83)
        front(tag+' square capital',x,19.70,cornice,5.55,5.61)
    for x in [-4.80,0,4.80]:
        front('recessed street door '+str(x),x+.20,3.83,'shadowed timber door',7.04,7.08)
    for x in [-9.60,9.60]:
        front('outer ground bay glass '+str(x),x+.40,3.23,glass,6.60,6.64)
    for x in [-9.6,-4.8,0,4.8,9.6]:
        for z in (8.24,12.52,16.76):
            front('three rows of broad windows '+str((x,z)),x+.34,z,glass,6.60,6.64)
    for x in (-17.77,-15.47,15.47,17.77):
        for z in (2.43,8.32,12.58,16.83):
            front('narrow wing windows '+str((x,z)),x+.17,z,glass,6.60,6.64)
    for pair in (-16.58,-9.6,-4.8,0,4.8,9.6,16.58):
        for offset in (-.70,.70):
            front('paired glazing above order '+str((pair,offset)),pair+offset+.13,22.03,glass,6.60,6.64)
    front('continuous dark coping',16.43,25.14,'dark coping',5.42,5.46)
    front('stone stringcourse between portals',0,6.39,cornice,5.89,5.94)
    front('wing clear of stringcourse',18.66,6.39,'warm grey masonry',6.28,6.32)
    front('pilaster continuous through stringcourse',2.4,6.39,stone,5.79,5.83)
    front('small central attic relief',.045,24.12,cornice,6.15,6.19)
    for j,x in enumerate((-4.6,.38,4.72)):
        probe('front step '+str(j),[x,.57,3],[0,0,-1],[base],2.806,2.834)
    probe('short construction section ends at rear',[0,5,13],[0,-1,0],['warm grey masonry'],1.65,1.70)
    probe('courtyard outside model depth',[0,4.55,12],[0,0,1],None,0,0,15)
    probe('road outside model extent',[0,.05,12],[0,0,1],None,0,0,15)
    return dict(passed=all(row['passed'] for row in samples),samples=samples)


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
