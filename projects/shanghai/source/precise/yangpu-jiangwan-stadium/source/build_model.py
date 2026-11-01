"""Original, photo-guided Jiangwan stadium exterior. MIT geometry.

Author-estimated elevations and detailing; frozen map chains constrain plan.
Open field and source gaps are retained. No field slab, sports lines, temporary
netting, golf sheds, indoor gymnasium, pool or interiors are authored here.
"""
from pathlib import Path
import argparse, json, math
import numpy as np
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union
from common.photo_architecture import Builder, Facade, opening

ROOT=Path(__file__).resolve().parent
ID='yangpu-jiangwan-stadium'
P=json.loads((ROOT/'model-parameters.json').read_text())
A=math.radians(P['design_rotation_ccw_deg']); C,S=math.cos(A),math.sin(A)
PALETTE={
 'weathered concrete':{'color':[.47,.49,.46],'roughness':.93},
 'seat edge':{'color':[.62,.63,.58],'roughness':.89},
 'pale artificial stone':{'color':[.69,.68,.60],'roughness':.82},
 'stone joint':{'color':[.43,.43,.38],'roughness':.90},
 'brick wall':{'color':[.48,.23,.15],'roughness':.91},
 'brick joint':{'color':[.40,.23,.17],'roughness':.94},
 'dark recessed glazing':{'color':[.12,.18,.18],'roughness':.31},
 'steel frame':{'color':[.12,.15,.14],'roughness':.48,'metallic':.35},
 'canopy sheet':{'color':[.12,.16,.16],'roughness':.56,'metallic':.24},
 'closed gate':{'color':[.075,.085,.08],'roughness':.68,'metallic':.25},
 'muted red seat':{'color':[.44,.11,.10],'roughness':.72},
 'bronze ornament':{'color':[.19,.20,.16],'roughness':.6,'metallic':.28},
}

def aligned(p):
 x,y=p;return (C*x+S*y,-S*x+C*y)
def enu(p):
 x,y,z=p;return [C*x-S*y,S*x+C*y,z]
def coords(source):
 r=next(r for r in P['source_parts'] if r['local_id']==source)
 return np.array([aligned(p) for p in r['geometry_local_enu']['coordinates'][0][:-1]])

def sample(chain,t):
 return np.array(LineString(chain).interpolate(float(t),normalized=True).coords[0])

