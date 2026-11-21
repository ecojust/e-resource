from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='changning-yuguang-village-pointed-chimney'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    rows=[]
    lime={'roughcast','coarse lime grain','sand grain'}
    def ray(label,origin,axis,materials,distance):
        result=scene.ray(origin,axis,2.8)
        ok=bool(result and result['material'] in materials and abs(result['distance_m']-distance)<.011)
        rows.append(dict(label=label,origin=origin,direction=axis,expected_material=sorted(materials),expected_distance_m=distance,observed=result,passed=ok))
    for x in [-.55,-.36,-.18,0,.18,.36,.55]:
        for z in [.20,.43,.79,.95]:
            ray('render below openings',[x,-.65,z],[0,1,0],lime,.40)
    for x in [-.57,-.23,.18,.57]:
        for z in [1.02,1.16,1.29,1.43,1.53]:
            ray('piers separating slots',[x,-.65,z],[0,1,0],lime,.40)
    dark={'shaft interior'}
    for x in [-.40,0,.40]:
        for dx in [-.045,0,.045]:
            for z in [1.05,1.14,1.28,1.39]:
                ray('long aperture and dark rear wall',[x+dx,-.65,z],[0,1,0],dark,.569)
        for z in [1.08,1.24,1.36]:
            ray('side reveal inside aperture',[x,-.20,z],[1,0,0],{'vent reveal'},.096)
    for z in [1.08,1.28,1.45,1.63]:
        for y in [-.032,0,.032]:
            ray('end aperture',[1.12,y,z],[-1,0,0],dark,.583)
    for y in [-.17,.17]:
        for z in [.32,.76,1.23,1.60]:
            ray('end cap',[1.12,y,z],[-1,0,0],lime,.406)
    for x in [-.60,-.35,-.10,.15,.38,.61]:
        ray('metal front apron',[x,-.65,.055],[0,1,0],{'dark metal flashing'},.374)
        ray('folded upper seam',[x,-.65,.118],[0,1,0],{'weathered seam'},.366)
    for y in [-.19,0,.19]:
        ray('return flashing',[1.12,y,.058],[-1,0,0],{'dark metal flashing'},.390)
    return dict(passed=all(row['passed']for row in rows),samples=rows)

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
