#!/usr/bin/env python3
"""Yangpu Library: complete connected exterior, ENU metres; no image textures.
Photo-informed visible faces; rear/courtyard bay counts and local dimensions are estimates.
"""
from pathlib import Path
import argparse, json, hashlib, math, sys
from collections import Counter
import numpy as np
from shapely.geometry import Polygon, box as rect, LineString
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'common'))
from photo_architecture import Builder, Facade, opening, pieces
PALETTE={
 'old limestone':{'color':[.64,.62,.555],'roughness':.86},
 'stone carved':{'color':[.73,.70,.62],'roughness':.78},
 'stone joints':{'color':[.37,.37,.33],'roughness':.96},
 'modern fluted stone':{'color':[.62,.615,.57],'roughness':.87},
 'modern fluting':{'color':[.47,.48,.45],'roughness':.95},
 'granite':{'color':[.33,.34,.32],'roughness':.82},
 'glass blue':{'color':[.10,.19,.24],'roughness':.18,'metallic':.25},
 'glass grey':{'color':[.17,.245,.25],'roughness':.22,'metallic':.2},
 'steel charcoal':{'color':[.065,.075,.077],'roughness':.4,'metallic':.5},
 'glazed ochre':{'color':[.62,.335,.07],'roughness':.31,'metallic':.08},
 'glazed gold':{'color':[.81,.48,.115],'roughness':.27,'metallic':.12},
 'ridge shadow':{'color':[.38,.19,.043],'roughness':.4},
 'paint turquoise':{'color':[.04,.36,.31],'roughness':.56},
 'paint blue':{'color':[.03,.10,.28],'roughness':.56},
 'paint vermilion':{'color':[.48,.065,.038],'roughness':.62},
 'paint cream':{'color':[.84,.76,.52],'roughness':.57},
 'old red door':{'color':[.24,.065,.048],'roughness':.65},
 'roof gravel':{'color':[.52,.53,.5],'roughness':.95},
 'garden hedge':{'color':[.22,.32,.09],'roughness':.96},
 'garden soil':{'color':[.19,.16,.105],'roughness':1},
 'brass':{'color':[.62,.44,.14],'roughness':.4,'metallic':.65},
 'lamp glass':{'color':[.87,.75,.41],'roughness':.22},
}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
class Library:
 def __init__(self,lod=False):
  self.lod=lod;self.b=Builder(PALETTE);self.features=[];self.c=json.loads((HERE/'calibration.json').read_text());self.anchor=self.c['anchor']
  self.outline=orient(Polygon(self.c['outline_enu'],self.c['courtyards_enu']),sign=1)
  self.courts=[Polygon(x) for x in self.c['courtyards_enu']]
  self.core=rect(4.0,-9.87,18.94,7.63).intersection(self.outline)
  self.front_center_y=-1.12
 def mark(self,kind,label,**v):self.features.append({'kind':kind,'label':label,**v})
 def line(self,a,b,r,mat,label):self.b.tube([a,b],r,mat,6 if self.lod else 8,label)
 def box(self,c,s,m,label):self.b.box(c,s,m,label=label)
 def pane(self,f,p,label,cols=2,rows=3,frame='steel charcoal',glass='glass blue',trim=False):
  x0,z0,x1,z1=p.bounds;inn=p.buffer(-.065,join_style=2);bars=[]
  for j in range(1,cols):
   u=x0+(x1-x0)*j/cols;bars.append(rect(u-.024,z0,u+.024,z1))
  for j in range(1,rows):
   z=z0+(z1-z0)*j/rows;bars.append(rect(x0,z-.024,x1,z+.024))
  cells=inn.difference(unary_union(bars));f.prism(cells,-.31,-.29,glass,label+'/glass')
  f.prism(p.buffer(-.015,join_style=2).difference(cells),-.25,-.12,frame,label+'/frame')
  if trim:f.prism(p.buffer(.12,join_style=2).difference(p),-.015,.085,'stone carved',label+'/surround')
  f.box((x0+x1)/2,z0-.05,x1-x0+.14,.10,.5,-.02,'stone carved',label+'/sill')
  self.mark('real_glazed_opening',f.label+'/'+label,face_origin_enu=f.center.tolist(),tangent_enu=f.t.tolist(),outward_enu=f.n.tolist(),polygon_uz=list(p.exterior.coords),wall_depth_m=[-.42,0],glass_depth_m=[-.31,-.29])
 def courses(self,f,area,modern=False):
  if self.lod:return
  x0,z0,x1,z1=area.bounds;cuts=[]
  if modern:
   for u in np.arange(x0+.16,x1,.32):cuts.append(rect(u-.006,z0,u+.006,z1))
  else:
   for k,z in enumerate(np.arange(.5,z1,.68)):
    cuts.append(rect(x0,z-.009,x1,z+.009))
    for u in np.arange(x0+(k%2)*.65,x1,1.52):cuts.append(rect(u-.007,z,u+.007,min(z+.68,z1)))
  for i,p in enumerate(pieces(unary_union(cuts).intersection(area))):
   f.prism(p,.001,.004,'modern fluting' if modern else 'stone joints',f'fine-surface-joint/{i}')
 def corner_offsets(self,points,index):
  # Solve inner offset-line intersections for a 1m wall thickness; Facade.wall scales by actual thickness.
  pts=[np.array(p,float) for p in points[:-1]];a=pts[index];b=pts[(index+1)%len(pts)]
  t=(b-a)/np.linalg.norm(b-a);n=np.array([t[1],-t[0]])
  prev=(a-pts[index-1]);prev/=np.linalg.norm(prev);nprev=np.array([prev[1],-prev[0]])
  nxt=pts[(index+2)%len(pts)]-b;nxt/=np.linalg.norm(nxt);nnxt=np.array([nxt[1],-nxt[0]])
  def solve(other,no):
   M=np.array([t,-other]).T
   return float(np.linalg.solve(M,n-no)[0]) if abs(np.linalg.det(M))>1e-8 else 0.
  return solve(prev,nprev),solve(nxt,nnxt)
 def standard(self,f,modern=False,court=False):
  H=10.45 if not modern else 10.4;holes=[];L=f.length
  if L>1.1:
   curtain=modern and (abs(f.center[0])<12 or court)
   if curtain:
    n=max(1,int(L/2.0));pitch=L/n
    for j in range(n):
     u=-L/2+(j+.5)*pitch;p=rect(u-pitch*.46,.5,u+pitch*.46,9.7);holes.append(p);self.pane(f,p,f'curtain/{j}',1,6,glass='glass grey')
   elif modern:
    n=max(1,int(L/2.4));pitch=L/n
    for j in range(n):
     u=-L/2+(j+.5)*pitch;p=rect(u-.36,1.65,u+.36,8.9);holes.append(p);self.pane(f,p,f'slit/{j}',1,3,glass='glass grey')
   else:
    n=max(1,int(round(L/3.9)));pitch=L/n
    for j in range(n):
     u=-L/2+(j+.5)*pitch;w=min(1.0,pitch*.38)
     for floor,(lo,hi) in enumerate([(.8,3.15),(4.8,9.1)]):
      p=rect(u-w/2,lo,u+w/2,hi);holes.append(p);self.pane(f,p,f'bay-{j}/floor-{floor+1}',2,2 if floor==0 else 5)
  surface=f.wall(0,H,holes,thickness=.42,material='modern fluted stone' if modern else 'old limestone')
  self.courses(f,surface,modern);f.beam(.24,.32,.10,'granite',label='plinth')
  f.beam(H,.18,.22,'stone carved',label='cornice')
  f.box(0,H+.19,L,.34,.35,-.12,'modern fluted stone' if modern else 'old limestone','parapet')
  f.beam(H+.4,.12,.11,'stone carved',label='coping')
 def front(self):
  # Face points south to north: tangent north, outward east. Main entrance is east.
  f=Facade(self.b,[18.94,-21.53],[18.94,21.84],'east-main-front');f.wall_corner_offsets=self.mainfront_corner_offsets;c=self.front_center_y-f.center[1]
  outline=Polygon([(-f.length/2,0),(f.length/2,0),(f.length/2,10.45),(c+8.75,10.45),(c+8.75,12.75),(c-8.75,12.75),(c-8.75,10.45),(-f.length/2,10.45)])
  holes=[]
  door=opening(c,.1,2.55,3.4,1.28,30);holes.append(door)
  f.prism(door.buffer(.38).difference(door).intersection(rect(-100,0,100,100)),-.035,.24,'stone carved','arched-entrance/stone-arch')
  self.pane(f,door,'arched-entrance',2,1,frame='old red door',glass='old red door')
  # External door is photo-visible geometric lattice, NOT an unobserved interior peacock gate.
  lattice=[]
  for sign in [-1,1]:
   for s in np.arange(-4,4,.45):
    line=LineString([(c-1.7,s),(c+1.7,s+sign*3.4)]).buffer(.024)
    lattice.append(line)
  region=door.buffer(-.22).intersection(rect(c-1.7,1.05,c+1.7,3.8))
  f.prism(unary_union(lattice).intersection(region),-.09,-.035,'brass','arched-entrance/geometric-lattice')
  for dx in [-.78,.78]:
   outer=rect(c+dx-.53,.33,c+dx+.53,.95);inner=outer.buffer(-.08)
   f.prism(outer.difference(inner),-.06,.005,'brass','arched-entrance/lower-panel')
   f.line((c+dx*.17,1.0,.02),(c+dx*.17,1.45,.02),.036,'brass',8,'arched-entrance/handle')
  for dx in [-3.9,3.9]:
   p=Polygon([(c+dx+.52*math.cos(math.tau*j/8+math.pi/8),2.42+.52*math.sin(math.tau*j/8+math.pi/8)) for j in range(8)])
   holes.append(p);self.pane(f,p,f'octagonal-{dx}',1,1,trim=True)
  for dx in [-2.1,0,2.1]:
   p=rect(c+dx-.50,5.25,c+dx+.50,10.35);holes.append(p);self.pane(f,p,f'tall-center-{dx}',3,7)
  for dx in [-18.3,-14.5,-10.0,10.0,14.5,18.3]:
   for k,(lo,hi) in enumerate([(.75,3.1),(5.0,9.2)]):
    p=rect(c+dx-.56,lo,c+dx+.56,hi);holes.append(p);self.pane(f,p,f'side-{dx}/floor-{k}',2,2 if not k else 5)
  surface=f.wall(0,12.75,holes,outline=outline,thickness=.5,material='old limestone');self.courses(f,surface)
  f.beam(.3,.38,.16,'granite',label='ground-plinth')
  for dx in [-10.6,10.6]:f.box(c+dx,7.8,.30,9.5,.30,.08,'stone carved','shoulder-quoin')
  # Balcony with actual open balusters, paired capitals and canted stone brackets.
  f.box(c,4.9,6.2,.32,1.4,.57,'stone carved','balcony/slab')
  for dx in [-2.8,-1.4,0,1.4,2.8]:
   f.box(c+dx,5.49,.18,1.0,.24,1.15,'stone carved','balcony/post')
   f.box(c+dx,6.02,.31,.16,.35,1.15,'stone carved','balcony/cap')
  f.box(c,5.93,6.2,.14,.26,1.15,'stone carved','balcony/handrail')
  for dx in np.arange(-2.6,2.7,.43):
   f.box(c+dx,5.48,.10,.65,.16,1.15,'stone carved','balcony/baluster')
  for dx in [-2.5,-1.25,0,1.25,2.5]:
   p=Polygon([(c+dx-.18,4.74),(c+dx+.18,4.74),(c+dx+.12,4.10),(c+dx-.12,4.10)])
   f.prism(p,.06,.75,'stone carved','balcony/bracket')
  for h,w,d in [(0.12,8.4,2.4),(.27,7.8,1.8),(.42,7.1,1.1)]:
   f.box(c,h/2,w,h,d,d/2+.02,'granite','entry-step')
  for dx in [-3.65,3.65]:self.lantern(f.point(c+dx,0,1.7)[:2],f'entry-lantern-{dx}')
  self.balustrade([18.96,-9.87],[18.96,7.63],12.78,'east-terrace')
  for y in [-9.87,7.63]:self.balustrade([12.0,y],[18.96,y],12.78,f'terrace-return-{y}')
 def lantern(self,xy,label):
  x,y=xy
  self.box([x,y,.18],[.78,.78,.36],'granite',label+'/base')
  self.b.lathe([x,y],[(.36,.26),(.55,.26),(.62,.13),(1.7,.10),(1.78,.24)],'steel charcoal',8,label+'/pedestal')
  self.box([x,y,2.19],[.37,.37,.76],'lamp glass',label+'/glass')
  for dx in [-.23,.23]:
   for dy in [-.23,.23]:self.box([x+dx,y+dy,2.19],[.065,.065,.9],'steel charcoal',label+'/frame')
  self.box([x,y,2.66],[.6,.6,.14],'steel charcoal',label+'/cap')
  self.b.lathe([x,y],[(2.73,.20),(2.85,.10),(2.95,.01)],'brass',8,label+'/finial')
 def balustrade(self,a,b,z,label):
  f=Facade(self.b,a,b,label);n=max(1,round(f.length/1.8));pitch=f.length/n
  f.box(0,z+.08,f.length,.16,.4,0,'stone carved','base')
  for j in range(n+1):
   u=-f.length/2+j*pitch;f.box(u,z+.65,.22,1.15,.32,0,'stone carved','post');f.box(u,z+1.26,.32,.14,.40,0,'stone carved','cap')
  for j in range(n):
   u=-f.length/2+(j+.5)*pitch
   f.box(u,z+1.03,pitch-.20,.14,.24,0,'stone carved','top-rail')
   f.box(u,z+.33,pitch-.20,.12,.20,0,'stone carved','bottom-rail')
   for du in [-.42,-.14,.14,.42]:
    if abs(du)<pitch/2-.1:f.box(u+du,z+.67,.10,.59,.18,0,'stone carved','carved-upright')
 def compound(self):
  # Ground and roof retain both true inner holes and the open north/south entrance notches.
  p=list(self.outline.exterior.coords)
  for i,(a,b) in enumerate(zip(p,p[1:])):
   f=Facade(self.b,a,b,f'outer-{i}');f.wall_corner_offsets=self.corner_offsets(p,i)
   if abs(a[0]-18.94)<.03 and abs(b[0]-18.94)<.03 and abs(a[1]-b[1])>40:
    self.mainfront_corner_offsets=f.wall_corner_offsets;continue
   modern=abs(f.center[1])>35 or (f.center[0]<1.2 and abs(f.center[1])>21)
   if abs(f.center[1]+40.91)<.02 and abs(f.center[0])<5:self.south_entry(f)
   elif f.center[0]>28 and abs(f.n[0])>.99 and 20<abs(f.center[1])<36:self.old_wing_end(f)
   else:self.standard(f,modern)
  for k,court in enumerate(self.courts):
   pts=list(orient(court,sign=-1).exterior.coords)
   for i,(a,b) in enumerate(zip(pts,pts[1:])):
    f=Facade(self.b,a,b,f'courtyard-{k}/face-{i}');f.wall_corner_offsets=self.corner_offsets(pts,i);self.standard(f,False,True)
   self.b.plan_prism(court,.02,.06,'granite',f'courtyard-{k}/ground')
   inner=court.buffer(-1.0,join_style=2)
   self.b.plan_prism(inner,.06,.13,'garden soil',f'courtyard-{k}/planter-soil')
   hedge=inner.difference(inner.buffer(-.5,join_style=2))
   self.b.plan_prism(hedge,.13,.55,'garden hedge',f'courtyard-{k}/perimeter-hedge')
   self.mark('open_courtyard',f'courtyard-{k}',outline_enu=list(court.exterior.coords),roof_absent=True)
  self.b.plan_prism(self.outline,.0,.10,'granite','ground-slab-with-two-court-holes')
  self.b.plan_prism(self.outline.buffer(-.40,join_style=2).difference(self.core),10.15,10.32,'roof gravel','flat-roof-with-two-court-holes')
  # The upper platform has no windows: author its three return walls as one
  # actual 2D Boolean wall band. This resolves the short map-derived corner jogs
  # without overlapping end caps. The east front already has a 0.50m wall.
  wall_band=self.core.difference(self.core.buffer(-.42,join_style=2))
  wall_band=wall_band.difference(rect(18.44,-100,100,100))
  self.b.plan_prism(wall_band,10.2,12.75,'old limestone','central-upper/continuous-return-wall-band')
  q=list(orient(self.core,sign=1).exterior.coords)
  for i,(a,b) in enumerate(zip(q,q[1:])):
   if abs(a[0]-18.94)<.02 and abs(b[0]-18.94)<.02:continue
   f=Facade(self.b,a,b,f'central-upper/side-{i}')
   self.courses(f,rect(-f.length/2,10.2,f.length/2,12.75))
  self.b.plan_prism(self.core.buffer(-.4),12.5,12.72,'roof gravel','central-upper-roof')
  self.front()
  # Photo-observed historic long-wing roof coping, distinct from modern rooftop gardens.
  for i,area in enumerate([rect(1.1,21.84,32.71,35.62),rect(1.59,-32.75,30.67,-21.53)]):
   a=area.buffer(-.62,join_style=2);ring=a.difference(a.buffer(-.35,join_style=2))
   self.b.plan_prism(ring,10.32,10.62,'stone carved',f'old-wing-roof-{i}/raised-perimeter-coping')
  # Garden strips on the four modern roof blocks, as in the licensed aerial.
  for k,(x0,y0,x1,y1) in enumerate([(-26,-61,-11,-36),(9,-60,24,-35),(-26,38,-13,61),(11,37,25,62)]):
   area=rect(x0,y0,x1,y1);inset=area.buffer(-.7,join_style=2)
   self.b.plan_prism(area,10.4,10.50,'garden soil',f'roof-garden-{k}/soil')
   for j,dep in enumerate([0,2.1,4.2]):
    a=inset.buffer(-dep,join_style=2)
    if a.is_empty:continue
    ring=a.difference(a.buffer(-.5,join_style=2));self.b.plan_prism(ring,10.5,10.73,'garden hedge',f'roof-garden-{k}/hedge-{j}')
 def old_wing_end(self,f):
  # The licensed 2019 aerial shows one axial high window and a small arched door.
  door=opening(0,.10,1.75,2.75,.87,22);win=rect(-.46,4.9,.46,9.2)
  self.pane(f,door,'axial-arched-door',2,2,frame='old red door',glass='old red door',trim=True)
  self.pane(f,win,'axial-high-window',2,5)
  surface=f.wall(0,10.45,[door,win],thickness=.42,material='old limestone');self.courses(f,surface)
  f.prism(door.buffer(.23).difference(door).intersection(rect(-100,0,100,100)),-.015,.15,'stone carved','door-arch-surround')
  f.box(0,4.67,2.15,.20,.83,.29,'stone carved','window-small-balcony/slab')
  for du in [-.83,.83]:
   f.box(du,4.99,.12,.55,.18,.62,'stone carved','window-small-balcony/post')
   f.box(du,4.42,.16,.30,.5,.14,'stone carved','window-small-balcony/bracket')
  f.box(0,5.22,2.15,.10,.17,.62,'stone carved','window-small-balcony/rail')
  for du in [-.55,-.27,0,.27,.55]:f.box(du,4.98,.07,.42,.12,.62,'stone carved','window-small-balcony/baluster')
  f.beam(.24,.32,.1,'granite',label='plinth');f.beam(10.45,.18,.22,'stone carved',label='cornice')
  f.box(0,10.64,f.length,.34,.35,-.12,'old limestone','parapet');f.beam(10.85,.12,.11,'stone carved',label='coping')
  self.mark('photo_observed_old_wing_east_end',f.label,high_windows=1,arched_doors=1,small_stone_balcony=True,dimensions_estimated=True)
 def south_entry(self,f):
  # Real open wall polygons, with inset glazing and one projecting canopy.
  door=rect(-f.length/2+.6,.25,f.length/2-.6,4.65)
  upper=rect(-f.length/2+1.3,6.7,f.length/2-1.3,8.5)
  self.pane(f,door,'wide-glazed-entry',6,2,glass='glass grey')
  self.pane(f,upper,'upper-horizontal-window',4,1,glass='glass grey')
  surface=f.wall(0,10.4,[door,upper],thickness=.42,material='modern fluted stone')
  self.courses(f,surface,True)
  f.box(0,4.9,f.length+.4,.32,1.5,.6,'modern fluted stone','canopy')
  f.beam(10.8,.12,.15,'stone carved',label='parapet-cap')
  self.mark('south_modern_entrance',f.label,wide_openings=2,frontal_glazing_is_recessed=True)
 def painted_band(self,cx,cy,hx,hy,z,label):
  pts=[(cx-hx,cy-hy),(cx+hx,cy-hy),(cx+hx,cy+hy),(cx-hx,cy+hy),(cx-hx,cy-hy)]
  for j,(a,b) in enumerate(zip(pts,pts[1:])):
   f=Facade(self.b,a,b,f'{label}/side-{j}');f.box(0,z,f.length,.74,.38,-.08,'paint blue','beam')
   for dz in [-.34,.34]:f.box(0,z+dz,f.length,.065,.46,0,'paint turquoise','border')
   n=max(1,round(f.length/1.3));pitch=f.length/n
   for k in range(n):
    u=-f.length/2+(k+.5)*pitch
    p=Polygon([(u-pitch*.36,z),(u-pitch*.24,z-.20),(u+pitch*.24,z-.20),(u+pitch*.36,z),(u+pitch*.24,z+.20),(u-pitch*.24,z+.20)])
    f.prism(p,.10,.13,'paint cream','cartouche-edge');f.prism(p.buffer(-.045),.13,.15,'paint turquoise','cartouche-field')
    f.line((u-pitch*.22,z,.17),(u+pitch*.22,z,.17),.025,'paint cream',6,'stylized-paint-line')
    # Multi-layer dougong block and outward bracket arms, individually 3D.
    for layer,(w,d,dz) in enumerate([(.26,.45,.45),(.50,.68,.63),(.81,.88,.80)]):
     f.box(u,z+dz,w,.13,d,d*.22,'paint turquoise' if layer!=1 else 'paint vermilion',f'dougong-{k}/arm-{layer}')
     for side in [-1,1]:f.box(u+side*w*.38,z+dz+.10,.14,.20,d*.75,d*.23,'paint cream',f'dougong-{k}/block-{layer}')
   self.mark('dougong_and_polychrome_band',f.label,brackets=n,pattern_is_stylized_not_traced=True)
 def roof(self):
  cx=12.0;cy=-1.12
  # Pavilion stone drum with three actual red arched east apertures.
  drum=rect(6.2,cy-5.55,17.8,cy+5.55);pts=list(orient(drum,sign=1).exterior.coords)
  for i,(a,b) in enumerate(zip(pts,pts[1:])):
   a=list(a);b=list(b)
   if abs(a[1]-b[1])<.001:
    a[0]=min(17.4,max(6.6,a[0]));b[0]=min(17.4,max(6.6,b[0]))
   f=Facade(self.b,a,b,f'pavilion-drum-{i}');holes=[]
   for j,dx in enumerate([-2.35,0,2.35]):
    if abs(f.n[0])>.8:p=opening(dx,13.0,1.3,1.75,.65,20)
    else:p=opening(dx,13.0,1.2,1.65,.6,20)
    holes.append(p);self.pane(f,p,f'red-arch-{j}',3,4,frame='old red door',glass='old red door',trim=True)
   area=f.wall(12.75,15.4,holes,thickness=.4,material='old limestone');self.courses(f,area)
  self.painted_band(cx,cy,6.0,5.75,15.05,'lower-polychrome')
  # Lower hipped eave is a true open ring: the upper tier emerges through it.
  outer=(7.0,6.9);inner=(4.4,4.8);n=7 if self.lod else 12
  for side in range(4):
   # Four trapezoid roof strips; mapping uses x/y swapped for N/S planes.
   long_y=side<2;sign=-1 if side%2==0 else 1
   width0=inner[1] if long_y else inner[0];width1=outer[1] if long_y else outer[0]
   dep0=inner[0] if long_y else inner[1];dep1=outer[0] if long_y else outer[1]
   def point(s,t):
    depth=dep0+(dep1-dep0)*t;along=s*(width0+(width1-width0)*t)
    z=15.72+1.65*(1-t)**1.55+.42*abs(s)**8*t**3
    return [cx+sign*depth,cy+along,z] if long_y else [cx+along,cy+sign*depth,z]
   self.roof_surface(point,n,'lower-roof',side,sign,long_y)
  # Clerestory below upper roof.
  self.box([cx,cy,17.52],[8.4,9.2,.8],'old red door','upper-clerestory-core')
  self.painted_band(cx,cy,4.35,4.75,17.75,'upper-polychrome')
  # Xieshan: front/back pitches retain a gable above the shortened hipped ends.
  hx=5.3;hy=5.7;ridge_half=3.9;break_t=.65
  for side,sign in enumerate([-1,1]):
   def point(s,t):
    half=ridge_half+(hy-ridge_half)*max(0,(t-break_t)/(1-break_t))
    return [cx+sign*hx*t,cy+s*half,18.49+3.12*(1-t)**1.55+.42*abs(s)**9*t**4]
   self.roof_surface(point,n,'upper-roof-main',side,sign,True)
  # Lower hip planes on N/S end; triangular upper gables remain distinct.
  zb=18.49+3.12*(1-break_t)**1.55
  for side,sgn in enumerate([-1,1]):
   def hip(s,t):return [cx+s*(hx*break_t+(hx-hx*break_t)*t),cy+sgn*(ridge_half+(hy-ridge_half)*t),18.49+(zb-18.49)*(1-t)+.42*abs(s)**9*t**4]
   self.roof_surface(hip,6 if self.lod else 10,'upper-roof-hip',side,sgn,False)
   gable=Polygon([(-hx*break_t,zb),(hx*break_t,zb),(0,21.60)])
   f=Facade(self.b,[cx+hx*break_t,cy+sgn*ridge_half],[cx-hx*break_t,cy+sgn*ridge_half],f'upper-gable-{side}') if sgn>0 else Facade(self.b,[cx-hx*break_t,cy+sgn*ridge_half],[cx+hx*break_t,cy+sgn*ridge_half],f'upper-gable-{side}')
   f.prism(gable,-.10,.04,'paint vermilion','triangular-gable')
   for z in [19.4,19.8,20.2]:
    area=gable.intersection(rect(-5,z-.035,5,z+.035));f.prism(area,.04,.07,'paint turquoise','gable-rail')
  self.line([cx,cy-ridge_half,21.65],[cx,cy+ridge_half,21.65],.15,'glazed gold','main-ridge')
  # End finials are bounded stylized profiles; individual historic beasts are not asserted.
  for s in [-1,1]:
   y=cy+s*ridge_half
   self.b.tube([[cx,y-s*.4,21.65],[cx,y,21.75],[cx,y+s*.22,22.0],[cx,y+s*.30,22.25],[cx,y+s*.15,22.36]],.15,'glazed gold',8,'ridge-end-finial')
  self.mark('double_eave_xieshan_roof','pavilion',upper_eave_nominal_m=18.49,actual_finial_peak_m=22.51,roof_dimensions_estimated=True,individual_tiles=not self.lod)
 def roof_surface(self,point,n,label,side,sign,long_y):
  vertices=[point(s,t) for t in np.linspace(0,1,n+1) for s in np.linspace(-1,1,n*2+1)];stride=n*2+1;faces=[]
  for j in range(n):
   for i in range(n*2):
    ids=[j*stride+i,j*stride+i+1,(j+1)*stride+i+1,(j+1)*stride+i]
    a,b,c=[np.array(vertices[k]) for k in ids[:3]]
    if np.cross(b-a,c-a)[2]<0:ids.reverse()
    faces.append(ids)
  self.b.add(vertices,faces,'glazed ochre',f'{label}/{side}/roof-shell')
  # Tile ridges follow the actual curved slope, not a flat coloured plane.
  width=np.linalg.norm(np.array(point(1,1))-np.array(point(-1,1)));count=max(6,int(width/(.34 if self.lod else .19)))
  for j,s in enumerate(np.linspace(-1,1,count+1)):
   # The lower roof N/S slopes share both hip-edge tiles with E/W slopes.
   # E/W own those exact edge tiles; emitting them twice makes Blender drop duplicate faces.
   if label=='lower-roof' and side>=2 and j in (0,count):continue
   pts=[np.array(point(s,t))+[0,0,.052] for t in np.linspace(0,1,6 if self.lod else 10)]
   self.b.tube(pts,.056 if self.lod else .048,'glazed gold',5 if self.lod else 6,f'{label}/{side}/tile-ridge-{j}')
   if not self.lod:
    for k,t in enumerate(np.linspace(.18,1,7)):
     p=np.array(point(s,t))+[0,0,.062]
     self.line(p+[-.035,0,0] if not long_y else p+[0,-.055,0],p+[.035,0,0] if not long_y else p+[0,.055,0],.019,'ridge shadow',f'{label}/{side}/tile-joint-{j}-{k}')
  edge=[np.array(point(s,1))+[0,0,.02] for s in np.linspace(-1,1,18)]
  self.b.tube(edge,.12,'glazed gold',8,f'{label}/{side}/eave-roll')
  for end in [-1,1]:
   # E/W lower slopes also own the shared hip roll and its three ridge figures.
   if label=='lower-roof' and side>=2:continue
   pts=[np.array(point(end,t))+[0,0,.13] for t in np.linspace(0,1,10)]
   self.b.tube(pts,.12,'glazed gold',8,f'{label}/{side}/hip-roll-{end}')
   for j,t in enumerate([.78,.88,.98]):
    p=np.array(point(end,t));self.b.lathe(p[:2],[(p[2]+.12,.10),(p[2]+.29,.10),(p[2]+.40,.035)],'glazed gold',6,f'{label}/{side}/stylized-ridge-figure-{end}-{j}')
 def build(self):
  self.compound();self.roof();seen=Counter()
  for p in self.b.parts:
   label=p['label'];seen[label]+=1
   if seen[label]>1:p['label']=label+f'/repeat-{seen[label]-1}'
  return self

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--lod',action='store_true');a=ap.parse_args()
 if a.out.exists():raise ValueError('Refuse existing output')
 m=Library(a.lod).build();a.out.mkdir(parents=True)
 extras={'id':'yangpu-library','anchor':m.anchor,'rotation_y':0,'axis':'glTF east/up/south, source ENU metres','ground_base_m':0,'height_estimate_m':22.51,'source_footprint_sha256':sha(HERE/'calibration.json'),'scope':'Complete old and modern connected library, two open inner courtyards; exterior only','textures_embedded':False,'lod_authored_simplification':a.lod,'copyright':'Geometry/code MIT; footprint OpenStreetMap contributors/Overture ODbL-1.0; photo observations attributed separately'}
 report=m.b.save(a.out/'yangpu-library.glb',extras)
 write(a.out/'features.json',{'features':m.features,'counts':dict(Counter(x['kind'] for x in m.features)),'calibration_sha256':sha(HERE/'calibration.json'),'lod':a.lod,'unmeasured_dimensions_are_estimates':True})
 write(a.out/'metadata.json',{'id':'yangpu-library','anchor':m.anchor,'rotation_y':0,'height_estimate_m':22.51,'ground_base_m':0,'raw':{k:report[k] for k in ['file','bytes','sha256','triangles','materials','parts','bounds_glb']},'features':len(m.features),'browser_passed':False,'appearance_review_passed':False,'lod':a.lod})
 print(json.dumps({k:report[k] for k in ['file','bytes','sha256','triangles','materials','parts','bounds_glb']}))
if __name__=='__main__':main()
