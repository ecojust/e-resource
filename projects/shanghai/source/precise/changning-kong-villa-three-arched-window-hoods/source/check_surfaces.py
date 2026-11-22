from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='changning-kong-villa-three-arched-window-hoods'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    from garden_hoods import BAYS,SUPPORTS
    from math import cos,sin,pi
    rows=[]
    def ray(label,start,vec,expected,dist,tol=.012):
        hit=scene.ray(start,vec,2.)
        ok=(hit is None) if expected is None else bool(hit and hit['material'] in expected and abs(hit['distance_m']-dist)<=tol)
        rows.append(dict(label=label,origin=start,direction=vec,expected_material=expected,expected_distance_m=dist,observed=hit,passed=ok))
    for cx,r,h,d,z in BAYS:
        for t in (.11,.19,.27,.34,.40,.5,.63,.74,.83,.91):
            a=t*pi
            x=cx+(r+.022)*cos(a);zw=z+(h+.022)*sin(a)
            overlap=(cx<0 and t==.11) or (cx>0 and t==.91)
            if overlap:
                ray('overlapping central lip in front of side hood',[x,-1.24,zw],[0,1,0],['rounded hood edge'],1.24-BAYS[1][3])
            y0=-.61 if overlap else -1.24
            ray('arch front rim',[x,y0,zw],[0,1,0],['rounded hood edge'],-y0-d)
        for u in (-.78,-.55,-.26,.04,.30,.61,.76):
            x=cx+r*u;rise=h*(1-u*u)**.5
            ray('open vault intrados',[x,-d*.50,z-.09],[0,0,1],['curved soffit'],rise+.09)
            outer=(h+.045)*(1-((x-cx)/(r+.045))**2)**.5
            ray('upper crown',[x,-d*.36,z+outer+.36],[0,0,-1],['ivory hood'],.36)
        for u in (-.26,0,.28):
            ray('opening under bracket level',[cx+r*u,-1.15,.68],[0,1,0],None,None)
    for x,d in SUPPORTS:
        for z in (.137,.162,.192):
            y={.137:.150,.162:.167,.192:.149}[z]
            ray('stepped heel',[x,-1.0,z],[0,1,0],['window surround'],1-y)
        for f in (.22,.40,.63,.83):
            z=.217+.855*(1-(1-f)**2);y=.115+(d-.115)*f*f*(.61+.39*f)
            ray('curved bracket profile',[x,-1.14,z],[0,1,0],['bracket stucco'],1.14-y,.020)
            for label,yt,expected in [('open cut-in ahead of curved cheek',-y-.030,None),('solid cheek behind curved profile',-y+.022,'bracket stucco')]:
                origin=[x-.155,yt,z]
                hit=scene.ray(origin,[1,0,0],.29)
                passed=(hit is None) if expected is None else bool(hit and hit['material']==expected and abs(hit['distance_m']-.09)<.002)
                rows.append(dict(label=label,origin=origin,direction=[1,0,0],expected_material=expected,observed=hit,passed=passed))
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
            if role!='raw':mesh.unlink()
    result=dict(id=ID,manifest_sha256=digest(args.manifest),checker_sha256=digest(Path(__file__)),
                reader_sha256=digest(READER),decoder_sha256=digest(DECODER),results=rows)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for role,r in rows.items():print(role,'pass' if r['passed'] else [q for q in r['samples'] if not q['passed']])
    return all(r['passed'] for r in rows.values())


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
