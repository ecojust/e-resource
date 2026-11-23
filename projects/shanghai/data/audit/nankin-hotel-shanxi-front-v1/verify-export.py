"""Check the delivered mesh itself for shutters, clear openwork and independently measured projections."""
from argparse import ArgumentParser
from pathlib import Path
import json,runpy,hashlib
import numpy as np

HERE=Path(__file__).resolve().parent
S=HERE.parents[2]/'source/precise/huangpu-nankin-hotel-shanxi-front/source'
Scene=runpy.run_path(str(HERE.parent/'postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']

def check(file,dims,entry):
    scene=Scene(file)
    tests=[]
    def strike(k,x,y,z,direction,material,target,axis,tolerance=.03):
        hit=scene.ray((x,y,z),direction,7)
        assert hit and hit['material'] in material,(k,x,y,z,hit,material)
        found=hit['point_enu_m'][axis]
        assert abs(found-target)<=tolerance,(k,x,y,z,found,target)
        tests.append(dict(part=k,origin=[x,y,z],direction=direction,material=hit['material'],point=hit['point_enu_m'],expected=target))
    def street(k,x,z,mat,y):
        strike(k,x,3,z,[0,-1,0],mat,y,1)
    for r in entry:
        street(r['name'],r['x'],r['z'],[r['material']],r['first_y'])
    for level,f in enumerate(dims['floors'],2):
        for x in dims['bay_axes']:
            if 'deck' in f:
                for dx in [-.90,.90]:
                    street(f'L{level} rear window',x+dx,f['head']-.37,['Shaded upper glazing'],-.145)
                # Sample the front crease and both shoulders at half the masonry height.
                z=(f['masonry_top']+f['deck'])/2
                h=dims['balcony_width']/2
                for dx in [-h+.082,-.01,h-.082]:
                    y=f['balcony_depth']-(f['balcony_depth']-dims['balcony_shoulder'])*abs(dx)/h
                    street(f'L{level} projecting masonry',x+dx,z,['Warm ivory stucco'],y)
                # Rays start above each terrace, inside its return and ahead of the rear wall.
                strike(f'L{level} open balcony floor',x+.17,.40,f['deck']+.81,[0,0,-1],
                       ['Warm ivory stucco'],f['deck'],2)
                street(f'L{level} upper handrail',x+.25,f['iron_top'],['Graphite balcony iron'],
                       f['balcony_depth']-(f['balcony_depth']-dims['balcony_shoulder'])*.25/h)
            else:
                for dx in (-.81,.81):
                    street(f'L{level} glazing',x+dx+.17,f['head']-.24 if level==6 else f['sill']+.42,
                           ['Shaded upper glazing'],f['face_y']-.145)
    assert len(tests)>=140
    return {'file':scene.asset,'triangles':len(scene.tri),'tests':tests}

if __name__=='__main__':
    ap=ArgumentParser();ap.add_argument('directory',type=Path);ap.add_argument('entry_rays',type=Path);ap.add_argument('output',type=Path);args=ap.parse_args()
    dims=json.loads((S/'dimensions.json').read_bytes());entries=json.loads(args.entry_rays.read_bytes())['variants']
    records={key:check(args.directory/file,dims,entries[int(key=='lod')]['rays']) for key,file in [('raw','raw.glb'),('full','decoded-full.glb'),('lod','decoded-lod.glb')]}
    assert records['raw']['triangles']==records['full']['triangles']>records['lod']['triangles']
    for first,second in zip(records['raw']['tests'],records['full']['tests']):
        assert first['material']==second['material'] and np.allclose(first['point'],second['point'],atol=1e-5)
    args.output.write_text(json.dumps({'passed':True,'read_source':hashlib.sha256((S/'dimensions.json').read_bytes()).hexdigest(),'models':records},ensure_ascii=False,indent=2)+'\n')
    print([(k,v['triangles'],len(v['tests'])) for k,v in records.items()])
