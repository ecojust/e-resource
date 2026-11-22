from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='jingan-ewo-packing-warehouse-river-balconies'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']








def test(scene,role):
    rows=[]
    def cast(k,x,z,mat,depth):
        h=scene.ray([x,-1.02,z],[0,1,0],1.60)
        rows.append(dict(feature=k,x=x,z=z,materials=sorted(mat),depth=depth,hit=h,passed=h is not None and h['material']in mat and abs(h['distance_m']-depth)<.014))
    for level,door,top in ((.43,.76,2.63),(3.19,.48,5.21)):
        for x in (-.98,-.67,-.42,-.21,0,.24,.43,.70,.95):
            cast('balcony top rail',x,level+.73,{'gallery iron'},.320)
            cast('flat iron fascia',x,level-.085,{'edge of deck'},.310)
        for j in range(1,21):
            x=-1.145+2.29*j/21
            cast('slender upright in front railing',x,level+.33,{'gallery iron'},.332)
            h=scene.ray([x+.039,-.88,level+.38],[0,1,0],.34)
            rows.append(dict(feature='clear interval beside an upright',x=x,hit=h,passed=h is None))
        for x in (-.31,-.16,.17,.32):
            for z in (.83,1.23,1.47):
                cast('door recessed behind gallery',x,level+z,{'rebated door'},1.175)
        for t in (-.88,-.67,-.42,-.15,.13,.37,.62,.84):
            x=door*t
            joint=door==.76 and t==.13
            cast('mortar in a radial joint' if joint else 'segmental brickwork over opening',x,top+.077*(1-t*t)+.067,{'mortar'} if joint else {'brick red','burnt red'},.975 if joint else .966)
        for x in (-1.04,1.04):
            for z in (.968,1.63):
                cast('brick pier alongside opening',x,level+z,{'brick red','burnt red','brick highlight'},1.005)
    return dict(samples=rows,passed=all(q['passed']for q in rows))

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
            rows[role]=dict(sha256=a['sha256'],**test(SerialScene(mesh),role))
            if role!='raw':mesh.unlink()
    result=dict(id=ID,manifest_sha256=digest(args.manifest),checker_sha256=digest(Path(__file__)),
                reader_sha256=digest(READER),decoder_sha256=digest(DECODER),results=rows)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for role,r in rows.items():print(role,'pass' if r['passed'] else [q for q in r['samples'] if not q['passed']])
    return all(r['passed'] for r in rows.values())


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
