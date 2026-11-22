from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='hongkou-dongtiyuhui-23-timber-gable'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']








def test(scene,role):
    rows=[]
    def cast(k,x,z,mat,depth):
        h=scene.ray([x,-.6,z],[0,1,0],1.06)
        ok=h is not None and h['material']in mat and abs(h['distance_m']-depth)<.008
        rows.append(dict(feature=k,x=x,z=z,materials=sorted(mat),expected_depth=depth,hit=h,passed=ok))
    for side in (-1,1):
        for x in (.274,.77,1.35):
            cap=1.87-abs(x)*1.87/2.03
            for frac in (.26,.45,.66,.84):
                cast('timber upright in gable',side*x,cap*frac,{'warm timber'},.552)
        for t in (.16,.31,.47,.66,.82):
            x=side*(.318+.452*t)
            z=.55+((1.87-.77*1.87/2.03-.059)-.55)*t
            cast('rising timber brace',x,z,{'worn timber'},.539)
            cast('descending timber brace',x,.55+(.027-.55)*t,{'warm timber'},.539)
        for x,z in ((.48,.56),(.55,.52),(.52,.44),(1.0,.26),(1.10,.32),(1.21,.23)):
            cast('infill inside a framed panel',side*x,z,{'infill'},.616)
        for x in (.43,.63,.94,1.19,1.42):
            z=2.101-(2.101-.024)*x/2.19
            cast('painted bargeboard',side*x,z,{'barge fascia'},.263)
        for x,z in [(1.34+.024,.050),(1.34+.066,.052),(1.34+.116,.042)]:
            cast('solid curved corner brace',side*x,z,{'warm timber'},.545)
    for x in (-.15,-.08,.03,.10,.17):
        for z in (.68,.807,.94,1.012):cast('upper central glass',x,z,{'window glass'},.662)
        for z in (.24,.37):cast('blind panel under the glazing',x,z,{'infill'},.616)
    for x in (-1.49,-1.21,-.96,-.626,-.14,.12,.51,.99,1.22,1.49):
        cast('timber foot across the gable',x,-.067,{'worn timber'},.523)
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
