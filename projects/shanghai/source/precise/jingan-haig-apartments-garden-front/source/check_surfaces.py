"""Trace the 2025 garden facade on raw, near-web and distant meshes."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='jingan-haig-apartments-garden-front'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    rows=[]
    def shoot(label,origin,direction,mat,low,high,length=64):
        hit=scene.ray(origin,direction,length)
        passed=hit is None if mat is None else hit is not None and hit['material']in mat and low<=hit['distance_m']<=high
        rows.append(dict(label=label,origin=origin,direction=direction,expected_materials=mat,distance_bounds_m=[low,high],actual=hit,passed=passed))
    glazing=['blue grey glass','dark bronze sashes'];stone=['buff limestone','pale coping'];render=['warm sandy render']
    for storey in range(7):
        z=7.23+3.46*storey
        for x in [-23.40,-4.66,4.66,23.40]:
            shoot('curved-head balcony glazing',[x+.23,-4,z+1.53],[0,1,0],glazing,4.34,4.42)
            shoot('iron upper rail in front of the balcony glass',[x,-4,z+1.24],[0,1,0],['black forged iron'],3.29,3.42)
            shoot('pier outside the curved opening',[x+2.23,-4,z+1.55],[0,1,0],render,3.98,4.04)
        for x in [-14.12,-9.68,-.81,.81,9.68,14.12]:
            shoot('recessed separate steel casement',[x+.16,-4,z+1.57],[0,1,0],glazing,4.10,4.22)
    for x in [-3.02,3.02]:
        shoot('freestanding urn on the portal shoulder',[x,-4,6.46],[0,1,0],['pale coping'],1.63,1.85)
    for x in [-2.9,2.9]:
        shoot('stone portal jamb outside the arch',[x,-4,2.32],[0,1,0],stone,1.78,1.90)
    for x in [-.91,.91]:
        shoot('under the arch before the doorway',[x,-4,2.01],[0,1,0],None,0,0,5.10)
        shoot('pair of recessed doors',[x,-4,2.01],[0,1,0],glazing,5.16,5.31)
    for x in [-23.34,23.34]:
        for offset in [-1.49,0,1.49]:
            shoot('open stone colonnade above rail',[x+offset,-4,4.45],[0,1,0],None,0,0,5.21)
            shoot('back of triple loggia',[x+offset,-4,4.45],[0,1,0],['recess plaster'],5.53,5.66)
        for shift in [-.775,.775]:
            shoot('tapered stone shaft',[x+shift,-4,3.86],[0,1,0],['pale coping'],3.75,3.88)
    for x,z,mat in [(23.4,31.455,'pale coping'),(14.8,35.89,'red tile'),(0,35.92,'red tile'),(9.655,38.015,'red tile')]:
        shoot('stepped garden skyline',[x,2.,45],[0,0,-1],[mat],45-z-.05,45-z+.09)
    for x,y in [(0.,-3.),(-27.,0.),(27.,0.),(0,4.00),(-13,6.20)]:
        shoot('lawn or preserved original rear',[x,y,45],[0,0,-1],None,0,0,46.)
    return dict(passed=all(v['passed']for v in rows),samples=rows)

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
    result=dict(id=ID,manifest_sha256=digest(args.manifest),checker_sha256=digest(Path(__file__)),
                reader_sha256=digest(READER),decoder_sha256=digest(DECODER),results=rows)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for role,r in rows.items():print(role,'pass' if r['passed'] else [q for q in r['samples'] if not q['passed']])
    return all(r['passed'] for r in rows.values())


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
