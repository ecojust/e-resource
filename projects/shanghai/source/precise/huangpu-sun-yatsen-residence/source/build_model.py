"""Original main-house exterior. Survey accuracy, hidden openings and interior are not claimed."""
import argparse,json,math,sys
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(HERE/'common'))
from photo_architecture import Builder,Facade,opening
from roof_geometry import Roof
ID='huangpu-sun-yatsen-residence'
D=json.loads((ROOT/'design-input.json').read_text());G=json.loads((ROOT/'geometry-input.json').read_text())
PAL={'pebbledash':{'color':[1,1,1],'roughness':1,'metallic':1,'texture':str(ROOT/'textures/sun-yatsen-original-pebbledash-basecolor.png'),'normal_texture':str(ROOT/'textures/sun-yatsen-original-pebbledash-normal.png'),'orm_texture':str(ROOT/'textures/sun-yatsen-original-pebbledash-orm.png'),'normal_scale':.35,'extras':{'license':'MIT','procedural_not_photo':True,'repeat_metres':.4,'occlusion_strength':.35}},
 'red wood':{'color':[.29,.065,.043],'roughness':.76},'red trim':{'color':[.38,.10,.064],'roughness':.75},
 'glass':{'color':[.12,.19,.20],'roughness':.32,'metallic':.10},'interior shadow':{'color':[.035,.031,.027],'roughness':1},
 'stone':{'color':[.48,.48,.45],'roughness':.92},'pale trim':{'color':[.73,.72,.66],'roughness':.86},
 'roof underlay':{'color':[.27,.105,.062],'roughness':.92},'brick':{'color':[.34,.12,.075],'roughness':.88},
 'brick joint':{'color':[.38,.32,.26],'roughness':.95},'metal':{'color':[.17,.15,.12],'roughness':.60,'metallic':.35}}
