from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='hongkou-royal-hotel-paired-brick-roundels'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']








def test(scene,role):
    from math import pi,cos,sin
    samples=[]
    def probe(name,x,z,y=None,materials=()):
        hit=scene.ray([x,-.45,z],[0,1,0],1.03)
        ok=(hit is None) if y is None else bool(hit and hit['material'] in materials and abs(hit['distance_m']-(.45+y))<.005)
        samples.append(dict(feature=name,x=x,z=z,expected_front_m=y,expected_materials=materials,hit=hit,passed=ok))
    for c in (-.88,.88):
        for j in range(32):
            a=2*pi*(j+.5)/32
            if (j%8) not in (0,7):probe('radial voussoir',c+.54*cos(a),1.34+.54*sin(a),-.038,['red brick','sunlit brick','burnt brick','header'])
            probe('open circular light',c+.36*cos(a),1.34+.36*sin(a))
        for j in range(4):
            a=j*pi/2
            for radius in (.47,.54,.63):probe('raised cross key',c+radius*cos(a),1.34+radius*sin(a),-.082,['header'])
    for c in (-1.84,0,1.84):
        for j in (3,6,8,13,18):probe('bonded pier',c,.31+.077*(j+.5),-.065,['red brick','burnt brick','header'])
    for x in (-1.72,-1.23,-.71,-.33,.23,.62,1.15,1.63):
        probe('base cornice',x,.178,-.108,['red brick'])
        probe('pale raking cap',x,2.92-.43*abs(x)+.072,-.081,['stone coping'])
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
