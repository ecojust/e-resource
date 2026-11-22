"""Test the vented plinth, open two-story veranda, corner posts, ironwork and recessed brick windows in the actual meshes."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='jingan-xiong-foxi-building-corner-veranda'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    rows=[]
    def shoot(label,origin,vector,ranges,materials,reach):
        hit=scene.ray(origin,vector,reach)
        good=hit is None if not materials else bool(hit and hit['material']in materials and ranges[0]<=hit['distance_m']<=ranges[1])
        rows.append(dict(check=label,origin=origin,direction=vector,range_m=ranges,materials=materials,hit=hit,passed=good))
    def south(label,x,z,ranges,materials,reach=6):
        shoot(label,[x,-1,z],[0,1,0],ranges,materials,reach)
    def east(label,y,z,ranges,materials,reach=7):
        shoot(label,[1,y,z],[-1,0,0],ranges,materials,reach)
    for post in [-5.11,-2.04,0]:
        for height in [1.16,2.12,2.84,3.35,5.26,6.95,7.28]:
            south('square timber south post',post,height,[.89,.94],['brown structural timber'])
    for post in [0,3.37]:
        for height in [1.16,2.12,2.84,3.35,5.26,6.95,7.28]:
            east('square timber east return',post,height,[.89,.94],['brown structural timber'])
    for coordinate in [-4.15,-3.55,-2.85,-1.56,-.86,-.35]:
        for height,mat,interval in [(4.025,['weathered timber'],[.88,.96]),(4.81,['weathered timber'],[.88,.95]),(4.99,['weathered timber'],[.904,.906]),(8.28,['dark timber edge'],[.75,.86]),(8.365,['terracotta'],[.72,.80])]:
            south('continuous fascias, forward upper deck edge, or eave',coordinate,height,interval,mat)
    for y in [.5,1.2,2.15,2.8]:
        for height,mat,interval in [(4.025,['weathered timber'],[.88,.96]),(4.81,['weathered timber'],[.88,.95]),(8.28,['dark timber edge'],[.75,.86]),(8.365,['terracotta'],[.72,.80])]:
            east('turn in the fascia or roof eave',y,height,interval,mat)
    for x in [-4.94,-3.36,-2.62,-1.48,-.59]:
        for z in [2.12,2.46,6.32,6.79]:
            south('open porch ahead of setback masonry',x,z,[0,0],[],2.50)
    for y in [.39,1.06,2.21,2.92]:
        for z in [2.12,2.46,6.32,6.79]:
            east('east porch clear between columns',y,z,[0,0],[],2.55)
    for x in [-4.41,-3.79]:
        for z in [2.04,2.43,6.39,6.65]:
            south('glazing behind the timber veranda',x,z,[4.33,4.40],['glass'])
    for x in [-4.97,-3.29,-2.81]:
        for z in [2.34,2.54,6.40,6.55]:
            south('recessed grey brick',x,z,[4.15,4.20],['grey brick','grey brick variant'])
    for x in [-4.81,-3.80,-2.79,-1.78,-.77]:
        south('dark circular vent behind pierced plinth',x,.43,[1.23,1.27],['dark timber edge'])
        south('grey plinth below vent',x,.14,[.99,1.02],['plinth stone'])
    for y in [.335,1.185,2.035,2.885]:
        east('circular foundation openings return',y,.43,[1.23,1.27],['dark timber edge'])
        east('east plinth solid',y,.14,[.99,1.02],['plinth stone'])
    for x in [-4.48,-3.12,-1.71,-.75]:
        for z in [1.77,5.14,6.10]:
            south('gallery continuous front iron rail',x,z,[.945,1.015],['iron'])
    for x,y in [(-4.70,.43),(-2.66,1.75),(-.67,2.89)]:
        for oz,surface,mats in [(2.7,.86,['floor stone']),(6.9,5.08,['weathered timber'])]:
            shoot('walkway deck has material and depth',[x,y,oz],[0,0,-1],[oz-surface-.02,oz-surface+.02],mats,4)
    for x,y in [(-4.70,-.34),(.32,1.25),(-5.51,1.9)]:
        shoot('outside the authored footprint',[x,y,9.1],[0,0,-1],[0,0],[],10)
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
