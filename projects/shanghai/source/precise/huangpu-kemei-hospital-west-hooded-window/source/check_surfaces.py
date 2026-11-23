"""Ray-check the west bay’s window, sloping canopy, coping and stepped cornice in each delivered mesh."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-kemei-hospital-west-hooded-window'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    checks = []
    def cast(name, origin, direction, materials, interval):
        hit = scene.ray(origin, direction, 6)
        passed = hit is None if not materials else (
            hit is not None and hit['material'] in materials and interval[0] <= hit['distance_m'] <= interval[1])
        checks.append(dict(check=name,origin=origin,direction=direction,expected_materials=materials,
                           expected_distance_m=interval,hit=hit,passed=passed))
    def front(name,x,e,materials,interval):
        cast(name,[x,-1.8,e-7.32],[0,1,0],materials,interval)
    brick=['rose brick','orange brick','brown brick','recessed joint']
    for x in [-1.02,-.90,-.75,.76,.91,1.03]:
        for e in [8.04,8.23,8.66,8.82,9.39,9.55,10.12,10.32,10.72,10.85]:
            front('brick side of recess',x,e,brick,[1.79,1.83])
    for x in [-.31,-.245,-.105,.12,.30,.38]:
        for e in [8.10,8.34,8.77,9.04,9.31,9.43]:
            front('glass behind brick face',x,e,['reflecting glass'],[1.995,2.024])
    for e in [8.11,8.34,8.86,9.34]:
        front('meeting stile',.025,e,['bronze sash'],[1.91,1.95])
    for x in [-.21,-.105,.30]:
        for e in [8.55,9.16]:
            front('horizontal sash',x,e,['bronze sash'],[1.91,1.95])
    for x in [-.73,-.55,-.35,-.10,.15,.36,.60,.73]:
        front('canopy fascia',x,9.782,['canopy face'],[1.303,1.32])
        for d in [.11,.23,.39]:
            # A genuine upward underside ray distinguishes the cantilever from a flat lintel.
            cast('canopy underside',[x,-d,9.49-7.32],[0,0,1],['canopy soffit'],[.23,.39])
            cast('sloping canopy surface',[x,-d,10.13-7.32],[0,0,-1],['canopy face'],[.17,.32])
    for x in [-1.11,-.60,0,.61,1.13]:
        front('parapet front',x,7.62,brick,[.70,.74])
        front('upper coping and drip',x,7.86,['coping stone'],[.667,.700])
        for e,d in [(10.54,.077),(11.12,.089),(11.225,.111),(11.305,.144),(11.395,.175),(11.495,.215)]:
            front('projecting brick cornice',x,e,['molded brick'],[1.80-d-.007,1.80-d+.007])
    for x,z in [(-1.36,10.22),(1.36,10.21),(0,11.67),(.62,7.10),(-.70,2)]:
        front('open beyond evidenced fragment',x,z,[],[0,0])
    return dict(passed=all(v['passed'] for v in checks),samples=checks)

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
