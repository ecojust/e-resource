import numpy as np
from gatehead import *
def test(tri,names,hit):
 result=[]
 def ray(label,x,z,expect):
  p=np.array([x,-2.,z]);direction=np.array([0.,1.,0.]);q=hit(tri,names,p,direction);material=q[0] if q else None
  assert material in expect,(label,material,expect)
  result.append(dict(label=label,origin=p.tolist(),direction=direction.tolist(),material=material,point=q[1] if q else None))
 for i,x in enumerate(np.linspace(-1.5,1.5,21)):
  ray('Tablet lower edge '+str(i),x,1.03,[WHITE]);ray('Lower horizontal cornice '+str(i),x,.943,[LEDGE]);ray('Air below beam '+str(i),x,.65,[None])
  ray('Upper horizontal course '+str(i),x,1.738,[LEDGE])
 for ch,polys in letters():
  for i,g in enumerate(getattr(polys,'geoms',[polys])):
   if g.area<.0002:continue
   pt=g.representative_point();ray('Raised '+ch+str(i),pt.x,pt.y,[GOLD])
 for side,x in [('Left',-1.95),('Right',1.95)]:
  for z in (.061,.203,.344,.512,.675,1.102,1.336):
   for dx in (-.24,.24):ray(side+' return '+str((dx,z)),x+dx,z,BRICKS+[JOINT])
  ray(side+' cap lip',x,1.776,[LEDGE]);ray(side+' open crown joint',x,1.853,[None])
 return result
