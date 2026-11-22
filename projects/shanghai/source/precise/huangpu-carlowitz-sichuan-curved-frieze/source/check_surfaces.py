from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-carlowitz-sichuan-curved-frieze'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    from curved_frieze import R,HALF,xyz,BRICK,STONE
    from math import sin,cos
    results=[]
    def radial(name,s,z,d,mats,tol=.012):
        o=xyz(s,-.38,z);a=s/R;r=scene.ray(o,[-sin(a),cos(a),0],.8)
        results.append(dict(feature=name,origin=o,expected_radial_depth=d,materials=list(mats),observed=r,passed=bool(r and r['material']in mats and abs(r['distance_m']-.38-d)<tol)))
    for i in range(19):
        s=-HALF+(i+.50)*.24
        radial('vertical stone tile',s,.392,-.145,STONE);radial('lower drip edge',s,.254,-.14,['shaded return'])
        radial('raised cap',s,.686,-.203,['moulded cap'])
    for i in range(32):
        s=-HALF+(i+.5)*(2*HALF/32)
        radial('bottom of U relief',s,.565,-.188,['pale relief']);radial('open inner face of loop',s,.61,-.167,['ornament ground'])
    for i in range(36):
        s=-HALF+.013+i*.126+.027;radial('projecting red brick tooth',s,.201,-.089,['dentil brick'])
        radial('gap between adjacent teeth',s+.070,.201,-.042,['deep brick fascia'])
    for i in range(15):
        radial('red brick directly above stone',-HALF+(i+.51)*.225,.782,-.002,BRICK)
    return dict(passed=all(r['passed']for r in results),samples=results)

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
