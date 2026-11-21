"""Check both turns, tread rises, independently open balusters and the glazed radial fanlight."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='xuhui-jewish-hospital-garden-stair'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']





def test(scene):
    from math import cos, sin, pi
    rows=[]
    def cast(name,origin,direction,length,material=None,distance=None,tolerance=.003):
        hit=scene.ray(list(origin),list(direction),length)
        ok=hit is None if material is None else (hit is not None and hit['material'] in material and abs(hit['distance_m']-distance)<tolerance)
        rows.append(dict(check=name,origin=origin,direction=direction,length=length,expected_materials=sorted(material or []),expected_distance_m=distance,tolerance_m=tolerance,hit=hit,passed=bool(ok)))
    def down(label,x,depth,z,mat):
        cast(label,(x,-depth,5.4),(0,0,-1),5.5,mat,5.4-z)
    H=.166*7
    for i in range(7):
        delta=(4.91-2.77)/7;depth=4.91-(i+.5)*delta
        for x in (-1.08,-.71,0,.70,1.09):down('central stair measured tread',x,depth,(i+1)*.166,{'speckled tread'})
        for side in (-1,1):
            for a,b,base,d in [(1.51,4.34,H,2.13),(4.34,2.56,2*H,.75)]:
                x=side*(a+(b-a)*(i+.5)/7)
                down('lateral flight turning at the end landing',x,d,base+(i+1)*.166,{'speckled tread'})
    for side in (-1,1):
        for i in range(3):
            xx=side*(1.51+.165);d=4.91-(i+.5)*(4.91-2.77)/3
            down('projecting coping above the central flight',xx,d,.81+i*.317+.105,{'light coping'})
        for d in (.31,.90,1.38,1.72,2.16):
            down('common returning side landing',side*4.73,d,2*H,{'speckled tread'})
        for x in (.35,.88,1.28):
            for d in (1.73,2.14,2.50):
                down('open half landing in front of the fanlight',side*x,d,H,{'speckled tread'})
        for x in (.40,1.16,1.96):
            down('upper landing behind balustrade',side*x,.66,3*H,{'speckled tread'})
    center=H+1.16
    for angle in (.105,.272,.492,.650,.899,1.205,1.343,1.752,2.021,2.270,2.585,2.907):
        for radius in (.42,.66):
            x=radius*cos(angle);z=center+radius*sin(angle)
            cast('glass behind the radial ironwork',(x,-2,z),(0,1,0),.9,{'garden glass'},2-(1.51-.128))
    for angle in (pi/4,pi/2,3*pi/4):
        for radius in (.36,.45,.64):
            x=radius*cos(angle);z=center+radius*sin(angle)
            cast('raised fanlight ray',(x,-2,z),(0,1,0),.9,{'charcoal glazing bar'},2-(1.51-.09))
    for x in (-.61,-.39,-.15,.13,.40,.64):
        for z in (H+.685,H+.912):
            cast('rectangular steel-light individual pane',(x,-2,z),(0,1,0),.9,{'garden glass'},2-(1.51-.128))
    for x in (-1.88,-1.31,1.32,1.85):
        for z in (H+.44,H+.88,H+1.25):
            cast('concrete flank at half level',(x,-2,z),(0,1,0),.8,{'washed concrete'},2-1.51)
    # Behind the recessed glass no solid central plinth obstructs the opening.
    for x in (-.67,-.35,.14,.58):
        cast('back of glazing in the opening',(x,-1.15,center-.10),(0,-1,0),.31,{'garden glass'},(1.51-.139)-1.15)
    for k in (1,3,5,8,10,12):
        xc=-2.56+5.12*k/14
        xgap=xc+5.12/28
        cast('air between terrace balusters',(xgap,-1.99,3*H+.51),(0,1,0),.7)
        cast('independent upright above the terrace',(xc,-1.99,3*H+.51),(0,1,0),.7,{'baluster granite'},1.99-(1.51+.018))
    return dict(passed=all(q['passed'] for q in rows),samples=rows)

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
