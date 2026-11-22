"""Verify the portico openings, actual window walls, balustrade gaps, steps and limits in all three delivered meshes."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='jingan-beijing-road-1394-garden-loggia'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    samples=[]
    def cast(label,start,direction,maxlen,materials,interval):
        hit=scene.ray(start,direction,maxlen)
        if materials:
            ok=bool(hit and hit['material'] in materials and interval[0] <= hit['distance_m'] <= interval[1])
        else:
            ok=hit is None
        samples.append(dict(check=label,start=start,direction=direction,maxlen=maxlen,
                            expected_materials=materials,expected_distance_m=interval,actual=hit,passed=ok))
    for x in (-3.24,-1.08,1.08,3.24):
        for z in (.62,.97,1.74,2.66,2.83):
            cast('standing exterior column and capital',[x,-2.,z],[0,1,0],2.1,['pale stucco trim'],[1.76,1.89])
    for x in (-2.16,0,2.16):
        for z in (1.49,2.17,2.57,2.82,3.15):
            cast('pass through each real front vault',[x+.14,-.75,z],[0,1,0],2.05,[],[0,0])
        for offset in (-.39,0,.39):
            cast('three vaults have moulded heads',[x+offset,-1,3.90],[0,1,0],1.4,['pale stucco trim','ivory render'],[.86,1.06])
        for dx in (-.29,.19):
            for z in (5.46,6.20,6.82):
                cast('upper dark glazed French windows',[x+dx,.44,z],[0,1,0],1.5,['shaded glass'],[1.20,1.31])
    for x in (-.33,.03,.39):
        for z in (.80,1.69,2.21):
            cast('central vestibule reaches the dark open threshold',[x,-1.,z],[0,1,0],3.2,['inner threshold shadow'],[2.95,3.02])
    for x in (-2.16,2.16):
        for dx in (-.21,.21):
            for z in (1.40,1.62,2.21):
                cast('side glass behind loggia',[x+dx,.56,z],[0,1,0],1.45,['shaded glass','timber sash'],[1.05,1.20])
    for y,z in ((-.99,.135),(-.64,.27),(-.36,.405),(-.04,.54),(.73,.54),(1.37,.54)):
        for x in (-.63,0,.63):
            cast('three stone rises and raised porch floor',[x,y,1.1],[0,0,-1],1.2,['stone step','porch paving'],[1.1-z-.004,1.1-z+.004])
    for x in (-2.59,-1.43,-.56,.55,1.51,2.64):
        cast('upper terrace floor',[x,.54,5.48],[0,0,-1],.8,['terrace surface'],[.375,.385])
    for x in (-2.7,-.5,.83,2.47):
        cast('handrail cap',[x,-.029,6.22],[0,0,-1],.9,['pale stucco trim'],[.24,.27])
    for a,b in ((-3.27,-1.11),(-1.04,1.04),(1.11,3.27)):
        d=(b-a)/9
        for i in [1,3,5,7]:
            cast('turned upper baluster solid',[a+(i+.5)*d,-1.,5.51],[0,1,0],1.1,['pale stucco trim'],[.85,1.03])
            cast('true daylight between turned balusters',[a+i*d,-.7,5.51],[0,1,0],1.9,[],[0,0])
    for x in [-4.06,3.84]:
        cast('both adjoining sections outside the independent model',[x,-1.2,3.84],[0,1,0],3.9,[],[0,0])
    return dict(passed=all(s['passed']for s in samples),samples=samples)

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
