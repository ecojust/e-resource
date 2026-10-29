"""Lu Xun residence: observed front component, not a speculative complete house.

All metric dimensions are estimates. Local +X right, +Y behind the facade, +Z up.
No map anchor or city replacement. Photographs are references, never textures.
"""
import argparse
import json
import math
import sys
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

HERE=Path(__file__).resolve().parent; ROOT=HERE.parent
sys.path.insert(0,str(HERE/'common'))
from photo_architecture import Builder, Facade, opening
ID='hongkou-luxun-residence-facade'
PAL={
 'stone':{'color':[1,1,1],'roughness':1,'metallic':1,'texture':str(ROOT/'textures/luxun-original-stone-basecolor.png'),'normal_texture':str(ROOT/'textures/luxun-original-stone-normal.png'),'orm_texture':str(ROOT/'textures/luxun-original-stone-orm.png'),'normal_scale':.35,'extras':{'license':'MIT','procedural_not_photo':True,'repeat_metres':.4,'occlusion_strength':.35}},
 'mortar':{'color':[.57,.54,.48],'roughness':.96},
 'wood':{'color':[.26,.055,.052],'roughness':.73},
 'glass':{'color':[.20,.28,.29],'roughness':.27,'metallic':.12},
 'metal':{'color':[.045,.055,.049],'roughness':.53,'metallic':.45},
 'soffit':{'color':[.63,.62,.56],'roughness':.90},
 'gutter':{'color':[.065,.14,.105],'roughness':.65,'metallic':.25},
 'plaque':{'color':[.38,.28,.12],'roughness':.6},
 'enamel':{'color':[.78,.78,.69],'roughness':.35},
}
for i,c in enumerate([[.44,.20,.115],[.39,.15,.09],[.48,.23,.14],[.43,.17,.10],[.36,.135,.085],[.46,.185,.11]]):
 PAL[f'brick{i}']={'color':c,'roughness':.90}

