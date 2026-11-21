from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='changning-anding-no16-arched-steel-windows'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    rows=[]
    def ray(label,x,z,material,distance,axis=None,origin=None):
        direction=axis or [0,1,0];source=origin or [x,-.52,z];result=scene.ray(source,direction,2.5)
        ok=bool(result and result['material']==material and abs(result['distance_m']-distance)<.012)
        rows.append(dict(label=label,origin=source,direction=direction,expected_material=material,expected_distance_m=distance,observed=result,passed=ok))
    for x in (-.683,.683):
        for dx in (-.36,-.12,.12,.36):
            for z in (.51,.79,1.06,1.34,1.55):
                ray('recessed four-column glass',x+dx,z,'window glass',.67)
        for dx in (-.2425,0,.2425):
            for z in (.55,.79,1.05,1.34,1.57):ray('vertical muntins',x+dx,z,'metal rails',.613)
        for dx in (-.335,-.12,.12,.335):
            for z in (.66,.927,1.202,1.484):ray('cross bars and transom',x+dx,z,'metal rails',.605)
        for dx in (-.35,-.2,0,.2,.35):
            import math
            z=1.385+math.sqrt(.46**2-dx**2);ray('arched head',x+dx,z,'metal rails',.603)
        ray('true opening reveal on left',x,1.05,'window reveal',.473,[-1,0,0],[x,.052,1.05])
    for x in (-1.13,-.73,-.38,0,.45,.80,1.14):
        ray('stone ledge',x,.357,'cut sill stone',.329)
        ray('lower trim',x,.153,'cut sill stone',.359)
    for j in range(20):
        x=-1.245+.1245*(j+.5);ray('scalloped tip',x,.213,'scalloped fascia',.36)
        x=-1.245+.1245*(j+.02);ray('shadow between scallops',x,.211,'sill shadow',.399)
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
