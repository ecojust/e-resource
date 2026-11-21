"""Check separated balusters, handrails, raised roundel, curved dentil shelf and cut capital."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='jingan-kwok-brothers-residence-historic-front'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']


def test(scene,role):
    rows=[]
    def ray(label, origin, direction, length, material, low=None, high=None):
        hit=scene.ray(origin,direction,length)
        valid=hit is None if material is None else bool(hit and hit['material']==material and
                      (low is None or low <= hit['distance_m'] <= high))
        rows.append(dict(test=label,origin=origin,direction=direction,length_m=length,
                         expected_material=material,expected_distance_range=[low,high],hit=hit,passed=valid))
    from math import radians,cos,sin
    def normal_ray(label,angle,z,offset,reach,material,lo=None,hi=None):
        t=radians(angle);radius=5.20+offset
        ray(label,[radius*sin(t),5.20-radius*cos(t),z],[-sin(t),cos(t),0],reach,material,lo,hi)
    for side in [-1,1]:
        for i in [0,2,4,6,8,10,12]:
            a=side*(5.55+3.11*i)
            normal_ray('individual bulb of a turned baluster',a,3.016,.31,.7,'pale carved stone',.222,.244)
            normal_ray('open gap between adjacent balusters',a+side*(1.54 if i==0 else -1.54),3.05,.30,.70,None)
        for a in [12,22,32,40]:
            normal_ray('curved handrail crown',a*side,3.480,.48,1,'pale carved stone',.279,.305)
            normal_ray('continuous cornice lip',a*side,2.469,.55,1,'warm stone moulding',.175,.206)
            normal_ray('fluted-band backing face',a*side,2.07,.50,1,'cream render',.363,.393)
    for i in [2,4,8,12,16,21,25,31]:
        angle=-44.2+i*(88.4/34)
        normal_ray('dentil front',angle,2.310,.52,.73,'pale carved stone',.195,.222)
        normal_ray('recess between dentils',angle+1.30,2.311,.52,.73,'warm stone moulding',.279,.312)
    for x,z,mat,low,high in [(0,3.380,'weathered circular relief',.255,.265),(.124,3.380,'pale carved stone',.230,.242),(0,3.012,'warm stone moulding',.168,.195)]:
        ray('pier roundel, projecting rim or corbel',[x,-.50,z],[0,1,0],1,mat,low,high)
    t=radians(16.4);r=5.20-.36;x=r*sin(t);y=5.20-r*cos(t)
    ray('exposed shaft and capital',[x,y-.40,.61],[0,1,0],.83,'pale carved stone',.215,.247)
    ray('space adjacent to upper shaft',[x+.40,y-.40,.61],[0,1,0],.83,None)
    ray('underside of curved soffit beside support',[x-.45,y,1.02],[0,0,1],.90,'recessed ochre soffit',.622,.630)
    for v in [-2,0,2]:
        ray('no reconstructed house or garden outside the fragment',[v,-.30,.15],[0,-1,0],1,None)
    return dict(triangles=len(scene.tri),samples=rows,passed=all(row['passed']for row in rows))


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
            rows[role]=dict(sha256=a['sha256'],**test(SerialScene(mesh),role))
    result=dict(id=ID,manifest_sha256=digest(args.manifest),checker_sha256=digest(Path(__file__)),
                reader_sha256=digest(READER),decoder_sha256=digest(DECODER),results=rows)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for role,r in rows.items():print(role,'pass' if r['passed'] else [q for q in r['samples'] if not q['passed']])
    return all(r['passed'] for r in rows.values())


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
