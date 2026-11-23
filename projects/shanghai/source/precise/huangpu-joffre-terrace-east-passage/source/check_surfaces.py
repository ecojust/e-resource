"""Ray-test the open lane, stepped parapet, four real windows and the three-letter portal name."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-joffre-terrace-east-passage'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    results=[]
    def test_ray(label,origin,direction,materials,span,reach=15):
        hit=scene.ray(origin,direction,reach)
        passed=hit is None if not materials else bool(hit and hit['material'] in materials and span[0]<=hit['distance_m']<=span[1])
        results.append(dict(check=label,origin=origin,direction=direction,materials=materials,range_m=span,hit=hit,passed=passed))
    def front(label,x,z,materials,lo,hi):
        test_ray(label,[x,-1.5,z],[0,1,0],materials,[lo,hi])
    for x in [-2.66,-1.89,-.88,.14,1.13,2.11,2.75]:
        for z in [.30,1.35,2.17,3.40,3.72]:
            front('complete street clearance below lintel',x,z,[],0,0)
        for y in [.38,.75,1.18]:
            test_ray('bottom of overhead soffit',[x,y,1.30],[0,0,1],['soffit plaster'],[2.485,2.500])
    for c in [-1.66,1.66]:
        for dx in [-.51,-.32,-.10,.10,.32,.51]:
            for z in [5.88,6.17,6.45,6.76,7.07]:
                front('separate lower metal-window lights',c+dx,z,['lower glazing','shadowed pane'],1.706,1.73)
        for dx in [-.30,.30]:
            for z in [9.17,9.65,10.05,10.43]:
                front('upper casement glazing',c+dx,z,['upper glazing'],1.706,1.73)
        for z in [9.14,9.6,10.17]:
            front('two upper casements meeting stile',c,z,['dark wood'],1.60,1.64)
        front('pronounced stone window hood',c+.34,10.714,['stone trim'],1.26,1.33)
        front('stone lower-window sill',c-.19,5.647,['stone trim'],1.30,1.34)
        for dx in [-.48,-.28,.25,.47]:
            front('cement field between floors',c+dx,8.16,['grey cement'],1.35,1.48)
    front('north window upper transom',1.38,10.313,['dark wood'],1.64,1.675)
    front('south window uninterrupted upper pane',-1.94,10.313,['upper glazing'],1.706,1.73)
    for x in [-.74,-.38,.13,.61]:
        front('inset stone plaque field',x,5.17,['weathered cement','lettering'],1.396,1.419)
    for i in [-1,0,1]:
        x=-.477 if i==-1 else 0 if i==0 else .477
        sample=(.165,.86) if i<1 else (.18,.52)
        front('raised stroke '+('淮海坊'[i+1]),x+(.88*sample[0]-.44)*.46,5.+(sample[1]-.5)*.476,['lettering'],1.397,1.406)
    for side in [-1,1]:
        front('incised semicircular surround',side*1.47,5.173,['weathered cement'],1.46,1.48)
        for d in [-.33,0,.33]:
            front('three bracket feet',side*2.83+d,11.60,['stone trim'],1.10,1.38)
        for z in [4.8,7.73,10.88,12.24]:
            front('slim edge pilaster',side*3.39,z,['stone trim'],1.285,1.305)
        front('outer shoulder below higher central parapet',side*3.07,12.67,[],0,0)
        for z in [3.76,5.,7.86,10.74,13.20]:
            front('outside both adjoining occupied houses',side*3.81,z,[],0,0)
    for x in [-2.40,-.84,.25,1.77,2.40]:
        front('raised central parapet',x,12.67,['grey cement','weathered cement','joint shadows'],1.49,1.52)
    return dict(passed=all(q['passed']for q in results),samples=results)

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
