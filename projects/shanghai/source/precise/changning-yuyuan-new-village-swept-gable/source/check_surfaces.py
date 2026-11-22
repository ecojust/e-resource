"""Measure the depth of masonry, green sashes, individual red courses and the curved verge on each delivered mesh."""
from math import *
from pathlib import Path
import os,runpy
from gable import *
p=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',Path(__file__).resolve().parents[4]))
Reader=runpy.run_path(str(p/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
def check(reader):
 rows=[]
 def test(name,x,z,d,mat):
  hit=reader.ray([x,-1,z],[0,1,0],7);good=hit is None if d is None else bool(hit and hit['material']==mat and abs(hit['distance_m']-(1+d))<.012)
  rows.append(dict(part=name,origin=[x,-1,z],hit=hit,expected=mat,expected_inside=d,passed=good))
 for x in (-2.84,-1.70,-.42,.37,1.36,2.76):
  for z in (.12,.48,.99,1.40,1.91,2.15):
   test('Grey brick field',x,z,0,BRICK)
 for x in (-2.87,-1.43,-.67,.35,1.21,2.41):
  for z in (.31,1.71,2.52):
   if z<height(x)-.14:test('Red string brick face',x,z,-.019,RED)
 for cx,z0,z1,w in WINDOWS:
  test('Left pane',cx-w*.23,z0+.29*(z1-z0),.133,GLASS)
  test('Right pane',cx+w*.22,z0+.83*(z1-z0),.133,GLASS)
  test('Outer window jamb',cx-w/2+.02,z0+.38*(z1-z0),.08,WOOD)
  test('Transom',cx+.032,z0+.66*(z1-z0),.07,WOOD)
  test('Sill projection',cx,z0-.034,-.072,SILL)
 for (a,z),(b,w)in zip(PROFILE,PROFILE[1:]):
  x=(a+b)/2;h=height(x)
  test('Pale fascia',x,h+.038,-.125,TRIM)
  test('Dark verge underside',x,h-.072,-.102,SOFFIT)
  test('Sky above finished roof',x,h+.16,None,None)
 return dict(passed=all(x['passed']for x in rows),samples=rows)
