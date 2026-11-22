"""Read the actual first material surface, depth of each leaf, fluting and stepped capitals."""
from pathlib import Path
import os,runpy
from hall import *
p=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',Path(__file__).resolve().parents[4]))
Reader=runpy.run_path(str(p/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
def check(reader):
 rows=[]
 def test(label,x,z,depth,material,tol=.018):
  hit=reader.ray([x,-1.1,z],[0,1,0],6.0);good=hit is None if depth is None else bool(hit and hit['material']==material and abs(hit['distance_m']-(1.1+depth))<tol)
  rows.append(dict(part=label,origin=[x,-1.1,z],expected_depth=depth,expected_material=material,hit=hit,passed=good))
 for i,(a,b)in enumerate(zip(HINGES,HINGES[1:])):
  for c in range(3):
   x=a+(b-a)*(c+.46)/3
   for j in range(5):
    z=.03+(j+.52)*.518
    test('Light through sash',x,z,sash_face(i,x)+.034,COOL if j<2 and (c+i+j)%3==0 else LIGHT)
  for c in (1,2):
   x=a+(b-a)*c/3
   test('Slim vertical glazing bar',x,1.22,sash_face(i,x)-.011,SASH)
  for j in range(1,5):
   x=a+.145;test('Horizontal glazing bar',x,.03+j*.518,sash_face(i,x)-.021,SASH)
  x=b-.033 if i==0 else a+.033
  test('Unobstructed edge stile',x,.225,sash_face(i,x)-.066,FRAME)
  if i==0:
   # This sight line to the outer stile first crosses the left fluted shaft.
   x=a+.033
   test('Shaft obscures outer stile',x,.225,-.238-sqrt(.210**2-(x+POST_X)**2),WOOD,.021)
 for x in (-POST_X,POST_X):
  for z in (.14,.67,1.21,1.74,2.42,2.73):test('Fluted shaft',x,z,-.238-.207,WOOD,.019)
  for z,r in [(2.87,.214),(2.952,.252),(3.080,.273)]:test('Rounded collar',x,z,-.238-r,RING)
 for x in (-1.52,-.76,.47,1.49):
  test('Curved plaster head',x,2.73,curve(x)-.08,PLASTER)
  test('Upper curved cornice',x,3.080,curve(x)-.155,FRAME)
 test('Transom fitting',0,2.845,curve(0)-.094,HARDWARE)
 return dict(passed=all(x['passed']for x in rows),samples=rows)
