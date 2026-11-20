"""Ray-test the main hotel door, the curved fascia, tower louvers and window recesses on both streets."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='hongkou-new-asia-hotel'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']


def test(scene):
    from math import cos, sin, hypot
    rows=[]
    def probe(label,origin,direction,material,distance,tolerance=.04):
        hit=scene.ray(origin,direction,45)
        ok=hit is None if material is None else bool(hit and hit['material']==material and abs(hit['distance_m']-distance)<=tolerance)
        rows.append(dict(label=label,origin=origin,direction=direction,expected_material=material,
                         expected_distance_m=distance,tolerance_m=tolerance,hit=hit,passed=ok))

    def face(label,a,b,offset,z,material,depth):
        dx,dy=b[0]-a[0],b[1]-a[1];w=hypot(dx,dy)
        tx,ty=dx/w,dy/w;nx,ny=ty,-tx
        ox=(a[0]+b[0])/2+offset*tx+nx*2
        oy=(a[1]+b[1])/2+offset*ty+ny*2
        probe(label,[ox,oy,z],[-nx,-ny,0],material,2+depth)
    def corner(theta):
        return (46.298+12*sin(theta),12-12*cos(theta))
    def straight(label,a,b,n,which):
        pitch=hypot(b[0]-a[0],b[1]-a[1])/n
        for i in which:
            u=(i+.5-n/2)*pitch
            for j in (0,2,4,6):
                face(label+' guest sash',a,b,u+.21,4.48+3.17*j+1.15,'warm window glass',.308)
            face(label+' street podium',a,b,u+.21,1.29,'smoked door glass',.38)
    straight('Tiantong Road',(-46.298,0),(46.298,0),22,[0,3,7,12,17,20,21])
    straight('North Sichuan Road',corner(1.225),(65.464,29.791),6,[0,2,5])
    angles=[1.225*i/5 for i in range(6)]
    for i in range(5):
        a,b=corner(angles[i]),corner(angles[i+1])
        for j in [0,2,4,6]:
            face('curved southeast guest room',a,b,.40,4.48+3.17*j+1.18,'warm window glass',.308)
        face('recessed entrance' if i==2 else 'corner stone podium',a,b,.37,1.38,'smoked door glass',.56 if i==2 else .38)
        face('curved gold band below letters',a,b,-.99,26.83,'golden bronze',-.24)
        if i in [2,4]:
            face('raised ivory fascia letter',a,b,-.99,27.45,'ivory sign glass',-.322)
    theta=1.225/2
    def oriented(label,r,u,z,material,depth):
        cx=46.298+r*sin(theta);cy=12-r*cos(theta)
        a=(cx-cos(theta),cy-sin(theta));b=(cx+cos(theta),cy+sin(theta))
        face(label,a,b,u,z,material,depth)
    for u in [-.82,.82]:
        oriented('tower ventilation recess',12-1.64,u,29.03,'satin dark metal',.27)
    for u in [-2.56,2.56]:
        oriented('tower pilaster raised stone',12-1.64,u,29.62,'buff architectural stone',-.30)
    oriented('roof sign steel stanchion',12-2.44,-1.57,34.10,'satin dark metal',-.0475)
    for x,y in [(0,8),(-58,9),(51,17),(52,27)]:
        probe('roof deck',[x,y,43],[0,0,-1],'terrace roofing',43-26.64)
    for x,y in [(0,20),(23,25),(0,-4),(69,30)]:
        probe('independent neighbor or road',[x,y,42],[0,0,-1],None,None)
    return dict(triangles=len(scene.tri), samples=rows, passed=all(r['passed'] for r in rows))


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
