#!/usr/bin/env python3
"""Sihang + Continental Bank warehouses: photo-informed six-storey exterior.

No photograph is read or embedded. All model coordinates and damage marks
come from explicit reviewable input, with unmeasured depths labelled estimates.
"""
from pathlib import Path
from collections import Counter
import argparse,hashlib,json,math,sys
import numpy as np
from shapely import affinity,set_precision
from shapely.geometry import Polygon,Point,box as rect,LineString
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'common'))
from photo_architecture import Builder,Facade,pieces
from sign_lettering import lettering_shapes

PALETTE={
 'weathered grey plaster':{'color':[.43,.42,.385],'roughness':.9},
 'pale grey pilaster':{'color':[.54,.525,.48],'roughness':.84},
 'recessed plaster panel':{'color':[.47,.455,.415],'roughness':.9},
 'stone reveal':{'color':[.39,.385,.35],'roughness':.9},
 'blue grey brick':{'color':[.29,.29,.26],'roughness':.94},
 'red brick border':{'color':[.39,.235,.175],'roughness':.92},
 'exposed aged brick':{'color':[.39,.315,.23],'roughness':.95},
 'mortar seam':{'color':[.205,.205,.18],'roughness':.98},
 'exposed concrete':{'color':[.48,.46,.40],'roughness':.94},
 'dark crater core':{'color':[.095,.085,.065],'roughness':.98},
 'restoration dark glass':{'color':[.045,.06,.065],'roughness':.21,'metallic':.18},
 'safety backing masonry':{'color':[.075,.07,.065],'roughness':.98},
 'charcoal steel frame':{'color':[.055,.065,.066],'roughness':.47,'metallic':.5},
 'warehouse blue grey glass':{'color':[.16,.22,.235],'roughness':.24,'metallic':.16},
 'warehouse muted glass':{'color':[.20,.25,.25],'roughness':.27,'metallic':.12},
 'translucent skylight glass':{'color':[.32,.42,.44],'roughness':.18,'metallic':.06,'alpha':.42},
 'roof light grey membrane':{'color':[.63,.64,.61],'roughness':.9},
 'roof equipment grey':{'color':[.39,.42,.42],'roughness':.65,'metallic':.25},
 'roof equipment blue':{'color':[.12,.24,.30],'roughness':.68,'metallic':.15},
 'terrace paving grey':{'color':[.45,.445,.41],'roughness':.91},
 'sign dark lettering':{'color':[.09,.13,.145],'roughness':.62,'metallic':.15},
 'faded inscription':{'color':[.18,.19,.17],'roughness':.95},
 'inscription pale patch':{'color':[.60,.59,.54],'roughness':.96},
}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')

