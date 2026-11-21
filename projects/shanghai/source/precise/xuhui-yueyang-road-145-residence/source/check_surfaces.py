"""Measure the garden glazing, paired curved roof gables, dormer, terrace and five chimney positions on three real GLBs."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='xuhui-yueyang-road-145-residence'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']


def test(scene):
    rows=[]
    def sample(label,origin,direction,materials,low,high):
        hit=scene.ray(origin,direction,55)
        passed=hit is None if materials is None else hit is not None and hit['material'] in materials and low<=hit['distance_m']<=high
        rows.append(dict(label=label,origin=origin,direction=direction,expected_materials=materials,distance_bounds_m=[low,high],
                         actual=hit,passed=passed))
    def front(label,x,z,materials,y0,y1):
        sample(label,[x,-3,z],[0,1,0],materials,y0+3,y1+3)
    def above(label,x,y,materials,z0,z1):
        sample(label,[x,y,20],[0,0,-1],materials,20-z1,20-z0)
    glass=['green grey garden glazing']; stone=['buff painted band']; frame=['painted window frames','varnished door leaves']
    red=['burnt red ceramic','weathered fish scale tile','sunlit fish scale tile']
    for cx in [-6.66,-3.33,0,3.32,6.67]:
        for z in [1.46,2.53,3.75]:front('glass across garden room',cx+.18,z,glass,.235,.251)
    for c in [-4.35,5.65]:
        for z in [6.12,6.70,9.31,9.81]:
            front('glazing in forward gable',c+.18,z,glass,1.814,1.841)
        for z in [6.20,9.55]:front('window mullion of forward gable',c,z,frame,1.72,1.77)
        for y in [2.12,2.55,2.90]:above('hipped gable cap',c+.10,y,red,11.72,12.82)
        above('longer terrace-level awning',c+.18,1.05,['green canvas sunshade'],7.33,7.41)
        above('shorter roof-level awning',c+.18,1.24,['green canvas sunshade'],10.66,10.83)
        for dx in [-2.47,2.47]:front('painted cheeks around roof opening',c+dx,8.65,['warm white stucco'],1.61,1.66)
    for x in [-.28,.28]:front('single central dormer casement',x,9.78,glass,3.999,4.04)
    for x in [-.61,.61]:front('dormer side surround',x,9.9,['warm white stucco'],3.80,3.86)
    for x in [-.66,.66]:front('central garden terrace doorway',x,6.48,glass,3.89,3.94)
    for x in [-7.5,-4,0,3,7.8]:
        for y in [.37,.70]:above('continuous terrace behind garden rail',x,y,['aged terrace paving'],4.80,4.85)
    for z in [5.14,5.46,5.83]:
        for x in [-6.23,.21,6.46]:front('terrace horizontal steel rails',x,z,['grey tubular railing'],-.13,-.04)
    for x,y,z in [(-7.72,5.10,13.44),(9.15,6.04,13.42),(-3.70,10.50,14.07),(0,9.85,14.50),(5.61,9.67,13.72)]:
        above('top of independent chimney',x,y,['shadowed smoke outlet','warm white stucco'],z-.05,z+.03)
    for x in [-1.04,1.48]:
        for y,z0,z1 in [(3.65,8.43,8.50),(3.96,8.73,8.95),(4.29,9.48,9.84)]:
            above('exposed fish scale skirt beside dormer',x,y,red,z0,z1)
    for x in [-4,0,4]:
        above('central roof ridge',x,7.875,red,13.34,13.41)
        above('uncovered garden approach',x,-2,None,0,20)
    for x in [-12,12]:
        for z in [1,7,11]:front('garden clear of building',x,z,None,0,0)
    return dict(passed=all(r['passed'] for r in rows),samples=rows)


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
