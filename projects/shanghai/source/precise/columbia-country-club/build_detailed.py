#!/usr/bin/env python3
"""Photo/plan-informed Club exterior. Metres; generated surfaces, no private pixels.

The low-detail spatial authoring stage is kept in build_model.py. Heights and
registration are drawing-derived estimates, not a measured digital twin.
"""
from pathlib import Path
import argparse,json,math,hashlib,sys
import numpy as np
from shapely.geometry import Polygon,Point,LineString,box as rect
from shapely.ops import unary_union
from shapely.affinity import translate,scale
from shapely.geometry.polygon import orient
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
from build_model import Club as SpatialClub, HERE, sha, write
from photo_architecture import Facade,opening,pieces

class Contours(BasePen):
 def __init__(self,gs):super().__init__(gs);self.paths=[];self.current=[]
 def _moveTo(self,p):self.current=[p]
 def _lineTo(self,p):self.current.append(p)
 def _curveToOne(self,a,b,c):
  p=np.array(self._getCurrentPoint());a=np.array(a);b=np.array(b);c=np.array(c)
  self.current.extend(tuple((1-t)**3*p+3*(1-t)**2*t*a+3*(1-t)*t*t*b+t**3*c) for t in np.linspace(0,1,7)[1:])
 def _qCurveToOne(self,a,b):
  p=np.array(self._getCurrentPoint());a=np.array(a);b=np.array(b)
  self.current.extend(tuple((1-t)**2*p+2*(1-t)*t*a+t*t*b) for t in np.linspace(0,1,7)[1:])
 def _closePath(self):
  if len(self.current)>2:self.paths.append(self.current)
  self.current=[]
 def _endPath(self):self._closePath()