def stepped_strip(b,outer,inner,label,detailed=True,rows=28,z0=.85,z1=11.15):
 """One closed solid swept along paired chains, with a true stepped top.

 Cross section follows inner-to-outer points. Outside wall is a separate
 opened masonry skin, with a bounded recess between it and this stand body.
 """
 outer=np.array(outer,float);inner=np.array(inner,float)
 n=max(12,int(max(LineString(outer).length,LineString(inner).length)/(2.0 if detailed else 5.5)))
 ts=sorted(set(np.linspace(0,1,n+1))|set(LineString(outer).project(Point(p),normalized=True) for p in outer)|set(LineString(inner).project(Point(p),normalized=True) for p in inner))
 frames=[]
 for t in ts:
  o,i=sample(outer,t),sample(inner,t);w=np.linalg.norm(o-i);o=o+(i-o)*min(1.35/w,.15)
  frames.append((o,i))
 # Counterclockwise cross-section in radial fraction,z.
 profile=[(0.,0.),(1.,0.),(1.,z1)]
 for k in range(rows-1,-1,-1):
  profile.append((k/rows,z0+(z1-z0)*(k+1)/rows))
  profile.append((k/rows,z0+(z1-z0)*k/rows))
 if profile[-1]!=(0.,0.):profile.append((0.,0.))
 profile=profile[:-1]
 # Keep unique cross-section vertices where the last tread meets inner face.
 profile=[q for j,q in enumerate(profile) if j==0 or q!=profile[j-1]]
 verts=[]
 for o,i in frames:
  for t,z in profile:verts.append([*(i+(o-i)*t),z])
 m=len(profile);faces=[]
 for k in range(len(frames)-1):
  for j in range(m):
   a=k*m+j;c=k*m+(j+1)%m;faces.append((a,c,c+m,a+m))
 # Triangulate end sections using shapely to handle concave stair profile.
 from shapely import constrained_delaunay_triangles
 from shapely.geometry.polygon import orient
 lookup={tuple(v):j for j,v in enumerate(profile)}
 for tri in constrained_delaunay_triangles(Polygon(profile)).geoms:
  q=list(orient(tri,sign=1).exterior.coords)[:3];ids=[lookup[tuple(v)] for v in q]
  faces.append(tuple(reversed(ids)));faces.append(tuple((len(frames)-1)*m+j for j in ids))
 # Derive global orientation from signed volume, independent of chain direction.
 tri=[]
 for f in faces:
  for j in range(1,len(f)-1):tri.append([f[0],f[j],f[j+1]])
 vv=np.array(verts);tt=np.array(tri);vol=np.sum(np.einsum('ij,ij->i',vv[tt[:,0]],np.cross(vv[tt[:,1]],vv[tt[:,2]])))/6
 if vol<0:faces=[tuple(reversed(f)) for f in faces]
 b.add(verts,faces,'weathered concrete',label+' / one-piece stepped body')
 # A thin rear walkway closes the top of the intentionally recessed exterior
 # shell. Its underside is above11m: it must never become a ground obstacle.
 original=[sample(outer,t).tolist() for t in ts]
 walkway=Polygon(original+[o.tolist() for o,i in reversed(frames)])
 if not walkway.is_valid:walkway=walkway.buffer(0)
 b.plan_prism(walkway,z1-.05,z1+.10,'weathered concrete',label+' / rear elevated walkway')
 # Separate pale tread lips and radial aisle strips make the real stair profile
 # readable from city scale without adding a roof or a field-level slab.
 for k in range(1,rows+1):
  if not detailed and k%2:continue
  t=k/rows;z=z0+(z1-z0)*k/rows+.025
  pts=[[*((i+(o-i)*t)),z] for o,i in frames]
  b.tube(pts,.045 if detailed else .06,'seat edge',sides=6,label=label+f' / row edge {k}')
 # Slender parapet rails follow the inner edge and rear walkway.
 for radial,z in [(0.,z0+1.0),(1.,z1+.85)]:
  pts=[[*((i+(o-i)*radial)),z] for o,i in frames]
  b.tube(pts,.045,'steel frame',sides=6,label=label+f' / safety top rail {radial}')
 for t in np.linspace(0,1,max(3,int(LineString(outer).length/5.0))):
  o,i=sample(outer,t),sample(inner,t);o=o+(i-o)*min(1.35/np.linalg.norm(o-i),.15)
  for p,z,height in [(i,z0,1.0),(o,z1,.85)]:b.tube([[*p,z],[*p,z+height]],.035,'steel frame',sides=6,label=label+' / parapet post')
 # Radial access stairs are bounded smaller steps over the seating slope.
 for idx,t in enumerate(np.linspace(.06,.94,max(3,int(LineString(outer).length/24)))):
  o,i=sample(outer,t),sample(inner,t);direction=o-i;length=np.linalg.norm(direction);d=direction/length;right=np.array([-d[1],d[0]])
  for k in range(rows*2):
   f=(k+.5)/(rows*2);pos=i+direction*f;z=z0+(z1-z0)*(k+1)/(rows*2)
   b.box([*pos,z-.035],[1.25,length/(rows*2)+.012,.07],'seat edge',basis=[[*right,0],[*d,0],[0,0,1]],label=label+f' / radial aisle {idx} step {k}')
  for sign in [-1,1]:
   p0=i+right*sign*.75;p1=o-direction/length*1.5+right*sign*.75
   b.tube([[*p0,z0+.8],[*p1,z1+.8]],.035,'steel frame',sides=6,label=label+f' / radial handrail {idx}/{sign}')
 return frames


def window(f,u,z,w,h,label,probes,detailed):
 shape=opening(u,z,w,h);f.prism(shape,-.70,-.64,'dark recessed glazing',label+' / rear glazing')
 outer=shape.buffer(-.035,join_style=2);inner=shape.buffer(-.11,join_style=2)
 bars=outer.difference(inner)
 if detailed:
  bars=unary_union([bars,box(u-.035,z,u+.035,z+h),box(u-w/2,z+h*.5-.035,u+w/2,z+h*.5+.035)])
 f.prism(bars,-.55,-.46,'steel frame',label+' / window frame')
 probes.append({'label':label,'point':list(f.point(u+w*.24,z+h*.28,0)),'normal':list(f.n),'depth':.64,'material':'dark recessed glazing','kind':'recess'})
 return shape


