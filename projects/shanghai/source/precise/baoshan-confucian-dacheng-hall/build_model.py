#!/usr/bin/env python3
"""Evidence-bound Baoshan Dacheng Hall, modern post-2015 exterior.
Geometry/code MIT. Photo observations attributed in calibration.json. No pixels.
Local x/y is the building's orthogonal frame, then rotated to frozen source ENU.
"""
from pathlib import Path
from collections import Counter
import argparse, json, math, hashlib, sys
import numpy as np
from shapely.geometry import Polygon, box as rect
from shapely.ops import unary_union
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'common'))
from photo_architecture import Builder, Facade
ID='baoshan-confucian-dacheng-hall'
P={
 'aged red brown timber':{'color':[.078,.032,.022],'roughness':.91},
 'worn timber edges':{'color':[.135,.069,.041],'roughness':.88},
 'dark door timber':{'color':[.055,.036,.027],'roughness':.88},
 'lime wall':{'color':[.72,.72,.67],'roughness':.95},
 'brick bench render':{'color':[.59,.61,.57],'roughness':.95},
 'granite base':{'color':[.37,.38,.35],'roughness':.94},
 'carved stone':{'color':[.49,.49,.44],'roughness':.93},
 'worn paving':{'color':[.43,.44,.405],'roughness':.94},
 'stone joints':{'color':[.24,.255,.24],'roughness':.96},
 'roof underlay':{'color':[.12,.13,.125],'roughness':.96},
 'grey tile 0':{'color':[.24,.255,.25],'roughness':.93},
 'grey tile 1':{'color':[.215,.23,.228],'roughness':.95},
 'grey tile 2':{'color':[.27,.278,.267],'roughness':.93},
 'ridge ceramic':{'color':[.30,.32,.31],'roughness':.92},
 'gilt':{'color':[.50,.36,.13],'roughness':.68,'metallic':.15},
 'plaque ground':{'color':[.065,.065,.052],'roughness':.83},
 'aged iron':{'color':[.11,.115,.105],'roughness':.73,'metallic':.25},
}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
class Contours(BasePen):
 def __init__(self,gs):super().__init__(gs);self.paths=[];self.current=[]
 def _moveTo(self,p):self.current=[p]
 def _lineTo(self,p):self.current.append(p)
 def _curveToOne(self,a,b,c):
  p=np.array(self._getCurrentPoint());a=np.array(a);b=np.array(b);c=np.array(c)
  self.current.extend(tuple((1-t)**3*p+3*(1-t)**2*t*a+3*(1-t)*t*t*b+t**3*c) for t in np.linspace(0,1,9)[1:])
 def _qCurveToOne(self,a,b):
  p=np.array(self._getCurrentPoint());a=np.array(a);b=np.array(b)
  self.current.extend(tuple((1-t)**2*p+2*(1-t)*t*a+t*t*b) for t in np.linspace(0,1,9)[1:])
 def _closePath(self):
  if len(self.current)>2:self.paths.append(self.current)
  self.current=[]
 def _endPath(self):self._closePath()
