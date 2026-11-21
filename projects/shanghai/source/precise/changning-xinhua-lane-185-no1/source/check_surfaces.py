"""Measure the three open bays, nine carved panels, roof planes, windows and chimneys on all three actual GLBs."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='changning-xinhua-lane-185-no1'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    rows=[]
    def hit(label,origin,direction,mats,a,b,maxdist=45):
        r=scene.ray(origin,direction,maxdist)
        valid=r is None if mats is None else r is not None and r['material']in mats and a<=r['distance_m']<=b
        rows.append(dict(label=label,origin=origin,direction=direction,expected_materials=mats,distance_bounds_m=[a,b],actual=r,passed=valid))
    def front(label,x,z,mats,y0,y1):
        hit(label,[x,-2,z],[0,1,0],mats,y0+2,y1+2)
    buff=['buff exposed aggregate']; steel=['black steel casement'];glass=['smoked window glass'];stone=['pale washed stone']
    brick=['garden red face brick','burnt sienna face brick','light red face brick','warm weathered brick joints']
    wood=['dark porch joinery'];clay=['old russet clay tile','warm brown plain tile','muted red roof tile','dark roof underlay']
    for i in (-1,0,1):
        for z in [.70,1.52,2.24,2.72]:
            hit('open portico bay from forecourt',[i*3.30,-1.0,z],[0,1,0],None,0,0,4.0)
        front('shallow Tudor head above bay',i*3.30,3.22,buff,-.016,.02)
    for x in (-4.98,-1.65,1.65,4.98):
        for z in (.46,1.51,2.39):front('four square portico piers',x,z,buff,-.016,.02)
    for i in (-1,0,1):
        for j in (-1,0,1):
            center=3.3*i+.93*j
            front('stone crossing in each of nine front panels',center,3.47+.17+.50*.66,buff,-.067,-.05)
            for dx in [-.16,.16]:
                hit('cut-through foliage below the crossed ribs',[center+dx,-.5,3.47+.17+.21*.66],[0,1,0],None,0,0,.80)
    for x in [-3.54,-.4,2.83]:
        front('recessed leaf inside the open portico',x,.87,wood,4.53,4.65)
    for x in [6.12,7.63,8.65,10.92,14.53]:
        for z in (1.34,5.08):front('casements facing the garden in the east wing',x,z,glass+steel,4.83,5.02)
    for x in [-2.50,-1.45]:
        front('attic casement pair in the main gable',x,8.13,glass+steel,4.21,4.34)
    for x in [-3.98,-1.69,.01]:
        front('red brick in the gable field',x,6.48,brick,4.10,4.134)
    for x in [2.02,2.57,3.40,3.81]:
        front('glazed shed dormer just east of the gable',x,8.12,glass+steel,5.84,5.99)
    for x,y,z in [(-5.3,5.35,10.77),(-.78,11.91,10.98),(9.08,10.57,11.74)]:
        hit('brick chimney canopy or open flue',[x-.17,y,16],[0,0,-1],['dark chimney cap','dark roof underlay'],16-z-.03,16-z+.04)
    for x,y,low,hi in [(13.2,7.1,8.53,9.29),(-1.94,5.5,10.47,10.70),(-7.67,2.50,5.29,5.48)]:
        hit('main roof, cross gable and low wing',[x,y,16],[0,0,-1],clay,16-hi,16-low)
    for x in (-8.72,-7.76,-6.65):
        front('roof pitch above west wing garden window',x,4.22,clay,.82,1.05)
    for x,y in [(-12,-2),(7,-1),(18,6),(3,-4),(17,15)]:
        hit('outside the residence',[x,y,16],[0,0,-1],None,0,0)
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
    result=dict(id=ID,manifest_sha256=digest(args.manifest),checker_sha256=digest(Path(__file__)),
                reader_sha256=digest(READER),decoder_sha256=digest(DECODER),results=rows)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for role,r in rows.items():print(role,'pass' if r['passed'] else [q for q in r['samples'] if not q['passed']])
    return all(r['passed'] for r in rows.values())


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
