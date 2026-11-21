from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='xuhui-cavendish-court-street-window-bands'
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
    for z0 in [.20,3.35]:
        for a,b,n in [(-1.99,-1.05,2),(.06,1.98,3)]:
            step=(b-a)/n
            for i in range(n):
                x=a+(i+.5)*step
                for dz in [.29,.73,1.37]:
                    sample('clear glazing behind the metal front',x,z0+dz,['shaded glass','daylit glass'],[1.178,1.185])
                sample('horizontal steel transom',x,z0+1.08,['grey steel'],[1.079,1.093])
                sample('steel head',x,z0+1.623,['grey steel'],[1.079,1.093])
            for i in range(1,n):
                sample('separate vertical steel mullion',a+step*i,z0+.81,['grey steel'],[1.071,1.083])
            for x in [a+.02,b-.02]:
                sample('outer jamb steel in the wall reveal',x,z0+.56,['grey steel'],[1.080,1.09])
        for j in [2,6,9,13,17,20]:
            for x in [-.93,-.54,-.09,2.14,2.50]:
                sample('brick front surface',x,z0+(j+.5)*1.64/23,['oxblood brick','brown brick','light mortar'],[.985,1.004])
            sample('visible light horizontal pointing',-.55,z0+j*1.64/23,['light mortar'],[.996,1.006])
        for x in [-2.8,-2.23]:
            sample('plain pier beside the left window',x,z0+.78,['cream roughcast'],[.974,.985])
        sample('separate street rainpipe cylinder',-2.63,z0+.835,['dark rainpipe'],[.829,.848])
    for x in [-2.96,-2.27,-1.65,-.7,0,.9,1.8,2.44]:
        for z in [.07,2.27,2.86,5.16]:
            sample('unbroken pale roughcast between the bands',x,z,['cream roughcast'],[.974,.985])
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
