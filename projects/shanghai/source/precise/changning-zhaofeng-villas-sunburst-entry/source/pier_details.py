"""The street number, set-back return, cement planter and clipped evergreen planting seen across the entry."""
from pathlib import Path
import json,math
import numpy as np
import wall_plane
from shapely.geometry import Polygon,box,GeometryCollection
HERE=Path(__file__).absolute().parent
def paint_line(b,text,x,z,width,height,y,material,label,lod=False):
 outlines=json.loads((HERE/'sign-lettering.json').read_bytes());shapes=[];advance=0.
 for char in text:
  if char==' ':advance+=280;continue
  rings=outlines[char];letter=GeometryCollection()
  for ring in rings:
   if len(ring)<3:continue
   p=Polygon(ring)
   if not p.is_valid:p=p.buffer(0)
   if not p.is_empty:letter=letter.symmetric_difference(p)
  if letter.is_empty:continue
  xmin,_,xmax,_=letter.bounds
  shapes.append((letter,advance-xmin));advance+=xmax-xmin+100.
 if not shapes:return
 advance-=100.;font_scale=min(width/advance,height/1000)
 for i,(letter,shift)in enumerate(shapes):
  def mapper(u,v,d):return (x+(u+shift-advance/2)*font_scale,y-d,z+v*font_scale)
  letter=letter.simplify(9. if lod else 4.,preserve_topology=True)
  for part in getattr(letter,'geoms',[letter]):
   if part.geom_type=='Polygon' and part.area>60:
    b.prism(part,0,.0028,mapper,material,label+' '+str(i+1))
def planter_leaves(b,lod):
 rng=np.random.default_rng(2407);count=30 if lod else 58;cycles=1 if lod else 2
 # The evergreen strip is clipped across its top but breaks around individual shrubs.
 # Offset rings describe the outside, including rounded returns at the ends.
 n=10 if lod else 17;ys=np.linspace(.13,2.72,n);rings=[]
 for i,x in enumerate(ys):
  taper=np.clip(min(i+1,n-i)/2,.55,1);h=.985+.088*math.sin(x*5)+.036*math.cos(x*17)
  d=.178*taper;row=[(-.084-d,.366),(-.084-d*1.14,.625),(-.084-d*.91,h-.05),(-.084-d*.53,h+.035),(-.084+d*.65,h+.045),(-.084+d*1.08,h-.06),(-.084+d*1.09,.625),(-.084+d*.83,.366)]
  rings.append([(x,y,z)for y,z in row])
 verts=[p for section in rings for p in section];k=len(rings[0]);faces=[]
 for i in range(n-1):
  for j in range(k):
   q=(j+1)%k;faces.append((i*k+j,i*k+q,(i+1)*k+q,(i+1)*k+j))
 # Reverse the ring winding for the external surfaces, and triangulate each end as a fan.
 faces=[tuple(reversed(f))for f in faces]
 for side,index in [(0,0),(1,n-1)]:
  center=len(verts);verts.append(tuple(np.mean(rings[index],axis=0)))
  for j in range(k):
   face=(center,index*k+j,index*k+(j+1)%k);faces.append(tuple(reversed(face)) if side else face)
 b.add(verts,faces,'evergreen foliage','planting/clipped shrub canopy')
 # Small leaves are closed lenses, with a raised middle vein. Combine leaves of one shade
 # into one editable plant object while retaining the individual closed shells.
 for group in range(3):
  v=[];f=[]
  for j in range(count*cycles):
   x=rng.uniform(.17,2.68);top=.985+.088*math.sin(x*5)+.036*math.cos(x*17);angle=rng.uniform(-1.4,1.4)
   if j%2:
    y=rng.uniform(-.19,.04);z=top+.038+rng.uniform(-.015,.027);across=np.array([0,1,0.]);normal=np.array([0,0,1.])
   else:
    y=-.270+rng.uniform(-.016,.004);z=rng.uniform(.51,top-.035);across=np.array([0,0,1.]);normal=np.array([0,-1,0.])
   along=np.array([1,0,0.]);u=math.cos(angle)*along+math.sin(angle)*across;t=-math.sin(angle)*along+math.cos(angle)*across
   c=np.array([x,y,z]);length=rng.uniform(.019,.034);width=rng.uniform(.009,.016);offset=len(v)
   v.extend([c-length*u,c-width*t,c+length*u,c+width*t,c+.004*normal,c-.002*normal])
   for a in range(4):
    q=(a+1)%4;f.extend([(offset+a,offset+q,offset+4),(offset+q,offset+a,offset+5)])
  b.add(v,f,'leaf shade '+str(group+1),'planting/outer leaf spray '+str(group+1))
