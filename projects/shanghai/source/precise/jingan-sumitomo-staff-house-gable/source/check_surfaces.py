"""Check the four openings, outer shoulders, recessed glass, timber and eaves against the three delivered meshes."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='jingan-sumitomo-staff-house-gable'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    rows=[]
    def cast(label,x,z,expected,depth):
        hit=scene.ray([x,-.65,z],[0,1,0],1.55)
        ok = hit is None if not expected else bool(hit and hit['material'] in expected and depth[0]<=hit['distance_m']<=depth[1])
        rows.append(dict(check=label,x=x,z=z,materials=expected,interval=depth,hit=hit,passed=ok))
    for center in (-1.30,0,1.30):
        for dx in (-.30,-.23,.23,.30):
            for z in (.78,1.13,1.62,1.78):
                cast('recessed main window light',center+dx,z,['smoky glass','window grille'],(.73,.89))
        cast('middle sash stile',center,1.05,['dark wood'],(.77,.82))
        cast('upper sash rail',center+.24,2.036,['dark wood','smoky glass'],(.77,.88))
        cast('projected sill',center,.365,['sill'],(.53,.65))
    for side in [-1,1]:
        cast('render above the low outer shoulder',side*1.67,2.37,['reddish brown render'],(.639,.65))
        cast('inside taller inner jamb',side*1.06,2.29,['smoky glass'],(.85,.88))
        for z in (.12,2.95,3.52,4.48):
            cast('solid cheek',side*2.31,z,['reddish brown render'],(.64,.65))
    for x in (-.29,-.20,.18,.30):
        cast('separate attic light',x,4.49,['attic glass'],(.85,.88))
    for x in (-2.59,-.88,.54,1.04,2.53):
        cast('painted projecting upright',x,4.35,['pale timber'],(.54,.60))
    for x in (-1.6,-.25,.25,1.65):
        cast('horizontal timber',x,4.04,['pale timber'],(.54,.59))
    for side in [-1,1]:
        for x in (.55,1.55,2.55):
            cap=7.12-(7.12-4.84)*(x/2.94)
            cast('twin sloping verges',side*x,cap,['painted eave edge'],(.44,.47))
        cast('open beside the cropped front',side*3.14,3.4,[],(0,0))
    cast('open above ridge',0,7.45,[],(0,0))
    return {'passed':all(r['passed']for r in rows),'samples':rows}

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
