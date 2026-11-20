"""Verify the open vestibule, two outdoor stair flights, courtyard windows and inscribed balcony."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-pure-heart-church'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']


def test(scene):
    rows=[]
    def sample(label,origin,direction,material,position,tolerance=.040):
        hit=scene.ray(origin,direction,55)
        passed=hit is None if material is None else hit is not None and hit['material']==material and abs(hit['distance_m']-position)<tolerance
        rows.append(dict(label=label,origin=origin,direction=direction,expected_material=material,expected_distance=position,actual=hit,passed=passed))
    from math import sqrt
    def xy(e,n):
        return ((n-e)/sqrt(2),-(e+n)/sqrt(2))
    def vertical(label,e,n,z,material):
        x,y=xy(e,n);sample(label,[x,y,12],[0,0,-1],material,12-z if z is not None else None)
    for north in (True,False):
        pos=lambda span,along:(span,along)if north else(along,span)
        title='north wing' if north else 'east wing'
        for i in range(17):
            along=4.36+(i+.50)*(4.93/17)
            vertical(title+' stone tread '+str(i+1),*pos(.73,along),3.06*(1-i/17),'washed grey stone')
        for t in [.10,.30,.50,.70,.90]:
            vertical(title+' sloping coping',*pos(1.405,4.36+t*4.93),3.06*(1-t)+.82,'pale cement cap')
        along=8.03 if north else 9.21;top=6.38 if north else 6.18;sill=1.49 if north else 1.48
        def toward(label,position,z,material,depth,tol=.043):
            e,n=pos(3.0,position);x,y=xy(e,n);dx,dy=xy(-1,0) if north else xy(0,-1)
            sample(title+' '+label,[x,y,z],[dx,dy,0],material,3-depth,tol)
        for off in [-.72,.19,.78]:
            toward('lead light behind triple sash',along+off,sill+.76,'brown violet glazing',-.245)
        toward('head glass inside arched crown',along,top-.26,'brown violet glazing',-.245)
        toward('sill below the arched bay',along+.43,sill-.065,'pale cement cap',.17)
        toward('brick above the arch',along+.13,top+.28,'russet face brick',0)
        toward('flat-sided pilaster',5.54 if north else 6.54,4.01,'russet face brick',.153)
        toward('pilaster capital',5.54 if north else 6.54,7.16,'pale cement cap',.235)
        vertical(title+' sloped roof strip',*pos(-.63,along+.11),7.38+.13+.63*.26,'weathered roof tile')
    front=-(4.36+1.40)/sqrt(2)
    for x in [-.62,0,.62]:
        sample('unobstructed entrance to the bounded vestibule',[x,front-2,1.55],[0,1,0],'deep opening',3.74)
    for x in [-1.28,1.28]:
        sample('brick jamb beside entrance',[x,front-2,1.51],[0,1,0],'russet face brick',2)
    for x in [-1.71,1.71]:
        sample('projecting inscribed stone tablet',[x,front-2,3.50],[0,1,0],'pale cement cap',1.7995)
    for glyph,x,z in [('清',-.537,3.42035),('心',-.13075,3.52425),('堂',.7958,3.43815)]:
        sample('raised Chinese inscription '+glyph,[x,front-2,z],[0,1,0],'gilt tablet lettering',1.765,.025)
    for x in [-.58,.58]:
        sample('projecting parapet coping',[x,front-2,3.955],[0,1,0],'pale cement cap',1.77)
    vertical('open paving beyond both stairs',6.8,6.8,None,None)
    vertical('open inner court in front of portal',3.8,3.8,None,None)
    vertical('rear mass deliberately left outside the relief',-3.3,-3.3,None,None)
    return dict(triangles=len(scene.tri),samples=rows,passed=all(x['passed']for x in rows))


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
