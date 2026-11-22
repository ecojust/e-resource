from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='yangpu-yangshupu-2086-two-fanlight-entrances'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']








def test(scene,role):
    from math import cos, sin, pi
    rows=[]
    def cast(label,x,z,materials,face,tolerance=.01):
        hit=scene.ray([x,-1.,z],[0,1,0],3)
        passed=bool(hit and hit['material'] in materials and abs(hit['distance_m']-(1+face))<tolerance)
        rows.append(dict(feature=label,center=[x,z],expected_face_y=face,hit=hit,passed=passed))
    for x,r,right in ((-1.69,.94,False),(1.65,1.025,True)):
        for j in range(24):
            a=pi*(j+.45)/24
            if .47*pi<a<.53*pi:continue
            cast('voussoir of the red brick arch',x+1.15*r*cos(a),3.13+1.15*r*sin(a),['pale brick','brick face','brick shade','mortar'],-.017,.055)
        for j in range(17):
            a=pi*(j+.5)/17
            cast('outer semicircular fanlight bar',x+.969*r*cos(a),3.13+.969*r*sin(a),['fanlight iron'],.012)
        for theta in (.195,.345,.487,.683,.773):
            a=pi*theta
            cast('dark radial glazing from the street side',x+.784*r*cos(a),3.13+.784*r*sin(a),['fanlight glass'],.125)
        width=r*.92
        for leaf in (-1,1):
            cx=x+leaf*width/2
            pb=1.59 if right else 1.62;pt=(2.80 if right else 2.76)-.102
            for col in range(3):
                for step in range(3):
                    qx=cx-width/2+.055+(col+.5)*(width-.11)/3
                    qz=pb+(step+.5)*(pt-pb)/3
                    cast('nine actual lights on each wooden leaf',qx,qz,['upper glass'],.0475)
            for ix in (-1,1):
                pz=(.125 if right else .30)+.555
                cast('recessed dark wood panels framed by moulded timber',cx+ix*width*.21,pz,['oak panel'],-.0205)
        cast('upward flaring stone keystone',x,3.13+1.30*r,['rusticated stone'],-.070)
        if right:
            for dx in (-.9,-.65,-.4,-.15,0,.15,.4,.65,.9):
                cast('right projecting stone door hood',x+dx,3.047,['coping stone'],-.350)
        else:
            for dx in (-.77,-.52,-.27,0,.27,.52,.77):
                cast('left shallow horizontal transom cap',x+dx,3.073,['coping stone'],-.1925)
    return dict(samples=rows,passed=all(item['passed'] for item in rows))

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
            if role!='raw':mesh.unlink()
    result=dict(id=ID,manifest_sha256=digest(args.manifest),checker_sha256=digest(Path(__file__)),
                reader_sha256=digest(READER),decoder_sha256=digest(DECODER),results=rows)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for role,r in rows.items():print(role,'pass' if r['passed'] else [q for q in r['samples'] if not q['passed']])
    return all(r['passed'] for r in rows.values())


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