def outer_walls(b,chain,label,detailed,probes):
 for j,(a,q) in enumerate(zip(chain,chain[1:])):
  f=Facade(b,a,q,label+f' / wall segment {j}');L=f.length
  if L<1.2:continue
  holes=[];count=max(1,int(L/5.0));centers=np.linspace(-L/2+L/count/2,L/2-L/count/2,count)
  for k,u in enumerate(centers if L>=10 else []):
   p=f.point(u,0,0)
   covered_by_end_gate=(p[1]>145 and abs(p[0]-1.45)<14.0) or (p[1]<-145 and abs(p[0]-6.8)<16.0)
   if covered_by_end_gate:continue
   for z in [6.3,8.5]:holes.append(window(f,float(u),z,.68,1.2,label+f' / segment{j} window{k} level{z}',probes,detailed))
  # Only selected long wall bays get a bounded entry recess. All have rear
  # closure and rising stair suggestion; none is labelled a field passage.
  if L>11:
   door=opening(0,0,3.0,4.4,arch=1.5,segments=24 if detailed else 12);holes.append(door)
   f.prism(door.buffer(-.08),-1.11,-1.05,'closed gate',label+f' / entry {j} rear closure')
   for u in np.linspace(-1.26,1.26,10 if detailed else 6):
    f.box(float(u),1.85,.045,3.5,.05,-.88,'steel frame',label+' / closed gate upright')
   for k in range(4):
    f.box(0,.1+k*.16,2.7,.14,.24,-.28-k*.24,'weathered concrete',label+' / entry rising stair')
   f.prism(door.buffer(.18).difference(door).intersection(box(-999,0,999,99)),-.02,.06,'brick joint',label+' / arch brick voussoir border')
   probes.append({'label':label+f' / arch {j} recess','point':list(f.point(.32,2.4,0)),'normal':list(f.n),'depth':1.05,'material':'closed gate','kind':'recess'})
  shape=box(-L/2+.025,0,L/2-.025,11.65).difference(unary_union(holes))
  f.prism(shape,-.46,0,'brick wall',label+' / opened brick exterior')
  f.prism(box(-L/2+.03,0,L/2-.03,.58).difference(unary_union(holes)),-.48,.08,'pale artificial stone',label+' / stone base')
  f.box(0,11.86,L-.03,.30,.66,-.18,'pale artificial stone',label+' / stone coping')
  # Sparse geometric joints, explicitly simplified, not photo-textured bricks.
  if detailed:
   for z in [1.6,3.2,4.8,6.4,8.0,9.6,11.2]:
    band=box(-L/2+.04,z-.012,L/2-.04,z+.012).difference(unary_union(holes))
    f.prism(band,.003,.018,'brick joint',label+' / selected brick course')


def urn(b,center,base,label,detailed):
 x,y=center
 b.lathe((x,y),[(base,.60),(base+.12,.60),(base+.22,.43),(base+.58,.76),(base+.90,.72),(base+1.05,.48),(base+1.14,.53)],'bronze ornament',segments=20 if detailed else 12,label=label+' / simplified ceremonial ding body')
 for sign in [-1,1]:
  b.tube([(x+sign*.62,y,base+.61),(x+sign*.96,y,base+.83),(x+sign*1.04,y,base+1.16)],.10,'bronze ornament',sides=8,label=label+' / raised handle')


