from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='changning-qishan-village-inscribed-stone-panel'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    from inscribed_panel import INSCRIPTION
    rows=[]
    def check(label,x,z,material,depth):
        hit=scene.ray([x,-.5,z],[0,1,0],1.2)
        rows.append(dict(label=label,origin=[x,-.5,z],direction=[0,1,0],expected_material=material,expected_distance_m=.5+depth,observed=hit,
                         passed=bool(hit and hit['material']==material and abs(hit['distance_m']-(.5+depth))<.001)))
    for i,strokes in enumerate(INSCRIPTION):
        for stroke in strokes:
            for p,q in zip(stroke,stroke[1:]):
                t=.51
                check('raised golden stroke',-.532+i*.355+.0336*(p[0]*(1-t)+q[0]*t),.665-.0336*(p[1]*(1-t)+q[1]*t),'gilded relief',.008)
    for x in (-.495,-.37,-.21,-.03,.16,.28,.47):
        for z in (.254,.274,.715):check('recessed stone field',x,z,'letter field',.027)
    for x in (-.337,-.283,-.148,.018,.163,.293,.33):
        check('green plate',x,.888,'plate enamel',-.021)
        check('grey plate border',x,.784,'plate rim',-.017)
    for x in (-.338,.338):
        for z in (.802,1.01):check('corner screw',x,z,'aged screw',-.025)
    digits='1032弄1–148号'
    for index in (0,5,7):
        left=-(len(digits)-1)*.059*.5+index*.059-4.5*.006
        for gy in (3.4,4.5,6.7):
            check('number one white enamel',left+5*.006,.988-gy*.006,'enamel white',-.023)
    return dict(passed=all(r['passed'] for r in rows),samples=rows)

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
