"""Photo-guided south building; dimensions and unseen rear construction estimated."""
import argparse
import json
import math
from pathlib import Path
import sys
import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

HERE=Path(__file__).resolve().parent; ROOT=HERE.parent
sys.path.insert(0,str(HERE/'common'))
from photo_architecture import Builder, Facade, opening
from roof_geometry import Roof
ID='xuhui-zikawei-south-building'
G=json.loads((ROOT/'geometry-input.json').read_text())
PAL={
 'pebbledash':{'color':[1,1,1],'roughness':1,'metallic':1,
  'texture':str(ROOT/'textures/zikawei-original-pebbledash-basecolor.png'),
  'normal_texture':str(ROOT/'textures/zikawei-original-pebbledash-normal.png'),
  'orm_texture':str(ROOT/'textures/zikawei-original-pebbledash-orm.png'),
  'normal_scale':.35,'extras':{'license':'MIT','procedural_not_photo':True,'repeat_metres':.4,'occlusion_strength':.35}},
 'pale trim':{'color':[.78,.77,.70],'roughness':.84},
 'shutter wood':{'color':[.205,.25,.265],'roughness':.80},
 'shutter edge':{'color':[.285,.32,.33],'roughness':.75},
 'red wood':{'color':[.30,.085,.065],'roughness':.78},
 'glass':{'color':[.12,.18,.19],'roughness':.32,'metallic':.10},
 'interior shadow':{'color':[.035,.041,.04],'roughness':1},
 'stone':{'color':[.44,.45,.42],'roughness':.94},
 'metal':{'color':[.09,.12,.13],'roughness':.62,'metallic':.35},
 'wood beam':{'color':[.12,.14,.14],'roughness':.88},
 'roof underlay':{'color':[.18,.20,.19],'roughness':.91},
}
PAL['carved pale stone']=PAL['pale trim']
for i,k in enumerate([.90,1.,1.06,1.12]):
 PAL[f'clay tile {i}']={'color':[.20*k,.215*k,.20*k],'roughness':.91}


def world_uv(part):
 old=np.asarray(part['vertices']);vertices=[];uv=[];faces=[]
 for tri in part['triangles']:
  xyz=old[list(tri)];n=np.cross(xyz[1]-xyz[0],xyz[2]-xyz[0]);n/=np.linalg.norm(n)
  u=np.cross([0.,0.,1.],n) if abs(n[2])<.999999 else np.array([1.,0.,0.])-n*n[0]
  u/=np.linalg.norm(u);v=-np.cross(n,u);start=len(vertices)
  vertices.extend(xyz.tolist());uv.extend([[float(np.dot(q,u)/.4),float(np.dot(q,v)/.4)] for q in xyz]);faces.append((start,start+1,start+2))
 part['vertices']=vertices;part['texcoords']=uv;part['triangles']=faces


