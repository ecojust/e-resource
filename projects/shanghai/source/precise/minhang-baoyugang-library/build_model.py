#!/usr/bin/env python3
"""Pao Yue-Kong Library, 2021 exterior. All non-source dimensions estimated.
Root executes this builder. No research photograph is embedded or read here.
"""
from pathlib import Path
from collections import Counter
import argparse,hashlib,json,math,sys
import numpy as np
from shapely import set_precision
from shapely.geometry import Polygon,box as rect,LineString
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'common'))
from photo_architecture import Builder,Facade,pieces

PALETTE={
 'terracotta ceramic':{'color':[.34,.145,.115],'roughness':.86},
 'terracotta warm':{'color':[.365,.158,.123],'roughness':.86},
 'terracotta muted':{'color':[.325,.14,.115],'roughness':.88},
 'terracotta deep joint':{'color':[.255,.127,.112],'roughness':.94},
 'red coping':{'color':[.39,.21,.17],'roughness':.78},
 'charcoal aluminium':{'color':[.075,.095,.10],'roughness':.39,'metallic':.55},
 'green grey glass':{'color':[.24,.34,.34],'roughness':.18,'metallic':.18,'alpha':.64},
 'blue grey glass':{'color':[.18,.27,.29],'roughness':.2,'metallic':.17,'alpha':.64},
 'canopy glass':{'color':[.30,.39,.39],'roughness':.15,'metallic':.12,'alpha':.48},
 'dark pergola':{'color':[.075,.065,.057],'roughness':.63,'metallic':.22},
 'interior plaster':{'color':[.60,.58,.52],'roughness':.92},
 'interior floor':{'color':[.40,.385,.34],'roughness':.86},
 'roof weathering':{'color':[.25,.265,.25],'roughness':.95},
 'terrace paving':{'color':[.45,.43,.39],'roughness':.91},
 'granite entry':{'color':[.48,.49,.45],'roughness':.87},
 'brushed door handle':{'color':[.35,.39,.38],'roughness':.33,'metallic':.8},
}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')

