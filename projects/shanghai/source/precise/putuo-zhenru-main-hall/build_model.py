#!/usr/bin/env python3
"""Zhenru main hall exterior in local metres; root executes actual raw generation.

Source owner geometry is unchanged. Square core, roof curves and ridge height
are explicitly estimated; published shaft dimensions are not a common survey.
The background pagoda is deliberately absent from this single-building mesh.
"""
from pathlib import Path
from collections import Counter
import argparse, hashlib, json, math, sys
import numpy as np
from shapely.geometry import Polygon, LineString, box as rect
from shapely.ops import unary_union
from shapely import constrained_delaunay_triangles, set_precision
from shapely.geometry.polygon import orient
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'common'))
from photo_architecture import Builder, Facade, pieces

P={
 'aged dark timber':{'color':[.145,.115,.083],'roughness':.87},
 'worn timber edge':{'color':[.24,.195,.137],'roughness':.88},
 'door timber':{'color':[.27,.20,.125],'roughness':.84},
 'wood end grain':{'color':[.115,.095,.073],'roughness':.93},
 'white lime infill':{'color':[.72,.715,.66],'roughness':.94},
 'grey lower plaster':{'color':[.32,.34,.34],'roughness':.95},
 'stone plinth':{'color':[.40,.405,.38],'roughness':.94},
 'worn stone edge':{'color':[.48,.47,.425],'roughness':.9},
 'stone joint':{'color':[.255,.265,.25],'roughness':.96},
 'roof underlayer':{'color':[.145,.15,.132],'roughness':.97},
 'tile 0':{'color':[.255,.263,.238],'roughness':.94},
 'tile 1':{'color':[.235,.246,.228],'roughness':.95},
 'tile 2':{'color':[.275,.28,.25],'roughness':.93},
 'ridge ceramic':{'color':[.34,.345,.31],'roughness':.9},
 'ridge shallow relief':{'color':[.39,.395,.36],'roughness':.88},
 'tile bedding':{'color':[.24,.25,.225],'roughness':.98},
 'dark iron':{'color':[.12,.13,.12],'roughness':.68,'metallic':.35},
 'plaque blue grey':{'color':[.17,.215,.215],'roughness':.85},
 'plaque worn gilt border':{'color':[.47,.385,.20],'roughness':.74,'metallic':.15},
}

def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,data):p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')

def flame_profile(width,bottom,top):
 """Observed flame/lotus-headed straight-lattice opening, not a round arch."""
 shoulder=bottom+(top-bottom)*.74
 curve=[(-.5,0),(-.5,.72),(-.43,.80),(-.31,.84),(-.23,.87),(-.16,.94),(-.08,.95),(0,1),(.08,.95),(.16,.94),(.23,.87),(.31,.84),(.43,.80),(.5,.72),(.5,0)]
 return orient(Polygon([(x*width,bottom+y*(top-bottom)) for x,y in curve]),sign=1)

