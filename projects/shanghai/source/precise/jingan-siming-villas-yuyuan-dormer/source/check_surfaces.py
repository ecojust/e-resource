from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='jingan-siming-villas-yuyuan-dormer'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']







def test(scene, role):
    rows=[]
    def cast(label,x,y,z,material):
        hit=scene.ray((x,-1.,z),(0,1,0),2.6)
        ok=hit is not None and hit['material']==material and abs(hit['distance_m']-(y+1))<.009
        rows.append(dict(feature=label,expected_material=material,x=x,z=z,depth=y,hit=hit,passed=ok))
    for c in range(4):
        mid=-.963+c*.642
        for row,z in enumerate((.68,1.015,1.32)):
            for k,dx in enumerate((-.13,.13)):
                cast('clear inset glass',mid+dx,.20,z,'warm grey glass'if (row+2*c+k)%4==0 else 'blue grey glass')
            cast('central thin bar',mid,.161,z,'steel glazing bar')
        for z in (.86,1.172):
            for dx in (-.18,.16):cast('thin horizontal divider',mid+dx,.159,z,'steel glazing bar')
    for j in range(5):
        for z in (.72,1.08,1.39):cast('primary painted jamb',-1.284+.642*j,.128,z,'painted frame')
    for c in range(6):
        cast('forward sill',-1.2+c*.48,.065,.420,'pale sill')
        cast('lip at window head',-1.2+c*.48,.084,1.61,'weathered eave')
    for x in (-1.42,1.41):
        for z in (.65,1.05,1.43):cast('pale side reveals',x,.108,z,'creamy reveal')
    source=runpy.run_path(str(SOURCE/'dormer.py'))
    for row in (0,1,3,5,8,9):
        for col in (0,1,17,18):
            x=-2.16+(col+.19*(row%2)+.50)*.232
            if x<-2.12 or x>2.12 or abs(x)<1.57:continue
            z=row*.188+.10
            cast('actual clay tile pan',x,source['slope'](z)-.021,z,source['TILES'][(col*13+row*3+col*row)%6])
    return dict(samples=rows,passed=all(r['passed'] for r in rows))
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