class Model:
 def __init__(self,lod=False):
  self.b=Builder(PAL);self.lod=lod;self.f=Facade(self.b,(-2.75,0),(2.75,0),'front');self.features=[]
 def bx(self,c,s,m,label):self.b.box(c,s,m,label=label)
 def tube(self,p,r=.018,label='metal rail',m='metal'):
  self.b.tube(p,r,m,6 if self.lod else 10,label)
 def bricks(self,f,shape,depth,label):
  # Each brick is a shallow separate prism; clipped against the actual openings.
  # LOD retains the same openings and proportions but drops individual brick relief.
  if self.lod:
   f.prism(shape,depth-.015,depth+.006,'brick0',label+' continuous LOD brick');return
  rng=np.random.default_rng(13209);x0,z0,x1,z1=shape.bounds
  pitch=.255;course=.081
  for row,z in enumerate(np.arange(math.floor(z0/course)*course,z1,course)):
   start=math.floor(x0/pitch)*pitch-(pitch/2 if row%2 else 0)
   for x in np.arange(start,x1,pitch):
    tile=shape.intersection(box(x+.006,z+.005,x+pitch-.006,z+course-.005))
    if not tile.is_empty and tile.area>1e-7:
     f.prism(tile,depth-.01,depth+float(rng.uniform(.009,.014)),f'brick{rng.integers(6)}',label+' running bond')
 def surround(self,p,width=.13):
  self.f.prism(p.buffer(width,join_style=2).difference(p),.015,.12,'stone','window reveal surround')
 def casement(self,f,x,z,w,h,label,angle=0,hinge='left',chevron=True):
  start=len(self.b.parts);shape=box(x-w/2,z,x+w/2,z+h)
  bar=.035;inner=shape.buffer(-bar,join_style=2);split=z+h*.76
  pane=inner.difference(box(x-w/2,split-.022,x+w/2,split+.022))
  f.prism(shape.difference(pane),-.13,-.055,'wood',label+' frame')
  f.prism(pane,-.17,-.155,'glass',label+' glazing')
  if chevron:
   for sign in [-1,1]:
    p=[f.point(x+sign*(w/2-.04),z+.28,-.04),f.point(x,z+.06,-.04)]
    self.tube(p,.019,label+' V brace','wood')
  if angle:
   # Open sash rotates as a rigid frame and pane around its jamb, never wall.
   pivot=f.point(x-w/2 if hinge=='left' else x+w/2,z,-.09)
   a=math.radians(angle);r=np.array([[math.cos(a),-math.sin(a),0],[math.sin(a),math.cos(a),0],[0,0,1]])
   for part in self.b.parts[start:]:part['vertices']=((np.asarray(part['vertices'])-pivot)@r.T+pivot).tolist()
 def windows(self):
  f=self.f
  # Six casements; the two right leaves are open in the 2011 photo.
  x0=-1.95;bottom=4.55;w=3.9;top=6.70;transom=6.15
  lower=box(x0,bottom,x0+w,top);self.surround(lower)
  f.prism(lower.difference(lower.buffer(-.065,join_style=2)),-.19,-.025,'wood','lower window outer frame')
  f.box(0,transom,w,.06,.13,-.09,'wood','lower transom crossbar')
  for i in range(6):
   x=x0+(i+.5)*w/6
   self.casement(f,x,bottom+.06,w/6-.026,transom-bottom-.08,'lower sash '+str(i),angle=-72 if i==4 else (72 if i==5 else 0),hinge='left' if i==4 else 'right')
   self.casement(f,x,transom+.035,w/6-.026,top-transom-.075,'transom '+str(i),chevron=False)
   f.box(x,transom+(top-transom)/2,.024,top-transom-.07,.08,-.07,'wood','transom small vertical divider')
  f.box(0,bottom-.085,4.18,.17,.43,.04,'stone','projecting lower sill')
  # Upper central balcony doors with two separate narrow windows.
  for x,w,label in [(0,1.60,'balcony door'),(-1.35,.68,'upper left'),(1.35,.68,'upper right')]:
   p=box(x-w/2,7.65,x+w/2,9.76);self.surround(p,.105)
   f.prism(p.difference(p.buffer(-.055,join_style=2)),-.19,-.035,'wood',label+' outer frame')
   f.box(x,9.22,w,.055,.13,-.09,'wood',label+' transom bar')
   count=2 if x==0 else 1
   for i in range(count):
    xx=x-w/2+(i+.5)*w/count
    self.casement(f,xx,7.71,w/count-.04,1.48,label+str(i),angle=-56 if x<0 else 0)
    self.casement(f,xx,9.26,w/count-.04,.44,label+' upperlight'+str(i),chevron=False)
   f.box(x,7.59,w+.20,.12,.40,.035,'stone',label+' sill')
  # Ground-left window is partly occluded in the references: simple closed sash.
  p=box(-2.05,.55,-1.05,2.45);self.surround(p,.09)
  for i in range(2):self.casement(f,-1.8+i*.5,.59,.46,1.82,'partly observed ground window '+str(i))
 def facade(self):
  f=self.f
  arch=opening(.95,.15,2.35,2.93,arch=.67,segments=20 if self.lod else 48)
  holes=[arch,box(-1.95,4.55,1.95,6.70),box(-.80,7.65,.80,9.76),box(-1.69,7.65,-1.01,9.76),box(1.01,7.65,1.69,9.76),box(-2.05,.55,-1.05,2.45)]
  surface=box(-2.75,.12,2.75,10.10).difference(unary_union(holes))
  f.prism(surface,-.30,0,'mortar','continuous front wall with six real openings')
  self.bricks(f,surface,0,'front brick')
  self.surround(arch,.14)
  # A recessed entrance leaf, including fanlight under the segmental arch.
  inner=Facade(self.b,(-2.75,.52),(2.75,.52),'entry inset')
  inner.prism(arch,-.10,-.06,'wood','entry recessed door backing')
  for x in [.37,1.53]:
   inner.prism(box(x-.49,.38,x+.49,2.25),-.035,.015,'wood','entry panel raised border')
   inner.prism(box(x-.42,.46,x+.42,1.24),.015,.025,'wood','entry lower panel')
   inner.prism(box(x-.42,1.40,x+.42,2.17),.016,.026,'glass','entry upper panel glass')
  fan=arch.intersection(box(-1,2.45,3,4));inner.prism(fan,-.04,-.025,'glass','entry fanlight')
  for x in np.linspace(-.17,2.07,7):
   strip=fan.intersection(box(x-.012,2.45,x+.012,3.2));inner.prism(strip,-.02,.015,'wood','entry fanlight mullion')
  inner.box(.95,2.44,2.35,.065,.12,0,'wood','entry fanlight bar')
  # Passage cheeks bridge the wall to the recessed door without closing the arch.
  ring=arch.buffer(.04).difference(arch);f.prism(ring,-.52,-.301,'stone','entry deep reveal')
  self.windows()
  panel=box(-2.17,3.22,2.17,4.24)
  f.prism(panel,.02,.07,'stone','large grey spandrel panel')
  f.prism(panel.buffer(.045,join_style=2).difference(panel),.035,.11,'stone','spandrel raised rim')
  # Stepped Art Deco relief above both brick piers.
  for x in [-2.36,2.36]:
   f.prism(box(x-.28,9.60,x+.28,10.05),.018,.05,'stone','upper pier panel')
   stepped=Polygon([(x-.25,10.03),(x+.25,10.03),(x+.25,9.84),(x+.14,9.84),(x+.14,9.73),(x+.06,9.73),(x+.06,9.66),(x-.06,9.66),(x-.06,9.73),(x-.14,9.73),(x-.14,9.84),(x-.25,9.84)])
   f.prism(stepped,.05,.10,'stone','stepped pier ornament')
  self.bx((0,-.22,10.13),(5.7,.86,.12),'soffit','observed eaves soffit; roof omitted')
  self.bx((0,-.66,10.21),(5.7,.10,.12),'gutter','front green gutter')
  self.bx((0,-.62,10.12),(5.7,.06,.05),'wood','eaves red fascia')
  self.features.append({'id':'front-wall','wall_depth':[-.30,0],'openings':[list(p.exterior.coords) for p in holes],'scope':'front component only'})
 def balcony(self):
  self.bx((0,-.58,7.48),(2.40,1.20,.16),'stone','balcony projecting slab')
  self.bx((0,-.58,7.39),(2.30,1.08,.06),'soffit','balcony soffit')
  for x in [-.95,.95]:
   # Side-elevation bracket, extrusion along X.
   p=Polygon([(-.02,7.40),(-1.10,7.40),(-.94,7.17),(-.65,7.12),(-.35,6.98),(-.02,6.98)])
   self.b.prism(p,x-.08,x+.08,lambda y,z,d:(d,y,z),'stone','balcony corbel')
  # Rounded front corners on the horizontal rail loops, as seen in the photo.
  for z in np.linspace(7.63,8.55,6):
   pts=[(-1.07,-.04,z),(-1.07,-.91,z)]
   pts += [(-.94+.13*math.cos(a),-.91+.13*math.sin(a),z) for a in np.linspace(math.pi,1.5*math.pi,7)[1:]]
   pts += [(.94,-1.04,z)]
   pts += [(.94+.13*math.cos(a),-.91+.13*math.sin(a),z) for a in np.linspace(-math.pi/2,0,7)[1:]]
   pts += [(1.07,-.04,z)]
   self.tube(pts,.021,'rounded balcony horizontal rail')
  for x in np.linspace(-.91,.91,13):self.tube([(x,-1.055,7.57),(x,-1.055,8.57)],.015,'balcony front vertical picket')
 def fence(self):
  f=Facade(self.b,(-2.75,-2.5),(2.75,-2.5),'front fence')
  # Post faces really contain three recessed flutes, including rounded ends.
  for x in [-.25,2.45]:
   shape=Polygon([(x-.25,0),(x+.25,0),(x+.25,2.97),(x,3.22),(x-.25,2.97)])
   grooves=[opening(x+dx,.22,.047,2.35,arch=.0235,segments=12) for dx in [-.12,0,.12]]
   f.prism(shape.difference(unary_union(grooves)),-.22,.22,'stone','fluted gatepost')
   for groove in grooves:f.prism(groove,-.22,.17,'stone','gatepost recessed flute bed')
  # Left fence has brick base and a metal chevron grille between stone rails.
  p=box(-2.75,.04,-.50,1.03);f.prism(p,-.12,.12,'mortar','fence low wall');self.bricks(f,p,.12,'fence brick')
  for z in [1.10,2.30]:f.box(-1.625,z,2.25,.18,.33,0,'stone','fence horizontal stone rail')
  for x in np.linspace(-2.65,-.60,9):self.tube([f.point(x,1.20,.02),f.point(x,2.20,.02)],.014,'fence vertical')
  for x in [-2.22,-1.13]:
   self.tube([f.point(x-.45,2.19,.04),f.point(x,1.40,.04),f.point(x+.45,2.19,.04)],.019,'fence V motif')
   self.tube([f.point(x-.45,1.40,.04),f.point(x,1.90,.04),f.point(x+.45,1.40,.04)],.015,'fence diamond motif')
  # Gate: open fan grille, ribbed solid lower panels and a low crossbar.
  left=.04;right=2.16;mid=(left+right)/2
  for x in [left,right]:f.box(x,1.37,.045,2.66,.06,.04,'metal','gate outer upright')
  for z in [.06,1.12,2.10,2.70]:f.box(mid,z,right-left,.045,.07,.04,'metal','gate crossbar')
  f.prism(box(left+.025,.09,right-.025,2.06),-.012,.005,'metal','gate lower panel')
  for x in np.arange(left+.08,right,.12):f.box(x,1.075,.016,1.94,.045,.025,'metal','gate vertical rib')
  for x in np.linspace(left+.05,right-.05,9):
   self.tube([f.point(mid,2.13,.05),f.point(x,2.67,.05)],.012,'gate fan grille')
  for x in [left+.04,right-.04]:
   for z in [.42,1.95]:f.box(x,z,.09,.12,.10,.08,'metal','gate hinge')
  # Blank plaques preserve physical mass without fabricated historic lettering.
  f.box(2.45,1.94,.37,.94,.035,.245,'plaque','unlettered commemorative plaque')
  f.box(-.25,2.83,.34,.19,.03,.24,'enamel','number plate')
  # No9 is an observed address. Simple original line-glyph, not copied calligraphy.
  self.tube([f.point(-.20,2.79,.263),f.point(-.20,2.88,.263),f.point(-.27,2.88,.263),f.point(-.27,2.84,.263),f.point(-.20,2.84,.263)],.009,'address numeral nine')
 def finish(self):
  self.facade();self.balcony();self.fence()
  for part in self.b.parts:
   if part['material']=='stone':world_uv(part)
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
 model=Model(a.lod).finish();role='lod' if a.lod else 'raw'
 result=model.b.save(a.out/f'{ID}-{role}.glb',metadata={'id':ID,'name':'上海鲁迅故居正立面与院门','scope':'Unregistered front facade component only; no roof, whole-house shell, hidden faces or interior','all_dimensions_estimated':True,'anchor':None,'source_owner':None,'map_replacement':False,'coordinates':'Local right/up/front in glTF; no geographic heading','photos_embedded':False,'copyright':'Original geometry and procedural materials MIT; separate reference photos CC BY-SA3.0/4.0'})
 (a.out/f'{role}-features.json').write_text(json.dumps(model.features,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='part_summary'}))
