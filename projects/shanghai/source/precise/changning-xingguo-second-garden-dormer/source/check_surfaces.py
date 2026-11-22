from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='changning-xingguo-second-garden-dormer'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']








def test(scene,role):
    rows=[]
    def shoot(origin,direction,mats,expected,label):
        hit=scene.ray(origin,direction,3);ok=bool(hit and hit['material']in mats and abs(hit['distance_m']-expected)<.006)
        rows.append(dict(feature=label,origin=origin,direction=direction,material_choices=mats,expected_distance_m=expected,hit=hit,passed=ok))
    for centre in [-.2785,.2785]:
        for dx in (-.14,.14):
            for z in [.19,.50,.80,1.12]:
                shoot([centre+dx,-1,z],[0,1,0],['smoked glass','window reflection'],1.068,'one light in each of the two paired eight-light sashes')
        for z in [.20,.48,.80,1.12]:shoot([centre,-1,z],[0,1,0],['dark glazing bar'],1.036,'fine vertical glazing bar')
        for z in [.349,.658,.967]:
            for dx in [-.152,.151]:shoot([centre+dx,-1,z],[0,1,0],['dark glazing bar'],1.034,'three glazing rails')
    for y,z in [(.17,.59),(.32,.80),(.61,.83),(.73,1.09),(1.02,1.18),(1.14,1.33)]:
        for s in (-1,1):shoot([s*1.31,y,z],[-s,0,0],['side copper sheet','second sheet patina'],.656,'standing wall before and after independent vertical seams')
    for s in (-1,1):
        for y in [.49,.89]:
            for z in [.83,1.22]:
                shoot([s*1.31,y,z],[-s,0,0],['standing seam'],.642,'raised vertical fold on copper cheek')
        for z in [.26,.62,.91,1.25]:shoot([s*.612,-1,z],[0,1,0],['oxidised cap edge'],.972,'bright vertical frame around the opening')
    for x in [-.49,-.24,.04,.29,.53]:
        shoot([x,-1,1.452],[0,1,0],['oxidised cap edge'],.925,'front folded cap edge')
        shoot([x,-1,1.419],[0,1,0],['deep cap shadow'],.935,'recess below cap')
    assert len(rows)==74
    return dict(samples=rows,passed=all(v["passed"] for v in rows))

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
