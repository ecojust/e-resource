from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='xuhui-baoqing-no3-iron-gallery'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    rows=[]
    def sample(label,x,z,expected,interval):
        hit=scene.ray([x,-1,z],[0,1,0],2.0)
        ok=hit is None if not expected else bool(hit and hit['material'] in expected and interval[0]<=hit['distance_m']<=interval[1])
        rows.append(dict(check=label,origin=[x,-1,z],direction=[0,1,0],materials=expected,distance=interval,hit=hit,passed=ok))
    for center in (-2.53,0,2.53):
        for dx in [-.77,-.47,.51,.76]:
            for z in [.440,.603,.770,.937,1.097]:
                sample('independent cast-iron horizontal bars',center+dx,z,['painted steel'],[1.016,1.029])
            sample('visible dark backing behind railing',center+dx,.696,['rebate shadow'],[1.346,1.361])
            sample('raised pale apron under balustrade',center+dx,.163,['cast pale stone'],[.942,.956])
        for dx in [-.9625,-.374,-.201,.201,.374,.9625]:
            sample('squared uprights in each photographed opening',center+dx,.685,['painted steel'],[1.012,1.039])
        for dx in [-.63,-.34,.34,.63]:
            for z in [1.48,1.94,2.44,2.69]:
                sample('glass behind the independent iron plane',center+dx,z,['shaded window glass'],[1.28,1.30])
        for dx in [-.47225,0,.47225]:
            sample('white window sash',center+dx,2.06,['white window frame'],[1.226,1.237])
        for dx in [-.9445,.9445]:
            sample('outer sash edges physically masked by masonry reveal',center+dx,2.06,['rebate shadow'],[1.115,1.126])
        for z in [1.721,2.221,2.590]:
            sample('white glazing bars',center+.35,z,['white window frame'],[1.261,1.272])
    for x in [-3.795,-1.265,1.265,3.795]:
        for z in [.252,1.041,2.47,2.857]:
            sample('brick face on central and side piers',x,z,['warm red brick','brown red brick','fine mortar'],[.978,1.004])
        sample('shallow pier neck below cornice',x,3.018,['weathered stone edge'],[.919,.931])
    for x in [-3.77,-2.53,-1.12,0,1.17,2.53,3.77]:
        sample('continuous pale stone cornice across bays',x,3.392,['cast pale stone'],[.742,.757])
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