def gate_frame(b,f,centers,width,height,label,detailed,probes):
 holes=[opening(u,0,width,height,arch=width/2,segments=32 if detailed else 16) for u in centers]
 pier_windows=[opening(u,z,.55,1.45) for u in [-14.5,-4.85,4.85,14.5] for z in [2.0,6.6,11.2]]
 f.wall(0,16.4,holes+pier_windows,.65,'pale artificial stone')
 if detailed:
  solid=box(-f.length/2,0,f.length/2,16.4).difference(unary_union(holes+pier_windows))
  for z in np.arange(.70,16.0,.70):
   joint=box(-f.length/2+.02,z-.012,f.length/2-.02,z+.012).intersection(solid)
   f.prism(joint,.002,.018,'stone joint',label+' / simplified masonry course')
 for k,(u,shape) in enumerate(zip(centers,holes)):
  f.prism(shape.buffer(.35).difference(shape).intersection(box(-999,0,999,99)),-.035,.15,'pale artificial stone',label+f' / arch surround {k}')
  # A genuinely recessed portal with a further small arched gate, not an
  # unsupported full straight tunnel through the grandstand seating.
  f.prism(shape.buffer(-.03),-5.8,-5.65,'pale artificial stone',label+f' / deep rear wall {k}')
  rear=opening(u,0,width*.64,height*.66,arch=width*.32,segments=24 if detailed else 12)
  f.prism(rear,-5.63,-5.56,'closed gate',label+f' / rear arched iron door {k}')
  # Side return skins terminate at the back wall; the portal remains open in front.
  for sign in [-1,1]:f.box(u+sign*(width/2+.26),height/2,.25,height,5.5,-2.7,'pale artificial stone',label+' / passage jamb return')
  f.box(u,height-.1,width,.3,5.5,-2.7,'pale artificial stone',label+' / passage ceiling')
  for du in np.linspace(-width*.28,width*.28,9 if detailed else 5):f.box(u+du,height*.24,.045,height*.47,.08,-5.48,'steel frame',label+' / rear gate bar')
  probes.append({'label':label+f' / deep arch {k}','point':list(f.point(u+width*.15,height*.32,0)),'normal':list(f.n),'depth':5.48,'material':'steel frame or closed gate','kind':'portal-bounded'})
  # Narrow recessed panel field and a simplified Chinese eave/bracket band.
  f.box(u,10.5,width+.35,1.6,.12,.05,'pale artificial stone',label+' / blank inscription panel')
  for off in np.linspace(-width*.44,width*.44,6 if detailed else 3):
   f.box(u+off,13.2,.20,.52,.78,.25,'pale artificial stone',label+' / bracket stem')
   f.box(u+off,13.55,.75,.18,.95,.28,'pale artificial stone',label+' / bracket arm')
   f.box(u+off,13.78,1.05,.16,1.12,.30,'pale artificial stone',label+' / bracket cap')
  for z,depth in [(14.05,1.25),(14.3,1.4),(14.52,1.25)]:f.box(u,z,width+.65,.15,depth,.30,'pale artificial stone',label+' / projecting eave band')
  if detailed:
   for du in np.linspace(-width*.48,width*.48,16):f.box(u+du,14.55,.075,.26,1.1,.30,'stone joint',label+' / eave rib')
 return holes