class Hall:
 def __init__(self):
  self.g=json.loads((HERE/'geometry-input.json').read_text());self.c=json.loads((HERE/'calibration.json').read_text())
  assert self.g['id']=='putuo-zhenru-main-hall' and sha(HERE/'geometry-input.json')==self.c['source_geometry_sha256']
  self.e=self.c['estimated'];self.o=self.c['official_constraints'];self.b=Builder(P)
  self.half=self.e['core_width_m']/2;self.floor=self.e['floor_z_m'];self.hw=self.e['roof_half_width_m'];self.hd=self.e['roof_half_depth_m'];self.gg=self.e['gable_half_length_m'];self.br=self.e['gable_break_run_m'];self.R=self.e['ridge_surface_z_m'];self.E=self.e['eave_surface_center_z_m']
  s1=self.e['roof_at_inner_column_y_m']/self.hd;s2=self.half/self.hd
  self.roof_poly=np.linalg.solve(np.array([[s1,s1*s1,s1**3],[s2,s2*s2,s2**3],[1,1,1]]),np.array([self.R-self.e['roof_at_inner_column_surface_z_m'],self.R-self.e['roof_at_outer_column_surface_z_m'],self.R-self.E]))
  slopes=[self.roof_poly@[1,2*s,3*s*s] for s in np.linspace(0,1,101)]
  assert min(slopes)>0,'Central roof must fall outward without a trough'
  self.parts_notes=[];self.apertures=[];self.tile_records=[];self.support_records=[];self.column_records=[]

 def shell(self,vertices,top_faces,thickness,mat,label):
  top=np.asarray(vertices,float);tris=[]
  for face in top_faces:
   for k in range(1,len(face)-1):
    tri=[face[0],face[k],face[k+1]];a,b,c=top[tri];normal=np.cross(b-a,c-a)
    if normal[2]<0:tri.reverse()
    if abs(normal[2])<1e-10:raise ValueError('Degenerate roof parameter cell '+label)
    tris.append(tuple(tri))
  n=len(top);vs=np.vstack([top,top-[0,0,thickness]])
  counts=Counter(tuple(sorted((a,b))) for f in tris for a,b in zip(f,f[1:]+f[:1]))
  fs=tris+[tuple(x+n for x in reversed(f)) for f in tris]
  for f in tris:
   for a,b in zip(f,f[1:]+f[:1]):
    if counts[tuple(sorted((a,b)))]==1:fs.append((b,a,a+n,b+n))
  self.b.add(vs,fs,mat,label)

 def profile_z(self,t):return self.R-float(self.roof_poly@[t,t*t,t*t*t])

 def point(self,field,s,t):
  """Four roof patches: front/back main pitches, east/west lower hips."""
  u=2*s-1
  if field in (0,1):
   y=self.hd*t;w=self.gg if y<=self.br else self.gg+(self.hw-self.gg)*(y-self.br)/(self.hd-self.br)
   z=self.profile_z(t)+self.e['eave_corner_lift_m']*t**3*abs(u)**8
   return np.array([u*w,(-1 if field==0 else 1)*y,z])
  x=self.gg+(self.hw-self.gg)*t;w=self.br+(self.hd-self.br)*t
  tt=w/self.hd;z=self.profile_z(tt)+self.e['eave_corner_lift_m']*tt**3*abs(u)**8
  return np.array([(1 if field==2 else -1)*x,u*w,z])

 def roof_z(self,x,y):
  ax,ay=abs(x),abs(y)
  if ax<=self.gg or ay>=self.br+(self.hd-self.br)*(ax-self.gg)/(self.hw-self.gg):
   t=ay/self.hd;w=self.gg if ay<=self.br else self.gg+(self.hw-self.gg)*(ay-self.br)/(self.hd-self.br)
   return float(self.point(0,(x/w+1)/2,t)[2])
  t=(ax-self.gg)/(self.hw-self.gg);w=self.br+(self.hd-self.br)*t
  return float(self.point(2,(y/w+1)/2,t)[2])

 def facade(self,which):
  h=self.half
  corners=[[-h,-h],[h,-h],[h,h],[-h,h]]
  return Facade(self.b,corners[which],corners[(which+1)%4],['south','east','north','west'][which])

 def column(self,x,y,inner,index):
  height=self.o['inner_column_shaft_height_m' if inner else 'eave_column_shaft_height_m'];radius=self.o['inner_column_diameter_m' if inner else 'eave_column_diameter_m']/2
  vector=np.array([x,y],float);corner=abs(abs(x)-self.half)<1e-6 and abs(abs(y)-self.half)<1e-6
  if corner:lean=np.zeros(2);scope='Corner kept vertical; no unsupported all-column radial lean'
  elif inner:lean=-vector/np.linalg.norm(vector)*self.o['central_bay_inner_column_lean_m'];scope='Central four, published magnitude with inferred inward orientation'
  else:
   axis=np.argmax(np.abs(vector));lean=np.zeros(2);lean[axis]=-np.sign(vector[axis])*self.o['central_bay_eave_column_lean_m'];scope='Central-bay eave post, published magnitude with inferred inward facade normal'
  z0=self.floor+.08;z1=z0+height;profile=[(0,radius*.98),(.04,radius),(height*.22,radius*1.035),(height*.72,radius*.96),(height,radius*.89)]
  vs=[];ns=16
  for z,r in profile:
   q=np.array([x,y])+lean*(z/height)
   vs.extend([q[0]+r*math.cos(a*math.tau/ns),q[1]+r*math.sin(a*math.tau/ns),z0+z] for a in range(ns))
  fs=[tuple(reversed(range(ns))),tuple((len(profile)-1)*ns+j for j in range(ns))]
  for row in range(len(profile)-1):
   for j in range(ns):fs.append((row*ns+j,row*ns+(j+1)%ns,(row+1)*ns+(j+1)%ns,(row+1)*ns+j))
  self.b.add(vs,fs,'aged dark timber',f'frame/column-{index}')
  self.b.lathe((x,y),[(self.floor-.015,radius*1.45),(self.floor+.03,radius*1.55),(z0+.015,radius*1.20)],'stone plinth',16,f'frame/stone-base-{index}')
  self.column_records.append({'index':index,'type':'inner' if inner else 'eave','base_local':[x,y,z0],'top_local':[x+lean[0],y+lean[1],z1],'nominal_shaft_height_m':height,'nominal_diameter_m':radius*2,'lean_application':scope})

 def timber_arm(self,f,u,d,z,halfspan,thick,depth,label,radial=False):
  xs=np.linspace(-halfspan,halfspan,9);low=[(x,z+.105*(abs(x)/halfspan)**2) for x in xs];high=[(x,z+.105*(abs(x)/halfspan)**2+thick) for x in xs[::-1]]
  mapper=(lambda x,zz,dd:f.point(u-dd,zz,d+x)) if radial else (lambda x,zz,dd:f.point(u+x,zz,d+dd))
  self.b.prism(Polygon(low+high),-depth/2,depth/2,mapper,'aged dark timber',label)

 def roof_bearing_saddle(self,f,u,base,label):
  # Closed support with an actual sloping upper face. The full footprint is
  # sampled, so a flat cap cannot pierce the descending ceramic roof.
  n=self.c['support_revision']['saddle_grid_stations'];top=[]
  for d in np.linspace(-.10,.22,n):
   for x in np.linspace(u-.16,u+.16,n):
    p=f.point(x,0,float(d));p[2]=self.roof_z(*p[:2])-self.c['support_revision']['saddle_top_below_roof_surface_m'];top.append(p)
  top=np.asarray(top);assert top[:,2].min()>base+.02
  bottom=top.copy();bottom[:,2]=base;vertices=np.vstack([top,bottom]);count=len(top);faces=[]
  for j in range(n-1):
   for i in range(n-1):
    q=(j*n+i,j*n+i+1,(j+1)*n+i+1,(j+1)*n+i)
    if np.cross(top[q[1]]-top[q[0]],top[q[2]]-top[q[0]])[2]<0:q=tuple(reversed(q))
    faces.append(q);faces.append(tuple(k+count for k in reversed(q)))
  edges=Counter(tuple(sorted((a,b))) for face in faces if max(face)<count for a,b in zip(face,face[1:]+face[:1]))
  for face in list(faces):
   if max(face)>=count:continue
   for a,b in zip(face,face[1:]+face[:1]):
    if edges[tuple(sorted((a,b)))]==1:faces.append((b,a,a+count,b+count))
  self.positive_add(vertices,faces,'wood end grain',f.label+'/'+label+'/roof-bearing-saddle')
  return {'base_z_m':base,'top_range_m':[float(top[:,2].min()),float(top[:,2].max())],'footprint_local':top[[0,n-1,n*n-1,n*(n-1)],:2].tolist(),'sampled_top_vertices':len(top)}

 def bracket(self,f,u,label):
  center=f.point(u,0,.04);roof=self.roof_z(*center[:2])-.10;shaft=self.floor+.08+4.28
  start=len(self.b.parts)
  for k in range(3):
   z=shaft+.06+k*.105;d=.03+k*.07
   self.timber_arm(f,u,d,z,.26+k*.10,.10,.15,label+f'/lateral{k}')
   self.timber_arm(f,u,d+.05,z+.025,.18+k*.05,.095,.14,label+f'/radial{k}',True)
  # Translate the connected stack as a whole; it remains joined to the deep
  # eave tie/column head. Small outer arms do not need to protrude through tiles.
  target=self.c['support_revision']['arm_roof_clearance_target_m']
  minimum=min(self.roof_z(v[0],v[1])-v[2] for part in self.b.parts[start:] for v in part['vertices'])
  shift=max(0.,target-minimum);assert shift<.55
  for part in self.b.parts[start:]:part['vertices']=[(x,y,z-shift) for x,y,z in part['vertices']]
  base=shaft+.06+2*.105+.025+.095-shift-.025
  saddle=self.roof_bearing_saddle(f,u,base,label)
  self.support_records.append({'kind':'bracket_to_roof','label':label,'point_local':center.tolist(),'roof_under_m':roof,'bearing_top_m':roof+.025,'intentional_embed_m':.025,'arm_stack_downward_shift_m':shift,'arm_roof_clearance_target_m':target,'saddle':saddle,'actual_exported_contact_and_no_protrusion_pending':True})

 def frame(self):
  h=self.half;grid=[-h,-self.e['central_bay_width_m']/2,self.e['central_bay_width_m']/2,h]
  self.b.plan_prism(rect(-h-.26,-h-.26,h+.26,h+.26),0,self.floor,'stone plinth','foundation/continuous-square-plinth')
  self.b.plan_prism(rect(-h-.29,-h-.29,h+.29,h+.29),self.floor-.085,self.floor+.015,'worn stone edge','foundation/stone-coping')
  # Three real treads, within this hall's source footprint. Height is estimated.
  for i in range(3):
   extent=1.44-i*.42;top=(i+1)*self.floor/3
   self.b.plan_prism(rect(-3.22,-h-extent,3.22,-h+.08),0,top,'stone plinth',f'foundation/front-tread-{i+1}')
   self.b.box((0,-h-extent+.03,top-.022),(6.48,.07,.045),'worn stone edge',label=f'foundation/tread-nosing-{i+1}')
  for x in [-2.2,0,2.2]:self.b.box((x,-h-.78,self.floor/3+.003),(.008,1.24,.006),'stone joint',label='foundation/tread-bounded-joint')
  for i,(x,y) in enumerate(( (x,y) for y in grid for x in grid)):
   self.column(x,y,abs(x)<h-.1 and abs(y)<h-.1,i)
  shaft=self.floor+.08+4.28
  for y in [-h,h]:
   self.b.box((0,y,shaft+.08),(2*h+.22,.28,.27),'aged dark timber',label='frame/east-west-tie')
  for x in [-h,h]:
   self.b.box((x,0,shaft+.10),(.26,2*h+.22,.25),'aged dark timber',label='frame/north-south-tie')
  # Four upper ties terminate at inner columns, rather than extending a tall
  # beam through the descending external roof on the outer faces.
  inner=self.e['central_bay_width_m']/2
  for axis in [0,1]:
   for side in [-1,1]:
    center=[0,0,self.floor+.08+6.45+.08];center[1-axis]=side*inner;size=[.26,.26,.26];size[axis]=2*inner+.26
    self.b.box(center,size,'aged dark timber',label='frame/inner-column-tie')
  for edge in range(4):
   f=self.facade(edge)
   f.box(0,shaft+.035,2*h+.24,.27,.27,.01,'aged dark timber','eave-tie')
   for u in [-h,-inner,0,inner,h]:self.bracket(f,u,f'frame/e{edge}/dougong{u:.3f}')
   f.box(0,4.44,2*h,.15,.14,.02,'worn timber edge','upper-wall-cap')

 def lattice_door(self,f,index,hinge_u,hinge_d,angle,width,bottom,top,label):
  angle=math.radians(angle);along=f.t*math.cos(angle)+f.n*math.sin(angle);normal=np.cross(along,[0,0,1]);origin=f.point(hinge_u,0,hinge_d)
  def mapper(u,z,d):return origin+along*u+np.array([0,0,z])+normal*d
  height=top-bottom;outer=rect(0,bottom,width,top);inner=rect(.065,bottom+.64,width-.065,top-.11)
  bars=[rect(.065,bottom+.64,width-.065,bottom+.71)]
  for k in range(1,5):
   x=.065+(width-.13)*k/5;bars.append(rect(x-.013,bottom+.64,x+.013,top-.11))
  for k in range(1,15):
   z=bottom+.64+(height-.75)*k/15;bars.append(rect(.065,z-.012,width-.065,z+.012))
  cut=inner.difference(unary_union(bars));panel=outer.difference(cut)
  self.b.prism(panel,-.035,.035,mapper,'door timber',label+f'/leaf-{index}')
  inset=rect(.10,bottom+.10,width-.10,bottom+.53)
  self.b.prism(inset,.034,.049,mapper,'worn timber edge',label+f'/leaf-{index}-lower-panel')
  self.b.box(mapper(width*.78,bottom+.95,.06),(.04,.04,.12),'dark iron',basis=[along,normal,[0,0,1]],label=label+f'/leaf-{index}-handle')
  self.apertures.append({'kind':'door_leaf_lattice','label':label+f'/leaf-{index}','hinge_local':origin.tolist(),'width_m':width,'angle_degrees':math.degrees(angle),'configuration_measured':False})

 def walls(self):
  h=self.half;door=rect(-self.e['front_door_width_m']/2,self.e['door_bottom_z_m'],self.e['front_door_width_m']/2,self.e['door_top_z_m'])
  windows=[flame_profile(self.e['flame_window_width_m'],self.e['flame_window_bottom_z_m'],self.e['flame_window_top_z_m'])]
  from shapely.affinity import translate
  windows=[translate(windows[0],xoff=x) for x in self.e['flame_window_centres_u_m']]
  for edge in range(4):
   f=self.facade(edge);is_front=edge==0;is_back=edge==2;holes=[door]+windows if is_front else [door] if is_back else []
   material='aged dark timber' if is_front else 'white lime infill'
   f.wall(self.floor,self.e['wall_top_z_m'],holes,.25,material)
   # Lower grey skirting is physically cut by the same central opening.
   lower=rect(-h,self.floor,h,1.23)
   if holes:lower=lower.difference(unary_union(holes))
   f.prism(lower,.004,.038,'grey lower plaster','lower-plinth-render')
   for u in [-h,-2.55,2.55,h]:f.box(u,2.48,.19,4.01,.18,.04,'aged dark timber','wall-post-face')
   for z in [3.96,4.20,4.39]:f.box(0,z,2*h,.07,.07,.04,'worn timber edge','restrained-upper-weatherboard')
   if is_front:
    for k,w in enumerate(windows):
     # The contour ring and bars are one open solid profile, with real gaps.
     ring=w.buffer(.055,join_style='mitre').difference(w.buffer(-.035,join_style='mitre'))
     x0,z0,x1,z1=w.bounds;bars=[]
     for x in np.arange(x0+.12,x1,.135):bars.append(rect(x-.023,z0,x+.023,z1).intersection(w))
     grille=set_precision(unary_union([ring,*bars]),.00001)
     f.prism(grille,-.035,.055,'worn timber edge',f'flame-window{k}/open-contour-and-straight-bars')
     f.box((x0+x1)/2,z0-.045,x1-x0+.20,.09,.28,.04,'worn timber edge',f'flame-window{k}/sill')
     self.apertures.append({'kind':'through_flame_window','edge':edge,'center_u':(x0+x1)/2,'width_m':x1-x0,'bottom_z_m':z0,'top_z_m':z1,'wall_only_ray_point':f.point((x0+x1)/2,z0+(z1-z0)*.4,.15).tolist(),'inward_direction':(-f.n).tolist()})
   if is_front or is_back:
    f.prism(door.buffer(.10,join_style='mitre').difference(door),-.025,.075,'worn timber edge','six-leaf-door-jamb-frame')
    width=self.e['front_door_width_m']/6-.014;bottom=self.e['door_bottom_z_m'];top=self.e['door_top_z_m']
    if is_front:
     # Reproducible partially folded banks; occlusion prevents exact hinge solve.
     arrangements=[(-2.5,.02,0),(-2.5+width,.02,78),(-2.5+width+width*math.cos(math.radians(78)),.02+width*math.sin(math.radians(78)),-65)]
     for k,(u,d,angle) in enumerate(arrangements):
      self.lattice_door(f,k,u,d,angle,width,bottom,top,'south/six-leaf-entrance')
      self.lattice_door(f,k+3,-u,d,180-angle,width,bottom,top,'south/six-leaf-entrance')
    else:
     for k in range(6):self.lattice_door(f,k,-2.5+k*self.e['front_door_width_m']/6,.025,0,width,bottom,top,'north/text-supported-six-leaf-entrance')
    self.apertures.append({'kind':'through_door_wall','edge':edge,'center_u':0,'width_m':5,'bottom_z_m':bottom,'top_z_m':top,'wall_only_ray_point':f.point(0,1.6,.18).tolist(),'inward_direction':(-f.n).tolist(),'door_configuration':'front estimated folded banks' if is_front else 'north closed6leaves,text+historicalrear uncertainty'})
  # The 2025 front shows a small hanging framed plaque. Its fine lettering is
  # not resolved by the selected image: no fabricated modern inscription.
  f=self.facade(0);tilt=math.radians(14)
  def plaque_mapper(u,z,d):
   return f.point(u,4.08+z*math.cos(tilt)+d*math.sin(tilt),.32-z*math.sin(tilt)+d*math.cos(tilt))
  self.b.prism(rect(-.385,-.47,.385,.47),-.035,.035,plaque_mapper,'plaque blue grey','south/hanging-plaque/estimated-board')
  border=rect(-.385,-.47,.385,.47).difference(rect(-.335,-.415,.335,.415))
  self.b.prism(border,.034,.055,plaque_mapper,'plaque worn gilt border','south/hanging-plaque/border')
  for side in [-1,1]:
   for z in np.linspace(-.33,.33,9):
    self.b.prism(Polygon([(side*.355,z-.024),(side*.373,z),(side*.355,z+.024),(side*.337,z)]),.054,.064,plaque_mapper,'plaque worn gilt border','south/hanging-plaque/estimated-border-motif')
  self.parts_notes.append({'feature':'2025 hanging front plaque','scope':'Board and border are photo-relative estimates; the selected photo does not resolve all characters, so modern lettering is not invented.'})
  # Gable infill is an independently closed timber triangle following roof edges.
  for side in [-1,1]:
   n=32;bottom=[];top=[]
   for y in np.linspace(-self.br,self.br,n+1):
    s=(y/self.br+1)/2;bottom.append((y,float(self.point(2,s,0)[2]-.12)))
    top.append((y,self.roof_z(side*self.gg,y)-.10))
   poly=Polygon(bottom+top[::-1]);poly=set_precision(poly,.000001)
   # Avoid a zero-area join right at each hip shoulder.
   poly=poly.buffer(-.012,join_style='mitre')
   mapper=(lambda u,z,d,side=side:np.array([side*self.gg+side*d,side*u,z]))
   self.b.prism(poly,-.10,.02,mapper,'aged dark timber',f'gable/{side}/closed-infill')
   for y in np.arange(-self.br+.25,self.br,.28):
    z0=float(self.point(2,(y/self.br+1)/2,0)[2]);z1=self.roof_z(side*self.gg,y)-.18
    if z1-z0>.15:self.b.box((side*(self.gg+.045),y,(z0+z1)/2),(.05,.05,z1-z0),'worn timber edge',label=f'gable/{side}/vertical-louver-relief')

 def grid_surface(self,field,ss,ts,offset=0):
  vs=[self.point(field,float(s),float(t))+[0,0,offset] for t in ts for s in ss];n=len(ss)
  faces=[(j*n+i,j*n+i+1,(j+1)*n+i+1,(j+1)*n+i) for j in range(len(ts)-1) for i in range(n-1)]
  return vs,faces

 def roof(self):
  for field in range(4):
   ts=sorted({*[float(t) for t in np.linspace(0,1,49)],self.br/self.hd}) if field<2 else np.linspace(0,1,25)
   vs,fs=self.grid_surface(field,np.linspace(0,1,49),ts)
   self.shell(vs,fs,self.e['roof_underlayer_thickness_m'],'roof underlayer',f'roof/field{field}/continuous-substrate')
   midrun=np.linalg.norm(self.point(field,.5,1)-self.point(field,.5,0));rows=max(8,int(round(midrun/self.e['tile_course_run_m'])))
   width=np.linalg.norm(self.point(field,1,.65)-self.point(field,0,.65));cols=max(20,int(round(width/self.e['tile_pitch_m'])))
   overlap=self.e['tile_course_overlap_fraction'];lift=self.e['tile_course_lift_m'];heel=self.e['tile_heel_raise_m'];skin=self.e['tile_skin_m']
   for row in range(rows):
    t0=row/rows;t1=min(1,(row+1+overlap)/rows)
    # Ceramic bedding at each heel is seated into the real substrate.
    vs,fs=self.grid_surface(field,np.linspace(0,1,max(16,cols//2)),[max(0,t0-.0025),min(1,t0+.006)],.008)
    self.shell(vs,fs,.029,'tile bedding',f'roof/field{field}/heel-bearing-row{row}')
    for col in range(cols):
     for kind in ['pan','cover']:
      if kind=='cover' and col==cols-1:continue
      if kind=='pan':s0,s1=(col+.025)/cols,(col+.975)/cols;ns=3
      else:s0,s1=(col+1-.16)/cols,(col+1+.16)/cols;ns=5
      ss=np.linspace(s0,s1,ns);vs=[]
      for t in [t0,t1]:
       fraction=(t-t0)/((1+overlap)/rows)
       for k,s in enumerate(ss):
        q=k/(ns-1);point=self.point(field,float(s),t)
        profile=self.e['tile_pan_edge_rise_m']*(2*q-1)**2 if kind=='pan' else self.e['tile_cover_arch_m']*math.sin(math.pi*q)
        point[2]+=(heel if kind=='pan' else self.e['tile_cover_base_raise_m'])+profile+lift*fraction;vs.append(point)
      fs=[(i,i+1,ns+i+1,ns+i) for i in range(ns-1)];mix=(field*79+row*13+col*23)%3
      label=f'roof/field{field}/{kind}/c{col}/r{row}'
      self.shell(vs,fs,skin,f'tile {mix}',label)
      if kind=='cover':
       # Narrow hidden grey mortar seat joins substrate and cover crest. This
       # is a support assembly, not an unsupported hollow decorative tube.
       center=(col+1)/cols;foot=.075/cols;seat=[]
       for t in [t0,t1]:
        fraction=(t-t0)/((1+overlap)/rows);base=self.point(field,center,t)
        left=self.point(field,center-foot,t);right=self.point(field,center+foot,t)
        left[2]-=.018;right[2]-=.018;base[2]+=self.e['tile_cover_base_raise_m']+self.e['tile_cover_arch_m']+lift*fraction-skin+.006
        seat.extend([left,base,right])
       faces=[(0,2,1),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5)]
       self.positive_add(seat,faces,'tile bedding',label+'/hidden-seated-bedding')
   for col in range(cols):
    s=(col+.5)/cols;end=self.point(field,s,1)+[0,0,heel+lift*.8];direction=self.point(field,s,1)-self.point(field,s,.995);direction/=np.linalg.norm(direction)
    self.b.tube([end-direction*.035,end+direction*.028],.057,f'tile {col%3}',10,f'roof/field{field}/round-eave-end{col}')
    points=[self.point(field,s,t)-[0,0,.14] for t in np.linspace(.03,1.012,9)]
    self.b.tube(points,.042,'aged dark timber',8,f'roof/field{field}/rafter{col}')
   self.tile_records.append({'field':field,'rows':rows,'columns':cols,'course_overlap_fraction':overlap,'pan_skin_m':skin,'heel_raise_m':heel,'course_lift_m':lift,'nominal_same-profile_lap_gap_m':lift/(1+overlap)-skin,'substrate_thickness_m':.10,'each_pan_has_heel_support':True,'each_cover_has_hidden_mortar_seat':True,'actual_exported_contact_check_pending':True})

 def positive_add(self,vs,faces,mat,label):
  vertices=np.asarray(vs,float);triangles=[(f[0],f[k],f[k+1]) for f in faces for k in range(1,len(f)-1)]
  volume=sum(float(np.dot(vertices[a],np.cross(vertices[b],vertices[c]))) for a,b,c in triangles)/6
  if volume<0:faces=[tuple(reversed(f)) for f in faces]
  self.b.add(vertices,faces,mat,label)

 def ridge_seat(self,points,halfwidth,height,label,gable_boundary=False):
  """A thick solid ridge profile; lower feet follow the actual local substrate."""
  points=np.asarray(points,float);vs=[]
  for i,p in enumerate(points):
   tangent=points[min(i+1,len(points)-1),:2]-points[max(0,i-1),:2];tangent/=np.linalg.norm(tangent);n=np.array([-tangent[1],tangent[0]])
   left=p[:2]-n*halfwidth;right=p[:2]+n*halfwidth
   # A vertical gable separates the high main pitch from the lower hip.
   # Descending gable ridges may bear on the high edge, not fill that wall
   # as a giant ceramic curtain down to the separate hip surface.
   def foot_z(xy):
    if gable_boundary:return self.roof_z(max(-self.gg,min(self.gg,float(xy[0]))),float(xy[1]))-.025
    return self.roof_z(*xy)-.025
   zl=foot_z(left);zr=foot_z(right)
   vs.extend([[*left,zl],[*right,zr],[*(p[:2]+n*halfwidth*.40),p[2]+height-.04],[*p[:2],p[2]+height],[*(p[:2]-n*halfwidth*.40),p[2]+height-.04]])
  ns=5;faces=[tuple(reversed(range(ns))),tuple((len(points)-1)*ns+i for i in range(ns))]
  for k in range(len(points)-1):
   for j in range(ns):faces.append((k*ns+j,k*ns+(j+1)%ns,(k+1)*ns+(j+1)%ns,(k+1)*ns+j))
  self.positive_add(vs,faces,'ridge ceramic',label)
  self.support_records.append({'kind':'solid_roof_ridge','label':label,'sections':len(points),'foot_embed_m':.025,'crest_height_above_roof_m':height,'scope':'Continuous seats, finite exported contacts still require independent audit'})

 def chiwen(self,side):
  x=side*self.gg;z=self.R+.25
  # Photographic silhouette with an outward curling tail, thick ceramic body,
  # mouth notch, eyebrow and restrained raised scales. It is not an exact scan.
  outline=Polygon([(-.42,0),(.32,0),(.40,.38),(.56,.78),(.55,1.16),(.34,1.46),(.03,1.53),(.11,1.31),(.10,1.13),(-.05,.88),(-.19,.64),(-.42,.46),(-.55,.28),(-.50,.12)])
  scale=self.e['chiwen_height_m']/1.53
  from shapely.affinity import scale as poly_scale
  outline=poly_scale(outline,xfact=scale,yfact=scale,origin=(0,0))
  # Mouth cutout is an actual silhouette notch, not a painted dark triangle.
  notch=Polygon([(-.55,.28),(-.22,.27),(-.13,.35),(-.25,.42),(-.52,.43)])
  notch=poly_scale(notch,xfact=scale,yfact=scale,origin=(0,0));outline=outline.difference(notch)
  mapper=lambda u,zz,d:np.array([x+side*u,-side*d,z+zz])
  self.b.prism(outline,-.21,.21,mapper,'ridge ceramic',f'ornament/chiwen-{side}/curved-ceramic-body')
  for d in [-.218,.218]:
   points=[mapper(u*scale,zz*scale,d) for u,zz in [(-.28,.52),(-.12,.62),(.04,.74),(.18,1.0),(.21,1.24)]]
   self.b.tube(points,.024,'ridge shallow relief',6,f'ornament/chiwen-{side}/raised-curl-line')
   eye=mapper(-.28*scale,.44*scale,d)
   self.b.tube([eye+np.array([0,-.012,0]),eye+np.array([0,.012,0])],.041,'ridge shallow relief',10,f'ornament/chiwen-{side}/eye-relief')
  for k in range(5):
   zz=.48+k*.13;u=.18+min(k,3)*.045
   self.b.tube([mapper(u*scale,zz*scale,-.17),mapper((u+.12)*scale,(zz+.055)*scale,0),mapper(u*scale,zz*scale,.17)],.027,'ridge shallow relief',6,f'ornament/chiwen-{side}/restrained-scale-{k}')

 def ridges(self):
  # Main ridge is a broad ceramic band, without a central finial.
  self.b.box((0,0,self.R+.17),(2*self.gg+.08,.40,.40),'ridge ceramic',label='ridge/continuous-main-ridge')
  self.b.box((0,0,self.R+.39),(2*self.gg+.12,.47,.09),'ridge shallow relief',label='ridge/main-upper-cap')
  for side in [-1,1]:
   self.b.box((0,side*.215,self.R+.15),(2*self.gg-.25,.025,.19),'ridge shallow relief',label='ridge/long-recessed-side-band')
   for x in np.arange(-self.gg+.32,self.gg,.32):self.b.box((x,side*.235,self.R+.16),(.012,.025,.16),'ridge ceramic',label='ridge/restrained-block-joint')
  for sx in [-1,1]:
   self.chiwen(sx)
   for sy in [-1,1]:
    upper=[np.array([sx*self.gg,sy*y,self.roof_z(sx*self.gg,sy*y)]) for y in np.linspace(0,self.br,32)]
    self.ridge_seat(upper,.16,.16,f'ridge/descending-gable-{sx}-{sy}',gable_boundary=True)
    hip=[self.point(0 if sy<0 else 1,0 if sx<0 else 1,t) for t in np.linspace(self.br/self.hd,1,28)]
    self.ridge_seat(hip,.14,.18,f'ridge/continuous-hip-{sx}-{sy}')
    # Small observed corner ornaments; simplified silhouettes, not invented text.
    for k,t in enumerate([.77,.88]):
     q=self.point(0 if sy<0 else 1,0 if sx<0 else 1,t);self.b.lathe(q[:2],[(q[2]+.12,.10),(q[2]+.18,.14),(q[2]+.31,.09),(q[2]+.39,.05)],'ridge ceramic',10,f'ornament/small-hip-finial-{sx}-{sy}-{k}')

 def rotate_to_enu(self):
  a=math.radians(self.c['orientation']['model_x_axis_degrees_ccw_from_east']);matrix=np.array([[math.cos(a),-math.sin(a),0],[math.sin(a),math.cos(a),0],[0,0,1.]])
  for p in self.b.parts:p['vertices']=(np.asarray(p['vertices'])@matrix.T).tolist()
  for r in self.apertures:
   for key in ['wall_only_ray_point','inward_direction','hinge_local']:
    if key in r:r[key.replace('_local','_enu') if key.endswith('_local') else key+'_enu']=(matrix@r[key]).tolist()
  return matrix

 def audit(self):
  failures=[];records=[];allpoints=[]
  for part in self.b.parts:
   v=np.asarray(part['vertices'],dtype=np.float32).astype(float);t=np.asarray(part['triangles'],dtype=np.int64);allpoints.append(v)
   cross=np.cross(v[t[:,1]]-v[t[:,0]],v[t[:,2]]-v[t[:,0]])
   _,inv=np.unique(v,axis=0,return_inverse=True);weld=inv[t]
   counts=Counter(tuple(sorted((int(a),int(b)))) for tri in weld for a,b in zip(tri,np.roll(tri,-1)))
   volume=float(np.einsum('ij,ij->',v[t[:,0]],np.cross(v[t[:,1]],v[t[:,2]]))/6);bad=sum(n!=2 for n in counts.values());zero=int(np.sum(np.linalg.norm(cross,axis=1)<1e-9))
   if bad or zero or volume<=0:failures.append({'label':part['label'],'nonmanifold_edges':bad,'zero_triangles':zero,'signed_volume_m3':volume})
   records.append({'label':part['label'],'material':part['material'],'triangles':len(t),'volume_m3':volume})
  allpoints=np.concatenate(allpoints)
  return {'schema':'zhenru-float32-geometry-v10','passed':not failures,'failures':failures,'source_geometry_sha256':sha(HERE/'geometry-input.json'),'calibration_sha256':sha(HERE/'calibration.json'),'parts':len(records),'triangles':sum(r['triangles'] for r in records),'part_records':records,'bbox_enu_m':[allpoints.min(0).tolist(),allpoints.max(0).tolist()],'column_records':self.column_records,'openings':self.apertures,'roof_parameters':{'polynomial_drop_coefficients':self.roof_poly.tolist(),'patches':4,'type':'single-eave hip-gable roof','central_finial':False},'roof_tile_records':self.tile_records,'support_records':self.support_records,'feature_notes':self.parts_notes,'topology_scope':'Exact FLOAT32 per-part welding; does not prove whole-assembly collision freedom','actual_exported_roof_contact_passed':False,'native_visual_passed':False,'browser_passed':False,'height_measured':False}

 def build(self,output):
  if output.exists():raise ValueError('Use a new output directory; prior outputs are immutable')
  self.frame();self.walls();self.roof();self.ridges();self.rotate_to_enu();qa=self.audit();output.mkdir(parents=True)
  write(output/'geometry-report.json',qa)
  if not qa['passed']:raise ValueError('Geometry audit failed: '+str(qa['failures'][:15]))
  photos=json.loads((HERE/'references/photo-register.json').read_text())['photos'];height=qa['bbox_enu_m'][1][2]
  copyright='Model CC-BY-SA-4.0; code MIT; references: ScareCriterion12 CC0 and CC-BY-SA-4.0, Ukmist CC-BY-SA-3.0, Haier7917 CC-BY-SA-3.0; source footprint © OpenStreetMap contributors via Overture Maps Foundation ODbL-1.0; no photograph pixels embedded.'
  meta={'id':self.g['id'],'name':'真如寺大殿（正殿）','model_revision':self.c['model_revision'],'copyright':copyright,'license':'CC-BY-SA-4.0','source_geometry_sha256':sha(HERE/'geometry-input.json'),'calibration_sha256':sha(HERE/'calibration.json'),'ground_base_m':0,'height_measured':False,'height_estimate_m':height,'height_basis':'Photo-relative roof and nominal published column dimensions, not a surveyed overall height. Neighbor TianwangHall dimensions excluded.','source_boundary':self.g['geometry'],'source_anchor':self.g['anchor'],'embedded_photos':False,'appearance_epoch':self.c['appearance_epoch'],'source_photos':[{'author':p['author'],'license':p['license'],'source':p['description_page'],'sha256':p['sha256'],'embedded_as_texture':False} for p in photos],'uncertainty':self.c['uncertainty']}
  raw=output/'putuo-zhenru-main-hall-raw.glb';self.b.save(raw,meta)
  record={'id':self.g['id'],'raw':{'file':raw.name,'bytes':raw.stat().st_size,'sha256':sha(raw)},'triangles':qa['triangles'],'parts':qa['parts'],'embedded_images':0,'ground_base_m':0,'height_estimate_m':height,'height_measured':False,'geometry_qa_passed':True,'native_visual_passed':False,'browser_passed':False,'source_geometry_sha256':sha(HERE/'geometry-input.json'),'limitations':self.c['uncertainty']}
  write(output/'asset-metadata.json',record);print(json.dumps(record,ensure_ascii=False,indent=2))

if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();Hall().build(a.output)