for i,k in enumerate([.92,1.,1.07,1.13]):PAL[f'clay tile {i}']={'color':[.32*k,.13*k,.075*k],'roughness':.9}
class House:
 def __init__(self,lod=False):self.b=Builder(PAL);self.lod=lod;self.roof=Roof();self.features=[];self.w=D['estimated']['width_m'];self.depth=D['estimated']['depth_m']
 def facade(self,edge,label):
  w=self.w/2;d=self.depth/2;points=[(-w,-d),(w,-d),(w,d),(-w,d)]
  if edge==1:return Facade(self.b,(w,-d+.30),(w,d-.30),label)
  if edge==3:return Facade(self.b,(-w,d-.30),(-w,-d+.30),label)
  return Facade(self.b,points[edge],points[(edge+1)%4],label)
 def bx(self,c,s,mat,label):self.b.box(c,s,mat,label=label)
 def window(self,f,shape,label,cols=3,rows=2):
  x0,z0,x1,z1=shape.bounds;inner=shape.buffer(-.09,join_style=2);bars=[]
  for i in range(1,cols):
   x=x0+(x1-x0)*i/cols;bars.append(box(x-.027,z0,x+.027,z1))
  for i in range(1,rows):
   z=z0+(z1-z0)*i/rows;bars.append(box(x0,z-.033,x1,z+.033))
  panes=inner.difference(unary_union(bars));frame=shape.buffer(-.012,join_style=2).difference(panes)
  f.prism(frame,-.17,-.035,'red wood',label+' frame and mullions')
  f.prism(inner,-.24,-.22,'glass',label+' inset glazing')
  f.prism(shape.buffer(-.025).difference(shape.buffer(-.05)),-.034,-.012,'red trim',label+' inner moulding')
  f.box((x0+x1)/2,z0-.065,x1-x0+.20,.13,.37,.035,'red trim',label+' sill')
  self.features.append({'id':label,'kind':'window','origin':f.center.tolist(),'u':f.t.tolist(),'normal':f.n.tolist(),'outline':list(shape.exterior.coords),'wall_depth_m':[-.30,0],'glass_depth_m':[-.24,-.22],'grid':[cols,rows],'dimensions_estimated':True})
 def walls(self):
  b=self.b;w=self.w/2;d=self.depth/2;floor=.45
  self.bx((0,0,.225),(self.w,self.depth,.45),'stone','main-house plinth; height estimated')
  f=self.facade(0,'garden-front');holes=[];portals=[]
  for i,u in enumerate([-6,-2,2,6]):
   low=.95 if i<3 else floor;h=4.25-low;shape=opening(u,low,3.15,h,arch=1.575,segments=40 if not self.lod else 20);holes.append(shape);portals.append(shape)
   self.features.append({'id':f'porch-arch-{i}','kind':'open-porch','center':[u,-d,(low+4.25)/2],'bottom':low,'top':4.25,'width':3.15,'estimated':True})
  windows=[(opening(2,5.1,2.7,2.7,arch=1.35,segments=32),'upper-east-1',3,2),(opening(6,5.1,2.7,2.7,arch=1.35,segments=32),'upper-east-2',3,2),(opening(-4.0,5.1,7.15,2.3),'upper-west-gallery',10,3)]
  vent=opening(4.8,8.65,.9,1.05,arch=.45,segments=20);holes.extend(p for p,_,_,_ in windows);holes.append(vent)
  a=(-w,-d);end=(w,-d);profile=self.roof.profile(a,end)
  outline=Polygon([(-w,floor),(w,floor)]+[(-w+self.w*t,z) for t,z in reversed(profile)]).simplify(1e-7,preserve_topology=True)
  f.wall(floor,12,holes,.30,'pebbledash',outline)
  for shape,label,cols,rows in windows:self.window(f,shape,label,cols,rows)
  # Vent opening has separate inset backing and clipped horizontal louvres.
  self.louvres(f,vent,'front-gable-vent')
  # Porches remain genuinely recessed; no photo or wall fills their outer arches.
  inner=Facade(b,(-w+.30,-d+2.30),(w-.30,-d+2.30),'porch-inner')
  doors=[opening(u,floor,2.45,3.05) for u in [-6,-2,2,6]]
  inner.wall(floor,4.55,doors,.22,'pebbledash')
  for i,p in enumerate(doors):self.window(inner,p,f'inset-door-{i}',4,3)
  self.bx((0,-d+1.30,4.48),(self.w-.60,2.0,.14),'pale trim','porch ceiling / upper gallery floor')
  for i,p in enumerate(portals):
   ring=p.buffer(.065).difference(p);f.prism(ring,.012,.055,'pebbledash',f'arch edge {i}')
   if i<3:f.box([-6,-2,2][i],.89,3.35,.12,.46,.08,'red trim','porch sill')
  for edge in [1,2,3]:
   ff=self.facade(edge,'unobserved-'+str(edge));a=ff.a[:2];bb=ff.b[:2]
   profile=self.roof.profile(a,bb);outline=Polygon([(-ff.length/2,floor),(ff.length/2,floor)]+[(-ff.length/2+ff.length*t,z) for t,z in reversed(profile)]).simplify(1e-7,preserve_topology=True)
   ff.wall(floor,12,[],.30,'pebbledash',outline)
  # No garden mesh or reconstructed public pavement is implied by these steps.
  for i in range(6):
   length=(6-i)*.28;h=(i+1)*.075;self.bx((6,-d-length/2,h/2),(3.6,length,h),'stone','estimated entrance tread')
  # Observed front-right downpipe, discretized bends with real tube geometry.
  b.tube([(w+.13,-d+.10,7.9),(w+.13,-d-.12,7.3),(w+.13,-d-.12,.50),(w+.25,-d-.25,.35)],.052,'red wood',10,'front east rainwater pipe')
  self.dormer()
 def louvres(self,f,shape,label):
  f.prism(shape,-.22,-.20,'interior shadow',label+' backing')
  f.prism(shape.buffer(.045).difference(shape),.01,.065,'red trim',label+' surround')
  x0,z0,x1,z1=shape.bounds
  for z in np.arange(z0+.04,z1,.085):
   band=shape.intersection(box(x0,z,x1,z+.040));f.prism(band,-.03,.025,'red wood',label+' slat')
 def dormer(self):
  y=-5.7;vol=self.roof.volumes[2];xs=np.linspace(-3,1.6,101)
  top=[(x,self.roof.volume_height(vol,x,y)-.08) for x in xs];bottom=[(x,self.roof.volume_height(self.roof.volumes[0],x,y)-.08) for x in xs]
  triangle=Polygon([(-3,9.7),(1.6,9.7)]+list(reversed(top)))
  hidden=Polygon([(-3,9),(1.6,9)]+list(reversed(bottom)))
  visible=triangle.difference(hidden).simplify(1e-6,preserve_topology=True)
  f=Facade(self.b,(-3,y),(1.6,y),'front-dormer')
  # Facade coordinates are centred at x=-.7; convert world-x outline to local u.
  from shapely.affinity import translate
  visible=translate(visible,xoff=.7)
  vent=visible.buffer(-.12,join_style=2)
  f.prism(visible.difference(vent),-.12,0,'pebbledash','dormer face')
  self.louvres(f,vent,'dormer louvres')
 def chimneys(self):
  for i,(x,y,top) in enumerate([(-6.4,5.4,12.9),(-6.8,-1.7,12.1),(6.4,1.4,12.0)]):
   base=self.roof.height(x,y)-.15;self.bx((x,y,(base+top)/2),(.65,.72,top-base),'brick','estimated chimney shaft')
   self.bx((x,y,top),(.82,.88,.15),'pale trim','chimney cap')
   if not self.lod:
    for z in np.arange(base+.08,top-.08,.11):
     for sign in [-1,1]:
      self.bx((x,y+sign*.362,z),(.65,.008,.008),'brick joint','chimney bed joint')
      self.bx((x+sign*.327,y,z),(.008,.72,.008),'brick joint','chimney side bed joint')
 def finish(self):
  self.walls();self.chimneys();self.roof_report=self.roof.add(self.b,self.lod)
  # Fix outward orientation of closed components before texture coordinates.
  for p in self.b.parts:
   v=np.asarray(p['vertices']);t=np.asarray(p['triangles']);vol=np.einsum('ij,ij->i',v[t[:,0]],np.cross(v[t[:,1]],v[t[:,2]])).sum()/6
   if vol<0:p['triangles']=[(a,c,b) for a,b,c in t]
  for p in self.b.parts:
   if p['material']=='pebbledash':world_uv(p)
  x=G['architecture_X_EN'];y=G['architecture_Y_EN'];r=np.array([[x[0],y[0],0],[x[1],y[1],0],[0,0,1]])
  for p in self.b.parts:p['vertices']=(np.asarray(p['vertices'])@r.T).tolist()
  return self

