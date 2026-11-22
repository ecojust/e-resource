"""Check the silhouettes of opened leaves, masonry spandrel, the shadow and exposed rafter ends."""
from eave_and_open_casements import *
def test(tri,materials,hit):
 rows=[]
 def at(x,z,material,label):
  q=hit(tri,materials,np.array([x,-2.3,z]),np.array([0.,1.,0.]));assert q and q[0]==material,(x,z,q,material);rows.append(dict(label=label,material=material,point=q[1]));return q[1]
 for z in [.38,.47,.63,.85,.96,1.064,1.36,1.49,1.63]:
  for x in [-.65,-.58,-.49]:at(x,z,GLASS2,'Reflecting glass on open left leaf')
  for x in [.29,.39,.5,.62]:at(x,z,GLASS,'Reflecting glass on wider projected right leaf')
  for x in [-.23,-.055,.045]:at(x,z,DARK,'Open space leading behind both leaves')
 for x in [-1.23,-.99,.98,1.26]:
  for z in [.39,.82,1.24,1.68,2.06,2.29]:at(x,z,WALL,'Original rendered spandrel and side wall')
 for x in [-1.368,-.694,.004,.704,1.365]:
  for z in [2.398,2.434]:at(x,z,WOOD,'Square end visible underneath shallow roof')
 for x in [-1.39,-1.11,-.83,-.52,-.19,.15,.49,.87,1.17,1.44]:at(x,2.55,EAVE,'Dark continuous eaves board')
 return rows
