"""Trace the courtyard colonnade, stair treads, doors and roof in each delivered mesh."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='xuhui-huaihai-road-1634-residence'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    samples = []
    def probe(label, origin, direction, material, minimum, maximum, length=30):
        hit = scene.ray(origin,direction,length)
        valid = hit is None if material is None else (hit is not None and
                hit['material'] in material and minimum <= hit['distance_m'] <= maximum)
        samples.append(dict(label=label,origin=origin,direction=direction,allowed=material,
                            expected_distance_m=[minimum,maximum],hit=hit,passed=valid))
    for x in (-4.38,-.01,4.46,8.93):
        probe('square gallery shaft',[x,-16,3.30],[0,1,0],['ivory painted stucco'],3.86,3.90)
        probe('moulded base',[x,-16,1.33],[0,1,0],['lime painted column moulding'],3.81,3.86)
    for k in range(11):
        x=9.53-3.04*(k+.5)/11
        z=1.86*(k+1)/11
        probe('granite tread '+str(k+1),[x,1.10,2.50],[0,0,-1],['pink granitic stair'],2.50-z-.005,2.50-z+.005)
    for y in (.78,1.47):
        probe('upper double door timber',[11.5,y,2.38],[-1,0,0],['brown timber joinery'],5.20,5.27)
        probe('upper door glass',[11.5,y,3.53],[-1,0,0],['dark blue grey glazing'],5.18,5.23)
    probe('lower service door',[11.5,3.63,1.24],[-1,0,0],['brown timber joinery'],2.43,2.54)
    probe('register plaque',[11.5,3.03,1.81],[-1,0,0],['grey metal register plaque'],2.20,2.29)
    probe('service wing upper window',[11.5,4.57,3.60],[-1,0,0],['dark blue grey glazing'],2.58,2.64)
    probe('bay casement',[11.5,-3.82,2.08],[-1,0,0],['dark blue grey glazing'],2.58,2.66)
    for x in (-3.26,1.15,5.5):
        probe('metal upper rail',[x,-15,1.98],[0,1,0],['black floral cast iron'],3.05,3.11)
    probe('open gallery to recessed door meeting stile',[1.36,-11.29,2.52],[0,1,0],['dark eave edge'],1.74,1.78)
    probe('open gallery to wall',[2.53,-11.29,2.52],[0,1,0],['ivory painted stucco'],1.55,1.65)
    for x,y in ((2,-8),(2,3),(8.08,4.28)):
        probe('visible pitched tiles',[x,y,10],[0,0,-1],['burnt red flat tiles','terracotta ridge and rolls'],2.50,4.58)
    for x,y in ((10.3,1.0),(-6,-12),(0,7)):
        probe('clear outside authored court section',[x,y,10],[0,0,-1],None,0,0)
    return dict(passed=all(row['passed'] for row in samples),samples=samples)


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
