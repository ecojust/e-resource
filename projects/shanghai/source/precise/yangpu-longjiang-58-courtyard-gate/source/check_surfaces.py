from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='yangpu-longjiang-58-courtyard-gate'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']








def test(scene,role):
    samples=[]
    def sample(x,z,label,material=None,y=0):
        hit=scene.ray([x,-.8,z],[0,1,0],2.1)
        passed=(not hit) if material is None else bool(hit and hit['material']==material and abs(hit['distance_m']-(y+.8))<.005)
        samples.append({'feature':label,'x':x,'z':z,'expected_material':material,'front':y if material else None,'hit':hit,'passed':passed})
    for x0,x1,z0,z1 in [(1.392,1.666,2.47,2.735),(1.914,2.038,1.95,2.343),(2.144,2.27,1.942,2.343),(2.377,2.498,1.938,2.34)]:
        for u in (.18,.5,.82):
            x=x0+(x1-x0)*u
            for v in (.18,.5,.82):
                sample(x,z0+(z1-z0)*v,'ray through the entire wall opening')
            sample(x,z0-.034,'solid render below each aperture','warm grey render')
        for z in (z0+.04,z1-.04):
            sample(x0-.027,z,'left cheek of actual opening','warm grey render')
            sample(x1+.027,z,'right cheek of actual opening','warm grey render')
    for i in range(10):
        x=.101+i*.09
        for z in (.77,1.3,2.18):
            sample(x,z,'inset red timber faces',['wood 1','wood 2','wood 3','wood 1','wood 2'][i%5],.100)
        for z in (.624,1.191):
            sample(x,z,'two exposed timber rails','weathered timber',.067)
    for x in (.184,.282,.362,.412):
        sample(x,1.914,'letter slot on the mailbox','dark joint',-.054)
        sample(x,1.748,'mailbox outer door','mailbox red',-.054)
    for x in (-1.61+.875*.10,-1.61+.875*.367,-1.61+.875*.634,-1.61+.875*.901):
        for z in (1.71,2.02,2.46,2.61):
            sample(x,z,'window bars stand in front of the glass','old iron',.031)
    for x in (.04,.62,1.3,1.89,2.14,2.54):
        sample(x,2.875,'continuous concrete coping','cement cap',-.072)
    sample(1.177,2.269,'face of actual green house number','green enamel',-.015)
    sample(.62,1.45,'small plate on the timber','brass plate',.084)
    return {'samples':samples,'passed':all(r['passed']for r in samples)}

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
