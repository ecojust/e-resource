"""Independently trace the street windows, curved stair lights and entrance of Empire Mansions."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='xuhui-empire-mansions-street-front'
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
    import math
    glazing=['blue grey glass','dark green steel']
    # Fixed measured local edges and outward vectors independent of the construction script.
    east=[(3.5800115,0),(60.9721701,23.0056533)]
    west=[(-3.5800115,0),(-47.7019389,62.4809795)]
    for label,ends,orientation in [('Huaihai',east,1),('Changshu',west,-1)]:
        (x0,y0),(x1,y1)=ends
        length=math.hypot(x1-x0,y1-y0)
        dx,dy=(x1-x0)/length,(y1-y0)/length
        nx,ny=orientation*dy,-orientation*dx
        def trace(label,d,z,materials,low,high,maxlen=64):
            origin=[x0+d*dx+nx*3,y0+d*dy+ny*3,z]
            shoot(label,origin,[-nx,-ny,0],materials,low,high,maxlen)
        for level in range(5):
            z=4.49+3.22*level
            for frac in [.126,.341,.601,.824,.970]:
                trace(label+' continuous steel window band',frac*length,z+.82,glazing,3.12,3.23)
            for frac in [.258,.753]:
                trace(label+' inset circular glazing',frac*length,z+1.14,glazing,3.03,3.13)
                trace(label+' curved white porthole shaft',frac*length,z+.57,['ivory stucco'],2.60,2.69)
            trace(label+' brown spine beside blade',length*.501+.36,z+.6,['brown facing brick'],2.80,2.89)
            trace(label+' center blade over dark channel',length*.501,z+.64,['pale cast trim'],2.50,2.58)
        trace(label+' crowning fin',length*.501,23.4,['pale cast trim'],2.38,2.60)
        trace(label+' top floor near the corner',4.80,22.97,glazing,3.17,3.29)
        trace(label+' above the terminal wing',length*.78,25.6,None,0,0,4)
        trace(label+' shopfront',length*.48,1.85,glazing,3.20,3.32)
    for sign in [-1,1]:
        shoot('1326 inset open portal before paired door',[sign*.68,-3,1.7],[0,1,0],None,0,0,4.61)
        shoot('1326 glazed door',[sign*.68,-3,1.7],[0,1,0],glazing,4.64,4.76)
        shoot('paired white columns',[sign*1.61,-3,1.70],[0,1,0],['pale cast trim'],2.69,2.76)
        shoot('upper raised corner casements',[sign*2.55,-3,22.92],[0,1,0],glazing,3.12,3.23)
    for x in [-.734,0,.734]:
        shoot('tall white corner fin',[x,-3,20.1],[0,1,0],['pale cast trim'],2.50,2.58)
    for x,y in [(0,-3),(-10,-8),(0,8),(-35,20),(40,42)]:
        shoot('outside the street relief or in the preserved core',[x,y,38],[0,0,-1],None,0,0,39)
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
