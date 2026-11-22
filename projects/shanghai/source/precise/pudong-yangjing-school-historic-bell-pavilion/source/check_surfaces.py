from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='pudong-yangjing-school-historic-bell-pavilion'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']








def test(scene,role):
    samples=[]
    def take(o,d,mat,low,hi,label):
        hit=scene.ray(o,d,4);ok=bool(hit and hit['material']in mat and low<=hit['distance_m']<=hi)
        samples.append(dict(feature=label,origin=o,direction=d,expected_material=mat,distance_bounds_m=[low,hi],hit=hit,passed=ok))
    for sy in (-1,1):
        for sx in (-1,1):
            for z in [.12,.37,.75,1.16,1.58,1.90,2.15]:
                y=sy*(.405+(.292-.405)*z/2.45)
                x=.470+(.309-.470)*z/2.45
                take([sx*1.40,y,z],[-sx,0,0],['aged post','post highlight'],1.40-x-.057,1.40-x-.053,'outward splay of one of four posts')
    for x in [-.18,0,.18]:
        for z in [2.354,2.398]:
            take([x,-1.10,z],[0,1,0],['beam end'],.756,.76,'front load-bearing beam')
    for x in [-.17,-.09,0,.09,.17]:
        take([x,-.91,1.941],[0,1,0],['bronze lip'],.91-(.228**2-x*x)**.5-.003,.91-(.222**2-x*x)**.5+.004,'rolled lip flares out below bell waist')
    for z,rad in [(1.985,.188),(2.022,.168),(2.075,.153),(2.127,.143),(2.186,.133)]:
        for x in [-.069,0,.069]:
            dist=.91-(rad*rad-x*x)**.5
            take([x,-.91,z],[0,1,0],['bronze'],dist-.004,dist+.005,'bronze casting curves inward from mouth to shoulder')
    for x in [-.020,0,.020]:take([x,-.91,1.896],[0,1,0],['clapper'],.865,.888,'clapper visible below hollow bell')
    for x in [-.485,-.30,0,.30,.485]:
        take([x,-.35,2.87],[0,0,-1],['roof boards','weathered roof boards'],.26,.39,'individual roof boards around the four-legged shelter')
    for sx in [-1,1]:
        for y in [-.36,-.16,.16,.36]:take([sx*.395,y,2.87],[0,0,-1],['roof boards','weathered roof boards'],.30,.37,'opposite roof hips')
    return dict(samples=samples,passed=all(v['passed'] for v in samples))

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
