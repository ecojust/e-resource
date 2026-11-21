from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='yangpu-tongji-wenyuan-entrance-canopy'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    from math import sqrt
    rows=[]
    def hit(label,start,walk,m,dist,tol=.014):
        v=scene.ray(start,walk,5.)
        rows.append(dict(label=label,origin=start,direction=walk,expected_material=m,expected_distance_m=dist,observed=v,passed=bool(v and v['material']==m and abs(v['distance_m']-dist)<tol)))
    for i,x in enumerate((-1.85,0,1.85)):
        for dx in (-.05,0,.05):
            for z in (.58,1.10,2.05,2.93,3.41):
                hit('smooth front shaft '+str(i+1),[x+dx,-.9,z],[0,1,0],'concrete columns',.9-sqrt(.157**2-dx**2))
    for i,y in enumerate((0,.96,1.92,2.66)):
        for dy in (-.05,0,.05):
            for z in (.74,1.73,2.74):
                hit('right column return '+str(i+1),[2.75,y+dy,z],[-1,0,0],'concrete columns',.9-sqrt(.157**2-dy**2))
    for x in (-1.31,-.42,.38,.94,1.47):
        for y,z in ((-.76,.13),(-.49,.26),(-.25,.39)):
            hit('three rising granite treads',[x,y,z+.60],[0,0,-1],'granite treads',.60)
        for z,m,depth in [(3.70,'soffit',-.343),(3.745,'rain-darkened fascia',-.374),(3.99,'warm plaster',-.36)]:
            hit('setback below canopy lip',[x,-.90,z],[0,1,0],m,.9+depth)
    for x in (-1.59,-1.21,-.59,-.18):
        for z,m,depth in ((.76,'lower door panels',2.874),(1.21,'pale door stiles',2.834),(1.51,'steel green glass',2.882),(2.32,'steel green glass',2.882),(2.90,'pale door stiles',2.834),(3.24,'steel green glass',2.880)):
            hit('recessed front door',[x,.51,z],[0,1,0],m,depth-.51)
    hit('narrow transom stile',[-1.68,.51,3.24],[0,1,0],'pale door stiles',2.835-.51)
    for x in (-1.2,-.61,.39,1.12):
        hit('covered entry ceiling',[x,.72,2.78],[0,0,1],'soffit',.90)
    return dict(passed=all(q['passed']for q in rows),samples=rows)

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