def special_west(b,detailed,probes):
 yc=-1.3
 # Outer west gate runs south-to-north; facade outward normal is west.
 f=Facade(b,(-95.30,15.18),(-95.30,-17.87),'west principal gate / outside')
 centers=[-9.7,0,9.7];gate_frame(b,f,centers,5.6,6.5,'west principal gate',detailed,probes)
 # Four masonry vertical blocks, with real narrow recessed windows.
 for i,u in enumerate([-14.5,-4.85,4.85,14.5]):
  width=4.1 if i in (0,3) else 2.7;ff=Facade(b,f.point(u-width/2,0,.5)[:2],f.point(u+width/2,0,.5)[:2],f'west gate pier {i}');holes=[]
  for z in [2.0,6.6,11.2]:holes.append(window(ff,0,z,.55,1.45,f'west gate pier {i}',probes,detailed))
  ff.wall(0,16.4,holes,1.25,'pale artificial stone');ff.box(0,16.55,width+.3,.32,1.7,-.34,'pale artificial stone','west gate pier coping')
 # Main-source jags form the lower flanking wings, independent from the towers.
 for sign in [-1,1]:
  y=yc+sign*22.1
  b.box((-87.65,y,5.35),(4.1,9.5,10.7),'pale artificial stone',label='west special stand / side wing')
  b.box((-87.65,y,10.85),(4.3,9.7,.3),'pale artificial stone',label='west special stand / side coping')
 # Main hall is intentionally closed below the audience platform, except the
 # visible recessed inner arches. It is not an interior walking room.
 core=Polygon([(-89.0,-19.5),(-69.2,-19.5),(-66.1,23.0),(-89.0,23.0)])
 b.plan_prism(core,0,4.5,'pale artificial stone','west special stand / closed raised platform')
 # Continuous front terrace visible in the2017field photograph. This elevated
 # slab joins the audience core to the field facade and side flights; it does
 # not fill the ground below or obstruct the4.05m-high recessed inner arches.
 front_terrace=Polygon([(-69.30,-19.64),(-64.90,-19.64),(-65.60,23.12),(-66.22,23.12)])
 b.plan_prism(front_terrace,4.35,4.50,'pale artificial stone','west special stand / continuous raised front terrace')
 # Estimated concealed structural links from the two inner gate piers to the
 # canopy rear edge. Only high-level beams are added; deep portals stay clear.
 for u in [-4.85,4.85]:
  p=f.point(u,0,0);b.box((-92.825,float(p[1]),13.575),(4.05,4.10,.35),'pale artificial stone',label='west special stand / estimated upper pier to canopy link')
 inner=Facade(b,(-64.9,-19.5),(-65.6,22.9),'west special stand / field elevation')
 arches=[opening(u,0,3.25,4.05,arch=1.625,segments=24 if detailed else 12) for u in [-7.8,0,7.8]]
 inner.wall(0,4.85,arches,.65,'pale artificial stone')
 inner.box(0,5.64,inner.length,.16,.22,.06,'pale artificial stone','west field platform top rail')
 for u in np.linspace(-inner.length/2+.2,inner.length/2-.2,18 if detailed else 10):
  inner.box(float(u),5.22,.20,.74,.24,.06,'pale artificial stone','west field platform stone post')
 if detailed:
  solid=box(-inner.length/2,0,inner.length/2,4.85).difference(unary_union(arches))
  for z in [.7,1.4,2.1,2.8,3.5,4.2]:inner.prism(box(-inner.length/2+.02,z-.012,inner.length/2-.02,z+.012).intersection(solid),.002,.018,'stone joint','west field platform masonry course')
 for u,shape in zip([-7.8,0,7.8],arches):
  inner.prism(shape.buffer(.22).difference(shape).intersection(box(-999,0,999,99)),-.02,.13,'pale artificial stone','west inner three arches / border')
  inner.prism(shape.buffer(-.04),-1.30,-1.22,'closed gate','west inner three arches / recessed closed door')
  probes.append({'label':'west inner arch bounded recess','point':list(inner.point(u+.33,1.95,0)),'normal':list(inner.n),'depth':1.22,'material':'closed gate','kind':'recess'})
 # Seating and aisle strips above the platform, underneath a local roof only.
 for k in range(16 if detailed else 12):
  rows=16 if detailed else 12;t=k/rows;x=-68.5-19.0*t;z=4.55+6.55*(k+1)/rows
  b.box((x,yc,z-.12),(19/rows+.015,33.8,.24),'weathered concrete',label='west special stand / stepped seating')
  if detailed:
   for y in np.linspace(yc-15.5,yc+15.5,33):
    b.box((x,y,z+.10),(.40,.70,.18),'muted red seat',label='west special stand / simplified seat')
    b.box((x-.19,y,z+.38),(.12,.70,.42),'muted red seat',label='west special stand / simplified seat back')
 # An inset window room seen beneath the canopy, with a real continuous reveal.
 rear=Facade(b,(-88.55,yc-12.0),(-88.55,yc+12.0),'west special stand / upper viewing room')
 holes=[]
 for u in [-8.0,0,8.0]:holes.append(window(rear,u,11.3,7.1,1.45,'west upper viewing room window',probes,detailed))
 rear.wall(10.8,13.4,holes,.4,'pale artificial stone')
 # The pavilion canopy has physical thickness, fascia, and discrete support ribs.
 b.box((-79.0,yc,13.9),(24.0,35.0,.35),'canopy sheet',label='west grandstand / local flat canopy')
 for y in np.linspace(yc-16.5,yc+16.5,9):
  b.box((-79.0,y,13.65),(23.3,.20,.25),'steel frame',label='west grandstand / canopy rib')
  b.box((-89.0,y,12.0),(.23,.23,3.3),'steel frame',label='west grandstand / rear canopy support')
 b.box((-67.0,yc,13.95),(.30,35.15,.55),'pale artificial stone',label='west grandstand / pale canopy front edge')
 # Field-facing stepped towers are aligned with the outside gate's outer piers.
 for y in [yc-14.5,yc+14.5]:
  b.box((-90.0,y,10.4),(8.2,4.1,12.0),'pale artificial stone',label='west grandstand / side tower above seating')
  for k in range(4):b.box((-90.0,y,16.5+.26*k),(8.5-.64*k,4.4-.44*k,.24),'pale artificial stone',label='west grandstand / stepped tower crest')
  urn(b,(-90.0,y),17.45,'west grandstand / field tower',detailed)