class Building:
 def __init__(self,lod=False):
  self.b=Builder(PAL);self.lod=lod;self.roof=Roof();self.features=[]
  self.outline=Polygon([(-11.7,-12),(11.7,-12),(11.7,12),(1.4,12),(1.4,26),(-11.7,26)])
  self.core=Polygon([(-11.7,-9.3),(11.7,-9.3),(11.7,12),(1.4,12),(1.4,26),(-11.7,26)])
  self.centers=[-9.36,-4.68,0,4.68,9.36]

 def bx(self,c,size,mat,label):self.b.box(c,size,mat,label=label)

 def shutter(self,f,shape,label):
  x0,z0,x1,z1=shape.bounds;inner=shape.buffer(-.075,join_style=2)
  f.prism(shape.buffer(.105,join_style=2).difference(shape),.008,.13,'pale trim',label+' surround')
  f.prism(shape.difference(inner),-.16,-.025,'shutter edge',label+' outer frame')
  f.prism(inner,-.265,-.245,'glass',label+' recessed backing glass')
  middle=(x0+x1)/2
  for side,(a,b) in enumerate([(x0+.075,middle-.02),(middle+.02,x1-.075)]):
   leaf=inner.intersection(box(a,z0,b,z1));panel=leaf.buffer(-.055,join_style=2)
   f.prism(leaf.difference(panel),-.12,-.035,'shutter edge',label+f' leaf {side} frame')
   f.prism(panel,-.185,-.165,'shutter wood',label+f' leaf {side} inset panel')
   if not self.lod:
    for z in np.arange(z0+.10,z1,.078):
     band=panel.intersection(box(x0,z,x1,z+.043))
     self.b.prism(band,-.105,-.083,lambda u,h,d,z=z:f.point(u,h,d+(h-z)*.46),'shutter wood',label+' inclined louvre')
   for z in [z0+(z1-z0)*.33,z0+(z1-z0)*.66]:
    f.prism(leaf.intersection(box(x0,z-.035,x1,z+.035)),-.075,-.025,'shutter edge',label+' horizontal rail')
  f.box(middle,z0-.055,x1-x0+.20,.11,.34,.025,'pale trim',label+' sill')
  # Segmental hood follows the same shallow arch; no painted opening.
  hood=shape.buffer(.21,join_style=2).difference(shape.buffer(.12,join_style=2))
  hood=hood.intersection(box(x0-.3,z1-.34,x1+.3,z1+.3))
  f.prism(hood,.10,.20,'pale trim',label+' segmental hood')
  self.features.append({'id':label,'kind':'closed-shutter-opening','outline':list(shape.exterior.coords),
   'origin':f.center.tolist(),'u':f.t.tolist(),'normal':f.n.tolist(),'dimensions_estimated':True})

 def wall(self,f,holes=(),observed=False):
  profile=self.roof.profile(f.a[:2],f.b[:2])
  outline=Polygon([(-f.length/2,.45),(f.length/2,.45)]+
   [(-f.length/2+f.length*t,z) for t,z in reversed(profile)]).simplify(1e-7,preserve_topology=True)
  f.wall(.45,17,holes,.30,'pebbledash',outline)

 def walls(self):
  self.b.plan_prism(self.outline,0,.45,'stone','estimated mapped south-building plinth')
  front=Facade(self.b,(-11.7,-9.3),(11.7,-9.3),'front-inner-wall')
  apertures=[]
  for level,base in enumerate([.45,4.2,7.95]):
   for bay,u in enumerate(self.centers):
    door=level>0 or bay==4
    shape=opening(u,base+(.08 if door else .65),1.80 if door else 1.66,2.95 if door else 2.36,arch=.21,segments=20 if not self.lod else 10)
    apertures.append(shape);self.shutter(front,shape,f'front-level-{level}-bay-{bay}')
  self.wall(front,apertures,True)
  points=list(self.core.exterior.coords)[:-1]
  # Join wall ends at outer corners while keeping their inward caps apart.
  for i,(a,b) in enumerate(zip(points,points[1:]+points[:1])):
   if i==0:continue
   a=np.array(a,float);b=np.array(b,float);t=(b-a)/np.linalg.norm(b-a)
   if i in [1,3,5]:a=a+t*.30;b=b-t*.30
   f=Facade(self.b,a,b,'side-or-estimated-rear-'+str(i));holes=[]
   if i==5:
    # The near end of the south side is partially visible in the references.
    # Exact spacing and occluded parts remain estimated; other rear walls plain.
    for level,base in enumerate([.45,4.2,7.95]):
     for j,y in enumerate([-6.7,-2.2]):
      u=float(np.dot(np.array([-11.7,y])-f.center[:2],f.t[:2]))
      shape=opening(u,base+.65,1.66,2.36,arch=.21,segments=16)
      holes.append(shape);self.shutter(f,shape,f'south-side-{level}-{j}-estimated-spacing')
   self.wall(f,holes)
  for z in [4.08,7.83,11.58]:
   front.box(0,z,23.4,.18,.22,.04,'pale trim','front storey cornice')

 def railing(self,a,b,z,label,white=False,start_post=True):
  a=np.array(a,float);b=np.array(b,float);t=(b-a)/np.linalg.norm(b-a);length=np.linalg.norm(b-a)
  def pt(u,h):return [*(a+t*u),z+h]
  material='pale trim' if white else 'metal';height=.64 if white else 1.0
  r=.035 if white else .022;sides=4 if white else (6 if self.lod else 8)
  self.b.tube([pt(0,.09),pt(length,.09)],r,material,sides,label+' lower rail')
  self.b.tube([pt(0,height),pt(length,height)],r,material,sides,label+' upper rail')
  n=max(1,round(length/(.85 if white else 1.10)))
  for j in range(n):
   lo=j*length/n;hi=(j+1)*length/n;mid=(lo+hi)/2
   if j or start_post:self.b.tube([pt(lo,.09),pt(lo,height)],r*.65,material,sides,label+' upright')
   self.b.tube([pt(lo,.09),pt(hi,height)],r*.65,material,sides,label+' diagonal A')
   self.b.tube([pt(lo,height),pt(hi,.09)],r*.65,material,sides,label+' diagonal B')
   if not white and not self.lod:
    self.b.tube([pt(mid+.115*math.cos(t),.54+.14*math.sin(t)) for t in np.linspace(0,math.tau,17)],.014,material,6,label+' oval')
  self.b.tube([pt(length,.09),pt(length,height)],r*.65,material,sides,label+' end upright')

 def veranda(self):
  for floor in [4.2,7.95,11.85]:
   # Leave a small real gap to the inner wall face to avoid overlapping caps.
   self.bx((0,-10.8,floor-.105),(23.4,2.9,.21),'pale trim' if floor==11.85 else 'shutter edge','veranda slab')
   self.bx((0,-12.23,floor-.12),(23.6,.16,.28),'pale trim' if floor==11.85 else 'shutter edge','veranda fascia')
   for x in np.arange(-11.4,11.5,.42 if not self.lod else 1.2):
    self.bx((float(x),-10.75,floor-.30),(.075,2.75,.18),'pale trim' if floor==11.85 else 'wood beam','visible veranda joist')
  for x in np.linspace(-11.7,11.7,6):
   self.bx((x,-12.05,2.325),(.66,.66,3.75),'pebbledash','lower square column pier')
   self.bx((x,-12.05,8.025),(.46,.46,7.65),'pebbledash','upper square column shaft')
   self.bx((x,-12.05,4.2),(.69,.69,.16),'pale trim','column transition')
   self.bx((x,-12.05,11.72),(.62,.62,.25),'pale trim','column capital')
   self.bx((x,-12.05,12.22),(.33,.33,.64),'pale trim','roof parapet post')
   self.bx((x,-12.05,12.57),(.46,.46,.10),'pale trim','roof parapet cap')
  for level in [4.2,7.95]:
   for a,b in zip(np.linspace(-11.7,11.7,6)[:-1],np.linspace(-11.7,11.7,6)[1:]):
    self.railing((a+.25,-12.10),(b-.25,-12.10),level,'front balcony')
   for x in [-11.7,11.7]:self.railing((x,-12.05),(x,-9.40),level,'balcony open side return')
  self.railing((-11.7,-12.05),(11.7,-12.05),11.90,'white roof X parapet',True)
  for x in [-11.7,11.7]:self.railing((x,-12.05),(x,-9.35),11.90,'white parapet return',True,False)
  for x in [-11.4,-2.2,7.1,11.4]:
   self.b.tube([(x,-9.6,12.65),(x,-12.35,11.7),(x,-12.35,.45)],.052,'pale trim',8,'estimated rainwater pipe routing')
  if not self.lod:
   f=Facade(self.b,(-11.7,-9.3),(11.7,-9.3),'front lamps')
   for level in [.45,4.2,7.95]:
    for u in [-11.1,-7.02,-2.34,2.34,7.02,11.1]:
     center=f.point(u,level+2.15,.22)
     self.b.lathe(center[:2],[(center[2]+h,r) for h,r in [(-.15,.03),(-.10,.09),(.12,.08),(.20,0)]],'metal',6,'estimated lantern body')
     self.b.tube([f.point(u,level+2.23,.02),center+[0,0,.08]],.022,'metal',6,'lamp bracket')

 def dormers(self):
  for cx in [-4.8,4.8]:
   y=-7.25;v=next(v for v in self.roof.volumes if v['id']==f'front-dormer-{cx}')
   base=self.roof.volume_height(self.roof.volumes[0],cx,y)
   shape=Polygon([(-1.15,base),(1.15,base),(1.15,14.26),(0,14.95),(-1.15,14.26)])
   f=Facade(self.b,(cx-1.15,y),(cx+1.15,y),'front roof dormer')
   aperture=box(-.78,base+.13,.78,14.22)
   f.prism(shape.difference(aperture),-.15,0,'shutter wood','dormer front with true opening')
   f.window(aperture,columns=3,rows=2,frame='shutter edge',trim=False,glass='glass',label='dormer recessed window')
   self.b.tube([(cx-1.24,y-.06,14.27),(cx,y-.06,15.03),(cx+1.24,y-.06,14.27)],.10,'red wood',6,'dormer red gable fascia')
   # Side cheeks close only the exposed area above the main roof.
   for x,reverse in [(cx-1.15,True),(cx+1.15,False)]:
    ya=y;yb=-2.4;ff=Facade(self.b,(x,yb) if reverse else (x,ya),(x,ya) if reverse else (x,yb),'dormer cheek')
    values=[]
    for u in np.linspace(-ff.length/2,ff.length/2,30):
     q=ff.point(u,0);low=self.roof.volume_height(self.roof.volumes[0],q[0],q[1]);top=self.roof.volume_height(v,q[0],q[1])
     if top>low:values.append((u,low,top))
    if len(values)>1:
     poly=Polygon([(u,lo) for u,lo,hi in values]+[(u,hi) for u,lo,hi in reversed(values)])
     ff.prism(poly,-.10,0,'shutter wood','exposed cheek')
   self.features.append({'id':f'dormer-{cx}','kind':'roof-window','x':cx,'y':y,'bottom':base+.13,'top':14.22,'estimated':True})

 def finish(self):
  self.walls();self.veranda();self.dormers();self.roof_report=self.roof.add(self.b,self.lod)
  for part in self.b.parts:
   v=np.asarray(part['vertices']);t=np.asarray(part['triangles'])
   if np.einsum('ij,ij->i',v[t[:,0]],np.cross(v[t[:,1]],v[t[:,2]])).sum()<0:
    part['triangles']=[(a,c,b) for a,b,c in t]
   if part['material']=='pebbledash':world_uv(part)
  x=G['architecture_X_EN'];y=G['architecture_Y_EN'];rotation=np.array([[x[0],y[0],0],[x[1],y[1],0],[0,0,1]])
  for part in self.b.parts:part['vertices']=(np.asarray(part['vertices'])@rotation.T).tolist()
  return self


if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True);parser.add_argument('--lod',action='store_true');a=parser.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 building=Building(a.lod).finish();role='lod' if a.lod else 'raw'
 result=building.b.save(a.out/f'{ID}-{role}.glb',metadata={'id':ID,'name':'徐家汇藏书楼南楼（原神父楼）',
  'scope':'South building exterior candidate; mapped western return and hidden roof/elevations estimated; north library excluded',
  'anchor':G['anchor'],'source_owner':G['source_owner'],'source_local_id':1595,
  'coordinates':'Anchor-local East/Up/-North; rotation baked','source_height_29_5m_not_used':True,
  'photos_embedded':False,'copyright':'Original geometry and procedural material: agent, MIT; references separately credited CC BY-SA 3.0/4.0; source context ODbL'})
 (a.out/f'{role}-features.json').write_text(json.dumps(building.features,indent=2)+'\n')
 (a.out/f'{role}-roof.json').write_text(json.dumps(building.roof_report,indent=2)+'\n')
 print(json.dumps({k:v for k,v in result.items() if k!='part_summary'}))
