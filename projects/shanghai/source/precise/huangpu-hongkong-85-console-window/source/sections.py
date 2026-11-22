"""Read four opening depths, the bracket pair, and the projecting cornice from each mesh."""
from console_window import *
def test(tri,materials,hit):
 rows=[]
 def at(x,z,mat,label):
  r=hit(tri,materials,np.array([x,-2,z]),np.array([0.,1.,0.]));assert r and r[0]==mat,(x,z,r,mat)
  rows.append(dict(label=label,material=mat,point=r[1]));return r[1]
 for z in (2.18,2.41,2.72,2.99,3.25,3.52):
  for x in (-.51,-.354,-.13,.123,.341,.50):at(x,z,GLASS,'Fixed transom glass')
 for z in (.31,.51,1.03,1.21,1.76,1.98):
  for x in (.13,.36,.51):at(x,z,GLASS,'Right closed glazing')
  for x in (-.522,-.398,-.301):
   p=at(x,z,GLASS,'Open pane stands proud of the inner frame');assert p[1]<.11
  for x in (-.104,-.068):at(x,z,INNER,'Open gap behind leading edge')
 for x in (-.78,.78):
  for z in (.5,1.27,1.72,2.44,3.21):at(x,z,STONE,'Tall stone window surround')
 for x in (-.895,.895):
  for z in (3.612,3.731,3.875,4.035):at(x+.037,z,CUT,'Projecting corbel at four heights')
 for x in (-.74,-.48,-.241,0,.246,.5,.752):
  for z,mat in [(4.19,STONE),(4.256,SHADE),(4.352,EDGE),(4.418,EDGE)]:at(x,z,mat,'Straight horizontal cornice')
 for x in (-1.35,1.35):
  for z in (1,2,3.5,4.3):at(x,z,BRICK,'Original adjacent brickwork')
 return rows