def end_gate(b,side,detailed,probes):
 south=side=='south';cx=6.8 if south else 1.45;v=-166.2 if south else 169.0
 width=29.0 if south else 23.0;h=14.0 if south else 12.8;passage=7.2 if south else 7.0
 # Outward-facing main gate, on the original end gap. The centre opening is
 # rectangular and genuinely empty through the stand, unlike west gate recesses.
 a=(cx-width/2,v) if south else (cx+width/2,v)
 q=(cx+width/2,v) if south else (cx-width/2,v)
 f=Facade(b,a,q,side+' end gate / outside')
 central=opening(0,0,passage,6.2 if south else 5.7)
 small=[]
 if south:small=[opening(u,0,2.7,4.05,arch=1.35,segments=24 if detailed else 12) for u in [-9.0,9.0]]
 f.wall(0,h,[central,*small],1.05,'pale artificial stone')
 for u,shape in zip([-9.0,9.0],small):
  f.prism(shape.buffer(.22).difference(shape).intersection(box(-999,0,999,99)),-.02,.12,'pale artificial stone','south small side arch border')
  f.prism(shape.buffer(-.04),-1.50,-1.42,'closed gate','south bounded side arch rear closure')
  probes.append({'label':'south end small side arch recess','point':list(f.point(u+.2,2.1,0)),'normal':list(f.n),'depth':1.42,'material':'closed gate','kind':'recess'})
 # Tall plain end blocks and narrow central flanking blocks summarize the
 # visible four-block south silhouette. The north gate is a separate two-block
 # hypothesis with its own single central opening, without copied west arches.
 positions=[-12.2,-4.75,4.75,12.2] if south else [-8.0,8.0]
 for j,u in enumerate(positions):
  w=4.6 if abs(u)>10 or not south else 2.0
  f.box(u,h/2,w,h,3.4,-.65,'pale artificial stone',side+' plain vertical tower')
  f.box(u,h+.22,w+.35,.44,3.75,-.65,'pale artificial stone',side+' tower coping')
  if detailed:
   # Thin panel frame, without an invented inscription or emblem.
   panel=box(u-w*.32,2.0,u+w*.32,h-1.2);inner=panel.buffer(-.08,join_style=2)
   f.prism(panel.difference(inner),1.04,1.085,'stone joint',side+' simple recessed panel line')
 # A shallow high linking band bridges the empty centre above the lintel.
 f.box(0,h-1.6,width-.3,.35,1.9,.02,'stone joint',side+' gate cornice lower')
 f.box(0,h-1.25,width-.15,.30,2.15,.07,'pale artificial stone',side+' gate cornice upper')
 # Main portal jambs and lintel have depth but never reach across the road below.
 for sign in [-1,1]:
  f.box(sign*(passage/2+.28),3.0,.36,6.0,5.0,-2.1,'pale artificial stone',side+' central passage return')
 f.box(0,6.45 if south else 5.95,passage,.36,5.0,-2.1,'pale artificial stone',side+' raised passage soffit')
 if south:
  for u in [-4.75,4.75]:
   f.box(u,14.6,1.0,1.0,1.1,-.65,'pale artificial stone','south narrow raised block')
 # The whole original end gap remains clear at walking height, including behind
 # this shallow gate. No unsupported mirrored internal hall is added.
 return {'side':side,'center_uv':[cx,v],'passage_width_m':passage,'passage_clear_height_m':6.2 if south else 5.7,'height_estimated':True}