class Hall:
 def __init__(self,lod=False,height=13.):
  self.b=Builder(P);self.lod=lod;self.height=height;self.zscale=(height-1.0)/12.0
  self.g=json.loads((HERE/'geometry-input.json').read_text());self.features=[]
  poly=np.array(self.g['model_geometry_local_east_north_m']['coordinates'][0][:4]);v=poly[1]-poly[0]
  self.theta=math.atan2(v[1],v[0]);self.hx=float(np.linalg.norm(v))/2;self.hy=float(np.linalg.norm(poly[2]-poly[1]))/2
  self.R=np.array([[math.cos(self.theta),-math.sin(self.theta),0],[math.sin(self.theta),math.cos(self.theta),0],[0,0,1.]])
  self.floor=1.;self.corex=6.36;self.corey=4.22;self.px=7.725;self.py=5.71
  self.lowerInner=(5.4,4.35);self.ux=8.5;self.uy=6.15;self.ridge=5.5;self.breaky=3.5
 def Z(self,z):return 1+(z-1)*self.zscale
 def mark(self,kind,**kw):self.features.append({'kind':kind,**kw})
 def box(self,c,s,m,label):self.b.box(c,s,m,label=label)
 def shell(self,vertices,quads,thick,material,label):
  v=np.array(vertices,float);tri=[]
  for q in quads:
   for k in range(1,len(q)-1):
    t=[q[0],q[k],q[k+1]]
    if np.cross(v[t[1]]-v[t[0]],v[t[2]]-v[t[0]])[2]<0:t.reverse()
    tri.append(tuple(t))
  n=len(v);vs=np.vstack([v,v-[0,0,thick]]);fs=tri+[tuple(i+n for i in t[::-1]) for t in tri]
  counts=Counter(tuple(sorted((a,b))) for t in tri for a,b in zip(t,t[1:]+t[:1]))
  for t in tri:
   for a,b in zip(t,t[1:]+t[:1]):
    if counts[tuple(sorted((a,b)))]==1:fs.append((b,a,a+n,b+n))
  self.b.add(vs,fs,material,label)
 def facade(self,hx,hy,edge,label):
  p=[[-hx,-hy],[hx,-hy],[hx,hy],[-hx,hy]]
  return Facade(self.b,p[edge],p[(edge+1)%4],label)
 def lower(self,field,s,t):
  u=2*s-1;ix,iy=self.lowerInner
  if field<2:
   x=u*(ix+(self.hx-ix)*t);y=(-1 if field==0 else 1)*(iy+(self.hy-iy)*t)
  else:
   x=(-1 if field==2 else 1)*(ix+(self.hx-ix)*t);y=u*(iy+(self.hy-iy)*t)
  z=4.15+2.05*(1-t)**1.65+.62*t**3*abs(u)**8
  return np.array([x,y,self.Z(z)])
 def upper(self,field,s,t):
  u=2*s-1
  def profile(t):return 6.80+4.90*(1-t)**1.55
  if field<2:
   y=self.uy*t;w=self.ridge+(self.ux-self.ridge)*max(0,(y-self.breaky)/(self.uy-self.breaky))
   return np.array([u*w,(-1 if field==0 else 1)*y,self.Z(profile(t)+.65*t**3*abs(u)**8)])
  x=self.ridge+(self.ux-self.ridge)*t;w=self.breaky+(self.uy-self.breaky)*t;tt=w/self.uy
  return np.array([(-1 if field==2 else 1)*x,u*w,self.Z(profile(tt)+.65*tt**3*abs(u)**8)])
 def roofZ(self,x,y,tier):
  if tier=='lower':
   ix,iy=self.lowerInner
   ty=(abs(y)-iy)/(self.hy-iy);tx=(abs(x)-ix)/(self.hx-ix)
   if ty>=tx:t=max(0,ty);w=ix+(self.hx-ix)*t;return float(self.lower(0,(x/w+1)/2,t)[2])
   t=max(0,tx);w=iy+(self.hy-iy)*t;return float(self.lower(2,(y/w+1)/2,t)[2])
  ay=abs(y);ax=abs(x)
  if ax<=self.ridge or ay>=self.breaky+(self.uy-self.breaky)*(ax-self.ridge)/(self.ux-self.ridge):
   w=self.ridge+(self.ux-self.ridge)*max(0,(ay-self.breaky)/(self.uy-self.breaky));return float(self.upper(0,(x/w+1)/2,ay/self.uy)[2])
  t=(ax-self.ridge)/(self.ux-self.ridge);w=self.breaky+(self.uy-self.breaky)*t;return float(self.upper(2,(y/w+1)/2,t)[2])
 def roof_patch(self,point,tier,field):
  n=7 if self.lod else 12;nu=n*2
  vs=[point(s,t) for t in np.linspace(0,1,n+1) for s in np.linspace(0,1,nu+1)]
  fs=[(j*(nu+1)+i,j*(nu+1)+i+1,(j+1)*(nu+1)+i+1,(j+1)*(nu+1)+i) for j in range(n) for i in range(nu)]
  self.shell(vs,fs,.085,'roof underlay',f'{tier}/field{field}/closed-curved-shell')
  width=np.linalg.norm(point(1,1)-point(0,1));count=max(10,round(width/(.39 if self.lod else .24)))
  for i in range(count):
   s=(i+.5)/count;pts=[point(s,t)+[0,0,.052] for t in np.linspace(0,1,7 if self.lod else 12)]
   self.b.tube(pts,.073 if self.lod else .062,f'grey tile {i%3}',6,f'{tier}/field{field}/cap-tile-course-{i}')
   if not self.lod:
    # Pan-tile cross-sections and each lap are actual shaped surfaces, not images.
    verts=[];rows=9;cols=2
    for t in np.linspace(0,1,rows):
     for j in range(cols+1):
      ss=(i+j/cols)/count;p=point(ss,t);p[2]+=.012+.036*(abs(j/cols-.5)*2)**2;verts.append(p)
    quads=[(k*(cols+1)+j,k*(cols+1)+j+1,(k+1)*(cols+1)+j+1,(k+1)*(cols+1)+j) for k in range(rows-1) for j in range(cols)]
    self.shell(verts,quads,.018,f'grey tile {(i+1)%3}',f'{tier}/field{field}/concave-pan-{i}')
    for j,t in enumerate(np.linspace(.12,.99,5)):
     p=point(s,t)+[0,0,.054];dir=point(s,min(1,t+.008))-point(s,max(0,t-.008));dir/=np.linalg.norm(dir)
     self.b.tube([p-dir*.009,p+dir*.009],.066,'ridge ceramic',6,f'{tier}/field{field}/tile-lap-{i}-{j}')
   end=point(s,1);out=end-point(s,.98);out/=np.linalg.norm(out);p=end+[0,0,.054]
   self.b.tube([p-out*.025,p+out*.035],.078,'ridge ceramic',8 if self.lod else 12,f'{tier}/field{field}/circular-end-tile-{i}')
   if not self.lod:
    crest=[p+[0,0,.05],p-out*.035+[0,0,.15],p-out*.025+[0,0,.25],p+out*.018+[0,0,.30]]
    self.b.tube(crest,.024,'ridge ceramic',5,f'{tier}/field{field}/small-upright-end-crest-{i}')
    cross=np.cross(out,[0,0,1]);cross/=np.linalg.norm(cross);vertical=np.cross(cross,out)
    ring=[p+out*.037+.052*(math.cos(a)*cross+math.sin(a)*vertical) for a in np.linspace(0,math.tau,9)]
    self.b.tube(ring,.009,'grey tile 2',4,f'{tier}/field{field}/end-tile-ring-{i}')
  for i,s in enumerate(np.linspace(.03,.97,10 if self.lod else 22)):
   pts=[point(s,t)-[0,0,.18] for t in np.linspace(.05,1,8)]
   self.b.tube(pts,.038,'aged red brown timber',5,f'{tier}/field{field}/underside-rafter-{i}')
  edge=[point(s,1)-[0,0,.09] for s in np.linspace(0,1,25)]
  self.b.tube(edge,.09,'aged red brown timber',8,f'{tier}/field{field}/eave-fascia')
  # Shared hips are owned by front/back only; avoid coincident duplicates.
  if field<2:
   start=0 if tier=='lower' else self.breaky/self.uy
   for side in [0,1]:
    pts=[point(side,t)+[0,0,.14] for t in np.linspace(start,1,17)]
    self.b.tube(pts,.15,'ridge ceramic',10,f'{tier}/field{field}/hip-ridge-{side}')
    for k,t in enumerate([.72,.80,.88,.96]):
     p=point(side,t)+[0,0,.22]
     self.beast(p,f'{tier}/field{field}/hip-figure-{side}-{k}',.75 if tier=='lower' else 1.)
  self.mark('curved_tiled_roof_patch',tier=tier,field=field,cap_courses=count,roof_shell_thickness_m=.085)
 def beast(self,p,label,scale=1.):
  # Small photographed ridge figures reconstructed as restrained silhouettes.
  x,y,z=p;s=scale
  self.b.lathe((x,y),[(z,.10*s),(z+.11*s,.12*s),(z+.25*s,.07*s),(z+.34*s,.045*s)],'ridge ceramic',6 if self.lod else 8,label+'/seated-body')
  self.b.tube([[x,y,z+.25*s],[x+.02*s,y-.04*s,z+.39*s],[x+.08*s,y-.06*s,z+.43*s]],.055*s,'ridge ceramic',6,label+'/head')
 def roofs(self):
  for tier,fn in [('lower',self.lower),('upper',self.upper)]:
   for field in range(4):self.roof_patch(lambda s,t:fn(field,s,t),tier,field)
  zb=self.upper(0,.5,self.breaky/self.uy)[2]
  for side in [-1,1]:
   f=Facade(self.b,[side*self.ridge,-self.breaky] if side>0 else [side*self.ridge,self.breaky],[side*self.ridge,self.breaky] if side>0 else [side*self.ridge,-self.breaky],f'upper-gable-{side}')
   # Curved gable follows the measured-in-model main-pitch profile, not an oversized triangle.
   pts=[(-self.breaky,zb),(self.breaky,zb)]+[(y,self.upper(0,.5,abs(y)/self.uy)[2]-.085) for y in np.linspace(self.breaky,-self.breaky,31)]
   gable=Polygon(pts).buffer(0)
   f.prism(gable,-.085,.015,'aged red brown timber','curved-gable-infill')
   for z in np.arange(zb+.3,self.Z(11.7),.42):
    band=gable.intersection(rect(-self.breaky,z-.027,self.breaky,z+.027));f.prism(band,.016,.04,'worn timber edges','horizontal-gable-boarding')
  # Two photographed pierced ceramic ridge bands, with actual repeated openings.
  f=Facade(self.b,[-self.ridge,0],[self.ridge,0],'upper-main-ridge-band')
  R=self.Z(11.70)
  for k,dz in enumerate([.07,.28]):
   outer=rect(-self.ridge,R+dz,self.ridge,R+dz+.16)
   from shapely.geometry import Point
   holes=[Point(x,R+dz+.08).buffer(.055,resolution=4 if self.lod else 6) for x in np.arange(-self.ridge+.12,self.ridge-.10,.23 if self.lod else .185)]
   f.prism(outer.difference(unary_union(holes)),-.12,.12,'ridge ceramic',f'pierced-band-{k}')
  for dz in [.035,.25,.475]:f.box(0,R+dz,2*self.ridge+.12,.055,.30,0,'ridge ceramic','continuous-ridge-coping')
  for side in [-1,1]:
   # Upturned open-jaw ceramic animal silhouette, observed modernphoto13;
   # small sculptural anatomy is estimated rather than claimed traced.
   profile=[(-.40,12.08),(.02,12.08),(.20,12.29),(.20,12.54),(.31,12.68),(.41,12.74),(.34,12.79),(.22,12.75),(.20,12.81),(.35,12.88),(.30,12.95),(.18,12.94),(.09,12.81),(-.02,12.57),(-.17,12.31),(-.40,12.20)]
   mapper=lambda u,z,d:(side*(self.ridge+u),-side*d,self.Z(z))
   self.b.prism(Polygon(profile),-.095,.095,mapper,'ridge ceramic',f'upper/ridge-terminal-animal-{side}')
   for facing in [-1,1]:
    self.b.tube([[side*(self.ridge+.18),facing*.095,self.Z(12.78)],[side*(self.ridge+.18),facing*.115,self.Z(12.78)]],.025,'grey tile 1',8,f'upper/ridge-terminal-eye-{side}-{facing}')
    self.b.tube([[side*(self.ridge+.25),facing*.10,self.Z(12.72)],[side*(self.ridge+.48),facing*.13,self.Z(12.78)],[side*(self.ridge+.64),facing*.16,self.Z(12.88)]],.015,'ridge ceramic',5,f'upper/ridge-terminal-whisker-{side}-{facing}')
   for k,z in enumerate([12.33,12.45,12.57,12.69]):
    x=-.12+(z-12.33)*.43
    self.b.tube([[side*(self.ridge+x),0,self.Z(z)],[side*(self.ridge+x-.12),0,self.Z(z+.07)]],.025,'ridge ceramic',5,f'upper/ridge-terminal-crest-{side}-{k}')
  self.mark('double_eave_xieshan',ridge_nominal_z_m=self.Z(11.70),height_parameter_m=self.height,shape='True open-ring lower roof; 2 main upper pitches plus 2 lower hips and separate curved gable infills')
 def bracket(self,f,u,base,tier,label):
  start=len(self.b.parts)
  for k in range(3):
   w=.40+k*.20;d=.03+k*.075;z=base+k*.14
   xs=np.linspace(-w/2,w/2,7);low=[(x,z+.09*(abs(x)/(w/2))**2) for x in xs];up=[(x,z+.09*(abs(x)/(w/2))**2+.12) for x in xs[::-1]]
   self.b.prism(Polygon(low+up),-.10,.10,lambda x,zz,dd:f.point(u+x,zz,d+dd),'aged red brown timber',label+f'/curved-arm-{k}')
   f.box(u,z+.08,.16,.17,.45+k*.10,d,'worn timber edges',label+f'/radial-arm-{k}')
   for sign in [-1,1]:f.box(u+sign*w*.38,z+.19,.14,.15,.16,d,'aged red brown timber',label+f'/bearing-block-{k}-{sign}')
  # Seat bracket to actual local roof surface; no support passing through roof.
  min_clear=min(self.roofZ(v[0],v[1],tier)-v[2] for p in self.b.parts[start:] for v in p['vertices'])
  shift=max(0,.16-min_clear)
  for p in self.b.parts[start:]:p['vertices']=[(x,y,z-shift) for x,y,z in p['vertices']]
  v=[]
  for d in [-.13,.18]:
   for x in [-.16,.16]:
    q=f.point(u+x,0,d);q[2]=self.roofZ(q[0],q[1],tier)-.062;v.append(q)
  # Quad is CCW in horizontal plane, then use closed variable-height solid.
  bottom=base+.39-shift;n=4;top=np.array(v)[[0,1,3,2]];low=top.copy();low[:,2]=bottom
  if top[:,2].min()>bottom:
   vv=np.vstack([top,low]);fs=[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]
   if np.cross(top[1]-top[0],top[2]-top[0])[2]<0:fs=[tuple(reversed(x)) for x in fs]
   self.b.add(vv,fs,'aged red brown timber',label+'/sloped-bearing-saddle')
  self.mark('bracket_set',label=label,tier=tier,arm_downshift_m=shift,roof_clearance_m=.16)
 def column(self,x,y,top,label):
  seg=12 if self.lod else 20
  self.b.lathe((x,y),[(self.floor-.015,.30),(self.floor+.04,.32),(self.floor+.20,.29),(self.floor+.27,.235)],'carved stone',seg,label+'/round-stone-foot')
  self.b.lathe((x,y),[(self.floor+.22,.205),(self.floor+.34,.22),(top-.3,.20),(top,.19)],'aged red brown timber',seg,label+'/tapered-round-shaft')
  self.mark('round_column',label=label,xy=[x,y],base_m=self.floor+.22,top_m=top)
 def walls_frame(self):
  xg=[-self.corex,-2.75,2.75,self.corex]
  top=self.Z(3.85)
  # Outer colonnade: six front/rear positions = 3 enclosed bays + two side porch openings.
  for y in [-self.py,self.py]:
   for i,x in enumerate([-self.px,*xg,self.px]):self.column(x,y,top,f'outer-colonnade/{y}/column-{i}')
  for x in [-self.px,self.px]:
   for i,y in enumerate([-2.,2.]):self.column(x,y,top,f'side-colonnade/{x}/column-{i}')
  for y in [-self.corey,self.corey]:
   for i,x in enumerate(xg):self.column(x,y,self.Z(4.4),f'inner-frame/{y}/post-{i}')
  for edge in range(4):
   f=self.facade(self.px,self.py,edge,f'outer-frame-{edge}')
   f.box(0,self.Z(3.87),f.length+.15,.30,.26,0,'aged red brown timber','long-eave-tie')
   n=round(f.length/1.4)
   for i,u in enumerate(np.linspace(-f.length/2+.14,f.length/2-.14,n+1)):self.bracket(f,float(u),self.Z(4.08),'lower',f'lower-bracket/{edge}/{i}')
  for edge in [1,2,3]:
   f=self.facade(self.corex,self.corey,edge,f'core-wall-{edge}')
   f.wall(self.floor,self.Z(4.42),[],.25,'lime wall')
   f.box(0,self.floor+.14,f.length,.28,.29,.015,'brick bench render','low-skirt')
   positions=[-self.corex,-2.75,2.75,self.corex] if edge==2 else [-self.corey,0,self.corey]
   for u in positions:f.box(u,(self.Z(4.42)+self.floor)/2,.15,self.Z(4.42)-self.floor,.10,.02,'aged red brown timber','exposed-timber-wall-frame')
   f.box(0,self.Z(4.36),f.length,.24,.20,.02,'aged red brown timber','wall-head-beam')
  for edge in range(4):
   f=self.facade(self.corex,self.corey,edge,f'concealed-upper-timber-{edge}')
   tops=[]
   for u in np.linspace(-f.length/2,f.length/2,41):
    q=f.point(u,0,0);outside=abs(q[0])>self.lowerInner[0] or abs(q[1])>self.lowerInner[1]
    z=min(self.Z(6.22),self.roofZ(q[0],q[1],'lower')-.095) if outside else self.Z(6.22)
    tops.append((float(u),z))
   outline=Polygon([(-f.length/2,self.Z(4.41)),(f.length/2,self.Z(4.41))]+tops[::-1])
   f.wall(self.Z(4.41),self.Z(6.22),[],.18,'aged red brown timber',outline=outline)
  # Front facade consists of genuine open lattice leaves, with no opaque wall behind.
  f=self.facade(self.corex,self.corey,0,'front-three-bay-door')
  for i,(left,right,count) in enumerate([(-6.16,-2.95,4),(-2.55,2.55,8),(2.95,6.16,4)]):
   width=(right-left)/count
   for j in range(count):self.door_leaf(f,left+j*width,width-.018,1.10,self.Z(4.05),f'bay{i}/leaf{j}')
   f.box((left+right)/2,self.Z(4.24),right-left+.15,.23,.21,0,'aged red brown timber',f'bay{i}/lintel')
  # Four plain brick/rendered benches at side and rear corridor edges; gaps are left passable.
  for x in [-self.px,self.px]:
   for a,b in [(-self.py,-2.),(-2.,2.),(2.,self.py)]:
    self.box((x,(a+b)/2,self.floor+.215),(.26,b-a-.45,.43),'brick bench render','corridor/official-0.48m-brick-bench')
    self.box((x,(a+b)/2,self.floor+.455),(.36,b-a-.40,.05),'worn paving','corridor/bench-stone-seat')
  for sign in [-1,1]:
   a=2.75*sign;b=self.px*sign
   self.box(((a+b)/2,self.py,self.floor+.24),(abs(a-b)-.4,.26,.48),'brick bench render','rear-corridor/bench')
  # Upper timber drum under the second eave, not another copied door facade.
  for edge in range(4):
   f=self.facade(5.4,4.35,edge,f'upper-drum-{edge}')
   f.wall(self.Z(5.98),self.Z(6.65),[],.18,'aged red brown timber')
   if not self.lod:
    for k,u in enumerate(np.arange(-f.length/2+.15,f.length/2-.12,.22)):
     pts=[f.point(float(u)+.09*math.cos(t),self.Z(6.43)+.065*math.sin(t),.105) for t in np.linspace(0,math.tau,9)]
     self.b.tube(pts,.012,'grey tile 2',4,f'upper-drum/{edge}/interlocking-fascia-loop-{k}')
   for z in [6.10,6.30,6.50]:f.box(0,self.Z(z),f.length,.065,.065,.05,'worn timber edges','horizontal-fascia-strip')
   for i,u in enumerate(np.linspace(-f.length/2+.2,f.length/2-.2,9)):
    self.bracket(f,float(u),self.Z(6.55),'upper',f'upper-bracket/{edge}/{i}')
  self.plaque()
  # Actual black couplet boards; inscription remains untranscribed, no invented glyphs.
  for x in [-2.75,2.75]:
   f=Facade(self.b,[x-.24,-self.py-.205],[x+.24,-self.py-.205],f'front-couplet-board-{x}')
   f.box(0,2.55,.44,2.60,.06,.015,'plaque ground','untranscribed-inscription-board')
   for z in [1.30,3.80]:
    pts=[f.point(.09*math.cos(t),z+.045*math.sin(t),.05) for t in np.linspace(0,math.tau,9)]
    self.b.tube(pts,.009,'gilt',4,'couplet-board/gold-end-ornament')
  self.mark('couplet_boards',count=2,inscription_transcribed=False,reason='Photographs insufficient for exactfulltext; no invented letters')
  self.mark('official_configuration',enclosed_bays_width=3,enclosed_bays_depth=3,wrap_corridor=True,bench_height_m=.48,front_door_leaves=[4,8,4],front_door_state='closed, photographed2021; lattice holes remain open')
 def door_leaf(self,f,left,width,bottom,top,label):
  panel=rect(left,bottom,left+width,top);opening=rect(left+.055,bottom+1.08,left+width-.055,top-.12)
  # Separate true apertures in the timber leaf. No dark plate masquerading as glass.
  holes=[];nx=4 if self.lod else 6;nz=10 if self.lod else 15
  ox,oz,ex,ez=opening.bounds
  for i in range(nx):
   for j in range(nz):
    xa=ox+(ex-ox)*i/nx+.010;xb=ox+(ex-ox)*(i+1)/nx-.010;za=oz+(ez-oz)*j/nz+.010;zb=oz+(ez-oz)*(j+1)/nz-.010
    holes.append(rect(xa,za,xb,zb))
  f.prism(panel.difference(unary_union(holes)),-.045,.025,'dark door timber',label+'/pierced-lattice-leaf')
  for z0,z1 in [(bottom+.10,bottom+.28),(bottom+.34,bottom+.94)]:
   outside=rect(left+.07,z0,left+width-.07,z1);inside=outside.buffer(-.032,join_style=2)
   f.prism(outside.difference(inside),.025,.055,'worn timber edges',label+'/raised-panel-moulding')
   f.prism(inside,.026,.035,'dark door timber',label+'/lower-solid-panel')
  self.mark('door_lattice_leaf',label=label,actual_apertures=len(holes),width_m=width,lower_solid_panel=True)
 def plaque(self):
  f=self.facade(5.4,5.70,0,'vertical-dacheng-plaque');z=self.Z(6.15)
  f.box(0,z,.68,1.58,.12,.12,'plaque ground','board');outer=rect(-.35,z-.8,.35,z+.8);inner=outer.buffer(-.035,join_style=2)
  f.prism(outer.difference(inner),.18,.195,'worn timber edges','wood-border')
  font=TTFont(HERE/'plaque-glyphs.otf');gs=font.getGlyphSet();cmap=font.getBestCmap()
  for i,ch in enumerate('大成殿'):
   pen=Contours(gs);gs[cmap[ord(ch)]].draw(pen);poly=Polygon()
   for points in pen.paths:
    p=Polygon(points).buffer(0);poly=poly.symmetric_difference(p)
   from shapely.affinity import scale,translate
   a,b,c,d=poly.bounds;fac=.43/max(c-a,d-b);poly=scale(poly,xfact=fac,yfact=fac,origin=(0,0));a,b,c,d=poly.bounds;poly=translate(poly,xoff=-(a+c)/2,yoff=z+.49-i*.49-(b+d)/2)
   f.prism(poly,.196,.209,'gilt',f'actual-vector-glyph-{ch}')
  self.mark('plaque',text='大成殿',font='Noto Serif CJK Bold subset / SIL OFL1.1',historical_horizontal_museum_sign_omitted=True)
 def platform(self):
  self.b.plan_prism(rect(-8.20,-9.35,8.20,6.22),0,1.,'granite base','foundation/stone-terrace')
  self.b.plan_prism(rect(-8.24,-9.39,8.24,6.26),.91,1.01,'worn paving','foundation/coping')
  for back in [False,True]:
   steps=6;y0=6.22 if back else -9.35;sgn=1 if back else -1
   for i in range(steps):
    depth=(steps-i)*.30;z=(i+1)/steps
    for left,right in ([(-6.45,6.45)] if back else [(-3.25,-.75),(.75,3.25)]):
     ya,yb=sorted([y0-.015*sgn,y0+depth*sgn]);self.b.plan_prism(rect(left,ya,right,yb),0,z,'worn paving',f'foundation/{"rear" if back else "front"}-stair-{i}')
   self.mark('real_stair_treads',side='rear' if back else 'front',risers=steps,total_rise_m=1.,estimated=True)
  # Sloped imperial-way slab, central carved dragon, bordered by two clear stairways.
  y0=-11.15;y1=-9.35;z0=.14;z1=1.05
  vs=[[-.72,y0,z0],[.72,y0,z0],[.72,y1,z1],[-.72,y1,z1]]
  self.shell(vs,[(0,1,2,3)],.13,'carved stone','front/central-imperial-way-slab')
  def onslab(x,y,dz=.025):return np.array([x,y,z0+(z1-z0)*(y-y0)/(y1-y0)+dz])
  for x in [-.66,.66]:self.b.tube([onslab(x,y0+.05),onslab(x,y1-.05)],.025,'granite base',6,'dragon-slab/border')
  if not self.lod:
   ys=np.linspace(y0+.34,y1-.30,36);pts=[onslab(.22*math.sin((y-y0)*7),y,.045) for y in ys]
   self.b.tube(pts,.055,'carved stone',8,'dragon-slab/stylized-single-dragon-body')
   self.b.tube([onslab(-.12,y1-.4,.05),onslab(.02,y1-.25,.08),onslab(.20,y1-.30,.07)],.08,'carved stone',8,'dragon-slab/dragon-head')
   for k,y in enumerate(np.linspace(y0+.35,y1-.5,6)):
    x=.22*math.sin((y-y0)*7);self.b.tube([onslab(x,y,.04),onslab(x+.22*(-1 if k%2 else 1),y+.14,.04),onslab(x+.30*(-1 if k%2 else 1),y+.10,.04)],.022,'carved stone',6,'dragon-slab/cloud-and-claw-relief')
   ring=[onslab(.17*math.cos(a),y0+.30+.16*math.sin(a),.04) for a in np.linspace(0,math.tau,21)];self.b.tube(ring,.023,'carved stone',6,'dragon-slab/pearl')
  self.mark('imperial_way_relief',motif='single dragon holding pearl',source='official text and actual Meipian14 close photo',exact_carving_trace=False)
  # Front terrace granite rails with true geometric openings and relief scrolls.
  railfaces=[([-8.04,-9.20],[-3.40,-9.20]),([3.40,-9.20],[8.04,-9.20]),([-8.04,-6.3],[-8.04,-9.2]),([8.04,-9.2],[8.04,-6.3])]
  for k,(a,b) in enumerate(railfaces):
   f=Facade(self.b,a,b,f'front-stone-rail-{k}');n=max(2,round(f.length/1.25));step=f.length/n
   f.box(0,1.20,f.length,.18,.20,0,'carved stone','bottom-rail');f.box(0,1.90,f.length,.14,.23,0,'carved stone','handrail')
   for j in range(n+1):
    u=-f.length/2+j*step;f.box(u,1.60,.18,1.12,.19,0,'carved stone','square-railing-post');p=f.point(u,0,0)
    self.b.lathe(p[:2],[(2.13,.13),(2.20,.16),(2.28,.09),(2.31,.04)],'carved stone',8,'front-rail/lotus-post-finial')
   for j in range(n):
    u=-f.length/2+(j+.5)*step;out=rect(u-step/2+.12,1.28,u+step/2-.12,1.82)
    hole=Polygon([(u-.26,1.40),(u-.13,1.40),(u-.13,1.34),(u+.13,1.34),(u+.13,1.40),(u+.26,1.40),(u+.26,1.68),(u+.13,1.68),(u+.13,1.76),(u-.13,1.76),(u-.13,1.68),(u-.26,1.68)])
    f.prism(out.difference(hole),-.065,.065,'carved stone','pierced-geometric-balustrade')
    if not self.lod:
     for side in [-1,1]:
      pts=[f.point(u+side*.35+.065*math.cos(t),1.54+.09*math.sin(t),.072) for t in np.linspace(0,math.tau*1.5,20)]
      self.b.tube(pts,.012,'granite base',5,'front-rail/shallow-cloud-scroll')
  # Actual bounded paving joints, only on exposed terrace; no huge ground plane.
  if not self.lod:
   for x in np.arange(-7.9,8,.8):self.box((x,-7.6,1.013),(.008,3.38,.006),'stone joints','terrace/front-paving-joint')
   for y in np.arange(-9.2,-5.9,.65):self.box((0,y,1.014),(16.2,.008,.006),'stone joints','terrace/front-course-joint')
 def finish(self):
  self.platform();self.walls_frame();self.roofs()
  # All parts are closed components; flip only wholly negative oriented components.
  failures=[];volumes=[]
  for part in self.b.parts:
   vs=np.array(part['vertices']);fs=np.array(part['triangles']);vol=float(np.einsum('ij,ij->i',vs[fs[:,0]],np.cross(vs[fs[:,1]],vs[fs[:,2]])).sum()/6)
   if vol<0:part['triangles']=[tuple(reversed(t)) for t in part['triangles']];vol=-vol
   if vol<1e-10:failures.append(part['label'])
   volumes.append(vol);part['vertices']=(vs@self.R.T).tolist()
  assert not failures,failures[:10]
  self.mark('part_solids_audit',parts=len(self.b.parts),min_positive_signed_volume_m3=min(volumes),zero_volume_parts=0)
  duplicates={};removed=Counter();kinds=Counter()
  for pi,p in enumerate(self.b.parts):
   verts=np.asarray(p['vertices'],dtype='<f4')
   for ti,t in enumerate(p['triangles']):
    key=tuple(sorted(tuple(float(x) for x in verts[i]) for i in t))
    if key in duplicates:
     op,ot=duplicates[key];pv=np.asarray(self.b.parts[op]['vertices'],dtype='<f4');old=self.b.parts[op]['triangles'][ot]
     n0=np.cross(pv[old[1]]-pv[old[0]],pv[old[2]]-pv[old[0]]);n1=np.cross(verts[t[1]]-verts[t[0]],verts[t[2]]-verts[t[0]])
     p['triangles'][ti]=None;removed[pi]+=1;kinds['same_winding_redundant_copy' if np.dot(n0,n1)>0 else 'opposed_internal_interface']+=1
     if np.dot(n0,n1)<0:self.b.parts[op]['triangles'][ot]=None;removed[op]+=1;duplicates.pop(key);kinds['opposed_internal_interface']+=1
    else:duplicates[key]=(pi,ti)
  for p in self.b.parts:p['triangles']=[t for t in p['triangles'] if t is not None]
  self.b.parts=[p for p in self.b.parts if p['triangles']]
  self.mark('paired_internal_face_removal',triangles_removed=sum(removed.values()),by_label_prefix=dict(kinds),rule='Exact Float32 duplicates: keep one same-winding face; remove both opposite-winding internal faces. Original closed-part volumes checked first')
  seen=Counter()
  for p in self.b.parts:
   seen[p['label']]+=1
   if seen[p['label']]>1:p['label']+=f'/repeat-{seen[p["label"]]-1}'
  return self

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--lod',action='store_true');ap.add_argument('--height',type=float,default=13.);a=ap.parse_args()
 if a.out.exists():raise ValueError('Use new bounded output directory')
 m=Hall(a.lod,a.height).finish();a.out.mkdir(parents=True)
 extras={'id':ID,'name':'宝山孔庙大成殿','anchor':m.g['anchor'],'rotation_y':0,'ground_base_m':0,'height_estimate_m':a.height,'axis':'glTF east/up/south, source ENU metres','scope':'Single surviving Dacheng Hall and its attached stone terrace; modern post2015 exterior','textures_embedded':False,'lod_authored_simplification':a.lod,'height_basis':'Secondary Shanghai dictionary13m; uncalibrated photos are visual evidence, not a survey','source_geometry_sha256':sha(HERE/'geometry-input.json'),'copyright':'Geometry/code MIT; source footprint © OpenStreetMap contributors / Overture ODbL1.0; original photo pixels absent; Noto glyphs SIL OFL1.1'}
 r=m.b.save(a.out/(ID+'.glb'),extras)
 write(a.out/'features.json',{'id':ID,'lod':a.lod,'features':m.features,'counts':dict(Counter(x['kind'] for x in m.features)),'unmeasured_details_are_estimates':True})
 write(a.out/'metadata.json',{**extras,'orientation_degrees_ccw_from_east':math.degrees(m.theta),'front_bearing_degrees':180-math.degrees(m.theta),'raw':{k:r[k] for k in ['file','bytes','sha256','triangles','materials','parts','bounds_glb']},'appearance_review_passed':False,'browser_passed':False})
 print(json.dumps({k:r[k] for k in ['file','bytes','sha256','triangles','materials','parts','bounds_glb']}),flush=True)
if __name__=='__main__':main()
