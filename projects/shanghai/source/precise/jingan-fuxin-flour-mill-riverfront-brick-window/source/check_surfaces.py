from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='jingan-fuxin-flour-mill-riverfront-brick-window'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    from factory_window import WINDOW,VENT,BRICKS,PIER
    results=[]
    def scan(name,x,z,y,materials,tol=.009):
        orig=[x,-.23,z];h=scene.ray(orig,[0,1,0],.7)
        results.append(dict(feature=name,origin=orig,expected_surface_y=y,materials=list(materials),observed=h,passed=bool(h and h['material']in materials and abs(h['distance_m']-.23-y)<tol)))
    for x in (-1.345,1.340):
        for j in (0,2,5,9,14,18,20,26,31,36,40,43):
            scan('red projecting pilaster',x,.069*j+.033,-.065,PIER)
    for i in (1,2,3,5,9,10):
        x=-1.245+i*.197+.038
        for j in (4,6,8,10,12,40):
            scan('stretcher in gray wall',x,j*.069+.022,-.004,BRICKS)
    lo,hi,bt,top=WINDOW;dx=(hi-lo-.09)/4;dz=(top-bt-.09)/4
    for i in range(4):
        for j in range(4):
            scan('recessed glazing',lo+.045+(i+.50)*dx,bt+.045+(j+.5)*dz,.137,['blue-gray glazing','dusty glazing','dark glazing'])
    for i in (1,2,3):
        for j in range(4):scan('casement upright',lo+.045+i*dx,bt+.045+(j+.35)*dz,.103,['steel casement'])
    for x in (-.62,-.43,-.17,0,.26,.52,.64):
        scan('sill',x,bt-.04,-.095,['limestone sill']);scan('lintel drip',x,top+.019,-.071,['limestone sill'])
    for x in (-.10,0,.09):scan('opening below sill',x,.958,.215,['vent shadow'])
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
