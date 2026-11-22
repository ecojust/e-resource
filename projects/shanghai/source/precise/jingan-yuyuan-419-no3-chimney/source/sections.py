"""Measure stack, cap, and the two interrupted tiled eaves directly on each delivered mesh."""
from chimney_and_eaves import *
def test(tri,materials,hit):
 rows=[]
 def read(x,z,m,detail):
  result=hit(tri,materials,np.array([x,-2,z]),np.array([0.,1.,0.]))
  assert result and result[0]==m,(detail,x,z,result,m);rows.append(dict(label=detail,material=m,point=result[1]))
  return result[1][1]
 for x in (-.534,-.39,-.206,0,.218,.407,.533):
  for z in (.3,1.1,2.43,2.69,2.92,3.37,3.97,4.55,5.11,5.78,6.25):assert abs(read(x,z,RENDER,'Continuous front face of stack')+.195)<.002
  for z,y in [(6.442,-.211),(6.493,-.233)]:assert abs(read(x,z,CAP,'Two shallow steps of the cap')-y)<.002
 for side in (-1,1):
  for x in (.69,.934,1.158,1.459,1.96,2.2):
   for z,m in [(.4,RENDER),(1.36,RENDER),(2.54,SHADOW),(2.61,FASCIA)]:read(x*side,z,m,'Wall and projecting eave either side of chimney')
  for y in (-.22,.237,.694):
   r=hit(tri,materials,np.array([side*.96,y,5]),np.array([0.,0.,-1.]))
   assert r and r[0] in (CLAY,PALE);rows.append(dict(label='Upper pitched roof surface',material=r[0],point=r[1]))
 return rows
