"""Probe the real first-hit brick, metal sash, two lozenges and separate chimney crown."""
from pathlib import Path
import os,runpy
from gable import *
p=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',Path(__file__).resolve().parents[4]))
Reader=runpy.run_path(str(p/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
def check(reader):
 rows=[]
 def test(part,x,z,y,material):
  pt=[float(x),-1.,float(z)];hit=reader.ray(pt,[0,1,0],6)
  ok=hit is None if y is None else bool(hit and hit['material']==material and abs(hit['distance_m']-(1+y))<.008)
  rows.append(dict(part=part,origin=pt,hit=hit,material=material,depth=y,passed=ok))
 for x in (-2.1,-1.8,-.73,-.39,.43,.58,1.64,2.02):
  for z in (.12,.42,1.27,1.96):test('Red wall',x,z,0,BRICK)
 for x in (-1.23,-.95,-.66,.6,.99,1.39):
  test('Grey verge',x,h(x)+.018,-.101,COPING)
  test('Air above stepped parapet',x,h(x)+.172,None,None)
 for a,b in PEN:
  for t in (.29,.62):
   v=np.array(a)+(np.array(b)-a)*t;test('Set dark bricks of front diamond',v[0],v[1],-.012,BROWN)
 test('Left edge of right sill',.70,.12,-.070,DARK)
 for z in (.42,1.27):test('Rubbed left jamb of right window',.70,z,-.020,RUBBED)
 for x,d in WINDOWS:
  test('Recessed glazing',x+.135,.86,.13,GLASS);test('Tall sash upright',x,.71,.08,WOOD)
  test('Horizontal bar',x+.13,1.23,.074,WOOD);test('Window sill',x,.112,-.07,DARK)
 for x in (-1.69,-.73,.23,1.44):
  test('Middle eave band',x,2.23,-.118,COPING);test('Parapet plinth',x,2.35,-.143,DARK)
 for z in (1.12,2.66,3.5,4.45):test('Chimney shaft',2.56,z,-.039,BRICK)
 for z,d,mt in [(4.64,-.084,DARK),(4.74,-.144,COPING),(4.91,-.079,COPING),(5.172,-.112,BAND),(5.238,-.160,COPING)]:test('Stepped chimney crown',2.58,z,d,mt)
 return dict(passed=all(r['passed']for r in rows),samples=rows)