def build(lod=False):
 detailed=not lod;b=Builder(PALETTE);probes=[];w=coords(1646);e=coords(1816)
 # West upper/lower sections stop at the special stand, not behind its arches.
 west_outer_upper=w[list(range(16,6,-1))]
 west_inner_full=w[17:33]
 def subline_y(chain,y0,y1):
  line=LineString(chain);poly=box(-250,min(y0,y1),250,max(y0,y1));g=line.intersection(poly)
  ps=np.array(g.coords);return ps if (abs(ps[0,1]-y0)<abs(ps[-1,1]-y0)) else ps[::-1]
 west_inner_upper=subline_y(west_inner_full,w[17,1],w[7,1])
 west_outer_lower=w[list(range(42,32,-1))]
 west_inner_lower=subline_y(west_inner_full,w[42,1],w[32,1])
 for out,inn,label in [(west_outer_upper,west_inner_upper,'west north ordinary stand'),(west_outer_lower,west_inner_lower,'west south ordinary stand')]:
  stepped_strip(b,out,inn,label,detailed,28 if detailed else 20);outer_walls(b,out,label,detailed,probes)
 # East half retains its original independent footprint and both end gaps.
 east_outer=e[list(range(39,16,-1))];east_inner=e[:17]
 east_body_outer=e[[i for i in range(39,16,-1) if i not in (29,30)]]
 stepped_strip(b,east_body_outer,east_inner,'east ordinary stand',detailed,28 if detailed else 20)
 outer_walls(b,east_outer,'east ordinary stand',detailed,probes)
 special_west(b,detailed,probes)
 for y0,y1,label in [(-28.78,-19.62,'west south side flight'),(23.12,28.59,'west north side flight')]:
  stepped_strip(b,[(-87.,y0),(-87.,y1)],[(-64.8,y0),(-64.8,y1)],label,detailed,28 if detailed else 20)
 end_gates=[end_gate(b,side,detailed,probes) for side in ['south','north']]
 # Eastern source projection is represented only as a bounded unroofed raised
 # platform. It is not a copy of the detailed west gate or covered pavilion.
 east_core=Polygon([(90.6,-18.3),(99.0,-18.3),(99.0,26.2),(90.6,26.2)])
 b.plan_prism(east_core,0,11.2,'brick wall','east special stand / bounded source-shaped back platform')
 east_upper=Polygon([e[i] for i in [31,30,29,28]])
 b.plan_prism(east_upper,11.10,11.45,'pale artificial stone','east special stand / unroofed parapet platform')
 # Final authored geometry is in east/north/up. Runtime heading remains zero.
 for part in b.parts:part['vertices']=[enu(v) for v in part['vertices']]
 for p in probes:
  p['point']=enu(p['point']);p['normal']=enu(p['normal'])
 vs=np.array([v for q in b.parts for v in q['vertices']])
 meta={'id':ID,'name':P['name'],'status':P['status'],'scope':'Two mapped outdoor stadium stand halves, detailed west gate/special stand, bounded east platform and asymmetrical end gates with clear central passages. Open field and end access gaps retained; modern courtyard sources remain independent.',
 'local_origin_wgs84':P['local_origin_wgs84'],'local_heading_deg':0,'source_local_ids':[1646,1816],
 'source_macro':'14-13722-6690','all_elevation_datums_estimated':True,'all_architectural_detail_dimensions_estimated':True,
 'ordinary_stand_top_selected_m':11.15,'current_height_surveyed_m':None,'field_slab_modeled':False,'whole_ring_roof':False,
 'source_gap_closure_modeled':False,'end_gate_central_passages_open':True,'end_gate_orientation_photo_inferred_not_GPS':True,'inner_arches_closed_at_depth':True,'temporary_golf_facilities_modeled':False,
 'indoor_gym_or_pool_modeled':False,'interiors_modeled':False,'walk_integration':False,'photos_embedded':False,
 'geometry_license':'MIT','map_reference_license':'ODbL-1.0','model_selected_architectural_top_m':float(vs[:,2].max()),
 'original_historic_state_claimed':False,'estimated_detail_note':'Stand rows, current elevations, rear construction and decorative simplifications are author choices constrained by six dated photos and1934design context; no current survey.'}
 features={'author_parts':len(b.parts),'ordinary_rows':28 if detailed else 20,'mapped_stand_halves':2,'west_gate_main_arches':3,'west_inner_recessed_arches':3,'west_canopy_only':True,'west_continuous_front_terrace_z_m':[4.35,4.50],'west_estimated_upper_pier_links_z_m':[13.40,13.75],'field_void':True,'north_south_source_gaps_retained':True,'end_gates':end_gates,'window_recess_probes':len(probes)}
 return b,meta,features,probes

def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--lod',action='store_true');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 b,meta,features,probes=build(a.lod);out=a.out/(ID+('-lod.glb' if a.lod else '-raw.glb'));record=b.save(out,meta)
 for name,obj in [(('features-lod.json' if a.lod else 'features.json'),features)]+([] if a.lod else [('surface-probes.json',probes),('model-input.json',P)]):
  (a.out/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:record[k] for k in ['file','bytes','sha256','triangles','parts','bounds_glb']},indent=2))
if __name__=='__main__':main()
