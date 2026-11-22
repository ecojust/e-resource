from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='yangpu-pingliang-250-hip-roof-chimney'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']








def test(scene,role):
    samples=[]
    def check(label,origin,direction,depth,materials,tolerance=.008):
        h=scene.ray(origin,direction,4)
        ok=bool(h and h['material'] in materials and abs(h['distance_m']-depth)<tolerance)
        samples.append(dict(feature=label,origin=origin,direction=direction,expected_m=depth,hit=h,passed=ok))
    red=['russet brick','deep brick','brown brick']
    for j in range(13,31):
        z=.136+.078*j
        for x in (-.38,-.21,.14,.36):
            check('north face of alternating brick bond',[x,-1.,z],[0,1,0],.591,red)
        check('return of upper shaft',[1.1,.076,z],[-1,0,0],.547,red)
    for x in (-.57,-.49,-.32,-.14,0,.15,.32,.49,.57):
        check('outer light coping',[x,-1.,2.775],[0,1,0],.505,['weathered cap'])
        check('dark drip below coping',[x,-1.,2.695],[0,1,0],.535,['shadow course'])
    for x in (-.41,-.25,0,.25,.41):
        check('inset upper course',[x,-1,2.865],[0,1,0],.57,['cap side'])
    for x in (-1.41,-1.16,-.9,.84,1.11,1.38):
        for y in (-1.08,-.82,-.56,.56,.82,1.03):
            hit=scene.ray([x,y,2.0],[0,0,-1],3.)
            calc=.54+.47*y+.18*max(0,x-.57)
            passed=bool(hit and hit['material'] in ['brown tile','red tile','dark tile'] and abs((2-hit['distance_m'])-calc)<.09)
            samples.append(dict(feature='visible lapped clay roof',x=x,y=y,expected_underlay_z=calc,hit=hit,passed=passed))
    return dict(samples=samples,passed=all(s['passed'] for s in samples))

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
