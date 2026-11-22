"""Measure the empty perforations, the surrounding cast faces, top and bottom mouldings."""
from pathlib import Path
import os,runpy
from shapely.geometry import Point
from gable import *
p=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',Path(__file__).resolve().parents[4]))
Reader=runpy.run_path(str(p/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
def check(reader):
 rows=[]
 def test(part,x,z,y,material):
  origin=[float(x),-.55,float(z)];hit=reader.ray(origin,[0,1,0],1.2);ok=hit is None if y is None else bool(hit and hit['material']==material and abs(hit['distance_m']-(.55+y))<.003)
  rows.append(dict(part=part,origin=origin,expected=material,depth=y,hit=hit,passed=ok))
 for label,outline in HOLES.items():
  poly=outline.buffer(-.011)
  assert not poly.is_empty
  p=poly.representative_point();test(label+' open centre',p.x,p.y,None,None)
  b=poly.bounds
  for x in np.linspace(b[0],b[2],6):
   for z in np.linspace(b[1],b[3],7):
    if poly.contains(Point(x,z)):test(label+' open section',x,z,None,None)
 solids=unary_union(list(HOLES.values())).buffer(.022)
 for x in np.linspace(-.30,.30,12):
  for z in np.linspace(.035,.55,12):
   if not solids.contains(Point(x,z)):test('Front cast web',x,z,0,FACE)
 for x in (-.24,0,.24):
  test('Base moulding',x,-.05+.002,-.032,SHADOW);test('Cap moulding',x,.595,-.030,CAP);test('Lower flange',x,-.025,-.026,PLINTH)
 return dict(passed=all(v['passed']for v in rows),samples=rows)
