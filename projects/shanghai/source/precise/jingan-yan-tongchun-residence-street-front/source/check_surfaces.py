"""Check wood leaves, carved lower panels, recessed tops, balcony-free porch and real iron windows."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='jingan-yan-tongchun-residence-street-front'
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
    def front(label,x,z,mat,lo=None,hi=None):
        ray(label,[x,-5,z],[0,1,0],8,mat,lo,hi)
    for x in (-5.67,-2.66,2.66,5.67):
        for z,i in ((1.005,12),(2.205,27),(4.835,60)):
            mat='warm grey facing brick' if i%5 in (1,4) else 'buff ribbed facing brick'
            front('independent buff-brick pier courses',x+.075,z,mat,3.856,3.866)
        front('mortar bed below a course',x+.081,1.276,'grey brown mortar',3.867,3.875)
    centers=(-5.67,-2.66,2.66,5.67)
    for j in range(3):
        lo,hi=centers[j]+.246,centers[j+1]-.246
        dl,dh=lo+.236,hi-.236
        leaves=6 if j==1 else 3
        unit=(dh-dl-.1)/leaves
        for i in range(leaves):
            x=dl+.05+(i+.5)*unit
            front('glass within visible upright leaf',x,1.76,'smoky porch glass',4.917,4.926)
            front('solid carved lower leaf field',x,.792,'reddish brown joinery',4.823,4.833)
            front('low rail above panel on each leaf',x,.923,'carved timber mouldings',4.798,4.808)
        for fx in (.27,.65):
            x=lo+(hi-lo)*fx
            front('continuous transom below toplights',x,2.485,'reddish brown joinery',4.814,4.824)
            front('solid stone rise below windows',x,3.752,'grey limestone spandrels',3.965,3.975)
            front('projecting stone sill',x,4.70,'sunlit stone arrises',3.921,3.932)
            front('upper iron sash horizontal',x,5.895,'dark iron glazing bars',4.065,4.075)
        c=(lo+hi)/2
        ray('clear space within the shallow porch',[c,-.65,1.63],[0,1,0],.28,None)
        ray('recess beneath stone spandrel',[c,-.65,3.02],[0,0,1],.5,'grey limestone spandrels',.341,.351)
        for frac in (.16,.38,.82):
            front('upper reflected glass behind steel',lo+(hi-lo)*frac,5.60,'grey blue upper glazing',4.114,4.125)
        front('front of cropped stone window head',c,6.69,'grey limestone spandrels',3.962,3.972)
    for x,y,z in [(-6.12,-.38,.46),(6.12,-.28,1.35),(.10,-1.30,1.71),(.2,.22,6.91)]:
        ray('limit of 2022 street section',[x,y,z],[0,0,1],.31,None)
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
