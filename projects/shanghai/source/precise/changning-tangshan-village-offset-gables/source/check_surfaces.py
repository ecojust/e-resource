"""Probe the two setbacks, pierced window wall and separate verge, tile, sash and sill."""
from pathlib import Path
import os,runpy
from gable import *
p=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',Path(__file__).resolve().parents[4]))
Reader=runpy.run_path(str(p/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
def check(reader):
 rows=[]
 def test(label,x,z,y,mat):
  o=[x,-1,z];hit=reader.ray(o,[0,1,0],5)
  ok=not hit if y is None else bool(hit and hit['material']==mat and abs(hit['distance_m']-(y+1))<.007)
  rows.append(dict(part=label,origin=o,hit=hit,depth=y,material=mat,passed=ok))
 for label,c,w,e,t,y,h,low,high in GABLES:
  for sign in (-1,1):
   for d in (.23,.45,.68,.83):
    x=c+sign*w*d;z=roof(x,c,w,e,t)
    test('Green pitched gable',x,z-.046,y-.077,VERGE)
    test('Pale arris',x,z-(.210 if y==0 else .150),y-.068,UNDER)
    test('Air above pitched gable',x,z+.106,None,None)
   for ratio in (.78,.87):
    x=c+sign*w*ratio
    for z in (.22,.66,1.09,1.77):
     if y and sign==1 and ratio==.87:
      test('Foreground right-gable drip edge',x,z,-.034,UNDER)
      test('Lower gable render behind and beside the drip',x-.16,z,y,BRICK)
     else:test('Wall on its own plane',x,z,y,BRICK)
  for z in (low+.15,low+.32,high-.112):
   if y==0 and z<low+(high-low)*.65:
    test('Short iron bar in the lower sash',c+h*.31,z,y+.055,IRON)
    test('Glass beside the short iron bar',c+h*.23,z,y+.138,GLASS)
   else:test('Setback glass',c+h*.31,z,y+.138,GLASS)
   if y==0 and z>low+(high-low)*.65:test('Upper glass above the short iron bars',c+h*.111111,z,y+.138,GLASS)
   else:test('Muntin',c+h*.111111 if y==0 else c+h*.50,z,y+.055,IRON)
  test('Sill projects',c,low-.03,y-.056,SILL)
  if y==0:
   test('Diamond near ridge',c,3.86,y-.043,MOULD)
   test('Narrow lower sash bar',c+.42/9,.56,y+.055,IRON)
   test('Lower glass between sash bars',c+.075,.56,y+.138,GLASS)
 return dict(passed=all(r['passed'] for r in rows),samples=rows)
