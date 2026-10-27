#!/usr/bin/env python3
"""Photo-informed main Wukang apartment exterior, with explicitly inferred sizes.

Coordinates come only from the frozen source contract. Photographs are evidence,
never embedded pixels. The brick PBR is an original generic procedural material.
"""
from pathlib import Path
import argparse,hashlib,json,math,sys
from collections import defaultdict
import numpy as np
from scipy.interpolate import CubicHermiteSpline
from shapely.geometry import Polygon,LineString,Point,box as rect,shape
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'common'))
from photo_architecture import Builder,Facade,opening,pieces
sys.path.insert(0,str(HERE))
from curved_facade import CurvedFacade
from trim_shared_end import clip_stone_tips

MATERIAL=HERE.parents[2]/'materials/wukang-brick-v1'
PALETTE={
 'stone':{'color':[.54,.52,.46],'roughness':.83},
 'carved pale stone':{'color':[.66,.64,.57],'roughness':.79},
 'stone recess':{'color':[.38,.38,.34],'roughness':.91},
 'rendered wall':{'color':[.61,.60,.54],'roughness':.86},
 'brick':{'color':[1.,1.,1.],'roughness':1.,'metallic':1.,
          'texture':str(MATERIAL/'maps/brick-basecolor.png'),
          'normal_texture':str(MATERIAL/'maps/brick-normal.png'),
          'normal_scale':.65,'orm_texture':str(MATERIAL/'maps/brick-orm.png'),
          'extras':{'materialSource':'Original procedural illustration, CC0-1.0; not a building scan'}},
 'window steel':{'color':[.065,.072,.068],'roughness':.43,'metallic':.48},
 'window glass':{'color':[.16,.21,.23],'roughness':.23,'metallic':.14},
 'window glass varied':{'color':[.23,.27,.27],'roughness':.30,'metallic':.10},
 'metal rail':{'color':[.075,.078,.069],'roughness':.46,'metallic':.5},
 'AC cover':{'color':[.54,.26,.145],'roughness':.69,'metallic':.10},
 'AC shadow':{'color':[.055,.035,.025],'roughness':.88},
 'roof membrane':{'color':[.26,.27,.25],'roughness':.94},
 'roof service':{'color':[.44,.44,.40],'roughness':.85},
 'interior shadow':{'color':[.035,.043,.04],'roughness':.96},
 'dark storefront metal':{'color':[.075,.08,.073],'roughness':.43,'metallic':.4},
}

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

