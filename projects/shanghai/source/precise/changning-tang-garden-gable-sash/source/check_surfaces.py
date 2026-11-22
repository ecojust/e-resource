from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='changning-tang-garden-gable-sash'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']








def test(scene,role):
    samples=[]
    def shoot(x,z,mat,y,label):
        hit=scene.ray([x,-.75,z],[0,1,0],1.5)
        passed=not hit if mat is None else bool(hit and hit['material'] in mat and abs(hit['distance_m']-.75-y)<.004)
        samples.append(dict(feature=label,x=x,z=z,material=mat,depth=y,hit=hit,passed=passed))
    for x in [-.42,-.31,-.16,.15,.27,.42,.49]:
        for z,m in [(.62,'sky reflection'),(.97,'reflected blue'),(1.27,'sky reflection'),(1.52,'reflected gold')]:shoot(x,z,[m],.144,'each of four glazed panels per leaf')
        for z in (.835,1.131,1.396):shoot(x,z,['sash red'],.094,'three horizontal glazing bars')
    for x in (-.56,-.016,.048,.568):
        for z in (.61,.90,1.19,1.55):shoot(x,z,['sash red'],.080,'jamb and paired meeting stiles')
    for x in (-.68,-.45,-.26,-.06,.17,.37,.57,.67):
        shoot(x,.413,['blue grey stone'],-.122,'projecting stone sill')
        shoot(x,2.696,['shade return'],-.316,'folded front edge of hood')
    def rectify(u,v):
        d=1-.00005386039015484505*u+.00004602515339975119*v
        return (.007870437701085326*u-.00022731245425621974*v-1.9003293740718754)/d,(-.003186649388646107*u-.009139069944796374*v+4.908281814957285)/d+.43
    for p,q in [((243,118),(278,143)),((239,120),(213,169)),((276,145),(254,173)),((231,113),(240,94)),((240,94),(250,100)),((270,140),(280,123)),((280,123),(290,129)),((198,177),(207,158))]:
        for t in (.24,.67):shoot(*rectify(p[0]+t*(q[0]-p[0]),p[1]+t*(q[1]-p[1])),['iron painted pale grey'],-.045,'iron anchor above hood')
    bricks=['burnt sienna','red ochre','umber brick','rose brick']
    for x in [-.96,-1.17,-1.35,.97,1.16,1.34]:
        for z in (.87,1.14,1.51):shoot(x,z,bricks,0,'solid gable brickwork at sides of sash')
    for x,z in [(-2.6,1.3),(2.95,1.4),(-1.2,4.5),(.9,4.5)]:shoot(x,z,None,0,'sky outside the two coping slopes')
    return dict(samples=samples,passed=all(r['passed'] for r in samples))

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