def world_uv(p):
 old=np.asarray(p['vertices']);verts=[];uv=[];faces=[]
 for tri in p['triangles']:
  xyz=old[list(tri)];n=np.cross(xyz[1]-xyz[0],xyz[2]-xyz[0]);n/=np.linalg.norm(n)
  u=np.cross([0.,0.,1.],n) if abs(n[2])<.999999 else np.array([1.,0.,0.])-n*n[0];u/=np.linalg.norm(u);v=-np.cross(n,u)
  k=len(verts);verts.extend(xyz.tolist());uv.extend([[float(np.dot(q,u)/.4),float(np.dot(q,v)/.4)] for q in xyz]);faces.append((k,k+1,k+2))
 p['vertices']=verts;p['texcoords']=uv;p['triangles']=faces
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--lod',action='store_true');args=p.parse_args();args.out.mkdir(parents=True,exist_ok=True)
 h=House(args.lod).finish();role='lod' if args.lod else 'raw'
 result=h.b.save(args.out/f'{ID}-{role}.glb',metadata={'id':ID,'name':'上海孙中山故居主楼','scope':'Photo-informed main-house exterior; hidden faces and dimensions estimated; no adjacent relics museum or interior','anchor':G['anchor'],'source_owner':'building:9bbed57b-ae4b-4abc-be77-0b5444bf0a9a','source_local_id':3433,'coordinates':'Anchor-local East/Up/-North; rotation baked','source_height_20_45m_not_used':True,'photos_embedded':False,'copyright':'Geometry and procedural materials MIT; references separately credited CC BY-SA 3.0/4.0; source context ODbL'})
 (args.out/f'{role}-features.json').write_text(json.dumps(h.features,indent=2)+'\n');(args.out/f'{role}-roof.json').write_text(json.dumps(h.roof_report,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='part_summary'}))