class Club(SpatialClub):
 def __init__(self,lod=False):
  super().__init__();self.lod=lod;self.roof_faces=[];self.roof_edges=[];self.audit=[]
  self.b.palette.update({
   'historic rough stucco':{'color':[.78,.76,.70],'roughness':.96},
   'east addition stucco':{'color':[.88,.87,.83],'roughness':.94},
   'stone trim':{'color':[.54,.51,.44],'roughness':.91},
   'rough sandstone':{'color':[.57,.54,.47],'roughness':.94},
   'glazing':{'color':[.27,.36,.35],'roughness':.20,'metallic':0,'alpha':.42},
   'glass guard':{'color':[.63,.73,.70],'roughness':.12,'metallic':0,'alpha':.20},
   'green ceramic':{'color':[.06,.22,.15],'roughness':.48},
   'dark grey grille':{'color':[.105,.115,.105],'roughness':.91},
   'white letters':{'color':[.91,.91,.86],'roughness':.62},
   'tile light':{'color':[.43,.20,.13],'roughness':.92},
   'tile dark':{'color':[.29,.105,.060],'roughness':.92},
   'aluminium frame':{'color':[.14,.15,.145],'roughness':.42,'metallic':.55},
   'brick floor':{'color':[.34,.20,.135],'roughness':.90},
  })
  self.font=TTFont(HERE/'shop-glyphs.otf');self.gs=self.font.getGlyphSet();self.cmap=self.font.getBestCmap()
 def mark(self,kind,**kw):self.features.append({'kind':kind,**kw})
 def line(self,f,pts,r=.025,mat='aged timber',label='detail'):
  self.b.tube([f.point(*p) for p in pts],r,mat,6 if self.lod else 8,f.label+'/'+label)
 def pane(self,f,u,bottom,w,h,arch,label):
  shape=opening(u,bottom,w,h,arch,12 if self.lod else 24);inner=shape.buffer(-.085,join_style=2)
  # Real cut-through wall, separate recessed transparent glazing and joined frame grid.
  frame='aluminium frame' if 'addition' in label else 'aged timber'
  f.prism(inner,-.22,-.205,'glazing',label+'/glass')
  bars=[];spring=bottom+h-arch;cross=spring
  bars.append(rect(u-.042,bottom,u+.042,bottom+h))
  if w>.90:
   for xx in [u-w*.25,u+w*.25]:bars.append(rect(xx-.016,bottom,xx+.016,cross))
  rows=5 if h<=3.0 else 6
  for j in range(1,rows):
   z=bottom+(cross-bottom)*j/rows;bars.append(rect(u-w/2,z-.018,u+w/2,z+.018))
  if arch:bars.append(rect(u-w/2,cross-.045,u+w/2,cross+.045))
  if arch:
   for ang in [math.pi/4,math.pi/2,math.pi*3/4]:
    line=LineString([(u,spring),(u+w/2*math.cos(ang),spring+arch*math.sin(ang))]).buffer(.022,cap_style=2)
    bars.append(line)
   # Semicircular fanlight ring reads separately from the rectangular door leaves.
   ring=LineString([(u+w*.35*math.cos(a),spring+arch*.70*math.sin(a)) for a in np.linspace(0,math.pi,17)]).buffer(.025)
   bars.append(ring)
  grid=shape.buffer(-.018).difference(inner.difference(unary_union(bars)))
  f.prism(grid,-.19,-.075,frame,label+'/continuous-mullion-fanlight-grid')
  if bottom<1.0:
   f.box(u,bottom+.16,w-.16,.28,.07,-.06,frame,label+'/solid-kick-panel')
   if not self.lod:
    for x in [u-.13,u+.13]:f.box(x,bottom+1.13,.032,.27,.045,-.02,'dark iron',label+'/door-pull')
  f.box(u,bottom-.045,w+.20,.09,.48,.06,'stone trim',label+'/sill')
  self.mark('actual_wall_opening',label=label,facade=f.label,width_m=w,height_m=h,arch_rise_m=arch)
  self.audit.append({'kind':'window_reveal','label':label,'center_principal_enu':f.point(u,bottom+h*.45,0).tolist(),'outward_principal_enu':f.n.tolist(),'width_m':w,'height_m':h})
 def shutters(self,f,u,z,w,h,label):
  for side in [-1,1]:
   c=u+side*(w*.75+.09);sw=w*.46
   f.box(c,z+h/2,sw,h,.09,.075,'aged timber',label+'/open-shutter')
   if not self.lod:
    for x in [-sw*.35,0,sw*.35]:f.box(c+x,z+h/2,.013,h-.08,.013,.126,'stone trim',label+'/plank-seam')
   for zz in [z+.18,z+h-.18]:f.box(c,zz,sw+.04,.06,.025,.14,'dark iron',label+'/shutter-strap')
 def surrounds(self,f,holes,shutter=True):
  for u,z,w,h,r,name in holes:
   if z>=5.7 and 'addition' not in name and shutter:self.shutters(f,u,z,w,h,name)
   if r:
    shp=opening(u,z,w,h,r,20);outer=shp.buffer(.12,join_style=2)
    f.prism(outer.difference(shp),.005,.09,'stone trim',name+'/archivolt')
 def detailed_wall(self,a,b,bottom,top,holes=(),mat='historic rough stucco',label='wall',shutter=True):
  f=self.wall(a,b,bottom,top,holes,mat,label);self.surrounds(f,holes,shutter)
  f.box(0,bottom+.13,f.length,.26,.10,.015,'stone trim','continuous-plinth')
  return f
 def body(self):
  for label,x0,x1,yfront in [('west-wing',74,176,413),('central-hall',176,511,365),('east-original-wing',511,610,413),('east-retained-addition',610,697,413)]:
   mat='east addition stucco' if 'addition' in label else 'historic rough stucco';width=(x1-x0)/12
   if label=='west-wing':front=[(u,.75,1.82,3.85,.91,f'west-ground-arch-{j}') for j,u in enumerate([-2.45,0,2.45])]+[(u,6.2,1.45,2.05,0,f'west-upper-{j}') for j,u in enumerate([-2.35,0,2.35])]
   elif label=='central-hall':
    front=[((x-(x0+x1)/2)/12,5.42 if x==342 else 6.1,1.8 if x==342 else 1.42,2.86 if x==342 else 2.0,.5 if x==342 else 0,f'central-upper-{j}') for j,x in enumerate([197,241,285,342,397,445,489])]
    # Ground hall to southern enclosed arcade: plan has eleven actual paired doors.
    front +=[(u,.75,1.45,3.65,.38,f'main-ground-to-arcade-{j}') for j,u in enumerate(np.linspace(-width/2+1,width/2-1,11))]
   elif label=='east-original-wing':front=[(0,.75,1.95,3.9,.55,'east-ground-curved-door'),(-2.5,2.1,.7,.75,0,'east-small-left'),(2.5,2.1,.7,.75,0,'east-small-right')]+[(u,5.95 if j==1 else 6.2,1.35,2.35 if j==1 else 2.1,.35 if j==1 else 0,f'east-upper-{j}') for j,u in enumerate([-2.3,0,2.3])]
   else:front=[(u,.75,1.45,3.75,.72,f'addition-ground-{j}') for j,u in enumerate([-2.25,0,2.25])]+[(u,6.1,1.35,2.,0,f'addition-upper-{j}') for j,u in enumerate([-2.2,0,2.2])]
   f=self.detailed_wall((x0,yfront),(x1,yfront),.75,9.,front,mat,label+'/south');f.beam(8.85,.18,.15,'stone trim')
   north=[(u,6.25,1.35,1.95,0,label+f'/north-upper-{j}') for j,u in enumerate(np.linspace(-width/2+.9,width/2-.9,max(2,round(width/2.8))))]
   self.detailed_wall((x1,209),(x0,209),.75,9.,north,mat,label+'/north')
   # Exposed side returns: upper-plan openings distinguish long wings from the hall.
   for side,a,b in [('west',(x0,209),(x0,yfront)),('east',(x1,yfront),(x1,209))]:
    external=(label=='west-wing' and side=='west') or ('addition' in label and side=='east')
    terrace_return=(label=='west-wing' and side=='east') or (label=='east-original-wing' and side=='west')
    if external:
     span=(yfront-209)/12;positions=[-span*.34,0,span*.34]
     holes=[(u,z,1.45,2.1,.55 if z<5 else 0,label+f'/{side}-{level}-{j}') for level,z in [('ground',2.0),('upper',6.15)] for j,u in enumerate(positions)]
     self.detailed_wall(a,b,.75,9.,holes,mat,label+'/'+side)
    elif terrace_return:
     # Only the last four metres of these walls face the recessed terrace.
     aa,bb=((x0,365),(x0,yfront)) if side=='west' else ((x1,yfront),(x1,365))
     self.detailed_wall(aa,bb,.75,9.,[(0,5.42,1.25,2.45,0,label+'/terrace-side-door')],mat,label+'/'+side+'-terrace')
   self.mark('different_historic_mass',label=label,south_bays=len(front),east_extension_distinct='addition' in label)
  # Main roof masses retain accepted heights. Visible surfaces are clipped to their upper envelope.
  self.hip(176,209,511,365,9.,12.,'main-long-hip')
  self.hip(74,209,176,413,9.,11.1,'west-long-wing',axis='y')
  self.hip(511,209,610,413,9.,11.5,'east-original-wing',axis='y',gable=True)
  self.hip(610,209,697,413,9.,10.9,'retained-east-addition',axis='y')
  f=self.facade((511,413),(610,413),'east-upper-gable');f.prism(Polygon([(-4.125,9.),(4.125,9.),(0,11.5)]),-.3,.02,'historic rough stucco','triangular-gable')
  self.line(f,[(-4.125,9.04,.08),(0,11.54,.08),(4.125,9.04,.08)],.085,'stone trim','gable-raking-cornice')
  for i,x in enumerate([177,510]):
   self.box(self.xyz(x,295,11.46),(1.15,1.45,4.92),'historic rough stucco',f'chimney-{i}/shaft')
   self.box(self.xyz(x,295,13.96),(1.31,1.61,.08),'stone trim',f'chimney-{i}/cap')
  # Interior floors and transverse circulation keep transparent glazing grounded.
  self.b.plan_prism(self.planbox(74,209,697,413),.752,.79,'brick floor','interior/ground-finish')
  self.b.plan_prism(self.planbox(176,209,511,365),5.402,5.44,'aged timber','interior/upper-hall-floor')
  self.mark('interior_scope',note='Floors, structural partitions and entrance stair only; furniture and obscured finishes not reconstructed')
 def diamond(self,u,z,w,h):return Polygon([(u-w/2,z),(u,z+h/2),(u+w/2,z),(u,z-h/2)])
 def grille(self,f,u,z,size=.44,label='flower-grille'):
  # Four rounded lobes create actual daylight apertures through each square block.
  holes=[Point(u+dx,z+dz).buffer(size*.12,resolution=6 if self.lod else 10) for dx,dz in [(0,size*.23),(size*.23,0),(0,-size*.23),(-size*.23,0)]]
  holes.append(self.diamond(u,z,size*.18,size*.18))
  for dx,dz in [(-1,-1),(-1,1),(1,-1),(1,1)]:holes.append(self.diamond(u+dx*size*.31,z+dz*size*.31,size*.12,size*.12))
  f.prism(rect(u-size/2,z-size/2,u+size/2,z+size/2).difference(unary_union(holes)),-.24,.02,'dark grey grille',label)
  self.mark('pierced_flower_vent',label=f.label+'/'+label,apertures=9,pattern_note='Fine floral/diamond pattern inferred from close photos; dark grey body, greenery is not assumed to be painted surface')
 def southern_arcade(self):
  f=self.facade((176,441),(511,441),'south-long-arcade');width=f.length;holes=[];vents=[]
  for j in range(11):
   u=(j-5)*width/11;holes.append((u,.75,1.98,3.82,.99,f'south-arch-{j}'))
   for k in [-1,0,1]:vents.append(rect(u+k*.47-.22,5.56,u+k*.47+.22,6.00))
  f.wall(.75,6.15,[opening(u,z,w,h,r,24) for u,z,w,h,r,name in holes]+vents,.34,'historic rough stucco')
  for u,z,w,h,r,name in holes:self.pane(f,u,z,w,h,r,name)
  for j in range(11):
   u=(j-5)*width/11
   for k in [-1,0,1]:self.grille(f,u+k*.47,5.78,.44,f'bay-{j}-vent-{k}')
   f.box(u,6.10,1.65,.095,.48,.08,'stone trim',f'vent-canopy-{j}')
  f.beam(6.23,.17,.17,'stone trim');f.box(0,.89,width,.28,.08,.02,'stone trim','plinth')
  for u in [-width/2+.27,width/2-.27]:self.quoin(f,u,.77,6.12,.70,'arcade-corner')
  for a,b,name in [((176,365),(176,441),'west'),((511,441),(511,365),'east')]:
   sf=self.detailed_wall(a,b,.75,6.15,[(0,.75,1.6,3.75,.8,'arcade-'+name+'-door')],label='arcade-'+name+'-return')
   sf.beam(6.23,.17,.17,'stone trim')
  # Modern transparent safety guard is behind the old solid pierced parapet.
  for j in range(17):
   u=-width/2+(j+.5)*width/17;f.box(u,6.52,width/17-.025,.64,.014,-.21,'glass guard',f'glass-balustrade-panel-{j}')
  for j,u in enumerate(np.linspace(-width/2,width/2,18)):f.box(float(u),6.52,.025,.70,.032,-.22,'dark iron',f'glass-guard-post-{j}')
  f.box(0,6.88,width,.025,.035,-.22,'dark iron','glass-guard-handrail')
  for z in [4.98,5.32]:f.box(0,z,2.85,.045,.06,.07,'dark iron','store-letter-mounting-rail')
  self.text(f,'蔦屋書店',0,5.15,.58,.11,'south-store-kanji',.72);self.text(f,'TSUTAYA BOOKS',0,4.72,.20,.11,'south-store-latin',.21)
  self.mark('south_arcade',ground_arches=11,vent_groups=11,glass_guard=True,modern_sign='蔦屋書店 / TSUTAYA BOOKS')
 def quoin(self,f,u,bottom,top,width,label):
  h=.34;count=int((top-bottom)/h)
  for j in range(count):
   w=width*(1.0 if j%2==0 else .76);z=bottom+(j+.5)*h
   # Eight-sided rough block with shallow irregular front instead of printed stone lines.
   q=np.array([[-w/2,-h*.44],[w*.41,-h*.46],[w/2,h*.32],[w*.37,h*.44],[-w*.39,h*.46],[-w/2,h*.29]])
   f.prism(Polygon(q+[u,z]),.015,.11+(j%3)*.012,'rough sandstone',f'{label}/course-{j}')
 def blind_arch(self,f,u,z,w,h,name):
  # North rectangular timber window sits below a recessed semicircular stucco tympanum.
  arch=opening(u,z,w,h,w*.5,20);rectwindow=rect(u-w/2,z,u+w/2,z+h-w*.5)
  f.prism(arch.difference(rectwindow),-.16,-.09,'historic rough stucco',name+'/blind-arched-infill')
  f.prism(arch.buffer(.075).difference(arch),.005,.055,'stone trim',name+'/blind-arch-border')
  dz=z+h-w*.24
  f.prism(self.diamond(u,dz,.34,.34),-.08,-.04,'green ceramic',name+'/green-diamond')
  f.prism(self.diamond(u,dz,.18,.18),-.035,-.025,'stone trim',name+'/diamond-inlay')
 def low_north_face(self,a,b,centers,label):
  f=self.facade(a,b,label);windows=[];cuts=[]
  for j,u in enumerate(centers):
   windows.append((u,1.55,1.32,2.25,0,label+f'/rect-window-{j}'))
   cuts.append(opening(u,1.55,1.32,2.91,.66,24))
  # Diamond ventilation openings cut through both the parapet and the office wall.
  for j,u in enumerate(centers):
   for k in [-2,-1,0,1,2]:cuts.append(self.diamond(u+k*.18,5.73,.14,.31))
  f.wall(.75,6.10,cuts,.30,'historic rough stucco')
  for u,z,w,h,r,name in windows:
   self.pane(f,u,z,w,h,0,name);self.blind_arch(f,u,z,w,h+w*.5,name)
   self.shutters(f,u,z,w,h,name)
  f.beam(6.13,.12,.08,'stone trim')
  f.box(0,.9,f.length,.30,.09,.02,'stone trim','plinth')
  for j,u in enumerate(centers):self.mark('north_diamond_vent_group',facade=label,index=j,actual_holes=5)
  return f
 def north_blocks(self):
  # Stepped north offices follow the source plan instead of an extruded rectangle.
  self.low_north_face((270,143),(176,143),[-1.8,1.8],'northwest-office/front')
  self.low_north_face((513,143),(415,143),[-1.85,1.85],'northeast-office/front')
  for a,b,label in [((299,126),(270,126),'west-return-forward'),((415,126),(382,126),'east-return-forward')]:
   f=self.facade(a,b,'north/'+label);holes=[(-.63,1.45,.63,2.55,.315,label+'-narrow0'),(.63,1.45,.63,2.55,.315,label+'-narrow1')]
   self.detailed_wall(a,b,.75,6.1,holes,label='north/'+label,shutter=False);f.beam(6.13,.12,.08,'stone trim')
  for a,b,label in [((270,126),(270,143),'west-step'),((415,143),(415,126),'east-step'),((176,143),(176,209),'westoffice-side'),((513,209),(513,143),'eastoffice-side')]:
   f=self.facade(a,b,label);holes=[]
   if f.length>3:holes=[(0,1.6,1.0,2.1,.5,label+'-side-opening')]
   self.detailed_wall(a,b,.75,6.10,holes,label=label,shutter=False)
  for label,pts in [('northwest-office',[(176,143),(270,143),(270,126),(299,126),(299,209),(176,209)]),('northeast-office',[(382,126),(415,126),(415,143),(513,143),(513,209),(382,209)])]:
   self.b.plan_prism(self.poly(pts),5.12,5.38,'stone paving',label+'/flat-terrace-roof')
  # Narrow vestibule remains an open passage to the inset main-hall doorway.
  self.detailed_wall((382,126),(299,126),.75,5.3,[(0,.75,2.25,3.45,0,'north-outer-entrance')],label='north-vestibule/front',shutter=False)
  for a,b,name in [((299,126),(299,209),'west'),((382,209),(382,126),'east')]:self.detailed_wall(a,b,.75,5.35,[],label='vestibule/'+name)
  self.b.plan_prism(self.planbox(299,126,382,209),5.10,5.36,'light interior','vestibule/roof')
  self.detailed_wall((366,167),(315,167),1.45,5.10,[(0,1.45,2.30,3.45,.55,'north-inset-arched-entry')],label='vestibule/inset-stair-door',shutter=False)
  for j in range(5):self.b.plan_prism(self.planbox(319,167+j*3.5,362,185),.75,.75+(5-j)*.14,'brick floor',f'vestibule/interior-stair-{j}')
  self.mark('north_entrance_inner_stairs',risers=5,height_inferred_m=.7,reference='Commons69886781; exact internal elevation unknown')
  # Diagonal northwest service room is present on the ground and upper plans.
  diag=[(58,210),(152,111),(153,145),(132,209),(74,251),(58,251)]
  self.b.plan_prism(self.poly(diag),5.10,5.38,'stone paving','northwest/diagonal-service-roof')
  self.detailed_wall((58,251),(58,210),.75,5.4,[(0,1.65,1.15,2.1,.35,'nw-service-west-window')],label='northwest/service-short-west')
  self.detailed_wall((58,210),(145,118),.75,5.4,[(-2.3,1.65,1.15,2.1,.35,'nw-diagonal-window0'),(1.0,1.65,1.15,2.1,.35,'nw-diagonal-window1')],label='northwest/diagonal-service-wall')
  for i,cx in enumerate([153,535]):self.rounded_turret(i,cx)
  self.mark('north_facade_uncertainty',note='Side/obscured openings follow published plan axes; no claim of unobscured orthographic photographic verification')
 def rounded_turret(self,i,cx):
  cy=145;radius=21;pts=[(cx-radius,209),(cx+radius,209),(cx+radius,cy)]+[(cx+radius*math.cos(a),cy-radius*math.sin(a)) for a in np.linspace(0,math.pi,33 if not self.lod else 17)[1:]]
  p=self.poly(pts);ring=list(p.exterior.coords);label=f'rounded-stair-{i}'
  # Cut the frontal door/window on a tangent plane through the centre of the curved wall.
  front=self.xy(cx,124);cutwidth=.94
  for j,(a,b) in enumerate(zip(ring,ring[1:])):
   f=Facade(self.b,a,b,label+f'/curved-wall-{j}');holes=[]
   # Use a long cross-facade opening polygon; clipping slices it through each curved segment.
   for z,h in [(.75,2.70),(6.15,1.80)]:
    corners=[]
    for x,zz in [(front[0]-cutwidth/2,z),(front[0]+cutwidth/2,z),(front[0]+cutwidth/2,z+h),(front[0]-cutwidth/2,z+h)]:
     if abs(f.t[0])>.05:corners.append(((x-f.center[0])/f.t[0],zz))
    if corners and max(a[1],b[1])>front[1]-.35:holes.append(Polygon(corners))
   f.wall(.75,9.5,holes,.28,'historic rough stucco')
  f=Facade(self.b,front+[-1,0],front+[1,0],label+'/front-window-plane')
  # Reverse tangent so the glazing faces north.
  f=Facade(self.b,front+[1,0],front+[-1,0],label+'/front-window-plane')
  self.pane(f,0,.75,.94,2.70,0,label+'/ground-door');self.pane(f,0,6.15,.94,1.80,0,label+'/upper-window')
  self.b.plan_prism(p.buffer(.22),9.48,9.62,'stone trim',label+'/curved-eave')
  coords=list(p.buffer(.24).exterior.coords)[:-1];center=self.xy(cx,168);v=[[x,y,9.62] for x,y in coords]+[[*center,10.0]];n=len(coords)
  self.b.add(v,[tuple(reversed(range(n)))]+[(j,(j+1)%n,n) for j in range(n)],'terracotta roof',label+'/curved-hip-cap')
  for j,(x,y) in enumerate(coords[::2 if self.lod else 1]):
   end=np.array([x,y,9.65]);peak=np.array([*center,10.02]);self.b.tube([end,end*.5+peak*.5,peak],.038,'tile light',6,label+f'/cap-tile-rib-{j}')
  self.mark('rounded_stair_turret',index=i,curved_wall=True,actual_openings=2,roof_peak_m=10.0)
 def spiral(self,f,u,z,r,turns=1.25,d=.12,mat='stone trim',label='scroll'):
  aa=np.linspace(0,math.tau*turns,18 if self.lod else 36);rr=np.linspace(r,.04,len(aa))
  self.line(f,[(u+a*math.cos(t),z+a*math.sin(t),d) for a,t in zip(rr,aa)],.036,mat,label)
 def capital(self,xy,z,label):
  self.b.lathe(xy,[(z,.195),(z+.08,.23),(z+.30,.31),(z+.38,.35)],'stone trim',12 if self.lod else 20,label+'/capital-body')
  self.box([*xy,z+.40],(.70,.70,.10),'stone trim',label+'/abacus')
  if not self.lod:
   for j in range(4):
    ang=j*math.pi/2;t=np.array([math.cos(ang),math.sin(ang)]);n=np.array([t[1],-t[0]]);center=xy+n*.25
    f=Facade(self.b,center-t*.5,center+t*.5,label+f'/capital-face-{j}')
    for u in [-.22,.22]:self.spiral(f,u,z+.27,.12,1.0,.07,label='ionic-volute')
    for u in [-.13,0,.13]:
     leaf=Polygon([(u-.075,z+.02),(u-.10,z+.12),(u-.06,z+.23),(u,z+.30),(u+.06,z+.23),(u+.10,z+.12),(u+.075,z+.02)])
     f.prism(leaf,.025,.075,'stone trim','acanthus-leaf')
 def north_portico(self):
  x0,x1,y0,y1=299,382,54,126
  for i,(x,y) in enumerate([(303,59),(311,59),(370,59),(378,59),(303,121),(311,121),(370,121),(378,121)]):
   xy=self.xy(x,y);label=f'north-portico/paired-column-{i}'
   self.b.lathe(xy,[(.75,.28),(.87,.28),(.91,.23),(1.03,.22),(1.08,.185),(2.6,.19),(4.05,.17),(4.15,.20),(4.23,.20)],'stone trim',12 if self.lod else 24,label+'/entasis-shaft')
   self.capital(xy,4.23,label)
  for edge,(a,b) in enumerate([((382,54),(299,54)),((382,126),(382,54)),((299,54),(299,126))]):
   f=self.facade(a,b,'north-portico-face-'+str(edge));length=f.length
   hole=opening(0,.75,length-1.05,3.45,.56,24);cuts=[hole]
   for j in range(9):cuts.append(self.diamond((j-4)*.24,5.35,.17,.36))
   f.wall(.75,5.75,cuts,.30,'historic rough stucco')
   f.prism(hole.buffer(.10).difference(hole),.005,.07,'stone trim','flat-arch-surround')
   # Upturned coping at each end, with square corner finials; no unsupported eagle.
   profile=[(-length/2-.05,5.86),(-length/2+.35,5.86),(-length/2+.60,5.70),(-length/2+.80,5.67),(length/2-.80,5.67),(length/2-.60,5.70),(length/2-.35,5.86),(length/2+.05,5.86)]
   self.line(f,[(u,z,.05) for u,z in profile],.095,'stone trim','curved-coping')
   for u in [-length/2+.26,length/2-.26]:
    f.box(u,5.95,.58,.16,.52,0,'stone trim','end-pedestal');f.box(u,6.18,.32,.36,.32,0,'stone trim','square-finial')
   if edge==2:
    self.text(f,'蔦屋書店',0,6.02,.33,.12,'west-side-store-kanji')
    self.text(f,'TSUTAYA BOOKS',0,5.80,.13,.12,'west-side-store-latin')
  self.b.plan_prism(self.planbox(x0,y0,x1,y1),4.65,4.91,'light interior','north-portico/single-ceiling-roof')
  # Distinct semicircular front steps and gently curved approach ramps in plan.
  c=self.xy(340.5,54);r=2.53
  for j in range(5):
   rr=r+(4-j)*.23;pts=[(c[0]-rr,c[1]),(c[0]+rr,c[1])]+[(c[0]+rr*math.cos(t),c[1]+rr*math.sin(t)) for t in np.linspace(0,math.pi,25)[1:]]
   self.b.plan_prism(Polygon(pts),0,(j+1)*.15,'stone paving',f'north-approach/semicircle-step-{j}')
  self.mark('north_portico',paired_corner_columns=8,side_openings_photo_supported=True,north_outer_opening='single wide opening inferred from plan; clear frontal photograph unavailable',historical_eagle_omitted=True,sign_side='west side inferred from cross-view reference')
  for side in [-1,1]:
   # Curved approach strips are visible in the published ground plan; exact gradient is inferred.
   xs=np.linspace(340.5+side*128,340.5+side*42,13);tt=np.linspace(0,1,13);yy=59+36*tt+9*np.sin(tt*math.pi)
   left=[];right=[]
   for k,(x,y) in enumerate(zip(xs,yy)):
    c0=self.xy(x,y);z=.03+.72*tt[k];left.append([*self.xy(x,y-13),z]);right.append([*self.xy(x,y+13),z])
   v=left+right+[[a,b,0] for a,b,z in left+right];n=len(left);faces=[]
   for j in range(n-1):faces +=[(j,j+1,n+j+1,n+j),(2*n+j,3*n+j,3*n+j+1,2*n+j+1),(j,2*n+j,2*n+j+1,j+1),(n+j,n+j+1,3*n+j+1,3*n+j)]
   faces +=[(0,n,3*n,2*n),(n-1,3*n-1,4*n-1,2*n-1)]
   self.b.add(v,faces,'stone paving',f'north-approach/curved-ramp-{side}')
   self.mark('drawn_curved_approach',side=side,gradient_inferred=True)
 def twisted_column(self,f,u,z0,z1,label):
  c=f.point(u,0,.04);levels=10 if self.lod else 24;sides=12 if self.lod else 20;vs=[]
  for z in np.linspace(z0+.18,z1-.20,levels):
   phase=(z-z0)/(z1-z0)*math.tau*1.6
   for j in range(sides):
    a=math.tau*j/sides;r=.18+.032*math.cos(3*a-phase)
    vs.append([c[0]+r*math.cos(a),c[1]+r*math.sin(a),z])
  faces=[tuple(reversed(range(sides))),tuple((levels-1)*sides+j for j in range(sides))]
  for k in range(levels-1):
   for j in range(sides):a=k*sides+j;b=k*sides+(j+1)%sides;faces.append((a,b,b+sides,a+sides))
  self.b.add(vs,faces,'stone trim',label+'/continuous-helical-shaft')
  self.b.lathe(c[:2],[(z0,.24),(z0+.10,.24),(z0+.17,.20),(z0+.20,.18)],'stone trim',16,label+'/base')
  self.b.lathe(c[:2],[(z1-.22,.18),(z1-.15,.23),(z1,.23)],'stone trim',16,label+'/capital')
  self.mark('twisted_stone_column',label=label,continuous_geometry=True)
 def balcony(self,f,u,z,w,depth,label,curved=False):
  # Supported projecting stone slab with a balustrade, true open spaces between rods.
  if curved:poly=Polygon([(u-w/2,0),(u+w/2,0)]+[(u+w/2*math.cos(a),depth*math.sin(a)) for a in np.linspace(0,math.pi,17)[1:]])
  else:poly=Polygon([(u-w/2,0),(u+w/2,0),(u+w/2,depth),(u-w/2,depth)])
  mapper=lambda x,y,d: f.point(x,d,y)
  # x,u then outward depth then z needs a positively oriented plan basis.
  coords=[f.point(x,0,d)[:2] for x,d in poly.exterior.coords];p=orient(Polygon(coords),sign=1)
  self.b.plan_prism(p,z-.16,z,'stone trim',label+'/projecting-slab')
  for off in [-w*.27,w*.27]:
   prism=Polygon([(off-.12,z-.95),(off+.12,z-.95),(off+.25,z-.17),(off-.25,z-.17)])
   f.prism(prism,.02,depth*.75,'stone trim',label+'/corbel')
  pts=[]
  for q in list(poly.exterior.coords)[1:]:
   if not pts or np.linalg.norm(np.array(q)-pts[-1])>1e-7:pts.append(q)
  path=[(x,z+.90,d) for x,d in pts]
  self.line(f,path,.035,'dark iron',label+'/curved-handrail')
  boundary=LineString(pts);count=max(8,round(boundary.length/.19))
  for j in range(count+1):
   x,d=boundary.interpolate(j/count,normalized=True).coords[0]
   self.line(f,[(x,z+.05,d),(x,z+.9,d)],.018,'dark iron',label+f'/iron-rod-{j}')
   if not self.lod and j%2==0:
    self.line(f,[(x-.055,z+.25,d),(x+.045,z+.43,d),(x-.045,z+.61,d),(x+.055,z+.78,d)],.012,'dark iron',label+'/scroll-iron')
  self.mark('open_iron_balcony',label=label,width_m=w,projection_m=depth)
 def south_ornament(self):
  west=self.facade((74,413),(176,413),'west-south-ornament')
  for u in [-1.225,1.225]:self.twisted_column(west,u,.75,3.72,'west-triple-arcade/twisted-'+str(u))
  for u in [-2.45,0,2.45]:
   # Individually cut voussoirs around each of the three stone arches.
   for j in range(9 if self.lod else 15):
    count=9 if self.lod else 15;a=j*math.pi/count+.012;b=(j+1)*math.pi/count-.012
    ps=[(u+r*math.cos(t),3.69+r*math.sin(t)) for r,t in [(1.00,a),(1.00,b),(1.42,b),(1.42,a)]]
    west.prism(Polygon(ps),.01,.13,'rough sandstone',f'west-arch-{u}/voussoir-{j}')
  for u in [-3.55,3.55]:self.quoin(west,u,.75,4.5,.80,'west-arcade-jamb')
  self.balcony(west,0,5.78,2.0,.93,'west-corbel-balcony')
  east=self.facade((511,413),(610,413),'east-south-ornament')
  self.balcony(east,0,5.78,2.10,.86,'east-curved-balcony',True)
  # Curved stone door canopy distinct from the western triple arch.
  profile=[(-1.4,3.4),(-1.18,3.44),(-.99,3.60),(-.81,4.08),(-.58,4.50),(0,4.67),(.58,4.50),(.81,4.08),(.99,3.60),(1.18,3.44),(1.4,3.4)]
  self.line(east,[(u,z,.12) for u,z in profile],.105,'stone trim','curved-ground-door-coping')
  for u in [-1.2,1.2]:self.quoin(east,u,.78,3.36,.45,'east-door-stone-jamb')
  for u in [-1.08,1.08]:self.spiral(east,u,3.63,.25,1.1,.15,label='door-canopy-scroll')
 def central_mission_gable(self):
  f=self.facade((302,365),(382,365),'recessed-central-mission-gable')
  p=[(-3.20,8.97),(-3.20,9.30),(-2.30,9.30),(-1.78,9.48),(-1.34,9.87),(-1.13,10.38),(-.95,10.65),(-.65,10.83),(.65,10.83),(.95,10.65),(1.13,10.38),(1.34,9.87),(1.78,9.48),(2.30,9.30),(3.20,9.30),(3.20,8.97)]
  apertures=[self.diamond(0,10.15,.19,.30),self.diamond(-.12,9.91,.13,.24),self.diamond(.12,9.91,.13,.24)]
  f.prism(Polygon(p).difference(unary_union(apertures)),-.25,.08,'historic rough stucco','curved-parapet-with-open-diamonds')
  self.line(f,[(u,z,.12) for u,z in p[1:-1]],.09,'stone trim','curved-profile-coping')
  for s in [-1,1]:
   self.spiral(f,s*1.78,9.57,.27,1.25,.16,label='gable-scroll')
   xy=f.point(s*2.65,0,0)[:2];self.b.lathe(xy,[(9.35,.19),(9.52,.24),(9.67,.14),(9.93,.09),(10.08,.025)],'stone trim',12 if self.lod else 20,'mission-gable/side-finial')
  xy=f.point(0,0,0)[:2];self.b.lathe(xy,[(10.83,.26),(10.94,.31),(11.12,.20),(11.30,.28),(11.53,.17),(11.67,.07)],'stone trim',16 if self.lod else 28,'mission-gable/central-urn')
  self.mark('mission_gable',plan_axis_x=342,wall_y=365,front_arcade_y=441,recession_m=76/12,open_diamonds=3,unrestored_eagle_omitted=True)
 def text(self,f,text,u,z,height,d,label,spacing=None):
  latin=all(ord(c)<128 for c in text);advance=spacing if spacing is not None else height*(.66 if latin else 1.03);width=advance*(len(text)-1)
  for j,ch in enumerate(text):
   if ch==' ':continue
   pen=Contours(self.gs);self.gs[self.cmap[ord(ch)]].draw(pen);poly=Polygon()
   for pts in pen.paths:poly=poly.symmetric_difference(Polygon(pts).buffer(0))
   if poly.is_empty:continue
   x0,y0,x1,y1=poly.bounds;fac=height/max(y1-y0,x1-x0);poly=scale(poly,xfact=fac,yfact=fac,origin=(0,0));x0,y0,x1,y1=poly.bounds
   poly=translate(poly,xoff=u-width/2+j*advance-(x0+x1)/2,yoff=z-(y0+y1)/2)
   f.prism(poly,d,d+.025,'white letters',label+'/'+ch)
  self.mark('legible_sign',text=text,label=label,font='Noto Sans CJK JP subset SIL OFL-1.1',not_exact_brand_font=True)
 def hip(self,x0,y0,x1,y1,eave,ridge,label,axis='x',gable=False):
  from club_roof import add_roof
  a=self.xy(x0,y1);b=self.xy(x1,y0)
  report=add_roof(self.b,a[0]-.38,a[1]-.38,b[0]+.38,b[1]+.38,eave,ridge,label,axis,gable,self.lod)
  self.mark('individual_barrel_tile_roof',**{k:v for k,v in report.items() if k!='support_faces'})
 def rainwater_and_courses(self):
  for a,b,label in [((176,441),(511,441),'south-arcade'),((270,143),(176,143),'northwest-office'),((513,143),(415,143),'northeast-office')]:
   f=self.facade(a,b,label)
   for u in [-f.length/2+.15,f.length/2-.15]:
    self.line(f,[(u,.90,.13),(u,5.85,.13),(u,6.08,.25)],.045,'dark iron','rainwater-pipe')
    for z in [1.45,3.1,4.8]:f.box(u,z,.14,.06,.13,.14,'dark iron','pipe-bracket')
  # Real paving joints on the attached outdoor terrace, authored only at close LOD.
  if not self.lod:
   p=self.planbox(78,441,655,528);minx,miny,maxx,maxy=p.bounds
   for x in np.arange(minx+.75,maxx,.75):self.box([(x), (miny+maxy)/2,.752],(.009,maxy-miny,.004),'stone trim','south-terrace/paving-joint-x')
   for y in np.arange(miny+.75,maxy,.75):self.box([(minx+maxx)/2,y,.752],(maxx-minx,.009,.004),'stone trim','south-terrace/paving-joint-y')
 def apply_surface_maps(self):
  base=HERE/'textures';maps={'texture':str(base/'Plaster001_1K-JPG_Color.jpg')}
  if not self.lod:maps.update(normal_texture=str(base/'Plaster001_1K-JPG_NormalGL.jpg'),roughness_texture=str(base/'Plaster001_1K-JPG_Roughness.jpg'),normal_scale=1.6)
  names=['historic rough stucco','east addition stucco']
  for name in names:self.b.palette[name].update(maps,extras={'materialSource':'ambientCG Plaster001; CC0-1.0','classification':'generic illustrative surface, NOT a scan of this building','repeat_metres':1.15,'normal_scale':1.6 if not self.lod else None})
  # Per-triangle major-axis projection keeps wall corners and curved returns correctly mapped.
  # The exporter subsequently joins coincident position/normal/UV tuples.
  for p in self.b.parts:
   if p['material'] not in names:continue
   old=np.array(p['vertices']);vs=[];uv=[];ts=[]
   for tri in p['triangles']:
    q=old[list(tri)];normal=np.cross(q[1]-q[0],q[2]-q[0]);axis=int(np.argmax(np.abs(normal)))
    inds=[1,2] if axis==0 else ([0,2] if axis==1 else [0,1]);t=[]
    for v in q:t.append(len(vs));vs.append(v.tolist());uv.append((v[inds]/1.15*np.array([1,-1])).tolist())
    ts.append(tuple(t))
   p.update(vertices=vs,triangles=ts,texcoords=uv)
  self.mark('generic_surface_material',asset='ambientCG Plaster001',original_image_bytes=True,repeat_metres=1.15,normal_strength=1.6 if not self.lod else None,not_a_building_surface_scan=True)
 def build(self):
  self.terrace();self.body();self.southern_arcade();self.north_blocks();self.north_portico();self.central_mission_gable();self.south_ornament();self.rainwater_and_courses();self.apply_surface_maps()
  for p in self.b.parts:
   vs=np.array(p['vertices']);ts=np.array(p['triangles']);volume=float(np.einsum('ij,ij->i',vs[ts[:,0]],np.cross(vs[ts[:,1]],vs[ts[:,2]])).sum()/6)
   if volume<0:p['triangles']=[tuple(reversed(t)) for t in p['triangles']]
   p['vertices']=(vs@self.R.T).tolist()
  return self

