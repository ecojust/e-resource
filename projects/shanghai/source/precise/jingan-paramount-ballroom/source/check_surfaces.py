"""Sample the actual serialized Paramount entrance and tower; render geometry is never reconstructed."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='jingan-paramount-ballroom'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']


def test(scene):
    from math import hypot, radians, sin, cos
    rows=[]
    def shot(label,position,direction,material,expected):
        hit=scene.ray(position,direction,90)
        passed=hit is None if material is None else (hit is not None and hit['material']==material and abs(hit['distance_m']-expected)<.065)
        rows.append(dict(label=label,origin=position,direction=direction,expected=material,expected_distance_m=expected,hit=hit,passed=passed))
    def on_wall(a,b,u,z,want,distance,label):
        dx=b[0]-a[0];dy=b[1]-a[1];length=hypot(dx,dy);tx=dx/length;ty=dy/length
        px=(a[0]+b[0])/2+u*tx;py=(a[1]+b[1])/2+u*ty
        shot(label,[px+ty*6,py-tx*6,z],[-ty,tx,0],want,distance)
    angles=[-52.1,-40,-29,-17,-6,6,17,29,40,52.1]
    points=[(.20+15.15*sin(radians(v)),15.27-15.15*cos(radians(v)))for v in angles]
    for i,(a,b)in enumerate(zip(points,points[1:])):
        centre=i in [3,4,5]
        if centre:
            on_wall(a,b,.22,1.67,'street glazing',7.37,'inset central door lights')
            for u in [-.55,.55]:
                on_wall(a,b,u+.13,6.05,'street glazing',6.34,'double continuous central lights')
                on_wall(a,b,u+.13,12.17,'street glazing',6.34,'upper central lights')
            on_wall(a,b,.17,15.83,'sash metal',5.935,'raised dark upper panel')
        else:
            for z in [4.83,8.89]:on_wall(a,b,.17,z,'street glazing',6.34,'two rows of narrow curved wall windows')
        if i in [2,6]:
            on_wall(a,b,.25,14.605,'ivory enamel',5.779,'ivory letter board')
            on_wall(a,b,-.227,17.02,'red enamel',5.700,'raised red P on both name boards')
    def lerp(a,b,s):return (a[0]+(b[0]-a[0])*s,a[1]+(b[1]-a[1])*s)
    south=(-31.83,43.33);north=(32.76,35.1);mid=lerp(south,points[0],.49);far=lerp(points[-1],north,.59)
    for a,b,n in [(south,mid,4),(mid,points[0],4),(points[-1],far,5),(far,north,3)]:
        length=hypot(a[0]-b[0],a[1]-b[1]);
        for j in [0,n-1]:on_wall(a,b,(j-(n-1)/2)*length/n+.17,8.15,'street glazing',6.34,'two named streets facade windows')
    for r,z,m,divisions in [(4.52,19.12,'aged gold tower',32),(3.36,20.97,'aged gold tower',26),(2.03,24.22,'opal tower glass',22),(1.28,30.29,'opal tower glass',16)]:
        # Between two actual metal ribs on the east side of each stage.
        phase=radians((int(.75*divisions)+.5)*360/divisions)
        offset=r*cos(phase);px=.16+offset
        shot('four raised concentric tower stages',[px,-3.5,z],[0,1,0],m,5.56+3.5-(r*r-offset*offset)**.5)
    for x,y,z,m in [(0.16,5.56,35.24,'bronzed street trim'),(3.91,4.92,20.01,'aged gold tower'),(-22,34.5,11.12,'flat roof')]:
        shot('tiered tower and low southwest wing',[x,y,48],[0,0,-1],m,48-z)
    for x,y in [(0,-7),(35,40),(-37,25),(0,46),(5,51)]:shot('road or undeveloped recess',[x,y,48],[0,0,-1],None,None)
    return dict(triangles=len(scene.tri),samples=rows,passed=all(r['passed'] for r in rows))

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
