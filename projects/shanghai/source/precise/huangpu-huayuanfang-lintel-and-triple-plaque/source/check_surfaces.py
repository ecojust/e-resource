"""Trace actual letters, frames, flutes, rails and open spaces from the street."""
from pathlib import Path
import os,runpy
from gable import letters,TRIM,RAIL,RED,PLASTER,FIELD
p=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',Path(__file__).resolve().parents[4]))
Reader=runpy.run_path(str(p/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
def check(reader):
    rows=[]
    def test(part,x,z,mat):
        org=[x,-.92,z];hit=reader.ray(org,[0,1,0],1.32)
        passed=bool(hit and hit['material']==mat)if mat else hit is None
        rows.append(dict(part=part,origin=org,direction=[0,1,0],expected_material=mat,hit=hit,passed=passed))
    for ch,geom in letters():
        cores=geom.buffer(-.005)
        for part in getattr(cores,'geoms',[cores]):
            if part.is_empty or part.area<.00017:continue
            pt=part.representative_point();test('Raised red glyph '+ch,pt.x,pt.y,RED)
    for x in (-1.,-.48,0.,.48,1.):
        for z in (3.223,3.357,3.49):test('Horizontal iron rail',x,z,RAIL)
        for z in (3.16,3.29,3.42):test('Daylight between iron rails',x,z,None)
        test('Lane opening',x,1.84,None)
        test('Lower projecting beam',x,2.83,PLASTER)
        test('Lower sign bead',x,3.706,TRIM)
        test('Pale field above lettering',x,4.423,FIELD)
        test('Top coping',x,4.583,TRIM)
    for side in (-1,1):
        for x in (1.335,1.391,1.447,1.503):test('Rib at end of name field',side*x,4.12,TRIM)
        for z in (.125,1.40,2.63):test('Gate pier and foot',side*1.52,z,PLASTER if z==1.40 else TRIM)
    return dict(passed=all(t['passed']for t in rows),samples=rows)
