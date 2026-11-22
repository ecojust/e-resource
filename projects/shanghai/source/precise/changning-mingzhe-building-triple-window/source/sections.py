import numpy as np
from window_bay import *
def test(tri,names,hit):
 result=[]
 def front(name,u,v,mats):
  d=np.array([0.,1.,0.]);p=np.array([X(u),-2.,Z(v)]);q=hit(tri,names,p,d);actual=q[0]if q else None
  assert actual in mats,(name,u,v,actual,mats)
  result.append(dict(label=name,origin=p.tolist(),direction=d.tolist(),material=actual,point=q[1]if q else None))
 for i,(l,r) in enumerate(OPEN):
  for u in [l+(r-l)*k for k in (.16,.36,.59,.83)]:
   for v in (119,150,228,285,325):front('Recessed glass',u,v,[GLASS if i!=2 else GLASS2])
  for v in (120,240,345):front('Vertical meeting bar',(l+r)/2,v,[FRAME])
  for x in (.14,.42,.77):front('Transom rail',l+(r-l)*x,176,[FRAME])
 for u in [150,256,448,559]:
  for v in [82,86,96,140,207,300,368,377]:front('Reeding and pilaster section',u,v,[CAP,LIM])
 for u in [165,213,283,348,403,489,542]:
  for v,mat in [(9,CAP),(42,LIM),(60,CAP),(70,SHADE),(386,CAP),(394,LIM)]: 
   if u==348 and v in (42,60):continue
   front('Lintel or sill moulding',u,v,[mat])
 for u,v in [(351,33),(351,47),(350,55)]:front('Carved shield face',u,v,[SHIELD])
 return result