def add(b,lod):
 b.palette.update({'ivory sign lettering':{'color':[.86,.85,.76],'roughness':.66},'engraved dark slate':{'color':[.20,.202,.181],'roughness':.88},'evergreen foliage':{'color':[.076,.15,.052],'roughness':.91}})
 for i,col in enumerate([[.077,.156,.047],[.115,.194,.065],[.056,.124,.045]]):b.palette['leaf shade '+str(i+1)]={'color':col,'roughness':.71}
 paint_line(b,'712弄1–168号',-5.30,2.750,.409,.062,-.399,'ivory sign lettering','address plate/white number',lod)
 paint_line(b,'长宁路',-5.30,2.710,.135,.031,-.399,'ivory sign lettering','address plate/street name',lod)
 # The municipal plaque's two legible headings use the contemporary bilingual
 # layout. The lines below and the code on the adjacent panel are not transcribed.
 x,y,z=wall_plane.pixel_to_world((577,419),.030*.80)
 paint_line(b,'优秀历史建筑',x,z,.378,.027,y-.001,'engraved dark slate','heritage plaque/designation heading',lod)
 if not lod:
  x,y,z=wall_plane.pixel_to_world((577,425),.030*.80)
  paint_line(b,'HERITAGE ARCHITECTURE',x,z,.365,.015,y-.001,'engraved dark slate','heritage plaque/English heading')
 # The round medallion carries a pitched-roof house and a projecting wing.
 def badge(poly,name):
  points=[wall_plane.pixel_to_world(uv,.029*.8) for uv in poly]
  b.prism(Polygon([(a[0],a[2]) for a in points]),.001,.003,lambda a,h,d:(a,points[0][1]-d,h),'engraved dark slate','history plaque/'+name)
 badge([(687,400),(701,408),(699,415),(689,420),(686,417)],'roof silhouette')
 badge([(673,411),(685,403),(685,410),(674,416)],'gable of the second wing')
 badge([(674,418),(683,412),(683,416),(677,420)],'projecting front bay')
 # The lower ashlar wall returns west towards the shop. The gate survey measures the visible length.
 outer=-5.85;w=1.95;mid=outer-w/2
 b.box((mid,-.225,.690),(w,.30,1.38),'grey-pink aggregate plaster',label='west return/masonry towards neighbouring shop')
 b.box((mid,-.225,1.416),(w+.028,.35,.078),'worn pale cement',label='west return/stone coping')
 # At the eastern end the fluted return projects beyond the name wall.
 x=3.09;front=.078;zed=2.89
 b.box((x,front+.15,zed/2),(.43,.30,zed),'grey-pink aggregate plaster',label='east pier/solid return at property edge')
 means=box(x-.21,.08,x+.21,zed-.09)
 for k in range(5):
  u=x-.134+k*.067;means=means.difference(box(u-.008,.13,u+.008,zed-.12))
 b.prism(means,-front,-front+.027,lambda u,v,d:(u,-d,v),'worn pale cement','east pier/five fine flutes')
 for i,(h,span,deep)in enumerate([(2.87,.47,.37),(2.94,.51,.40),(3.04,.56,.44)]):
  b.box((x,front+.125,h),(span,deep,.092),'worn pale cement',label='east pier/projecting capital '+str(i+1))
 for j in range(31):
  b.box((.04+j*.092,-.343,.113),(.019,.024,.05),'worn pale cement',label=f'planter/cast front lip rib {j+1:02}')
 planter_leaves(b,lod)
 return b
