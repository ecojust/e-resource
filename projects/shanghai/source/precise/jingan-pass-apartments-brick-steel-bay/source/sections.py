from brick_steel_bay import *
def test(tri,materials,hit):
 rows=[]
 def probe(x,z,mat,label):
  a=hit(tri,materials,np.array([x,-3,z]),np.array([0.,1.,0.]));assert a and a[0]==mat,(x,z,mat,a)
  rows.append(dict(label=label,material=mat,point=a[1]));return a[1][1]
 for x in (-1.5,-1.31,1.34,1.54,1.73,1.91,2.10):
  for z in (.23,.87,1.49,2.16,2.72,3.12,3.67,4.85,5.57):
   assert abs(probe(x,z,BRICK,'Front wall and the projecting pier')-(-.138 if x>1.60 else 0))<.001
 for s in (.47,3.39):
  for i in range(4):
   for j in range(3):probe(-1.056+2.112*(i+.5)/4,s+.048+1.543*(j+.5)/3,GLASS if (i+j)%3 else SHADE,'Rectangular steel-window lights')
  for x in (-1.056,-.528,0,.528,1.056):
   for dz in (.24,.71,1.15,1.47):probe(x,s+dz,STEEL,'Vertical steel mullions')
  for x in (-.83,-.31,.21,.79):
   probe(x,s-.028,SILL,'Shallow projecting lower sill')
   for dz in np.linspace(.048,1.591,4):probe(x,s+dz,STEEL,'Horizontal steel bars')
 return rows
