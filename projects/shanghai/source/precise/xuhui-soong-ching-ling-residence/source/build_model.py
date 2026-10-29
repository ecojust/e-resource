"""Photo-informed Soong Ching-ling main-house exterior; not survey geometry."""
import argparse,json,math,sys
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(HERE/'common'))
from photo_architecture import Builder,Facade,opening
from roof_geometry import Roof
ID='xuhui-soong-ching-ling-residence'
PAL={
 'pebbledash':{'color':[1,1,1],'roughness':1,'metallic':1,'texture':str(ROOT/'textures/soong-original-pebbledash-basecolor.png'),'normal_texture':str(ROOT/'textures/soong-original-pebbledash-normal.png'),'orm_texture':str(ROOT/'textures/soong-original-pebbledash-orm.png'),'normal_scale':.35,'extras':{'license':'MIT','procedural_not_photo':True,'repeat_metres':.4,'occlusion_strength':.35}},
 'pale trim':{'color':[.74,.73,.68],'roughness':.82},'grey trim':{'color':[.42,.45,.43],'roughness':.82},
 'green wood':{'color':[.055,.085,.071],'roughness':.72},'cream wood':{'color':[.73,.69,.53],'roughness':.74},
 'glass':{'color':[.12,.19,.19],'roughness':.29,'metallic':.12},'metal':{'color':[.045,.065,.054],'roughness':.55,'metallic':.40},
 'stone':{'color':[.35,.35,.31],'roughness':.92},'roof underlay':{'color':[.26,.10,.06],'roughness':.95},
 'dormer red':{'color':[.48,.09,.075],'roughness':.60},'ridge red':{'color':[.54,.17,.075],'roughness':.85},
 'shadow':{'color':[.025,.028,.023],'roughness':1},'lantern glass':{'color':[.49,.31,.16],'roughness':.38},
}
for i,k in enumerate([.85,.96,1.04,1.12]):PAL[f'tile{i}']={'color':[.20*k,.07*k,.035*k],'roughness':.9}
class House:
 def __init__(self,lod=False):self.b=Builder(PAL);self.lod=lod;self.roof=Roof(lod);self.features=[]
 def bx(self,c,s,m,label):self.b.box(c,s,m,label=label)
 def tube(self,pts,r=.02,m='metal',label='metalwork'):self.b.tube(pts,r,m,6 if self.lod else 10,label)
 def window(self,f,p,label,cols=2,rows=4,wood='green wood'):
  x0,z0,x1,z1=p.bounds;inner=p.buffer(-.07,join_style=2);bars=[]
  for i in range(1,cols):
   x=x0+(x1-x0)*i/cols;bars.append(box(x-.022,z0,x+.022,z1))
  for i in range(1,rows):
   z=z0+(z1-z0)*i/rows;bars.append(box(x0,z-.025,x1,z+.025))
  pane=inner.difference(unary_union(bars));f.prism(p.difference(pane),-.17,-.04,wood,label+' frame')
  f.prism(pane,-.235,-.22,'glass',label+' recessed glazing')
  f.box((x0+x1)/2,z0-.06,x1-x0+.18,.12,.36,.035,'pale trim',label+' sill')
  self.features.append({'id':label,'facade_origin':f.center.tolist(),'normal':f.n.tolist(),'outline':list(p.exterior.coords),'glass_inset_m':.22})
 def shutters(self,f,x,z,w,h,label,closed=False):
  for sign in [-1,1]:
   sx=x+sign*(w/4 if closed else w*.76);sw=w*.49
   p=box(sx-sw/2,z,sx+sw/2,z+h);inner=p.buffer(-.055,join_style=2)
   f.prism(p.difference(inner),.025,.105,'green wood',label+' shutter frame')
   if self.lod:f.prism(inner,.032,.06,'green wood',label+' LOD shutter panel')
   else:
    for zz in np.arange(z+.065,z+h-.06,.085):f.box(sx,zz,sw-.11,.045,.085,.061,'green wood',label+' shutter louvre')
 def walls(self):
  b=self.b
  footprint=Polygon([(-11,-7),(-8,-7),(-8,-5.4),(8,-5.4),(8,-7),(11,-7),(11,7),(-11,7)])
  b.plan_prism(footprint,0,.35,'stone','main-house plinth; dimensions estimated')
  central=Facade(b,(-8,-5.4),(8,-5.4),'south recessed gallery')
  holes=[];windows=[]
  for i,x in enumerate([-5.2,0,5.2]):
   for floor in [0,1]:
    p=opening(x,.45 if floor==0 else 4.2,2.55 if floor==0 else 1.65,2.65 if floor==0 else 2.35)
    holes.append(p);windows.append((p,f'south gallery {floor}-{i}',floor,x))
  central.wall(.35,7.62,holes,.28,'pebbledash')
  for p,label,floor,x in windows:
   self.window(central,p,label,4 if not floor else 2,2 if not floor else 4,wood='cream wood' if not floor else 'green wood')
   if floor:self.shutters(central,x,4.2,1.65,2.35,label,closed=x==5.2)
  # Front wings and observed decorated east window; unobserved side surfaces remain simple.
  for sign in [-1,1]:
   x=sign*9.5;f=Facade(b,(x-1.5,-7),(x+1.5,-7),'south wing '+str(sign))
   low=opening(0,.45,2.15,2.8);upper=opening(0,4.8,2.15,1.75)
   f.wall(.35,7.62,[low,upper],.28,'pebbledash')
   self.window(f,low,'wing ground '+str(sign),4,2,wood='cream wood');self.window(f,upper,'wing upper '+str(sign),4,4)
   f.box(0,4.59,2.40,.27,.48,.09,'pale trim','decorative window box')
   f.prism(box(-1.12,4.49,1.12,4.69).difference(box(-1.05,4.52,1.05,4.66)),.342,.36,'grey trim','window box rim')
   diamond=Polygon([(-.20,4.59),(0,4.70),(.20,4.59),(0,4.48)]);f.prism(diamond.difference(diamond.buffer(-.04)),.36,.385,'grey trim','window box diamond')
   for u in [-.9,0,.9]:f.box(u,4.36,.15,.18,.32,.07,'pale trim','window box bracket')
   panel=box(-1.12,3.93,1.12,4.22);f.prism(panel.buffer(.045,join_style=2).difference(panel),.008,.045,'grey trim','wing spandrel rim')
  # Outer side walls stop inside the full-width front and back faces.
  for a,c,name in [((11,-6.72),(11,6.72),'east hidden'),((-11,6.72),(-11,-6.72),'west hidden'),((-8,-6.72),(-8,-5.4),'west gallery return'),((8,-5.4),(8,-6.72),'east gallery return')]:
   Facade(b,a,c,name).wall(.35,7.62,[],.28,'pebbledash')
  back=Facade(b,(11,7),(-11,7),'north entrance')
  door=opening(0,.35,1.65,2.65);upper=opening(0,4.2,1.6,2.25)
  back.wall(.35,7.62,[door,upper],.28,'pebbledash')
  self.window(back,door,'north entrance door',2,3,wood='cream wood');self.window(back,upper,'north balcony door',2,4)
  self.shutters(back,0,4.2,1.6,2.25,'north balcony')
  # Eave soffit follows the actual roof rectangle, not the recessed wall line.
  ring=box(-11.6,-7.6,11.6,7.6).difference(footprint)
  b.plan_prism(ring,7.56,7.62,'pale trim','eave underside')
  for x in np.arange(-10.8,11,.65):
   profile=Polygon([(-7.02,7.55),(-7.57,7.55),(-7.48,7.45),(-7.31,7.45),(-7.20,7.34),(-7.02,7.34)])
   b.prism(profile,x-.035,x+.035,lambda y,z,d:(d,y,z),'pale trim','eaves bracket')
 def railing(self,points,z,label):
  points=np.asarray(points);lengths=np.r_[0,np.cumsum(np.linalg.norm(np.diff(points,axis=0),axis=1))];total=lengths[-1]
  for height in [z+.08,z+1.00]:self.tube([(x,y,height) for x,y in points],.026,label=label+' horizontal rail')
  for d in np.arange(.07,total,.16):
   i=min(len(points)-2,np.searchsorted(lengths,d,side='right')-1);t=(d-lengths[i])/(lengths[i+1]-lengths[i]);x,y=points[i]*(1-t)+points[i+1]*t
   self.tube([(x,y,z+.10),(x,y,z+.98)],.011,label=label+' vertical picket')
  for i in [0,len(points)//2,len(points)-1]:
   x,y=points[i];self.bx((x,y,z+.52),(.07,.07,1.10),'metal',label+' post')
 def balcony(self):
  arc=[(x,-7.15-1.0*math.sqrt(max(0,1-(x/8)**2))) for x in np.linspace(-8,8,41 if not self.lod else 21)]
  poly=Polygon([(-8,-5.4)]+arc+[(8,-5.4)])
  self.b.plan_prism(poly,3.62,3.86,'grey trim','curved south balcony slab')
  self.b.plan_prism(poly.buffer(.055,join_style=2),3.70,3.78,'pale trim','south balcony moulding')
  self.railing([(-8,-5.5)]+arc+[(8,-5.5)],3.88,'south balcony')
  # Photo-led oval ornaments, deliberately not exact historic insignia.
  for x in [-5.3,0,5.3]:
   y=-7.15-math.sqrt(1-(x/8)**2)-.035
   self.tube([(x+.37*math.cos(t),y,4.42+.23*math.sin(t)) for t in np.linspace(0,2*math.pi,33 if not self.lod else 17)],.014,label='balcony oval ornament')
   self.tube([(x-.24,y,4.42),(x,y,4.58),(x+.24,y,4.42),(x,y,4.26),(x-.24,y,4.42)],.014,label='balcony ornamental diamond')
  for x in [-7.65,-2.55,2.55,7.65]:
   y=-7.15-math.sqrt(1-(x/8)**2)+.16
   self.column(x,y,.35,3.62,'south veranda column')
  # North entry portico seen in the 2016 photo, separate from the annex.
  self.bx((0,8.05,.16),(4.6,2.65,.32),'stone','north porch platform')
  for x in [-1.9,1.9]:self.column(x,9.0,.32,3.65,'north porch column')
  for z,w,d in [(3.64,4.5,2.55),(3.79,4.7,2.70),(3.91,4.6,2.60)]:self.bx((0,8.18,z),(w,d,.14),'grey trim','north portico entablature')
  self.railing([(-2.15,7.10),(-2.15,9.35),(2.15,9.35),(2.15,7.10)],4.0,'north balcony')
  # Pendant lamp is exterior furniture; no emissive or extra runtime light.
  self.tube([(0,8.35,3.57),(0,8.35,3.04)],.018,label='entry lantern suspension')
  self.bx((0,8.35,2.82),(.28,.28,.42),'lantern glass','entry lantern body')
  for x in [-.15,.15]:
   for y in [8.20,8.50]:self.tube([(x,y,2.59),(x,y,3.05)],.018,label='lantern corner')
  for z in [2.59,3.05]:self.bx((0,8.35,z),(.34,.34,.045),'metal','lantern cap')
 def column(self,x,y,bottom,top,label):
  self.bx((x,y,(bottom+top)/2),(.30,.30,top-bottom),'grey trim',label+' shaft')
  for z,size,h in [(bottom+.10,.48,.20),(bottom+.24,.38,.08),(top-.07,.48,.14),(top-.18,.38,.08)]:self.bx((x,y,z),(size,size,h),'pale trim',label+' moulding')
 def dormers(self):
  for i,cx in enumerate(self.roof.centres):
   z=self.roof.base;f=Facade(self.b,(cx-.85,self.roof.front),(cx+.85,self.roof.front),'south dormer '+str(i))
   outline=opening(0,z-.04,1.70,.89,arch=.85,segments=40 if not self.lod else 20)
   p=opening(0,z+.035,1.42,.73,arch=.71,segments=36 if not self.lod else 18)
   f.prism(outline.difference(p),-.14,.015,'dormer red','dormer curved face')
   f.prism(p.difference(p.buffer(-.055,join_style=2)),-.09,-.035,'pale trim','dormer white frame')
   pane=p.buffer(-.055,join_style=2);f.prism(pane,-.13,-.115,'glass','dormer inset glass')
   # Radial fanlight bars are real tubes clipped within the semicircle.
   for t in np.linspace(.18,math.pi-.18,5):
    self.tube([f.point(0,z+.07,-.025),f.point(.64*math.cos(t),z+.07+.64*math.sin(t),-.025)],.012,'pale trim','dormer radial fanlight')
   self.features.append({'id':'dormer'+str(i),'x':cx,'front_y':self.roof.front,'base_z':z,'roof_cutout':True})
 def chimneys(self):
  for i,x in enumerate([-4.8,4.8]):
   y=.65;bottom=self.roof.height(x,y)-.12;top=12.0
   self.bx((x,y,(bottom+top)/2),(1.8,.90,top-bottom),'pebbledash','chimney shaft')
   self.bx((x,y,top),(1.95,1.06,.16),'pale trim','chimney cap')
   for xx in [-.57,-.19,.19,.57]:self.b.lathe((x+xx,y),[(12.08,.10),(12.18,.10),(12.21,.14),(12.25,.14)],'pale trim',8 if self.lod else 16,'chimney small pot')
   if i==0:self.b.lathe((x+.30,y+.10),[(12.10,.09),(13.20,.09),(13.23,.13),(13.28,.13)],'pale trim',12,'tall ventilator pipe')
  for x in [-8.1,8.1]:
   self.tube([(x,-5.5,7.45),(x,-5.5,7.0),(x,-5.6,.40)],.05,'metal','south rainwater pipe')
 def finish(self):
  self.walls();self.balcony();self.dormers();self.chimneys();self.roof_report=self.roof.add(self.b)
  for part in self.b.parts:
   if part['material']=='pebbledash':world_uv(part)
  return self
def world_uv(p):
 old=np.asarray(p['vertices']);verts=[];uv=[];faces=[]
 for tri in p['triangles']:
  xyz=old[list(tri)];n=np.cross(xyz[1]-xyz[0],xyz[2]-xyz[0]);n/=np.linalg.norm(n)
  u=np.cross([0.,0.,1.],n) if abs(n[2])<.999999 else np.array([1.,0.,0.])-n*n[0];u/=np.linalg.norm(u);v=-np.cross(n,u)
  k=len(verts);verts.extend(xyz.tolist());uv.extend([[float(np.dot(q,u)/.4),float(np.dot(q,v)/.4)] for q in xyz]);faces.append((k,k+1,k+2))
 p['vertices']=verts;p['texcoords']=uv;p['triangles']=faces
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--lod',action='store_true');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 h=House(a.lod).finish();role='lod' if a.lod else 'raw'
 result=h.b.save(a.out/f'{ID}-{role}.glb',metadata={'id':ID,'name':'上海宋庆龄故居主楼','scope':'Photo-informed main-house exterior candidate; hidden sides/rear simplified; no annex, garden or interior','anchor':None,'source_owner':None,'all_dimensions_estimated':True,'coordinates':'Local right/up/front; no geographic heading','map_replacement':False,'photos_embedded':False,'copyright':'Geometry and procedural materials MIT; separate references CC BY-SA4.0'})
 for suffix,data in [('features',h.features),('roof',h.roof_report)]: (a.out/f'{role}-{suffix}.json').write_text(json.dumps(data,indent=2)+'\n')
 print(json.dumps({k:v for k,v in result.items() if k!='part_summary'}))