class Model:
 def __init__(self,inp,lod=False):
  self.input=inp;self.g=json.loads(inp.read_text());self.src=shape(self.g['model_geometry_local_east_north_m']);self.original=np.array(self.src.exterior.coords)[:-1];self.b=Builder(PALETTE);self.lod=lod;self.features=[];self.window_count=0;self.ac_count=0;self.baluster_count=0
  # Smooth only the southwest nose. A Hermite curve interpolates all four
  # observed source vertices, with tangents from the adjacent street faces.
  q=self.original[16:20];t=np.r_[0,np.cumsum(np.linalg.norm(np.diff(q,axis=0),axis=1))];der=np.zeros_like(q)
  der[0]=(q[0]-self.original[15])/np.linalg.norm(q[0]-self.original[15]);der[-1]=(self.original[0]-q[-1])/np.linalg.norm(self.original[0]-q[-1])
  for i in [1,2]:der[i]=(q[i+1]-q[i-1])/(t[i+1]-t[i-1])
  spline=CubicHermiteSpline(t,q,der);self.nose_points=spline(np.linspace(0,t[-1],25 if not lod else 13))
  self.poly=orient(Polygon(np.vstack([self.original[:16],self.nose_points])),sign=1)
  self.nose_deviation=max(self.src.distance(Point(p)) for p in self.nose_points)
  if self.nose_deviation>.35:raise ValueError(f'Nose smoothing exceeded .35m: {self.nose_deviation}')
  self.nose=CurvedFacade(self.b,self.nose_points[::-1].tolist(),'nose')
  self.nose_line=LineString(self.nose_points[::-1]);self.xy0=np.array(self.g['anchor'])
  e=self.original[15]-self.original[16];self.xaxis=e/np.linalg.norm(e);self.yaxis=np.array([-self.xaxis[1],self.xaxis[0]])
  self.front_length=float(np.linalg.norm(e));self.frames=[];self.uv_surface_counts=defaultdict(int)

 def add_uv(self,start,f):
  for part in self.b.parts[start:]:
   if part['material']!='brick':continue
   # A wall thickness/reveal cannot reuse a collapsed front-wall UV. Split
   # attribute indices per face, then let the exporter weld equal pos/normal/UV
   # again. No extra surface triangles are added by this operation.
   old=np.asarray(part['vertices']);verts=[];uvs=[];tris=[]
   for tri in part['triangles']:
    xyz=old[list(tri)];mid=xyz.mean(0);nn=np.cross(xyz[1]-xyz[0],xyz[2]-xyz[0]);nn/=np.linalg.norm(nn)
    if f is self.nose:
     along=self.nose_line.project(Point(mid[:2]));pa=np.array(self.nose_line.interpolate(max(0,along-.001)).coords[0]);pb=np.array(self.nose_line.interpolate(min(self.nose_line.length,along+.001)).coords[0]);tt=(pb-pa)/np.linalg.norm(pb-pa);normal=np.array([tt[1],-tt[0]])
    else:tt=f.t[:2];normal=f.n[:2]
    if abs(nn[2])>.7:kind='horizontal_cap_u_depth'
    elif abs(np.dot(nn[:2],tt))>abs(np.dot(nn[:2],normal)):kind='vertical_reveal_depth_z'
    else:kind='facade_u_z'
    self.uv_surface_counts[kind]+=1
    ids=[]
    for v in xyz:
     if f is self.nose:
      along=self.nose_line.project(Point(v[:2]));on=np.array(self.nose_line.interpolate(along).coords[0]);u=along;d=np.dot(v[:2]-on,normal)
     else:u=np.dot(v-f.a,f.t);d=np.dot(v-f.a,f.n)
     uv=[u/1.984,d/1.184] if kind=='horizontal_cap_u_depth' else [d/1.984,v[2]/1.184] if kind=='vertical_reveal_depth_z' else [u/1.984,v[2]/1.184]
     ids.append(len(verts));verts.append(v.tolist());uvs.append(uv)
    tris.append(tuple(ids))
   part['vertices']=verts;part['triangles']=tris;part['texcoords']=uvs

 def prism(self,f,poly,back,front,mat,label):
  start=len(self.b.parts);f.prism(poly,back,front,mat,label);self.add_uv(start,f)

 def beam(self,f,z,h,proj,mat='carved pale stone',label='cornice',u=0,w=None):
  w=f.length if w is None else w
  self.prism(f,rect(u-w/2,z-h/2,u+w/2,z+h/2),-.24,proj,mat,label)

 def wall(self,f,bottom,top,holes,mat,label):
  panel=rect(-f.length/2,bottom,f.length/2,top)
  if holes:panel=panel.difference(unary_union(holes))
  self.prism(f,panel,-.48,0,mat,label)

 def window(self,f,p,cols=4,rows=4,label='window',arched=False):
  # Real recessed glass and one connected thin steel grid, not painted panes.
  x0,z0,x1,z1=p.bounds;inner=p.buffer(-.075,join_style=2);outer=p.buffer(-.018,join_style=2)
  if inner.is_empty:return
  self.prism(f,inner,-.35,-.335,'window glass varied' if self.window_count%7==0 else 'window glass',label+'/recessed-glass')
  bars=[]
  if arched:
   radius=(x1-x0)/2;cx=(x0+x1)/2;spring=z1-radius
   for k in range(1,cols):
    x=x0+(x1-x0)*k/cols;bars.append(rect(x-.018,z0,x+.018,spring))
   for k in range(1,3):
    zz=z0+(spring-z0)*k/3;bars.append(rect(x0,zz-.018,x1,zz+.018))
   bars.append(rect(x0,spring-.024,x1,spring+.024))
   for angle in np.linspace(0,math.pi,9)[1:-1]:
    bars.append(LineString([(cx,spring),(cx+radius*math.cos(angle),spring+radius*math.sin(angle))]).buffer(.017,cap_style=2))
   for fraction in [.45,.73]:
    arc=[(cx+radius*fraction*math.cos(a),spring+radius*fraction*math.sin(a)) for a in np.linspace(0,math.pi,21)]
    bars.append(LineString(arc).buffer(.017,cap_style=2))
  else:
   for k in range(1,cols):
    x=x0+(x1-x0)*k/cols;bars.append(rect(x-.018,z0,x+.018,z1))
   for k in range(1,rows):
    z=z0+(z1-z0)*k/rows;bars.append(rect(x0,z-.018,x1,z+.018))
  panes=inner.difference(unary_union(bars)) if bars else inner
  self.prism(f,outer.difference(panes),-.28,-.21,'window steel',label+'/fine-steel-grid')
  self.beam(f,z0-.038,.075,.07,'stone',label=label+'/thin-aged-sill',u=(x0+x1)/2,w=x1-x0+.16)
  # Ordinary brick windows have brick directly above; do not invent repeated
  # bright projecting caps. Third-level pediments are authored separately.
  self.window_count+=1

 def rail(self,f,u,width,z,projection=.85,stone=False,label='rail'):
  lo,hi=u-width/2,u+width/2
  # Deck includes a small wall overlap; front and end rails are truly separate.
  self.prism(f,rect(lo-.06,z-.16,hi+.06,z+.02),-.10,projection+.10,'carved pale stone',label+'/deck')
  if stone:
   self.prism(f,rect(lo,z+.04,hi,z+.16),projection-.13,projection+.10,'carved pale stone',label+'/stone-foot')
   self.prism(f,rect(lo-.04,z+.93,hi+.04,z+1.07),projection-.16,projection+.14,'carved pale stone',label+'/stone-cap')
   count=max(2,round(width/.37))
   for j in range(count):
    uu=lo+(j+.5)*width/count;pt=f.point(uu,z+.16,projection)
    self.b.lathe(pt[:2],[(z+.16,.095),(z+.23,.10),(z+.29,.055),(z+.43,.11),(z+.61,.115),(z+.75,.052),(z+.83,.062),(z+.94,.093)],'carved pale stone',8 if self.lod else 10,label+f'/turned-baluster-{j}')
    self.baluster_count+=1
  else:
   us=np.linspace(lo,hi,max(2,math.ceil(width/.28))+1)
   self.b.tube([f.point(v,z+1.02,projection) for v in np.linspace(lo,hi,max(2,round(width/.35))+1)],.028,'metal rail',6,label+'/toprail')
   self.b.tube([f.point(v,z+.16,projection) for v in np.linspace(lo,hi,max(2,round(width/.35))+1)],.021,'metal rail',6,label+'/lowerrail')
   for j,v in enumerate(us):
    self.b.tube([f.point(v,z+.14,projection),f.point(v,z+1.03,projection)],.019,'metal rail',6,label+f'/upright-{j}')
   if not self.lod:
    for j in range(len(us)-1):
     m=(us[j]+us[j+1])/2;rw=(us[j+1]-us[j])*.43
     curve=[f.point(m+rw*math.cos(a),z+.58+.19*math.sin(a),projection) for a in np.linspace(0,2*math.pi,13)]
     self.b.tube(curve,.012,'metal rail',5,label+f'/oval-{j}')
  for v in [lo,hi]:
   self.b.tube([f.point(v,z+1.02,d) for d in [.02,projection]],.027,'metal rail' if not stone else 'carved pale stone',6,label+'/end-return')

 def bracket(self,f,u,z,width=.24,projection=.55,label='bracket',height=.95):
  # Distinct deep corbel with a swept side profile and curled lower volute.
  pt=f.point(u,z,0);step=np.array(f.point(u+.01,z,0))-np.array(pt);tan=step/np.linalg.norm(step);n=np.cross(tan,[0,0,1]);n/=np.linalg.norm(n)
  profile=Polygon([(0,z-height),(.12,z-height),(.18,z-height*.95),(.25,z-height*.84),(.28,z-height*.70),(.27,z-height*.54),(.25,z-height*.45),(.28,z-height*.37),(.40,z-height*.24),(projection,z-height*.10),(projection,z),(-.08,z)])
  mapper=lambda d,zz,q:np.array(pt)+n*d+np.array([0,0,zz-z])-tan*q
  self.b.prism(profile,-width/2,width/2,mapper,'carved pale stone',label+'/scroll-body')
  if not self.lod:
   for sgn in [-1,1]:
    pts=[]
    for a in np.linspace(0,1.7*math.pi,17):
     rr=.13*(1-a/(2.5*math.pi));d=.14+rr*math.cos(a);zz=z-height*.80+rr*math.sin(a);pts.append(np.array(pt)+n*d+tan*(sgn*(width/2+.009))+np.array([0,0,zz-z]))
    self.b.tube(pts,.021,'stone recess',5,label+'/incised-volute')

 def pediment(self,f,u,top,width):
  outer=Polygon([(u-width/2-.18,top+.04),(u+width/2+.18,top+.04),(u,top+.57)])
  inner=Polygon([(u-width/2+.04,top+.14),(u+width/2-.04,top+.14),(u,top+.45)])
  self.prism(f,outer,.025,.20,'carved pale stone','third-storey/triangular-pediment')
  self.prism(f,inner,.201,.216,'stone recess','third-storey/pediment-inset')
  self.beam(f,top+.035,.14,.24,u=u,w=width+.45,label='third-storey/pediment-horizontal-cornice')

 def ac(self,f,u,z,label):
  w,h,d=.82,.58,.46
  self.prism(f,rect(u-w/2,z-h/2,u+w/2,z+h/2),.025,d,'AC cover',label+'/box')
  self.prism(f,rect(u-w/2+.055,z-h/2+.045,u+w/2-.055,z+h/2-.045),d+.001,d+.012,'AC shadow',label+'/dark-vent')
  for k in range(6 if not self.lod else 4):
   zz=z-h/2+.075+k*(h-.13)/(5 if not self.lod else 3)
   self.prism(f,rect(u-w/2+.045,zz-.013,u+w/2-.045,zz+.013),d+.013,d+.047,'AC cover',label+'/separated-louver')
  self.ac_count+=1

 def make_face(self,f,n,kind='street',small_balconies=(),all_ac=True):
  pitch=f.length/n;centres=[-f.length/2+(i+.5)*pitch for i in range(n)]
  self.frames.append({'name':f.label,'bays':n,'kind':kind,'length_m':f.length})
  widths=[min(2.25,pitch*.61) for _ in centres]
  # Front arcade is open down to ground. Wukang/returns have raised glazed sills.
  arch_open=kind in ['huaihai','nose']
  holes=[]
  for i,u in enumerate(centres):
   ww=min(2.90,pitch-.62)
   p=opening(u,-.05 if arch_open else .55,ww,3.48 if arch_open else 2.95,arch=ww/2,segments=16)
   holes.append(p)
   if not arch_open:self.window(f,p,cols=5,rows=4,label=f'ground/arch-window-{i}',arched=True)
   ring=p.buffer(.13,join_style=2).difference(p).intersection(rect(-f.length/2,.10,f.length/2,3.78))
   self.prism(f,ring,-.015,.12,'carved pale stone',f'ground/arch-ring-{i}')
   self.prism(f,Polygon([(u-.13,3.25),(u+.13,3.25),(u+.19,3.67),(u-.19,3.67)]),.05,.20,'carved pale stone',f'ground/keystone-{i}')
  self.wall(f,.10,3.70,holes,'stone','ground/true-arched-wall')
  for z in [.60,1.20,1.80,2.40,3.0,3.60]:
   strip=rect(-f.length/2,z-.013,f.length/2,z+.013).difference(unary_union(holes))
   self.prism(f,strip,.002,.013,'stone recess','ground/rusticated-horizontal-joint')
  if arch_open and kind!='nose':
   for i,u in enumerate(centres):
    p=rect(u-pitch*.46,.12,u+pitch*.46,3.55)
    self.prism(f,p,-2.36,-2.34,'window glass',f'storefront/recessed-shop-glass-{i}')
    for x in [u-pitch*.46,u,u+pitch*.46]:
     self.prism(f,rect(x-.035,.12,x+.035,3.55),-2.32,-2.25,'dark storefront metal',f'storefront/mullion-{i}')
    self.prism(f,rect(u-pitch*.47,2.85,u+pitch*.47,3.40),-2.30,-2.20,'dark storefront metal',f'storefront/plain-modern-sign-board-{i}')
  # Windows and open wall shells for seven residential rows.
  windows_by_floor={}
  levels=[(2,3.70,7.20,4.45,1.75),(3,7.20,10.60,7.63,2.28),
          (4,10.60,14.,11.05,2.08),(5,14.,17.40,14.45,2.08),
          (6,17.40,20.80,17.85,2.08),(7,20.80,24.20,21.25,2.08),
          (8,24.20,28.65,24.91,2.04)]
  for floor,z0,z1,bottom,h in levels:
   holes=[]
   for i,(u,w) in enumerate(zip(centres,widths)):
    ww=min(1.78,w) if floor==2 else w
    p=opening(u,bottom,ww,h);holes.append(p)
    self.window(f,p,cols=4 if ww>1.8 else 3,rows=4,label=f'floor-{floor}/window-{i}')
    if floor==3 and kind not in ['recess','service']:self.pediment(f,u,bottom+h,ww)
    if floor in [3,4,5,6,7] and all_ac:
     self.ac(f,u+min(pitch*.34,1.55),bottom-.34,f'floor-{floor}/ac-{i}')
   self.wall(f,z0,z1,holes,'brick' if floor in [3,4,5,6,7] else 'rendered wall',f'floor-{floor}/wall-with-openings')
   if floor==2:
    for zz in [4.0,4.6,5.2,5.8,6.4,7.0]:
     course=rect(-f.length/2,zz-.012,f.length/2,zz+.012).difference(unary_union(holes))
     self.prism(f,course,.002,.014,'stone recess','stone-base/second-storey-horizontal-joint')
   windows_by_floor[floor]=holes
  if kind not in ['service','recess']:
   self.rail(f,0,f.length,7.20,.72,stone=True,label='third-storey/continuous-stone-balustrade')
   self.rail(f,0,f.length,24.20,1.02,stone=False,label='eighth-storey/continuous-metal-balcony')
   for i,u in enumerate(centres):
    self.bracket(f,u+pitch/2-.10,7.10,width=.34,projection=.72,height=1.65,label=f'stone-base/large-scroll-corbel-{i}')
    self.bracket(f,u+pitch/2-.10,24.10,width=.19,projection=.77,label=f'upper-balcony/corbel-{i}')
   for ix in small_balconies:
    u=centres[ix]
    for floor,z in [(4,10.60),(5,14.0),(6,17.40),(7,20.80)]:
     self.rail(f,u,min(2.75,pitch*.82),z,.93,stone=False,label=f'floor-{floor}/small-balcony-{ix}')
     for uu in [u-.75,u+.75]:self.bracket(f,uu,z-.08,.15,.52,label=f'floor-{floor}/small-balcony-bracket')
  # Nested cornice bands are separate relief rather than black interstorey gaps.
  if kind!='service':
   for z,h,pr in [(7.12,.22,.24),(7.28,.12,.34),(27.70,.18,.18),(27.93,.13,.36),(28.20,.22,.50),(28.50,.16,.35)]:
    self.beam(f,z,h,pr,label='profiled-horizontal-cornice')
   if not self.lod:
    for u in np.linspace(-f.length/2+.20,f.length/2-.20,max(2,round(f.length/.42))):
     self.beam(f,28.04,.14,.43,u=u,w=.13,label='cornice/separate-dentil')
  return centres

 def corridor(self,f):
  # Glazed bands at the actual deeply recessed wall, with opaque floor edges.
  for floor,z0,z1 in [(1,.10,3.70),(2,3.70,7.20),(3,7.20,10.60),(4,10.60,14.),(5,14.,17.40),(6,17.40,20.80),(7,20.80,24.20),(8,24.20,28.65)]:
   p=rect(-f.length/2+.20,z0+.42,f.length/2-.20,z1-.24)
   self.wall(f,z0,z1,[p],'rendered wall','corridor/closed-spandrel-open-window')
   self.window(f,p,cols=max(3,round(f.length/.55)),rows=3,label=f'corridor/floor-{floor}')
   self.beam(f,z0+.12,.22,.08,'stone',label='corridor/floor-edge')

 def build(self):
  # All source edges except the four-point nose are indexed without mutation.
  p=self.original
  streets=[(16,15,16,'huaihai',[2,8,14]),(0,19,4,'wukang-south',[]),(4,3,3,'wukang-middle',[]),(10,9,5,'wukang-north',[])]
  done=set()
  for ia,ib,n,label,bal in streets:
   f=Facade(self.b,p[ia],p[ib],label);done.add((ia,ib));self.make_face(f,n,'huaihai' if label=='huaihai' else 'street',bal)
  self.make_face(self.nose,3,'nose',[1])
  # An inward normal offset deeper than the tightest local nose radius folds.
  # Build nose storefronts on the actual non-self-intersecting inset polygon
  # instead of applying the curved mapper at d=-2.34 m. This also retains a
  # usable arcade cavity rather than narrowing it to fit the mapper.
  nose_core=self.poly.buffer(-2.34,join_style=2)
  if not nose_core.is_valid:raise ValueError('Invalid inset storefront core')
  nose_shop_panels=0
  for core in pieces(nose_core):
   coords=list(core.exterior.coords)
   for aa,bb in zip(coords,coords[1:]):
    mid=(np.asarray(aa)+np.asarray(bb))/2
    if np.dot(mid-self.original[16],self.xaxis)>5.5:continue
    ff=Facade(self.b,aa,bb,f'nose/inset-shop-{nose_shop_panels}')
    if ff.length<.08:continue
    ff.prism(rect(-ff.length/2,.12,ff.length/2,3.55),-.045,0,'window glass','planar-glazing-on-valid-inset-boundary')
    for uu in np.linspace(-ff.length/2,ff.length/2,max(1,math.ceil(ff.length/.75))+1):
     ff.box(uu,1.84,.045,3.43,.06,.018,'dark storefront metal','storefront-mullion')
    ff.box(0,3.12,ff.length,.44,.07,.015,'dark storefront metal','plain-shop-signboard')
    nose_shop_panels+=1
  for ia,ib in [(2,1),(6,5)]:
   f=Facade(self.b,p[ia],p[ib],f'nw-recess-{ia}');self.corridor(f);done.add((ia,ib))
  for ia in range(1,17):
   ib=ia-1
   if (ia,ib) in done:continue
   f=Facade(self.b,p[ia],p[ib],f'return-{ia}-{ib}')
   if f.length<2.5:
    for z0,z1,mat in [(0.10,7.20,'rendered wall'),(7.20,24.20,'brick'),(24.20,28.65,'rendered wall')]:self.wall(f,z0,z1,[],mat,'narrow-jamb/closed-wall')
   elif ia>=11:
    # Shared northeast end has no outward balconies, cornices or AC boxes.
    # Its unobserved openings are conservatively omitted, not invented.
    for z0,z1,mat in [(0.10,7.20,'rendered wall'),(7.20,24.20,'brick'),(24.20,28.65,'rendered wall')]:self.wall(f,z0,z1,[],mat,'shared-end/closed-wall-estimate')
   else:
    self.make_face(f,max(1,round(f.length/4.0)),'recess',[],all_ac=False)
  # Interior floors stop at the inner wall skin; no complete hidden brick cubes.
  inside=self.poly.buffer(-.49,join_style=2)
  for z in [.10,3.70,7.20,10.60,14.,17.40,20.80,24.20]:
   self.b.plan_prism(inside,z-.10,z,'interior shadow',f'interior/occlusion-floor-{z}')
  # Floor of the street arcade remains at source footprint and not beyond it.
  self.b.plan_prism(self.poly,0,.095,'stone','ground/source-footprint-paving')
  self.b.plan_prism(self.poly,28.65,28.85,'roof membrane','roof/flat-membrane-with-real-recesses')
  # Subtle authored membrane seams, clipped to the actual roof; no photo pixels.
  inner_roof=self.poly.buffer(-.45,join_style=2)
  for j,u in enumerate(np.arange(-42,43,2.6)):
   line=LineString([self.xaxis*u+self.yaxis*(-45),self.xaxis*u+self.yaxis*45])
   strip=line.buffer(.012,cap_style=2).intersection(inner_roof)
   if not strip.is_empty:self.b.plan_prism(strip,28.851,28.861,'stone recess',f'roof/membrane-seam-{j}')
  parapet=self.poly.difference(self.poly.buffer(-.32,join_style=2))
  self.b.plan_prism(parapet,28.85,30.,'rendered wall','roof/parapet-main')
  coping=self.poly.difference(self.poly.buffer(-.42,join_style=2))
  self.b.plan_prism(coping,30.,30.10,'carved pale stone','roof/parapet-coping')
  # Inset parapet panels follow faces; only public street edges receive external
  # relief. Hidden attached end stays within the exact source boundary.
  for ia,ib,n,label,_ in streets:
   f=Facade(self.b,p[ia],p[ib],label+'/parapet')
   for j in range(n):
    u=-f.length/2+(j+.5)*f.length/n;w=f.length/n-.24
    self.prism(f,rect(u-w/2,29.02,u+w/2,29.84),.002,.035,'stone recess','parapet/recess-panel')
    ring=rect(u-w/2,29.02,u+w/2,29.84).buffer(.055,join_style=2).difference(rect(u-w/2,29.02,u+w/2,29.84))
    self.prism(f,ring,.03,.08,'carved pale stone','parapet/panel-raised-frame')
  # Three inferred service groups on observed flat roof. No annex garden/shed.
  lo,hi=self.poly.bounds[0],self.poly.bounds[2]
  candidates=[]
  for frac in [.26,.58,.82]:
   local=self.original[16]+(self.original[15]-self.original[16])*frac+self.yaxis*5.1
   if self.poly.buffer(-2.0).contains(Point(local)):candidates.append(local)
  for i,c in enumerate(candidates):
   corners=[c+self.xaxis*x+self.yaxis*y for x,y in [(-.725,-.575),(.725,-.575),(.725,.575),(-.725,.575)]]
   for j,(a,bb) in enumerate(zip(corners,corners[1:]+corners[:1])):
    ff=Facade(self.b,a,bb,f'roof/inferred-flue-{i}/brick-side-{j}')
    self.wall(ff,28.85,30.75,[],'brick','observed-brick-shaft')
   self.b.box([*c,30.84],(1.75,1.45,.18),'carved pale stone',label=f'roof/inferred-flue-{i}/cap-base')
   # Curved cap section extruded along facade axis, with explicit overhang.
   f=Facade(self.b,c-self.xaxis*.9,c+self.xaxis*.9,f'roof/flue-{i}')
   profile=[(-.9,30.94),(.9,30.94)]+[(.9*math.cos(a),30.94+.43*math.sin(a)) for a in np.linspace(0,math.pi,13)]
   f.prism(Polygon(profile),-.82,.82,'carved pale stone','curved-masonry-cap')
   boxc=c+self.xaxis*2.8
   if self.poly.buffer(-1.3).contains(Point(boxc)):
    self.b.box([*boxc,29.6],(1.4,1.2,1.5),'roof service',label=f'roof/vent-{i}/box')
    ff=Facade(self.b,boxc-self.xaxis*.65,boxc+self.xaxis*.65,f'roof/vent-{i}')
    for zz in np.linspace(29.1,30.2,7):self.beam(ff,zz,.065,.69,'stone recess',label='roof/vent/separate-louver')
  self.shared_end_clip=clip_stone_tips(self.b,self.original[15],self.original[14])
  self.features=[{'kind':'source-fitted-main-shell','true_open_nw_recesses':2,'occupied_storeys':8,'main_nominal_height_m':30,'height_not_surveyed':True},
                 {'kind':'real_facade_openings','window_groups':self.window_count,'glazing_setback_m':.335,'thin_steel_grid':True},
                 {'kind':'different_ground_facades','huaihai_arcade_open':True,'wukang_arch_windows_with_sills':True,'wukang_fanlight_radial_and_concentric_mullions':True,'arcade_estimated_depth_m':2.34,'nose_storefront_planar_panels_on_valid_inset_boundary':nose_shop_panels,'deep_curved_mapper_offsets_removed':True},
                 {'kind':'bounded_nose_smoothing','outside_source_max_m':self.nose_deviation,'allowed_tolerance_m':.35,'global_corners_not_rounded':True},
                 {'kind':'projecting_decor','turned_stone_balusters':self.baluster_count,'separate_louver_ac_covers':self.ac_count,'central_nose_balcony_stack_four':True},
                 {'kind':'roof_services','inferred_groups':len(candidates),'positions_not_surveyed':True,'annex_terrace_excluded':True},
                 {'kind':'brick_uv_axes','triangles_by_projection':dict(self.uv_surface_counts),'vertical_v':'z/1.184','facade_u':'along facade/1.984','reveal_u':'wall depth/1.984','horizontal_uv':'along facade/1.984, wall depth/1.184','extra_surface_triangles_created':0},
                 {'kind':'shared_ne_end_only_three_stone_tips_clipped','clearance_m':self.shared_end_clip['clearance_m'],'maximum_actual_cut_m':self.shared_end_clip['maximum_actual_cut_m'],'other_geometry_parts_edited':False}]
  return self

 def clean_internal_caps(self):
  buckets=defaultdict(list)
  for pi,p in enumerate(self.b.parts):
   vs=np.asarray(p['vertices'],dtype='<f4')
   for ti,t in enumerate(p['triangles']):
    key=tuple(sorted(tuple(float(v) for v in vs[k]) for k in t));buckets[key].append((pi,ti))
  remove=defaultdict(set);opposite=0;same=0
  for group in buckets.values():
   if len(group)<2:continue
   # Exact coincident internal caps of neighboring solids have opposite normals.
   normals=[]
   for pi,ti in group:
    p=self.b.parts[pi];v=np.asarray(p['vertices'],dtype='<f4');a,b,c=v[list(p['triangles'][ti])];n=np.cross(b-a,c-a);normals.append(n/np.linalg.norm(n))
   if any(np.dot(normals[0],n)<-.999 for n in normals[1:]):
    for pi,ti in group:remove[pi].add(ti)
    opposite+=len(group)
   else:
    for pi,ti in group[1:]:remove[pi].add(ti)
    same+=len(group)-1
  for pi,ts in remove.items():self.b.parts[pi]['triangles']=[t for ti,t in enumerate(self.b.parts[pi]['triangles']) if ti not in ts]
  self.b.parts=[p for p in self.b.parts if p['triangles']]
  return {'exact_opposite_internal_cap_triangles_removed':opposite,'same_orientation_duplicates_removed':same,'based_on_actual_float32_coordinates':True}