def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--lod',action='store_true');a=p.parse_args();assert not a.out.exists();m=Club(a.lod).build();a.out.mkdir(parents=True)
 meta={'id':'columbia-country-club','name':'哥伦比亚乡村俱乐部','anchor':m.g['anchor'],'rotation_y':0,'ground_base_m':0,'axis':'glTF east/up/south','stage':'DETAILED EXTERIOR / authored LOD' if a.lod else 'DETAILED EXTERIOR / full','height_estimate_m':14.,'height_note':'Rounded starting levels 0.75/5.4/9/12/14 m inferred from separately scaled2018architect drawings; ±0.5–1m, not surveyed height; exact exported envelope separately audited','source_geometry_sha256':sha(HERE/'geometry-input.json'),'copyright':'Original authored geometry/code MIT; source footprint ©OpenStreetMap contributors / Overture ODbL-1.0; ambientCG CC0-1.0 original generic Plaster001 maps; Noto Sans CJK glyphs SIL OFL-1.1; private reference pixels absent','textures_embedded':True,'authored_lod':a.lod,'uncertainty':['Mapped quad is an approximate coverage owner, not measured walls; plan fitted to its principal axis without shearing.','All heights and detailed dimensions are inferred from drawings and photographs, not surveyed.','North frontal portico opening and obscured facade details are plan-informed estimates.','Generic CC0 microstucco is illustrative and not a scan of this building.','Interior limited to structural walls, floors and entrance stair; furniture and hidden service details omitted.','Shop text is verified traditional 蔦屋書店 / TSUTAYA BOOKS; exact commercial lettering typeface is approximated by licensed Noto glyph geometry.']}
 r=m.b.save(a.out/'columbia-country-club.glb',meta)
 write(a.out/'features.json',{'features':m.features,'counts':{k:sum(f['kind']==k for f in m.features) for k in sorted(set(f['kind'] for f in m.features))}})
 write(a.out/'feature-probes-input.json',{'probes':m.audit,'rotation_radians':m.angle})
 write(a.out/'metadata.json',{**meta,'raw':{k:r[k] for k in ['file','bytes','sha256','triangles','parts','bounds_glb']}})
 print(json.dumps({k:r[k] for k in ['bytes','sha256','triangles','parts','bounds_glb']}),flush=True)
if __name__=='__main__':main()
