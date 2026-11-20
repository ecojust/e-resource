"""Check the actual open entrance, 36 panes, five raised characters and later bronze tablet in three released GLBs."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='xuhui-jianye-li-main-lane-gate'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']


def test(scene):
    rows=[]
    def sample(label,origin,direction,material,position,tolerance=.040):
        hit=scene.ray(origin,direction,55)
        passed=hit is None if material is None else hit is not None and hit['material']==material and abs(hit['distance_m']-position)<tolerance
        rows.append(dict(label=label,origin=origin,direction=direction,expected_material=material,expected_distance=position,actual=hit,passed=passed))
    def front(label,x,z,material,depth):
        sample(label,[x,-3,z],[0,1,0],material,None if depth is None else 3-depth,.012)
    def above(label,x,y,z,material):
        sample(label,[x,y,9],[0,0,-1],material,None if z is None else 9-z,.013)
    for center in (-.865,.865):
        width=1.385;bottom=4.60;height=1.075
        for leaf in range(3):
            cx=center-width/2+(leaf+.5)*width/3
            front('middle muntin in timber leaf',cx,bottom+.24,'red timber sash',-.064)
            front('timber leaf transom',cx+.093,bottom+height/3,'red timber sash',-.064)
            for col in (-1,1):
                for row in range(3):
                    x=cx+col*.100
                    front('window pane',x,bottom+height*(row+.50)/3,'smoky window glass',-.204)
        front('stone sill',center,4.542,'pale moulded stone',.090)
    for char,x,z in [('建',-1.4703,3.4891),('業',-.5636,3.4617),('里',-.0015,3.4638),
                     ('總',.5232,3.533),('衖',1.6501,3.3477)]:
        front('registered character '+char,x,z,'dark raised bronze',.113)
    for i,(x,z) in enumerate([(-.3513,2.9866),(-.1928,2.997),(-.1167,2.9895),
                              (-.0165,2.9829),(.0848,2.9822),(.1822,2.9889),(.3155,2.997)]):
        front('CAPELLA tablet glyph '+str(i+1),x,z,'light brass inlay',.108)
    front('small star',0,3.117,'light brass inlay',.110)
    front('bronze tablet ground',.70,3.087,'aged brown brass',.095)
    for side in (-1,1):
        front('door pier',side*3.105,1.32,'warm grey artificial stone',.122)
        front('pier footing',side*3.105,.11,'pale moulded stone',.215)
        front('recessed upper field',side*2.19,5.15,'warm grey artificial stone',.047)
        front('clearance at opening edge',side*2.60,2.60,None,None)
        front('solid stone above chamfer',side*2.65,2.76,'warm grey artificial stone',0)
        above('end pier cap',side*3.0,.14,6.74,'warm grey artificial stone')
    for x in [-2.55,-1.8,-.9,0,.9,1.8,2.55]:
        front('open visible passage',x,1.83,None,None)
    for i in [0,3,6,9,12,15,18,21,24,27]:
        pitch=5.83/28;x=-5.83/2+(i+.27)*pitch
        front('stone meander elbow '+str(i+1),x,4.13,'pale moulded stone',.118)
    for i in [0,12,25,37,49]:
        x=-5.83/2+(i+.5)*5.83/50
        front('dentil '+str(i+1),x,4.34,'pale moulded stone',.125)
    sample('open soffit at middle depth',[0,.83,1.12],[0,0,1],'shaded entrance stone',2.83-1.12,.013)
    above('top stone cap',0,0,7.444,'pale moulded stone')
    above('street before main gate',0,-.75,None,None)
    above('unmodeled interior beyond gate',0,1.72,None,None)
    return dict(triangles=len(scene.tri),samples=rows,passed=all(x['passed']for x in rows))


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