def main():
 p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--lod',action='store_true');a=p.parse_args()
 if a.out.exists():raise ValueError('Use a fresh output directory')
 m=Model(a.input,a.lod).build();clean=m.clean_internal_caps();a.out.mkdir(parents=True)
 meta={'id':'xuhui-wukang-mansion','name':'武康大楼主楼','anchor':m.g['anchor'],'ground_base_m':0,'rotation_y':0,'height_estimate_m':31.4,'height_note':'Main facade nominal30m from2023 secondary publication; roof flues and endpoints inferred, not surveyed','stage':'LOD' if a.lod else 'FULL EXTERIOR REVIEW CANDIDATE','source_geometry_sha256':sha(a.input),'material_manifest_sha256':sha(MATERIAL/'material.json'),'textures_embedded':True,'source_photographs_embedded':False,'architecture_style':'French Renaissance-influenced historic multi-household apartment','detail_note':'Two street facades differentiated, true ground arcade versus glazed arches, source recesses, curved nose, recessed steel windows, stone/metal balustrades, cornices, generic procedural brick PBR','uncertainty':['30m source has unspecified endpoint; per-floor values and roof-service sizes inferred','Current post2019 exterior; mutable signs/plants not dated reproduction','Hidden attached northeast end and roof-service layout estimated','Not whole-neighborhood or all ordinary residential completion'],'copyright':'Authored geometry/code MIT; source footprint ©OpenStreetMap contributors / Overture ODbL-1.0; original procedural brick material by agent, CC0-1.0; private photographs are not textures'}
 result=m.b.save(a.out/('wukang-mansion-lod.glb' if a.lod else 'wukang-mansion-raw.glb'),meta)
 meta.update(raw={k:result[k] for k in ['file','bytes','sha256','triangles','parts','bounds_glb']},internal_caps_cleanup=clean)
 (a.out/'metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2));(a.out/'features.json').write_text(json.dumps(m.features,ensure_ascii=False,indent=2));(a.out/'face-layout.json').write_text(json.dumps(m.frames,ensure_ascii=False,indent=2));(a.out/'shared-end-clip.json').write_text(json.dumps(m.shared_end_clip,indent=2));print(json.dumps(meta['raw'],ensure_ascii=False),flush=True)

if __name__=='__main__':main()
