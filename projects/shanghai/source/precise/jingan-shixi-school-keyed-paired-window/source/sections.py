"""Check both lower and upper glazing, the central divider, the six keys and the lateral wall."""
from keyed_school_window import *
def test(tri,materials,hit):
 rows=[]
 def at(x,z,mat,label):
  r=hit(tri,materials,np.array([x,-1.9,z]),np.array([0.,1.,0.]));assert r and r[0]==mat,(x,z,mat,r);rows.append(dict(label=label,material=mat,point=r[1]));return r[1]
 for hand in [-1,1]:
  for x in [.12,.22,.415,.515]:
   for z in [.5,.58,.775,.852,1.02,1.17,1.45,1.615,1.89,2.036]:at(hand*x,z,DARK if z<1.29 else GLASS,'Daylight and shadow in two leaves')
  for z in [.638,1.164,1.732]:
   for off in [-.055,0,.055]:at(hand*.881,z+off,LIMESTONE,'Projecting jamb key')
  for z in [.91,1.42,2.04]:at(hand*.881,z,WALL,'Pebbled wall between keys')
  for z in [.51,.86,1.46,2.06]:at(hand*.76,z,LIMESTONE,'Stone sides')
 for z in [.51,.72,1.05,1.46,1.8,1.97]:at(0,z,MULLION,'Pale continuous divider')
 for x in [-.78,-.57,-.2,0,.2,.57,.78]:at(x,.258,LIP,'Front of projecting sill')
 return rows