class Library:
 def __init__(self,lod=False):
  self.g=json.loads((HERE/'geometry-input.json').read_text());self.c=json.loads((HERE/'calibration.json').read_text());assert sha(HERE/'geometry-input.json')==self.c['source_geometry_sha256'];assert self.g['id']=='minhang-baoyugang-library'
  self.e=self.c['estimated'];self.b=Builder(PALETTE);self.lod=lod;self.profiles=[orient(Polygon(p),sign=1) for p in self.e['level_profiles_uv_m']];self.openings=[];self.contacts=[];self.facades=[];self.semantic=[]
  self.Z=self.e['level_base_z_m'];self.t=np.array(self.c['coordinate_frame']['u_eastward_ENU']);self.n=np.array(self.c['coordinate_frame']['v_northward_ENU'])

 def slab(self,p,z,thick,material,label):self.b.plan_prism(p,z-thick,z,material,label)
 def beam(self,a,b,width,depth,material,label):
  a,b=np.array(a,float),np.array(b,float);t=b-a;length=np.linalg.norm(t);t/=length;aux=np.array([0,0,1.]) if abs(t[2])<.9 else np.array([0,1.,0]);side=np.cross(t,aux);side/=np.linalg.norm(side);up=np.cross(side,t)
  self.b.box((a+b)/2,(length,width,depth),material,[t,side,up],label)

 def window_grid(self,f,shape,level,label,slanted=False,door=False):
  x0,z0,x1,z1=shape.bounds;w=x1-x0;h=z1-z0
  def mapper(u,z,d):
   # Upper edge 0.55m farther outward than lower edge, a geometric tilted plane.
   return f.point(u,z,d+(.55*(z-z0)/h-.10 if slanted else 0))
  if slanted:
   # Closed wedge reveal joins the tilted glazing to the vertical wall.
   # Work in local height so the prism's mapper-handedness check is valid.
   outer_reveal=rect(x0-.075,-.075,x1+.075,h+.075)
   inner_reveal=rect(x0+.035,.035,x1-.035,h-.035)
   def wedge_map(u,zz,d):return f.point(u,zz+z0,-.28+d*(.20+.55*zz/h))
   self.b.prism(outer_reveal.difference(inner_reveal),0,1,wedge_map,'red coping',label+'/closed-sloped-jamb-header-reveal')
  # Regular frame perimeter embeds20mm beyond the clear wall opening.
  # The clear inner cells/glass are unchanged. Slanted frames retain their
  # original outer profile because their separate wedge reveals are pending
  # complete independent v1 contact review.
  inset=shape.buffer(-.065,join_style=2);outer=shape.buffer(-.018 if slanted else .020,join_style=2)
  cols=max(1,int(round(w/(1.35 if door else 1.5))));rows=1 if h<1.9 else 2
  if door:cols=4;rows=1
  bars=[]
  for j in range(1,cols):
   x=x0+w*j/cols;bars.append(rect(x-.032,z0,x+.032,z1))
  if rows==2:
   z=z1-.46;bars.append(rect(x0,z-.027,x1,z+.027))
  cells=inset.difference(unary_union(bars)) if bars else inset
  frame=outer.difference(cells)
  self.b.prism(frame,-.20,-.045,mapper,'charcoal aluminium',label+'/continuous-frame-grid')
  for j,cell in enumerate(pieces(cells)):
   self.b.prism(cell,-.157,-.139,mapper,'green grey glass' if (level+j)%3 else 'blue grey glass',label+f'/glass-pane-{j}')
  # Deep red sill connects actual wall thickness to the recessed frame.
  if not door:
   self.b.prism(rect(x0-.04,z0-.055,x1+.04,z0+.005),-.285,.045,mapper,'red coping',label+'/sill')
  self.openings.append({'label':label,'kind':'slanted_glazed_opening' if slanted else ('glazed_entry_door' if door else 'wall_window'),'level':level+1,'face_center_local_uv':f.center[:2].tolist(),'face_tangent_local_uv':f.t[:2].tolist(),'face_outward_local_uv':f.n[:2].tolist(),'bounds_face_u_z':list(shape.bounds),'glass_depth_m':[-.157,-.139],'wall_depth_m':[-.28,0],'slant_top_minus_bottom_m':.55 if slanted else 0,'pane_count':len(pieces(cells)),'frame_outer_offset_m':(-.018 if slanted else .020),'solid_frame_material':'charcoal aluminium','glass_materials':['green grey glass','blue grey glass'],'counts_measured':False})
  if door:
   for u in [x0+w*.44,x0+w*.56]:
    self.b.tube([mapper(u,z0+.9,-.015),mapper(u,z0+1.6,-.015)],.018,'brushed door handle',8,label+'/door-pull')

 def face_style(self,f,k):
  u,v=f.center[:2];south=f.n[1]<-.35
  if k<3 and abs(v+8.7)<.01 and -5.4<u<15.3:return 'entry-void'
  if k==0 and u>16 and south:return 'ground-east-glazing'
  if u>16 and (south or f.n[0]>.65):return 'east-small'
  if south or f.n[0]<-.35:return 'south-ribbon'
  return 'north-service'

 def face(self,f,k):
  z=self.Z[k];top=self.Z[k+1] if k<5 else self.e['roof_z_m'];style=self.face_style(f,k);L=f.length
  if style=='entry-void':return
  holes=[];margin=.23
  if L>.9:
   if style=='east-small':
    # Observed repeated small upright openings; total count is a bounded estimate.
    pitch=4.35;width=.98;height=1.52;count=max(1,int(L/pitch));bottom=z+1.15
   elif style=='north-service':
    pitch=5.4;width=1.9;height=1.75;count=max(1,int(L/pitch));bottom=z+1.1
   else:
    pitch=3.55;width=None;height=2.35 if k!=0 else 2.9;count=max(1,int(round((L-.3)/pitch)));bottom=z+(.65 if k==0 else .9)
   if k==5 and style=='south-ribbon':height=2.65;bottom=z+.55
   spacing=(L-2*margin)/count
   if width is None:width=max(.3,spacing-.23)
   width=min(width,spacing-.14)
   for j in range(count):
    center=-L/2+margin+(j+.5)*spacing;holes.append(rect(center-width/2,bottom,center+width/2,min(bottom+height,top-.37)))
  face=rect(-L/2,z-.03,L/2,top+.025)
  cut=unary_union(holes) if holes else Polygon();solid=face.difference(cut)
  mat=['terracotta ceramic','terracotta warm','terracotta muted'][k%3]
  f.prism(solid,-.28,0,mat,'pier-and-spandrel-wall')
  self.facades.append({'label':f.label,'level':k+1,'style':style,'center_uv':f.center[:2].tolist(),'length_m':L,'window_count_estimated':len(holes),'evidence':'2021 exterior001/003 and F1/F6 architect plan, no calibrated dimensions or complete pane count' if style!='north-service' else '2021 unscaled F1/F6 service-room plan; north exterior less visible, rhythm explicitly estimated'})
  for j,hole in enumerate(holes):
   slanted=k==1 and style=='south-ribbon' and f.n[1]<-.15
   self.window_grid(f,hole,k,f.label+f'/window-{j}',slanted)
  # Bounded physical tile joints, clipped by the real wall openings. Their
  # depth is 2.5mm and they never bridge a window or close an actual aperture.
  if not self.lod and (style!='north-service' or k<2):
   strips=[]
   fine=k<=2 and style in ('south-ribbon','ground-east-glazing')
   course=.15 if fine else .30; joint_pitch=.30 if fine else 1.2
   for zz in np.arange(z+course/2,top,course):strips.append(rect(-L/2,zz-.0015,L/2,zz+.0015))
   for xx in np.arange(-L/2+joint_pitch/2,L/2,joint_pitch):strips.append(rect(xx-.0015,z,xx+.0015,top))
   joint=set_precision(unary_union(strips).intersection(solid),.0001)
   for j,p in enumerate(pieces(joint)):
    if p.area>1e-6:f.prism(p,.0008,.0033,'terracotta deep joint',f'fine-tile-joints-{j}')
  # Small true slab/header return at each facade, no floating face decal.
  f.box(0,top-.15,L+.012,.20,.34,-.12,'red coping','floor-edge-coping')

 def envelope(self):
  self.b.plan_prism(self.profiles[0],0,.46,'terracotta muted','foundation/estimated-ground-plinth')
  for k,p in enumerate(self.profiles):
   z=self.Z[k]
   self.slab(p,z,.27,'interior floor',f'floor/F{k+1}/structural-slab')
   ring=list(p.exterior.coords)
   for j,(a,b) in enumerate(zip(ring,ring[1:])):self.face(Facade(self.b,a,b,f'facade/F{k+1}/edge-{j}'),k)
   # Physical ceilings and sparse aligned interior columns provide depth
   # through glazing without falsely reproducing the renovated furnishings.
   top=self.Z[k+1] if k<5 else self.e['roof_z_m']
   self.slab(p.buffer(-.29,join_style=2),top-.045,.10,'interior plaster',f'floor/F{k+1}/plain-interior-soffit')
   for u in np.arange(-32,38,8.0):
    for v in [-2,5]:
     if p.buffer(-.5).covers(rect(u-.25,v-.25,u+.25,v+.25)):
      self.b.box((u,v,(z+top)/2),(.44,.44,top-z+.05),'interior plaster',label=f'interior/F{k+1}/column-{u}-{v}')
  roof=self.profiles[-1]
  self.slab(roof,self.e['roof_z_m']+.06,.25,'roof weathering','roof/main-warm-roof')
  ring=list(roof.exterior.coords)
  for j,(a,b) in enumerate(zip(ring,ring[1:])):
   f=Facade(self.b,a,b,f'roof/parapet-{j}');f.box(0,(24.85+25.7)/2,f.length,.85,.25,-.12,'terracotta ceramic','closed-upstand');f.box(0,25.68,f.length+.015,.06,.31,-.12,'red coping','cap')
  # Ground portico platform is inside the front structural envelope; the
  # large landscape stairs/lake plaza are scene context, not this owner.
  platform=rect(-5.45,-14.65,15.3,-8.4)
  self.slab(platform,.45,.45,'granite entry','entry/raised-platform')
  for j in range(3):
   v=-14.8+j*.30;self.b.plan_prism(rect(-5.45,v,15.3,-13.80),0,.15*(j+1),'granite entry',f'entry/front-step-{j+1}')
  # Small west service landing constrained by source's skinny projection.
  self.b.plan_prism(rect(-50.8,.95,-41.5,2.35),.0,.30,'granite entry','west/service-landing-estimated')

 def entry(self):
  e=self.e['entry'];f=Facade(self.b,[e['u_range_m'][0],e['glazing_v_m']],[e['u_range_m'][1],e['glazing_v_m']],'entry/atrium-glazing');z0=self.Z[0];top=e['portico_top_z_m'];L=f.length
  door=rect(-1.5,z0,6.5,z0+2.85);full=rect(-L/2,z0,L/2,top-.17)
  # Curtain wall made from floor-sized cells, with one actual door opening.
  for k in range(3):
   a=self.Z[k];b=self.Z[k+1] if k<2 else top
   span=rect(-L/2,a+.04,L/2,b-.11).difference(door)
   for j,p in enumerate(pieces(span)):self.window_grid(f,p,k,f'entry/atrium/F{k+1}/field-{j}')
  self.window_grid(f,door,0,'entry/doors',door=True)
  for i,u in enumerate(e['column_u_m']):
   v=e['forecourt_v_m']+.3
   self.b.lathe((u,v),[(.43,.48),(.51,.48),(.55,.42),(top+.035,.42)],'terracotta ceramic',24,f'entry/portico-round-column-{i}')
   self.contacts.append({'kind':'portico-column-platform-F4-slab','column':f'entry/portico-round-column-{i}','base_z_m':.43,'top_z_m':top+.035,'uv':[u,v],'actual_serialized_contact_pending':True})
  # Ground eastern wing remains glazed beneath the small-window upper mass.
  # Three red circular supports are estimated from the partially visible2021
  # undercroft; they are distinct from the two tall entrance supports.
  for i,u in enumerate([19.2,24.0,28.8]):
   self.b.lathe((u,-14.7),[(0,.29),(.45,.29)],'granite entry',20,f'east-wing/ground-column-base-{i}')
   self.b.lathe((u,-14.7),[(.43,.245),(4.585,.245)],'terracotta ceramic',20,f'east-wing/ground-round-column-{i}')
   self.contacts.append({'kind':'east-wing-ground-column-to-base-and-F2-slab','label':f'east-wing/ground-round-column-{i}','uv':[u,-14.7],'base_z_m':.43,'top_z_m':4.585,'count_estimated':True,'actual_serialized_contact_pending':True})
  # Barrel-shaped canopy along the facade. Segmented transparent thick shells
  # have matching steel ribs, two lateral ledgers and vertical support posts.
  u0,u1=e['canopy_u_m'];v0,v1=e['canopy_v_range_m'];edge=e['canopy_edge_z_m'];crown=e['canopy_crown_z_m'];ns=16
  def z(v):return edge+(crown-edge)*math.sin(math.pi*(v-v0)/(v1-v0))
  us=np.linspace(u0,u1,9);vs=np.linspace(v0,v1,ns+1)
  for i in range(8):
   for j in range(ns):
    a,b=vs[j],vs[j+1];A,B=us[i],us[i+1];verts=[(A,a,z(a)),(B,a,z(a)),(B,b,z(b)),(A,b,z(b))];verts+= [(x,y,zz-.018) for x,y,zz in verts]
    faces=[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]
    self.b.add(verts,faces,'canopy glass',f'entry/canopy/glass-{i}-{j}')
  for i,u in enumerate(us):self.b.tube([(u,v,z(v)-.055) for v in vs],.045,'charcoal aluminium',8,f'entry/canopy/arch-rib-{i}')
  for j,v in enumerate([v0,(v0+v1)/2,v1]):self.beam([u0-.05,v,z(v)-.055],[u1+.05,v,z(v)-.055],.09,.11,'charcoal aluminium',f'entry/canopy/longitudinal-ledger-{j}')
  for i,u in enumerate([u0,u1]):
   self.b.box((u,v0,(.45+edge-.055)/2),(.11,.11,edge-.055-.45+.035),'charcoal aluminium',label=f'entry/canopy/front-post-{i}')
  self.contacts.append({'kind':'canopy-grid-to-front-posts-and-rear-glazing-ledger','note':'actual intersections of rib/ledgers/posts require exported-geometry check','actual_serialized_contact_pending':True})

 def rail(self,a,b,z,label):
  f=Facade(self.b,a,b,label);length=f.length;n=max(1,int(math.ceil(length/1.55)))
  # Posts penetrate the coping/floor by 25mm; thin open upper/lower rails.
  for j,u in enumerate(np.linspace(-length/2+.07,length/2-.07,n+1)):
   f.box(u,z+.48,.035,1.01,.035,-.08,'charcoal aluminium',f'post-{j}')
  for j,h in enumerate([.18,.54,.99]):f.box(0,z+h,length,.028,.035,-.08,'charcoal aluminium',f'open-horizontal-{j}')

 def terraces(self):
  for lower in [1,2,3,4]:
   z=self.Z[lower+1];outer=self.profiles[lower];inner=self.profiles[lower+1]
   exposed=outer.difference(inner.buffer(.03,join_style=2));self.slab(exposed,z,.27,'interior floor',f'terrace/F{lower+2}/structural-deck');self.slab(exposed,z+.018,.08,'terrace paving',f'terrace/F{lower+2}/exposed-floor')
   ring=list(outer.exterior.coords)
   for j,(a,b) in enumerate(zip(ring,ring[1:])):
    f=Facade(self.b,a,b,f'terrace/F{lower+2}/edge-{j}');mid=(np.array(a)+np.array(b))/2
    if lower==4 and -20<f.center[0]<20.8 and f.center[1]<-5.35:continue
    if not inner.buffer(.45).covers(Polygon([mid+[-.01,-.01],mid+[.01,-.01],mid+[.01,.01],mid+[-.01,.01]])) and f.n[1]<.45:
     f.box(0,z+.11,f.length,.23,.26,-.13,'terracotta ceramic','low-open-rail-upstand');self.rail(a,b,z+.23,f.label+'/railing')
  # F5 colonnade supports the projecting F6 terrace. It is distinct from
  # F6's metal pergola and from the two much taller entry portico columns.
  deck=rect(-20.0,-13.7,20.8,-5.35);self.slab(deck,20.95,.30,'terracotta ceramic','terrace/F6/colonnade-roof-deck');self.slab(deck,20.98,.045,'terrace paving','terrace/F6/colonnade-walking-surface')
  for i,u in enumerate([-17,-10.2,-3.4,3.4,10.2,17]):
   self.b.lathe((u,-12.7),[(16.82,.34),(16.94,.34),(16.98,.285),(20.70,.285)],'terracotta ceramic',20,f'colonnade/F5/round-column-{i}')
   self.contacts.append({'kind':'F5-round-column-F4-floor-F6-deck','label':f'colonnade/F5/round-column-{i}','uv':[u,-12.7],'bottom_z_m':16.82,'top_z_m':20.70,'actual_serialized_contact_pending':True})
  for a,b in [([-20,-13.7],[20.8,-13.7]),([-20,-5.35],[-20,-13.7]),([20.8,-13.7],[20.8,-5.35])]:self.rail(a,b,20.98,'terrace/F6/long-railing')
  e=self.e['pergola'];u0,u1=e['u_range_m'];v0,v1=e['v_range_m'];top=e['beam_top_z_m'];floor=20.98
  for i,u in enumerate(np.linspace(u0,u1,7)):
   for j,v in enumerate([v0+.35,v1-.18]):
    self.b.box((u,v,(floor+top-.13)/2),(.12,.12,top-.13-floor+.05),'dark pergola',label=f'pergola/F6/post-{i}-{j}')
  for j,v in enumerate([v0+.35,v1-.18]):self.beam([u0-.25,v,top-.20],[u1+.25,v,top-.20],.16,.22,'dark pergola',f'pergola/F6/primary-long-beam-{j}')
  rib_count=57
  for i,u in enumerate(np.linspace(u0-.2,u1+.2,rib_count)):
   self.beam([u,v0-.25,top-.07],[u,v1+.25,top-.07],.065,.18,'dark pergola',f'pergola/F6/open-roof-rib-{i}')
  self.contacts.append({'kind':'F6-pergola-floor-post-beam-ribs','posts':14,'roof_ribs':rib_count,'actual_serialized_contact_pending':True})

 def west_returns_and_roof_raised_volume(self):
  # Contemporary photo confirms multiple open west-end terraces; these two
  # pentagonal cut-outs are bounded approximations, not a claimed count of
  # all historic arrow windows. Each is a real hole in a closed wall shell.
  for k,x in [(2,-42.6),(3,-36.9)]:
   z=self.Z[k];f=Facade(self.b,[x,7.8],[x,3.0],f'west-terrace/F{k+1}/open-return')
   shape=Polygon([(-1.85,z+.72),(.25,z+.72),(1.55,z+1.65),(.25,z+2.58),(-1.85,z+2.58)])
   f.prism(rect(-2.4,z-.025,2.4,z+3.15).difference(shape),-.26,0,'terracotta ceramic','pentagonal-aperture-wall')
   f.box(0,z+3.16,4.84,.12,.31,-.12,'red coping','top-coping')
   self.openings.append({'label':f.label+'/pentagonal-aperture-wall','kind':'open_west_terrace_aperture','level':k+1,'face_center_local_uv':f.center[:2].tolist(),'face_tangent_local_uv':f.t[:2].tolist(),'face_outward_local_uv':f.n[:2].tolist(),'shape_face_u_z':list(shape.exterior.coords),'glass_present':False,'exact_historical_profile_claimed':False})
  e=self.e['roof_raised_volume'];u,v=e['center_uv_m'];ru,rv=e['radii_uv_m'];base=e['base_z_m'];top=e['wall_top_z_m'];roof=e['cap_top_z_m'];n=e['sides_estimated']
  xy=[(u+ru*math.cos(math.tau*i/n+math.pi/n),v+rv*math.sin(math.tau*i/n+math.pi/n)) for i in range(n)]
  p=orient(Polygon(xy),sign=1);self.slab(p,24.94,.12,'roof weathering','roof/raised-volume/base-platform')
  ring=list(p.exterior.coords)
  for i,(a,b) in enumerate(zip(ring,ring[1:])):
   f=Facade(self.b,a,b,f'roof/raised-volume/side-{i}');holes=[]
   if i%2==0 and f.length>1.5:holes=[rect(-.55,25.2,.55,25.94)]
   f.wall(base,top,holes,.24,'terracotta ceramic')
   for j,h in enumerate(holes):self.window_grid(f,h,5,f'roof/raised-volume/side-{i}/estimated-window-{j}')
  verts=[(x,y,top-.09) for x,y in xy]+[(x,y,top) for x,y in xy]+[(u+(x-u)*.32,v+(y-v)*.32,roof) for x,y in xy]
  faces=[tuple(reversed(range(n))),tuple(2*n+i for i in range(n))]
  for i in range(n):
   j=(i+1)%n;faces.extend([(i,j,n+j,n+i),(n+i,n+j,2*n+j,2*n+i)])
  self.b.add(verts,faces,'terracotta muted','roof/raised-volume/low-hipped-cap-estimated')
  self.contacts.append({'kind':'roof-raised-volume-base-walls-hipped-cap','actual_serialized_contact_pending':True,'dimensions_and_window_count_estimated':True})

 def build(self):
  self.envelope();self.entry();self.terraces();self.west_returns_and_roof_raised_volume()
  # All builder geometry is authored in architectural u/v/up. Rotate exactly
  # once to frozen owner ENU, never reflect an architectural axis.
  for p in self.b.parts:
   a=np.asarray(p['vertices']);xy=a[:,:2]@np.array([self.t,self.n]);a[:,:2]=xy;p['vertices']=a.tolist()
  for p in self.b.parts:
   a=np.asarray(p['vertices']);self.semantic.append({'label':p['label'],'material':p['material'],'vertices':len(a),'triangles':len(p['triangles']),'bounds_enu_m':[a.min(0).tolist(),a.max(0).tolist()],'protected_in_lod':not ('fine-tile-joints' in p['label'])})
  return self

 def save(self,out):
  freeze_path=HERE/'source-freeze.json'
  if not freeze_path.is_file():raise ValueError('Freeze source inputs before generating a release raw')
  freeze=json.loads(freeze_path.read_text())
  for item in freeze['files']:
   file=HERE/item['path']
   if not file.is_file() or file.stat().st_size!=item['bytes'] or sha(file)!=item['sha256']:raise ValueError('Source freeze mismatch: '+item['path'])
  out=Path(out);out.mkdir(parents=True,exist_ok=True);name=self.g['id']+('-authored-lod' if self.lod else '')
  if (out/(name+'.glb')).exists():raise ValueError('Do not overwrite prior raw/evidence; select a new run directory')
  metadata={'geometry_revision':'geometry-v2','baseline_rejected_raw_sha256':'094f7d5a944cfe936c2aceaf8f9b11cddfd7c1af3da622d806ed126a77915051','source_freeze_sha256':sha(freeze_path),'authored_lod':self.lod,'id':self.g['id'],'name':'Pao Yue-Kong Library — 2021 appearance reconstruction','appearance_epoch':'2021','height_m_estimate':self.e['overall_height_m'],'height_is_measured':False,'source_geometry_sha256':sha(HERE/'geometry-input.json'),'calibration_sha256':sha(HERE/'calibration.json'),'source_building_id':self.g['source']['overture_id'],'source_osm_record':'w279302450@5','neighbor_information_wing_375_retained':True,'photos_embedded':False,'reconstruction_limits':self.c['limits'],'lod_protected':self.c['lod_protection'],'copyright':'Geometry MIT; source owner map OpenStreetMap contributors / Overture ODbL-1.0; no private reference images included.'}
  report=self.b.save(out/(name+'.glb'),metadata)
  if report['bytes']>=45_000_000:raise ValueError('Raw exceeds requested45MB engineering budget; do not release')
  write(out/(name+'.roles.json'),{'schema':'pao-yue-kong-library-actual-generated-roles-v1','raw':{'file':name+'.glb','bytes':report['bytes'],'sha256':report['sha256']},'part_count':len(self.semantic),'parts':self.semantic,'openings_design_records':self.openings,'support_design_records':self.contacts,'facade_schedule':self.facades,'not_independent_geometry_acceptance':True,'native_and_browser_pending':True})
  write(out/(name+'.metadata.json'),{'schema':'library-author-generated-model-metadata-v1','id':self.g['id'],'macro':self.g['source']['owner_macro_id'],'raw':{'file':name+'.glb','bytes':report['bytes'],'sha256':report['sha256']},'source_freeze_sha256':sha(freeze_path),'source_geometry_sha256':sha(HERE/'geometry-input.json'),'height_estimate_m':self.e['overall_height_m'],'height_is_measured':False,'ground_base_m':0,'actual_bounds_glb':report['bounds_glb'],'authored_lod':self.lod,'independent_acceptance_pending':True,'native_visual_pending':True,'browser_pending':True})
  print(json.dumps({k:report[k] for k in ['file','bytes','sha256','triangles','parts','bounds_glb']}))

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);ap.add_argument('--lod',action='store_true');args=ap.parse_args();Library(args.lod).build().save(args.out)
