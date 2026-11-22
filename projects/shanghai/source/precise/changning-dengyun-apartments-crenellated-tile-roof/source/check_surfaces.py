"""Verify projections on both cornices, selected window frames, open crenels and roof hips."""
from pathlib import Path
import os,runpy
from gable import *
p=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',Path(__file__).resolve().parents[4]))
Reader=runpy.run_path(str(p/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
def check(reader):
 rows=[]
 def ray(name,origin,dir,mat,dist,tol=.009):
  hit=reader.ray(origin,dir,10)
  ok=not hit if mat is None else bool(hit and hit['material']in mat and abs(hit['distance_m']-dist)<tol)
  rows.append(dict(part=name,origin=origin,hit=hit,material=mat,expected_distance=dist,passed=ok))
 for x in WINS:
  for z in (.34,.65,1.05):ray('Glazed opening',[x+.12,-1,z],[0,1,0],[GLASS],1.139)
  ray('Mullion',[x,-1,.68],[0,1,0],[WOOD],1.087)
 for x in (-2.69,-2.09,-1.18,-.52,.28,.79,1.5,2.68):
  for z,y,m in [(1.91,-.064,BAND),(2.005,-.105,SOFFIT),(2.08,-.14,STONE),(2.15,-.024,STONE)]:
   centers=[-HALF+.15+i*(2*HALF-.30)/16 for i in range(17)]
   if z==1.91 and any(abs(x-c)<.047 for c in centers):
    ray('Stone bracket in front of the lowest band',[x,-1,z],[0,1,0],[SOFFIT],.913)
    safe=x+.085 if all(abs(x+.085-c)>.06 for c in centers)else x-.085
    ray('Cornice next to the bracket',[safe,-1,z],[0,1,0],[m],1+y)
   else:ray('Cornice projection',[x,-1,z],[0,1,0],[m],1+y)
 for i in range(14):
  x=-HALF+.215+(2*HALF-.43)*i/13
  ray('Dark face of crenel',[x,-1,2.35],[0,1,0],[PARAPET],.993)
  ray('Light cap on crenel',[x,-1,2.439],[0,1,0],[STONE],.983)
 ray('Raised central parapet block',[.59,-1,2.62],[0,1,0],[PARAPET],1.012)
 ray('Raised block light coping',[.59,-1,2.767],[0,1,0],[STONE],.985)
 for i in range(17):
  x=-HALF+.15+i*(2*HALF-.30)/16;ray('Vertical corbel',[x,-1,1.70],[0,1,0],[SOFFIT],.913)
 for x,y in [(-2.73,.72),(-2.34,1.23),(-1.71,.53),(-.79,.584),(.42,1.08),(1.22,.49),(1.84,.64),(2.35,2.09),(2.72,1.71),(1.35,2.71),(.63,2.83),(-1.17,2.88)]:
  ray('Actual surface of tile slope',[x,y,5],[0,0,-1],[TILE,LIGHT],5-roof_z(x,y),.065)
 ray('Roof continuity at a tiled-course joint',[-.81,.58,5],[0,0,-1],[TILE,LIGHT,'Roof bedding'],5-roof_z(-.81,.58),.066)
 for sign in (-1,1):
  for yy,peak in ((.16,1.65),(DEPTH-.14,DEPTH-.14-1.49)):
   for frac in (.19,.44,.79):
    x=sign*((HALF-.18)-2.18*frac);y=yy+(peak-yy)*frac
    ray('Raised diagonal hip tile',[x,y,5],[0,0,-1],[RIDGE],5-roof_z(x,y)-.066,.016)
 for y in (.45,.76,1.26,2.43,2.93):ray('Side projecting eave',[5,y,2.055],[-1,0,0],[STONE],5-(HALF+.14+.05))
 return dict(passed=all(q['passed']for q in rows),samples=rows)
