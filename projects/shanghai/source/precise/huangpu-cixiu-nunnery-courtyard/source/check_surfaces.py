"""Independently probe the separate hall, open galleries, timber balusters, ground and later transparent roof."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-cixiu-nunnery-courtyard'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']


def test(scene,role):
    rows=[]
    def ray(label,start,direction,length,materials,span=None):
        hit=scene.ray(start,direction,length)
        ok=hit is None if not materials else bool(hit and hit['material']in materials and (not span or span[0]<=hit['distance_m']<=span[1]))
        rows.append(dict(test=label,origin=start,direction=direction,maximum_m=length,
                         expected_materials=materials,expected_distance_m=span,hit=hit,passed=ok))
    stone='dressed grey stone';wood='dark cinnabar timber';lacquer='red lacquer lattice';glass='recessed dark windowpane'
    roof='charcoal clay pantiles';clear='later translucent courtyard glazing';steel='later steel roof framing'
    for x in [-3.2,-1.0,.75,3.5]:
        for y in [-8.30,-5.70,-2.20,-.45]:
            ray('walkable court paving',[x,y,1],[0,0,-1],2,[stone],[.95,.98])
            ray('air below high court cover',[x,y,1.5],[0,0,1],4,[])
    for x in [-3.75,-1.09,.87,2.26,3.79]:
        z=8.11-abs(x)*.205
        ray('later glazing above the open court',[x,-4.15,12],[0,0,-1],10,[clear],[12-z-.015,12-z+.015])
    for x in [-3.53,1.06,4.62]:
        for y in [1.52,3.1,4.85]:
            ray('north hall pitched tiled roof',[x,y,12],[0,0,-1],10,[roof],[4.4,5.3])
    for x in [-4.02,-2.21,-.42,.47,2.23,3.85]:
        for z in [1.61,4.56]:
            ray('north hall timber or recessed lights',[x,-1,z],[0,1,0],4,[glass,lacquer,wood],[1.95,2.18])
    ray('north main hall signboard',[.22,-.9,2.80],[0,1,0],3,[lacquer,'gilt hall inscription'],[1.72,1.81])
    for sign in (-1,1):
        x=sign*4.55;out=[sign,0,0]
        for i in range(3):
            y=-8.8+(i+.5)*8.82/3
            ray('vase baluster on gallery front',[x-sign*.50,y,3.79],out,1,[wood],[.39,.49])
            ray('open gap between upper balusters',[x-sign*.30,y+.18,3.79],out,.77,[])
            ray('lower open gallery passage',[x-sign*.30,y,1.5],out,1.23,[])
        for y in [-7.65,-5.59,-2.25]:
            ray('under gallery floor',[sign*5.08,y,1.3],[0,0,1],3,[wood],[1.80,1.89])
            ray('walkable side gallery paving',[sign*5.08,y,1.3],[0,0,-1],2,[stone],[1.20,1.25])
        for y in [-8.8,-5.86,-2.92,.02]:
            ray('lower timber gallery post',[x-sign*.68,y,1.30],out,1,[wood],[.55,.60])
    for x,y in [(-8,0),(8,0),(0,7),(0,-9.3)]:
        ray('outside modeled section',[x,y,12],[0,0,-1],16,[])
    return dict(triangles=len(scene.tri),samples=rows,passed=all(r['passed']for r in rows))


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
