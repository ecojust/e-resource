from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='yangpu-ye-garden-white-hall-pierced-parapet'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    rows=[]
    def ray(label,x,y,z,axis,material,distance):
        result=scene.ray([x,y,z],axis,3.)
        match=result is None if material is None else bool(result and result['material']==material and abs(result['distance_m']-distance)<.013)
        rows.append(dict(label=label,origin=[x,y,z],direction=axis,expected_material=material,expected_distance_m=distance,observed=result,passed=match))
    for j in range(6):
        x=.435*(j-2.5)
        for side in (-1,1):
            y=side*.46;axis=[0,-side,0]
            for dx,z in [(0,.36),(0,.55),(0,.78),(-.185,.47),(-.185,.81),(-.113,.708),(.115,.431)]:
                ray('pierced fret material '+str(j+1),x+dx,y,z,axis,'painted parapet',.369)
            for dx,z in [(-.113,.43),(-.113,.55),(.115,.70),(.115,.79)]:
                ray('through-opening '+str(j+1),x+dx,y,z,axis,None,None)
        ray('projecting crown '+str(j+1),x,-.55,1.032,[0,1,0],'cap weathering',.379)
        ray('plinth '+str(j+1),x,-.55,.178,[0,1,0],'painted parapet',.445)
    for x in (-1.63,1.63):
        for y,direction in ((-.60,1),(.60,-1)):
            for z in (.365,.45,.55):
                ray('rectangular tablet',x,y,z,[0,direction,0],'recessed tablet',.439)
            for dx in (-.208,.208):
                ray('square end pier',x+dx,y,.714,[0,direction,0],'painted parapet',.446)
            ray('pier foot',x,y,.142,[0,direction,0],'painted parapet',.395)
        ray('top surface',x,0,1.54,[0,0,-1],'cap weathering',.476)
    return dict(passed=all(row['passed'] for row in rows),samples=rows)

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
