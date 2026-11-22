"""Test the gable, inner reveal, open casement and roof shells in the exported mesh."""
import numpy as np
from math import sin,cos
from gable import *
def test(tri,materials,hit):
 rows=[]
 def ray(label,origin,direction,expected):
  q=hit(tri,materials,np.array(origin,float),np.array(direction,float));mat=q[0] if q else None
  assert mat in expected,(label,origin,direction,mat,expected)
  rows.append(dict(label=label,material=mat,point=q[1] if q else None))
  return q
 for factor in (.16,.44,.75,.93,1.22,1.5):
  for dx,dz in ((1,0),(0,1),(-1,0),(0,-1),(.5,.5),(-.5,.5)):
   x=VENT[0]+factor*VR*dx;z=VENT[1]+factor*VH*dz
   q=ray('Diamond-opening perimeter and recessed view',(x,-1,z),(0,1,0),[SHADOW if factor<1 else WALL])
   assert abs(q[1][1]-(.62 if factor<1 else 0))<.002
 for x in np.linspace(X0+.16,RIDGE-.14,7):
  for j in range(8):
   ray('Rounded caps over left roof',(x,j*.189+.002,4),(0,0,-1),[CLAY,DARK_CLAY,LIGHT_CLAY])
   ray('Concave tiles between covers',(x,j*.189+.0945,4),(0,0,-1),[CLAY])
 for y in np.linspace(.005,DEPTH-.038,9):
  ray('Ridge caps transverse to field tiles',(RIDGE,y,4),(0,0,-1),[CLAY])
 for z in (.36,1.13,1.56):
  for y in (.32,.65,.94,1.37):ray('Side return receives the clay eave',(X0-.5,y,z),(1,0,0),[WALL])
 for x in (X0+.15,-1.1,.33,.69,.87):
  for z in (1.46,1.62,1.85):ray('Gable plaster above opening',(x,-1,z),(0,1,0),[WALL])
 for hinge,angle,side in ((WIN[0]+.019,2.08,1),(WIN[1]-.019,1.90,-1)):
  for u in (.10,.21,.33,.45):
   x=hinge+side*u*cos(angle)
   for z,mat in ((.24,GLASS),(.438,FRAME),(.69,GLASS),(.838,FRAME),(1.07,GLASS)):
    ray('Hinged sash rails alternate with glass',(x,-2,z),(0,1,0),[mat])
 return rows
