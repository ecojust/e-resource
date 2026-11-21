"""Shoot upward from the historical room side at a photographed ceiling bay."""
from pathlib import Path
import math, os, runpy
here=Path(__file__).resolve().parent
p=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',here.parents[3]))
Reader=runpy.run_path(str(p/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
def check(scene):
 samples=[]
 def probe(part,x,y,z,direction,material,distance=2):
  hit=scene.ray([x,y,z],direction,distance)
  passed=bool(hit and hit['material']==material) if material else hit is None
  samples.append(dict(part=part,origin=[x,y,z],direction=direction,expected=material,hit=hit,passed=passed))
 for radius in (0,.42,.92,1.18):
  for i in range(1 if radius==0 else 8):
   a=i*math.pi/4+.082
   probe('bright circular panel',radius*math.cos(a),radius*math.sin(a),.5,[0,0,1],'bright round panel')
 for radius,material in [(1.304,'incised rib fillet'),(1.327,'faceted edge of plaster rib'),(1.357,'circular rebate'),(1.384,'faceted edge of plaster rib')]:
  for i in range(8):
   a=i*math.pi/4
   probe('circular stepped edge',radius*math.cos(a),radius*math.sin(a),.51,[0,0,1],material)
 for x in (-1.98,1.98):
  for y in (-1.03,0,1.03):
   probe('plaster between ribs',x,y,.35,[0,0,1],'toned ceiling plaster')
  for sign in (-1,1):
   probe('bounded transverse rib',x,sign*(1.78-.093),.40,[0,0,1],'faceted edge of plaster rib')
   probe('narrow flanking fillet',x,sign*(1.78-.093)+.065,.40,[0,0,1],'incised rib fillet')
 for sign in (-1,1):
  for angle in (.22,.59,.96,1.25):
   for y in (-.61,.78):
    x=sign*(2.30+.77*math.sin(angle));z=1.52-.95+.77*math.cos(angle)
    probe('curved side plaster',x,y,z,[sign*math.sin(angle),0,math.cos(angle)],'toned ceiling plaster',.40)
   y=-1.78+.093
   probe('curved transverse rib',x,y,z,[sign*math.sin(angle),0,math.cos(angle)],'faceted edge of plaster rib',.40)
 for y in (-2.03,2.03):
  probe('beyond the cropped bay',0,y,0,[0,0,1],None)
 return dict(passed=all(s['passed']for s in samples),samples=samples)
