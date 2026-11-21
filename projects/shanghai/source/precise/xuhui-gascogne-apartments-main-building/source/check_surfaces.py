"""Check both twin loggia bays, three vertical fins, two garden portals, canopy lights and stepped roof on delivered surfaces."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='xuhui-gascogne-apartments-main-building'
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
    glazing=['smoky blue-green glass','steel sash and railing'];tile=['honey buff facing tile','fine sandy joints'];pale=['light cement fins','ivory balcony concrete']
    for floor in range(11):
        bottom=4.18+3.79*floor
        for x in [-12.26,-7.49,7.55,12.19]:
            shoot('deep opening in paired loggia',[x,-5.30,bottom+1.81],[0,1,0],None,0,0,4.9)
            shoot('actual recessed balcony glazing',[x,-5.30,bottom+1.81],[0,1,0],glazing,5.66,5.82)
            shoot('pale balcony front below the railing',[x,-5.30,bottom+.36],[0,1,0],pale,3.70,3.80)
        for x in [-3.51,3.82]:
            shoot('steel sash adjoining central fins',[x,-5.30,bottom+1.76],[0,1,0],glazing,4.02,4.19)
        for x in [-.91,0,.91]:
            shoot('three raised cement fins',[x,-5.30,bottom+1.76],[0,1,0],pale,3.59,3.65)
        for x in [-10.16,10.16]:
            shoot('full-depth dividing pier between two recessed balconies',[x,-5.30,bottom+1.60],[0,1,0],pale,3.72,3.83)
    for x in [-4,4]:
        shoot('open garden portal up to the interior cut',[x,-5.30,2.06],[0,1,0],None,0,0,5.35)
        shoot('bounded entry recess in both portals',[x,-5.30,2.06],[0,1,0],['neutral cut'],5.62,5.70)
    for x in (-18.75,-9.01,8.35,15.47):
        shoot('lower dark stone band with separate casements',[x,-5.30,2.04],[0,1,0],glazing,4.02,4.17)
    for idx,(x,y)in enumerate([(-4.17,-3.25),(.22,-3.40),(4.27,-3.26)]):
        shoot('frosted panel in entrance canopy',[x,y,3.25],[0,0,1],['frosted canopy glass'],.65,.79)
    for y,lo,hi in [(-4.63,1.79,1.89),(-4.36,1.64,1.74),(-4.05,1.49,1.59),(-3.75,1.34,1.44),(-3.43,1.19,1.29)]:
        shoot('five rising garden entrance treads',[0,y,2.00],[0,0,-1],['pale granite steps'],lo,hi)
    for x in [-2.38,2.38]:
        shoot('black stone behind canopy between doorways',[x,-5.30,2.09],[0,1,0],['polished charcoal stone'],3.94,4.02)
    for x in [-24.9,24.9]:
        shoot('outside the photographed tower strip',[x,-1.,55.0],[0,0,-1],None,0,0,56.)
    for x,top in [(-23.,4.18+8*3.79),(19.6,4.18+10*3.79),(-16.3,4.18+11*3.79),(7.32,4.18+11*3.79+3.44),(0,4.18+11*3.79+6.06)]:
        shoot('stepped garden-facing roof silhouette',[x,2.30,55.],[0,0,-1],['flat grey roof'],55-top-.045,55-top+.045)
    for x,y in [(-5.,6.),(0.,-5.7),(15.,9.)]:
        shoot('courtyard or separately retained rear mass',[x,y,55],[0,0,-1],None,0,0,56.)
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
