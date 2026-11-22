from shapely.geometry import Polygon
import numpy as np
BRICK="Photographic facade finish"
def slab(b,s,y0,y1,mat,name):
 for part in getattr(s,'geoms',[s]):
  if part.geom_type=='Polygon'and part.area>1.e-7:b.prism(part,-y1,-y0,lambda x,z,j:(x,-j,z),mat,label=name)
def cb(b,x0,x1,y0,y1,z0,z1,mat,name):
 b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),mat,label=name)
def bricks_uv(b):
 for p in b.parts:
  if p['material']!=BRICK:continue
  vertices=[];tris=[];uv=[];before=np.array(p['vertices'])
  for tri in p['triangles']:
   pts=before[np.asarray(tri)];start=len(vertices);vertices.extend(pts.tolist());tris.append([start,start+1,start+2]);axis=np.argmax(np.abs(np.cross(pts[1]-pts[0],pts[2]-pts[0])))
   for x,y,z in pts:uv.append([(x+2.70)/5.30 if axis!=0 else (y+.22)/1.20,1-z/4.40])
  p.update(vertices=vertices,triangles=tris,texcoords=uv)