class Warehouse:
 def __init__(self,lod=False):
  self.c=json.loads((HERE/'calibration.json').read_text());self.g=json.loads((HERE/'geometry-input.json').read_text());self.e=self.c['estimated'];self.lod=lod
  assert self.c['source_geometry_sha256']==sha(HERE/'geometry-input.json')
  self.b=Builder(PALETTE);self.features=[];self.fine=[];self.fine_index=0
  self.outline=orient(Polygon(self.c['plan_interpretation']['model_body_polygon_enu']),sign=1)
  p=self.c['plan_interpretation']['model_body_polygon_enu'];self.front=Facade(self.b,p[0],p[1],'south')
  self.west=Facade(self.b,p[-1],p[0],'west-memorial');self.east=Facade(self.b,p[1],p[2],'east-end')
  self.atriums=[orient(Polygon(x),sign=1) for x in self.c['plan_interpretation']['atriums_enu']]
  self.Z=self.e['main_floor_z_m'];L=self.front.length;w=L*self.e['south_west_fraction'];self.portals=[]
  for ident,start,end,count,width,depth in [('west',0,w,5,self.e['south_west_entry_width_m'],self.e['south_west_recess_m']),('east',w,L,4,self.e['south_east_entry_width_m'],self.e['south_east_recess_m'])]:
   center=(start+end)/2-L/2
   self.portals.append({'id':ident,'start':start-L/2,'end':end-L/2,'center':center,'width':width,'depth':depth,'bays_each_side':count})
  cuts=[Polygon([self.front.point(x,z=0,d=d)[:2] for x,d in [(q['center']-q['width']/2,.8),(q['center']+q['width']/2,.8),(q['center']+q['width']/2,-q['depth']),(q['center']-q['width']/2,-q['depth'])]]) for q in self.portals]
  self.body=self.outline.difference(unary_union(cuts));self.courts=unary_union(self.atriums)

 def mark(self,kind,label,**kw):self.features.append({'kind':kind,'label':label,**kw})
 def beam3(self,a,b,width,height,mat,label):
  a,b=np.array(a,float),np.array(b,float);t=b-a;length=float(np.linalg.norm(t));t/=length
  aux=np.array([0,0,1.]) if abs(t[2])<.9 else np.array([0,1.,0]);s=np.cross(t,aux);s/=np.linalg.norm(s);v=np.cross(s,t)
  self.b.box((a+b)/2,(length,width,height),mat,[t,s,v],label)

 def grid_window(self,f,shape,label,cols=7,rows=4,material='warehouse blue grey glass',back=-.29,front=-.07,wall_depth=.48):
  x0,z0,x1,z1=shape.bounds;inner=shape.buffer(-.07,join_style=2)
  bars=[]
  for j in range(1,cols):
   x=x0+(x1-x0)*j/cols;bars.append(rect(x-.0225,z0,x+.0225,z1))
  for j in range(1,rows):
   z=z0+(z1-z0)*j/rows;bars.append(rect(x0,z-.0225,x1,z+.0225))
  cells=inner.difference(unary_union(bars)) if bars else inner
  frame=shape.buffer(.025,join_style=2).difference(cells)
  f.prism(frame,back,front,'charcoal steel frame',label+'/frame')
  glass=[]
  for i,cell in enumerate(pieces(cells)):
   part=f.label+'/'+label+f'/pane-{i}'
   f.prism(cell.buffer(.003,join_style=2).intersection(shape),back+.026,back+.044,material,label+f'/pane-{i}');glass.append(part)
  f.prism(rect(x0-.04,z0-.06,x1+.04,z0+.01),-.43,.065,'pale grey pilaster',label+'/sill')
  self.mark('framed_glazed_opening',f.label+'/'+label,face_origin_enu=f.center.tolist(),face_tangent_enu=f.t.tolist(),outward_enu=f.n.tolist(),
   opening_face_polygon=list(shape.exterior.coords),wall_depth_m=[-wall_depth,0],frame_depth_m=[back,front],glass_depth_m=[back+.026,back+.044],
   glass_part_labels=glass,frame_part_label=f.label+'/'+label+'/frame',columns=cols,rows=rows)

 def mortar(self,f,area,face_depth,scope):
  if self.lod:return
  minx,minz,maxx,maxz=area.bounds;pitch=.27;course=.115;joint=.0028
  for k,z in enumerate(np.arange(math.floor(minz/course)*course,maxz+course,course)):
   strip=rect(minx,z-joint/2,maxx,z+joint/2).intersection(area)
   for p in pieces(strip):
    if p.area<.00001:continue
    label=f'fine-masonry-joint/{self.fine_index}';self.fine_index+=1
    self.b.prism(p,face_depth-.001,face_depth+.002,f.point,'mortar seam',label)
    self.fine.append({'label':label,'scope':scope,'face_origin_enu':f.center.tolist(),'face_tangent_enu':f.t.tolist(),'face_outward_enu':f.n.tolist(),'face_bounds_uz':list(p.bounds),'depth_m':[face_depth-.001,face_depth+.002],'thickness_m':.003,'role':'surface mortar seam; not structure, opening or glass'})
   lo=max(minz,z+joint/2);hi=min(maxz,z+course-joint/2)
   if hi<=lo:continue
   for x in np.arange(math.floor(minx/pitch)*pitch+(pitch*.5 if k%2 else 0),maxx+pitch,pitch):
    for p in pieces(rect(x-joint/2,lo,x+joint/2,hi).intersection(area)):
     if p.area<.00001:continue
     label=f'fine-masonry-joint/{self.fine_index}';self.fine_index+=1
     self.b.prism(p,face_depth-.001,face_depth+.002,f.point,'mortar seam',label)
     self.fine.append({'label':label,'scope':scope,'face_origin_enu':f.center.tolist(),'face_tangent_enu':f.t.tolist(),'face_outward_enu':f.n.tolist(),'face_bounds_uz':list(p.bounds),'depth_m':[face_depth-.001,face_depth+.002],'thickness_m':.003,'role':'surface mortar seam; not structure, opening or glass'})

 def spandrel(self,f,u,width,z,kind,label):
  outer=rect(u-width*.46,z-.72,u+width*.46,z+.95)
  inner=outer.buffer(-.15,join_style=2)
  if kind=='east':
   f.prism(outer.difference(inner),-.01,.055,'red brick border',label+'/red-brick-surround')
   f.prism(inner,-.012,.022,'blue grey brick',label+'/blue-grey-brick-infill')
   self.mortar(f,inner,.022,label)
  else:
   f.prism(outer.difference(inner),-.01,.075,'pale grey pilaster',label+'/plaster-frame')
   f.prism(inner,-.01,.028,'recessed plaster panel',label+'/panel')
   for du in [-width*.27,-width*.20,width*.20,width*.27]:
    f.box(u+du,z+.12,.022,1.25,.012,.026,'stone reveal',label+'/incised-panel-line')

 def south(self):
  f=self.front;top=self.Z[-1]
  for q in self.portals:
   a,b,center,width=q['start'],q['end'],q['center'],q['width'];count=q['bays_each_side'];kind=q['id'];hole=[];centres=[];piers=set()
   for start,end in [(a,center-width/2),(center+width/2,b)]:
    pitch=(end-start)/count
    for j in range(count):
     u=start+(j+.5)*pitch;centres.append((u,pitch));piers.update([start+j*pitch,start+(j+1)*pitch])
     for k,z in enumerate(self.Z[:-1]):
      shape=rect(u-pitch*.36,z+1.1,u+pitch*.36,z+3.1);hole.append(shape)
      self.grid_window(f,shape,f'{kind}/bay-{len(centres)-1}/floor-{k+1}',7 if kind=='west' else 6,4 if kind=='west' else 3)
      if k:self.spandrel(f,u,pitch,z,kind,f'{kind}/bay-{len(centres)-1}/spandrel-{k}')
   face=unary_union([rect(a,0,center-width/2,top),rect(center+width/2,0,b,top)])
   f.prism(face.difference(unary_union(hole)),-.48,0,'weathered grey plaster',kind+'/continuous-pier-and-spandrel')
   for i,u in enumerate(sorted(piers)):
    f.box(u,top/2,.43,top,.28,.08,'pale grey pilaster',f'{kind}/pilaster-{i}')
    for side in [-1,1]:f.box(u+side*.22,top/2,.075,top,.34,.12,'stone reveal',f'{kind}/pilaster-edge-{i}-{side}')
    f.box(u,22.85,.62,1.45,.56,.15,'pale grey pilaster',f'{kind}/parapet-post-{i}')
   for i,(u,pitch) in enumerate(centres):
    f.box(u,22.77,pitch-.52,.65,.30,-.04,'weathered grey plaster',f'{kind}/parapet-panel-{i}')
    f.box(u,23.12,pitch-.45,.12,.45,.015,'pale grey pilaster',f'{kind}/parapet-coping-{i}')
    f.line((u-pitch/2+.3,23.36,.06),(u+pitch/2-.3,23.36,.06),.025,'charcoal steel frame',8,f'{kind}/parapet-rail-{i}')
   self.portal(q)
  f.beam(22.25,.38,.58,'pale grey pilaster',label='continuous-cornice-bridge')
  f.beam(.16,.30,.05,'stone reveal',label='base-plinth')

 def lettering(self,f,text,u,z,width,height,label,low=.02,high=.033):
  font=HERE/'fonts/SihangSubset.otf'
  for i,(_,shape) in enumerate(lettering_shapes(text,width,height,font=font)):
   f.prism(affinity.translate(shape,xoff=u,yoff=z),low,high,'sign dark lettering',label+f'/glyph-{i}')

 def portal(self,q):
  f=self.front;c=q['center'];w=q['width'];dep=q['depth'];name=q['id'];top=self.Z[-1]
  back=Facade(self.b,f.point(c-w/2,0,-dep)[:2],f.point(c+w/2,0,-dep)[:2],name+'-entry-back')
  holes=[]
  for k,z in enumerate(self.Z[:-1]):
   h=rect(-w/2+.4,z+.3 if k==0 else z+1.05,w/2-.4,z+3.35);holes.append(h)
   self.grid_window(back,h,f'floor-{k+1}',5 if name=='west' else 4,2)
   if k:self.spandrel(back,0,w-.8,z,'west',f'photo-observed-recess-spandrel-{k}')
  back.prism(rect(-w/2,0,w/2,top).difference(unary_union(holes)),-.48,0,'weathered grey plaster','recessed-wall')
  for side in [-1,1]:
   x=c+side*w/2
   a,b=(f.point(x,0,0)[:2],f.point(x,0,-dep)[:2]) if side<0 else (f.point(x,0,-dep)[:2],f.point(x,0,0)[:2])
   wall=Facade(self.b,a,b,name+f'-portal-return-{side}');wall.wall(0,top,thickness=.35,material='pale grey pilaster')
   f.box(x,top/2,.52,top,.46,.13,'pale grey pilaster',name+'/outer-portal-pilaster')
  # Floor/threshold connects to the deeply inset, closed exterior door plane.
  p=Polygon([f.point(x,0,d)[:2] for x,d in [(c-w/2,0),(c+w/2,0),(c+w/2,-dep),(c-w/2,-dep)]])
  self.b.plan_prism(p,0,.12,'terrace paving grey',name+'/recess-floor')
  rain_z=3.72 if name=='west' else 3.4
  self.b.plan_prism(p,rain_z,rain_z+.025,'translucent skylight glass',name+'/transparent-entry-rain-canopy')
  for k in range(5):
   u=c-w/2+k*w/4
   self.beam3(f.point(u,rain_z+.025,0),f.point(u,rain_z+.025,-dep),.055,.07,'charcoal steel frame',name+f'/rain-canopy-rib-{k}')
  self.mark('glazed_entry_rain_canopy',name+'/transparent-entry-rain-canopy',outline_enu=list(p.exterior.coords),z_m=rain_z,documented_presence=True,shape_and_elevation_estimated=True)
  sign_z=4.15 if name=='west' else 2.35
  if name=='west':
   # A distinct stepped crown stands on the fifth-floor cornice above this
   # entrance. It is separate from the much lower inscribed door lintel.
   half=(w-.7)/2
   crown=Polygon([(c-half,22.40),(c+half,22.40),(c+half,23.15),
    (c+2.65,23.15),(c+2.65,23.48),(c+1.28,23.48),(c+1.28,23.85),
    (c-1.28,23.85),(c-1.28,23.48),(c-2.65,23.48),(c-2.65,23.15),(c-half,23.15)])
   crown_panel=crown.buffer(-.12,join_style=2)
   f.prism(crown,-.16,.27,'weathered grey plaster','west/fifth-floor-stepped-crown-core')
   f.prism(crown.difference(crown_panel),.24,.34,'pale grey pilaster','west/fifth-floor-stepped-crown-border')
   f.prism(crown_panel,.26,.285,'recessed plaster panel','west/fifth-floor-stepped-crown-recess')
   self.mark('photo_observed_fifth_floor_stepped_crown','south/west/fifth-floor-stepped-crown',face_polygon_uz=list(crown.exterior.coords),source_photo_pageid=148812398,maximum_z_m=23.85,dimensions_estimated=True)
   for step,ww,zz in [(0,w-.55,4.15),(1,w-.95,4.65),(2,w-1.4,5.1),(3,w-2.5,5.42)]:
    f.box(c,zz,ww,.45,.55,-.45,'pale grey pilaster',f'{name}/stepped-lintel-{step}')
   plate=Facade(self.b,f.point(c-(w-.8)/2,0,-.20)[:2],f.point(c+(w-.8)/2,0,-.20)[:2],name+'-entry-sign')
   self.lettering(plate,'THE JOINT TRUST WAREHOUSE',0,4.08,w-1.25,.30,'english-name')
   self.lettering(plate,'庫倉部分海上部託信行銀',-.45,4.62,w-2.7,.30,'historic-right-to-left-name')
   self.lettering(plate,'大中金鹽',w/2-1.15,4.71,.72,.14,'bank-names-upper')
   self.lettering(plate,'陸南城業',w/2-1.15,4.53,.72,.14,'bank-names-lower')
  else:
   back.box(0,1.30,w,.75,.16,.08,'pale grey pilaster','entrance-inscription-support')
   plate=Facade(self.b,f.point(c-w/2,0,-dep+.135)[:2],f.point(c+w/2,0,-dep+.135)[:2],name+'-entry-sign')
   self.lettering(plate,'THE CONTINENTAL BANK WAREHOUSE',0,1.05,w-.5,.22,'english-name')
   self.lettering(plate,'庫倉行銀陸大海上',0,1.42,w-1.0,.29,'historic-right-to-left-name')
   # Visible pitched glazed upper-entry cover. Exact slope and panel sizes
   # are estimates; both pitches have physical glass and a steel seat grid.
   upper_labels=[]
   for side in [-1,1]:
    origin=f.point(c+side*w*.44,22.45,.06)
    ridge=f.point(c,23.60,.06)
    eave_back=f.point(c+side*w*.44,22.45,-dep*.90)
    du=ridge-origin;dv=eave_back-origin;lu=float(np.linalg.norm(du));lv=float(np.linalg.norm(dv));du/=lu;dv/=lv
    dn=np.cross(du,dv);dn/=np.linalg.norm(dn)
    if dn[2]<0:origin=eave_back;dv=-dv;dn=-dn
    def roofpoint(u,z,d):return origin+du*u+dv*z+dn*d
    pane_label=name+f'/upper-canopy-glass-pitch-{side}'
    self.b.prism(rect(0,0,lu,lv),.006,.031,roofpoint,'translucent skylight glass',pane_label);upper_labels.append(pane_label)
    for row in range(4):
     v=lv*row/3
     self.beam3(roofpoint(0,v,.04),roofpoint(lu,v,.04),.065,.075,'charcoal steel frame',name+f'/upper-canopy-cross-rib-{side}-{row}')
    for col in range(3):
     u=lu*col/2
     self.beam3(roofpoint(u,0,.04),roofpoint(u,lv,.04),.065,.075,'charcoal steel frame',name+f'/upper-canopy-slope-rib-{side}-{col}')
   self.mark('upper_entry_pitched_glass_canopy',name+'/upper-canopy',glass_part_labels=upper_labels,estimated_eaves_z_m=22.45,estimated_ridge_z_m=23.60,photo_pageids=[148812398,83213122],shape_estimated=True)
  self.mark('deep_south_entry',name+'-portal',center_face_u=c,width_m=w,recess_depth_m=dep,top_m=top,source='Commons148812398/65213484/195996200 + interpreted upper-floor plan; depth estimated')

 def ordinary_face(self,f,count,role):
  holes=[];pitch=f.length/count
  for k,z in enumerate(self.Z[:-1]):
   for j in range(count):
    u=-f.length/2+(j+.5)*pitch;width=min(3.5,pitch-.65);h=rect(u-width/2,z+1.12,u+width/2,z+3.03)
    holes.append(h);self.grid_window(f,h,f'floor-{k+1}/bay-{j}',6,3)
  f.wall(0,self.Z[-1],holes,thickness=.48,material='weathered grey plaster')
  f.beam(22.25,.35,.32,'pale grey pilaster',label='cornice')
  for j in range(count+1):f.box(-f.length/2+j*pitch,11.1,.33,22.2,.18,.025,'pale grey pilaster',f'column-{j}')
  self.mark('ordinary_elevation',f.label,role=role,window_bays=count,exact_count_supported=(role=='east_end_three_bays'),hidden_detail_estimated=True)

 def damage(self):
  f=self.west;L=f.length;top=self.Z[-1];H=np.array(self.c['west_damage_mapping']['photo_to_normalized_wall_uz_homography'])
  def uz(point):
   q=H@np.r_[point,1.];q=q[:2]/q[2];return [L*(q[0]-.5),top*q[1]]
  large=json.loads((HERE/'west-wall-large-openings.json').read_text())['openings']
  through=[];pits=[];shapes={}
  for q in large:
   p=Polygon([uz(x) for x in q['pixel_polygon']]);assert p.is_valid
   shapes[q['id']]=p
   (pits if q['id']=='H6-right-small-left' else through).append(p)
  self.through_damage_shapes={key:p for key,p in shapes.items() if key!='H6-right-small-left'}
  small=json.loads((HERE/'dark-damage-centers.json').read_text())['points'];smallsh=[]
  for q in small:
   xy=np.array(q['pixel_center']);center=np.array(uz(xy));unit=np.linalg.norm(np.array(uz(xy+[1,0]))-center)
   radius=float(np.clip(q['dark_core_equivalent_radius_px']*unit,.055,.16));p=Point(center).buffer(radius,quad_segs=4)
   smallsh.append((q,p,center,radius))
  cut=unary_union(through);pit_union=unary_union(pits+[p for _,p,_,_ in smallsh]);wall=rect(-L/2,0,L/2,top)
  exposed_norm=[[.11,.39],[.18,.43],[.22,.42],[.29,.36],[.37,.39],[.44,.35],[.52,.37],[.59,.34],[.68,.34],[.73,.27],[.72,.22],[.69,.17],[.68,.11],[.66,0],[.60,0],[.59,.07],[.52,.10],[.44,.08],[.39,.13],[.36,.20],[.30,.20],[.26,.25],[.20,.26],[.16,.30],[.12,.32]]
  exposed=Polygon([(L*(u-.5),top*z) for u,z in exposed_norm]);rim=cut.buffer(.34,join_style=2).difference(cut)
  plaster=wall.difference(unary_union([cut,pit_union,exposed,rim]))
  f.prism(wall.difference(unary_union([cut,pit_union])),-.48,-.055,'exposed aged brick','continuous-masonry-core')
  f.prism(plaster,-.055,0,'weathered grey plaster','retained-irregular-plaster')
  f.prism(rim.intersection(wall),-.055,-.003,'exposed aged brick','large-damage-brick-reveals')
  # Designer documents a continuous full-height safety backing wall. It is
  # tied into each structural floor slab, not a group of floating patches.
  f.prism(rect(-L/2+.25,0,L/2-.25,top),-1.465,-1.285,'safety backing masonry','continuous-safety-backing-wall')
  self.mark('continuous_west_safety_wall',f.label+'/continuous-safety-backing-wall',face_origin_enu=f.center.tolist(),face_tangent_enu=f.t.tolist(),outward_enu=f.n.tolist(),face_bounds_uz=[-L/2+.25,0,L/2-.25,top],depth_m=[-1.465,-1.285],touching_floor_part_labels=[f'structural-floor-slab-{i}' for i in range(6)],setback_reference_estimated=True)
  for q in large:
   p=shapes[q['id']];label=q['id'];is_pit=label=='H6-right-small-left'
   if is_pit:
    f.prism(p,-.48,-.30,'dark crater core',label+'/closed-brick-backed-recess')
    self.mark('large_brick_backed_recess',f.label+'/'+label,face_origin_enu=f.center.tolist(),face_tangent_enu=f.t.tolist(),outward_enu=f.n.tolist(),face_polygon_uz=list(p.exterior.coords),wall_depth_m=[-.48,0],surface_depth_m=-.30,part_label=f.label+'/'+label+'/closed-brick-backed-recess',photo_pixel_polygon=q['pixel_polygon'])
   else:
    frame=p.buffer(.075,join_style=2).difference(p.buffer(-.015,join_style=2))
    f.prism(frame,-.72,-.43,'stone reveal',label+'/inner-reveal-seat')
    f.prism(p.buffer(.035,join_style=2),-.68,-.662,'restoration dark glass',label+'/dark-glass-lining')
    f.prism(p.buffer(.12,join_style=2),-1.46,-1.28,'safety backing masonry',label+'/safety-backing')
    self.mark('large_glass_backed_damage',f.label+'/'+label,face_origin_enu=f.center.tolist(),face_tangent_enu=f.t.tolist(),outward_enu=f.n.tolist(),face_polygon_uz=list(p.exterior.coords),wall_depth_m=[-.48,0],glass_depth_m=[-.68,-.662],backing_depth_m=[-1.46,-1.28],glass_part_label=f.label+'/'+label+'/dark-glass-lining',seat_part_label=f.label+'/'+label+'/inner-reveal-seat',backing_part_label=f.label+'/'+label+'/safety-backing',photo_pixel_polygon=q['pixel_polygon'])
  for q,p,center,radius in smallsh:
   f.prism(p,-.48,-.10,'dark crater core',q['id']+'/pit-bottom')
   self.mark('observed_minor_pit',f.label+'/'+q['id'],photo_pixel_center=q['pixel_center'],face_center_uz=center.tolist(),face_origin_enu=f.center.tolist(),face_tangent_enu=f.t.tolist(),outward_enu=f.n.tolist(),radius_estimated_m=radius,depth_estimated_m=.10,part_label=f.label+'/'+q['id']+'/pit-bottom',historical_cause_not_individually_verified=True)
  # Surviving concrete columns/beams are clipped to the observed plaster-loss
  # patch; orange exposed brick does not become one enormous wall opening.
  bars=[]
  for u in [.205,.285,.365,.445,.525,.605,.685]:bars.append(rect(L*(u-.5)-.18,0,L*(u-.5)+.18,top*.5))
  for z in [.19,.375]:bars.append(rect(-L/2,top*z-.16,L/2,top*z+.16))
  frame=unary_union(bars).intersection(exposed).difference(cut)
  f.prism(frame,-.06,.004,'exposed concrete','surviving-exposed-frame')
  self.mark('west_damage_wall_structure',f.label+'/structural-surface',face_origin_enu=f.center.tolist(),face_tangent_enu=f.t.tolist(),outward_enu=f.n.tolist(),width_m=L,height_m=top,core_part_label=f.label+'/continuous-masonry-core',plaster_part_label=f.label+'/retained-irregular-plaster',damage_rim_part_label=f.label+'/large-damage-brick-reveals',exposed_frame_part_label=f.label+'/surviving-exposed-frame',exposed_brick_patch_face_polygon=list(exposed.exterior.coords),core_depth_m=[-.48,-.055],plaster_depth_m=[-.055,0])
  bricks=exposed.difference(unary_union([frame,cut,pit_union]));self.mortar(f,bricks,-.055,'west-exposed-lower-masonry')
  # Only individually legible surviving characters are reconstructed. The
  # full historical wording is not guessed across destroyed/illegible areas.
  legible=[('庫',[276,112]),('倉',[345,121]),('部',[415,127]),('海',[543,142]),('部',[661,157])]
  for j,(char,pixel) in enumerate(legible):
   u=uz(pixel)[0];z=top*.86
   patch=rect(u-.75,z-.82,u+.75,z+.82).difference(unary_union([cut,pit_union]))
   if not patch.is_empty:f.prism(patch,-.001,.003,'inscription pale patch',f'inscription-patch-{j}')
   for k,(_,p) in enumerate(lettering_shapes(char,1.15,1.30,font=HERE/'fonts/SihangSubset.otf')):
    p=affinity.translate(p,xoff=u,yoff=z).difference(unary_union([cut,pit_union]))
    if not p.is_empty:f.prism(p,.002,.005,'faded inscription',f'historic-inscription-{j}-{k}')
  f.beam(top,.36,.40,'pale grey pilaster',label='memorial-cornice')
  f.box(0,top+.58,L,.85,.30,-.15,'weathered grey plaster','memorial-parapet')

 def roof_and_atriums(self):
  top=self.Z[-1]
  # Fifth-floor terrace and sixth-floor retreat; the north street wall stays
  # at the north plan boundary, unlike a uniform inward buffer of every side.
  bands=[]
  for f,dep in [(self.front,3.25),(self.west,2.35),(self.east,2.2)]:bands.append(LineString([f.a[:2],f.b[:2]]).buffer(dep,cap_style=2))
  upper=self.body.difference(unary_union(bands));upper=orient(max(pieces(upper),key=lambda p:p.area),sign=1)
  self.b.plan_prism(self.body.difference(self.courts),top-.20,top,'terrace paving grey','fifth-floor-terrace-slab')
  pts=list(upper.exterior.coords)
  for i,(a,b) in enumerate(zip(pts,pts[1:])):
   f=Facade(self.b,a,b,f'sixth-floor-{i}');holes=[]
   if f.length>1.2:
    count=max(1,int(round(f.length/5.2)));pitch=f.length/count
    for j in range(count):
     u=-f.length/2+(j+.5)*pitch;w=max(.3,pitch-.38)
     h=rect(u-w/2,top+.75,u+w/2,top+2.45);holes.append(h);self.grid_window(f,h,f'clerestory-{j}',max(1,int(round(w/.9))),2,wall_depth=.32)
   f.wall(top,26.8,holes,thickness=.32,material='pale grey pilaster')
   f.box(0,27.25,f.length,.90,.25,-.13,'pale grey pilaster','roof-parapet')
  self.b.plan_prism(upper.difference(self.courts),26.60,26.80,'roof light grey membrane','sixth-floor-roof-slab')
  for k,court in enumerate(self.atriums):
   # Closed inner walls with real glazed openings bound the atrium void.
   p=list(orient(court,sign=-1).exterior.coords)
   for i,(a,b) in enumerate(zip(p,p[1:])):
    f=Facade(self.b,a,b,f'atrium-{k}-wall-{i}');holes=[];count=max(1,int(round(f.length/4.2)));pitch=f.length/count
    for level,z in enumerate(self.Z[:-1]):
     for j in range(count):
      u=-f.length/2+(j+.5)*pitch;w=max(.4,pitch-.7);shape=rect(u-w/2,z+1.05,u+w/2,z+3.15);holes.append(shape);self.grid_window(f,shape,f'level-{level+1}/bay-{j}',4,2,back=-.21,wall_depth=.24)
    f.wall(0,26.4,holes,thickness=.24,material='recessed plaster panel')
   self.b.plan_prism(court,.0,.08,'terrace paving grey',f'atrium-{k}/ground-paving')
   self.b.plan_prism(court,26.40,26.425,'translucent skylight glass',f'atrium-{k}/glazed-roof')
   # Explicit perimeter frame and repeated spanning bars, not a photo plane.
   ring=court.buffer(.08,join_style=2).difference(court.buffer(-.06,join_style=2))
   self.b.plan_prism(ring,26.39,26.50,'charcoal steel frame',f'atrium-{k}/roof-perimeter-frame')
   bounds=court.bounds
   for j,x in enumerate(np.arange(bounds[0],bounds[2],1.4)):
    area=rect(x-.035,bounds[1],x+.035,bounds[3]).intersection(court)
    if not area.is_empty:self.b.plan_prism(area,26.425,26.49,'charcoal steel frame',f'atrium-{k}/roof-bar-{j}')
   self.mark('atrium',f'atrium-{k}',outline_enu=list(court.exterior.coords),glazed_roof_z_m=26.4,plan_number7_is_use_not_seventh_floor=True)
  # A small bounded roof-services array follows the aerial arrangement, with
  # counts and sizes explicitly estimated rather than invented precise plant.
  available=upper.buffer(-2).difference(self.courts.buffer(1.2));minx,miny,maxx,maxy=available.bounds;placed=0
  for y in np.linspace(miny+3,maxy-3,4):
   for x in np.linspace(minx+3,maxx-3,5):
    p=rect(x-.7,y-.42,x+.7,y+.42)
    if not available.contains(p) or placed>=12:continue
    self.b.plan_prism(p,26.8,27.35,'roof equipment grey',f'roof-services/fan-box-{placed}')
    for s in range(7):self.b.box([x-.55+s*.18,y,27.385],[.045,.73,.07],'charcoal steel frame',label=f'roof-services/grille-{placed}-{s}')
    placed+=1
  self.mark('estimated_roof_services','roof-services',boxes=placed,roof_plan_enu=list(upper.exterior.coords),dimensions_measured=False)

 def build(self):
  self.south();self.damage();self.ordinary_face(self.east,3,'east_end_three_bays')
  p=self.c['plan_interpretation']['model_body_polygon_enu']
  for i in range(2,len(p)-1):
   f=Facade(self.b,p[i],p[i+1],f'north-curved-{i-2}');self.ordinary_face(f,max(1,int(round(f.length/5.3))),'north_plan_and_photo_constrained_estimate')
  for k,z in enumerate(self.Z):
   # Keep the floor edges inside the masonry with60mm overlap. Letting their
   # vertical skins coincide with the wall exterior produces false dark
   # horizontal stripes. The two glazed atrium voids remain real openings.
   area=self.body if k==0 else self.body.buffer(-.42,join_style=2).difference(self.courts.buffer(.18,join_style=2))
   if k:
    # A floor edge must not impersonate an original beam inside a glass-
    # backed photograph-traced aperture. Notch only its actual vertical
    # intersection with the seven apertures, behind glass and its seat.
    # The remaining floor continues through the safety wall at-1.285m.
    zlo=max(0,z-.18);zhi=z+.01
    for opening_id,hole in self.through_damage_shapes.items():
     segment=hole.buffer(.045,join_style=2).intersection(rect(-self.west.length/2,zlo-.01,self.west.length/2,zhi+.01))
     if segment.is_empty or segment.area<1e-10:continue
     umin,_,umax,_=segment.bounds;umin-=.02;umax+=.02
     notch=Polygon([self.west.point(u,0,d)[:2] for u,d in [(umin,.05),(umax,.05),(umax,-.86),(umin,-.86)]])
     area=area.difference(notch)
     self.mark('localized_floor_clearance_behind_glass',f'structural-floor-slab-{k}/clearance/{opening_id}',slab_part_label=f'structural-floor-slab-{k}',opening_id=opening_id,slab_z_m=[zlo,zhi],face_u_m=[umin,umax],clip_depth_m=[-.86,.05],glass_back_depth_m=-.68,seat_back_depth_m=-.72,safety_wall_front_depth_m=-1.285,intersected_uz_polygons=[list(x.exterior.coords) for x in pieces(segment)],notch_plan_enu=list(notch.exterior.coords),not_a_photo_observed_beam=True)
   self.b.plan_prism(area,max(0,z-.18),z+.01,'recessed plaster panel',f'structural-floor-slab-{k}')
  self.roof_and_atriums()
  names=[p['label'] for p in self.b.parts]
  if len(names)!=len(set(names)):
   # Stable per-part suffixes disambiguate facade helpers used for matched
   # parallel trim without altering semantic feature base labels.
   seen=Counter()
   for p in self.b.parts:
    name=p['label'];seen[name]+=1
    if seen[name]>1:p['label']=name+f'/repeat-{seen[name]-1}'
  assert np.isfinite([v for p in self.b.parts for v in p['vertices']]).all()
  return self

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--lod',action='store_true');a=ap.parse_args()
 if a.out.exists():raise ValueError('Only a new output directory is permitted')
 freeze=json.loads((HERE/'source-freeze.json').read_text())
 for r in freeze['files']:
  p=HERE/r['path'];assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],r['path']
 model=Warehouse(a.lod).build();a.out.mkdir(parents=True)
 path=a.out/'jingan-sihang-warehouse.glb'
 extras={'id':model.g['id'],'name':model.g['name_en'],'source_geometry_sha256':sha(HERE/'geometry-input.json'),
 'calibration_sha256':sha(HERE/'calibration.json'),'source_freeze_sha256':sha(HERE/'source-freeze.json'),
 'height_estimate_m':27.7,'height_source':'SIADR project nominal total height; local dimensions estimated','ground_base_m':0,
 'geometry_scope':'Complete two-warehouse compound; five-storey exterior frame plus set-back sixth floor; no later seventh floor',
 'lod_authored_subtraction':a.lod,'reference_images_embedded':False,
 'copyright':'Geometry and code: MIT; geographic source: OpenStreetMap contributors / Overture Maps, ODbL-1.0; referenced photographs retain CC BY4.0, CC BY-SA4.0 and CC0; font: SIL OFL1.1'}
 report=model.b.save(path,extras)
 features={'schema':'sihang-authored-semantic-geometry-v12','id':model.g['id'],'lod':a.lod,'raw_sha256':report['sha256'],
 'features':model.features,'fine_masonry_parts':model.fine,'all_part_labels':[p['label'] for p in model.b.parts],
 'source_geometry_sha256':extras['source_geometry_sha256'],'calibration_sha256':extras['calibration_sha256'],
 'finite_vertex_checks':len(model.b.parts),'no_private_pixels_or_photo_textures':True}
 write(a.out/'feature-manifest.json',features)
 metadata={'schema':'sihang-warehouse-model-v12','id':model.g['id'],'raw':{'file':path.name,'bytes':report['bytes'],'sha256':report['sha256']},
 'height_estimate_m':27.7,'height_is_project_nominal_not_surveyed':True,'ground_base_m':0,'triangles':report['triangles'],'parts':report['parts'],
 'calibration_sha256':extras['calibration_sha256'],'source_freeze_sha256':extras['source_freeze_sha256'],
 'model_appearance_review_passed':False,'browser_passed':False,'lod':a.lod,
 'feature_counts':dict(Counter(x['kind'] for x in model.features)),'fine_masonry_parts':len(model.fine),
 'budget_under40MB':report['bytes']<40000000,'all_files_must_be_strictly_under100000000':True}
 write(a.out/'metadata.json',metadata)
 print(json.dumps(metadata,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
