#!/usr/bin/env python3
"""Executable Songjiang Fangta geometry. Run by root; no Blender/network/registration.

Nominal42.65m total and6m base brick side follow documented official values.
The source owner quadrilateral stays separate from the true-square model.
Taper,storeys,porch and roof/finial joint remain explicit estimates.
"""
from pathlib import Path
from collections import Counter
import argparse,hashlib,json,math,sys
import numpy as np
from shapely.geometry import Polygon,LineString,box as rect
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from shapely import constrained_delaunay_triangles,set_precision
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'common'))
from photo_architecture import Builder,Facade,pieces
from geometry_primitives import cusped_opening_profile

P={
 'warm white plaster':{'color':[.70,.675,.60],'roughness':.94},
 'aged red timber':{'color':[.40,.125,.085],'roughness':.84},
 'dark bracket timber':{'color':[.13,.115,.095],'roughness':.90},
 'dark porch timber':{'color':[.115,.125,.115],'roughness':.95},
 'dark end grain':{'color':[.10,.09,.075],'roughness':.95},
 'weathered railing':{'color':[.17,.16,.14],'roughness':.92},
 'worn pale wood':{'color':[.29,.28,.25],'roughness':.93},
 'grey platform edge':{'color':[.20,.205,.19],'roughness':.95},
 'grey stone base':{'color':[.28,.285,.27],'roughness':.97},
 'shallow joint':{'color':[.20,.205,.19],'roughness':.97},
 'roof underlayer':{'color':[.095,.10,.09],'roughness':.97},
 'tile 0':{'color':[.18,.185,.165],'roughness':.95},
 'tile 1':{'color':[.16,.17,.15],'roughness':.95},
 'tile 2':{'color':[.20,.205,.185],'roughness':.94},
 'iron finial':{'color':[.075,.08,.075],'roughness':.70,'metallic':.42},
 'dull gold bottle':{'color':[.55,.35,.075],'roughness':.48,'metallic':.55},
 'aged bell bronze':{'color':[.23,.175,.09],'roughness':.74,'metallic':.40},
}
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')

def inset_ring(ring,depth):
 ring=np.asarray(ring,float);lines=[]
 for a,b in zip(ring,np.roll(ring,-1,axis=0)):
  t=(b-a)/np.linalg.norm(b-a);n=np.array([-t[1],t[0]])
  lines.append((n,float(n@a-depth)))
 return np.array([np.linalg.solve(np.array([lines[i-1][0],lines[i][0]]),np.array([lines[i-1][1],lines[i][1]])) for i in range(len(ring))])


class Pagoda:
 def __init__(self):
  self.g=json.loads((HERE/'geometry-input.json').read_text());self.c=json.loads((HERE/'calibration.json').read_text())
  assert sha(HERE/'geometry-input.json')==self.c['source_geometry_sha256']
  assert self.g['id']=='songjiang-fangta-pagoda'
  self.owner_ring=np.asarray(self.g['polygon_local_east_north'],float)
  assert len(self.owner_ring)==4 and Polygon(self.owner_ring).is_valid
  frame=self.g['proposed_architecture_frame'];u=np.asarray(frame['axis_u_east_north']);v=np.asarray(frame['axis_v_east_north'])
  assert abs(np.dot(u,v))<1e-12 and abs(np.linalg.norm(u)-1)<1e-12 and abs(np.linalg.norm(v)-1)<1e-12
  half=self.c['model_square_base_side_m']/2
  self.ring=np.asarray([half*u-half*v,-half*u-half*v,-half*u+half*v,half*u+half*v])
  assert not Polygon(self.ring).exterior.is_ccw and abs(Polygon(self.ring).area-36)<1e-10
  self.b=Builder(P);self.apertures=[];self.roof_records=[];self.assembly=[];self.rail_precision=[];self.walltop_records=[];self.ridge_seat_records=[];self.porch_records=[];self.finial_records=[]

 def facades(self,ring,prefix):return [Facade(self.b,ring[(i+1)%4],ring[i],f'{prefix}/edge{i}') for i in range(4)]

 def shell(self,vertices,top_faces,thickness,mat,label):
  top=np.asarray(vertices,float);tris=[]
  for face in top_faces:
   for i in range(1,len(face)-1):
    tri=[face[0],face[i],face[i+1]];a,b,c=top[tri]
    cross=np.cross(b-a,c-a)
    if cross[2]<0:tri.reverse()
    if abs(cross[2])<1e-10:raise ValueError('Degenerate surface cell: '+label)
    tris.append(tuple(tri))
  n=len(top);vs=np.vstack([top,top-[0,0,thickness]])
  counts=Counter(tuple(sorted((a,b))) for f in tris for a,b in zip(f,f[1:]+f[:1]))
  fs=tris+[tuple(x+n for x in reversed(f)) for f in tris]
  for f in tris:
   for a,b in zip(f,f[1:]+f[:1]):
    if counts[tuple(sorted((a,b)))]==1:fs.append((b,a,a+n,b+n))
  self.b.add(vs,fs,mat,label)

 def wall_ring(self,scale,z0,z1,through,blind,thickness,recess,label,roof_level=None):
  """One shared four-face shell, real holes and blind recesses; no corner caps."""
  outer=self.ring*scale;inner=inset_ring(outer,thickness)
  fronts=self.facades(outer,label);backs=self.facades(inner,label+'-inner')
  vertices=[];faces=[];lookup={}
  def index(point):
   key=tuple(round(float(v),10) for v in point)
   if key not in lookup:lookup[key]=len(vertices);vertices.append(key)
   return lookup[key]
  for edge,(f,back) in enumerate(zip(fronts,backs)):
   def at(u,z,d):
    if d=='back':return back.point(u*back.length/f.length,z)
    return f.point(u,z,float(d))
   def surface(poly,d,reverse=False):
    for piece in pieces(poly):
     for tri in constrained_delaunay_triangles(piece).geoms:
      pts=list(orient(tri,sign=1).exterior.coords)[:3];ids=[index(at(u,z,d)) for u,z in pts]
      faces.append(tuple(reversed(ids)) if reverse else tuple(ids))
   def side(points,lo,hi,skip_end=False):
    for a,b in zip(points,points[1:]):
     if skip_end and abs(a[0]-b[0])<1e-8 and abs(abs(a[0])-f.length/2)<1e-7:continue
     faces.append((index(at(*a,lo)),index(at(*b,lo)),index(at(*b,hi)),index(at(*a,hi))))
   full=rect(-f.length/2,z0,f.length/2,z1);backfull=full
   front_top=[];back_top=[]
   if roof_level is not None:
    for u in np.linspace(-f.length/2,f.length/2,17):
     outer_z=self.roof_under_at(roof_level,f.point(u,0))+.015
     inner_z=self.roof_under_at(roof_level,back.point(u*back.length/f.length,0))+.015
     front_top.append((float(u),outer_z));back_top.append((float(u),inner_z))
    full=Polygon([(-f.length/2,z0),(f.length/2,z0),*front_top[::-1]])
    backfull=Polygon([(-f.length/2,z0),(f.length/2,z0),*back_top[::-1]])
    self.walltop_records.append({'level':roof_level['level'],'edge':edge,'embed_in_substrate_m':.015,'outer_top_u_z':front_top,'inner_top_u_z':back_top,'policy':'L9 only; L1–8 continuous masonry cores remain joined to gallery slabs'})
   holes=through.get(edge,[]);niches=blind.get(edge,[])
   allcuts=unary_union(holes+niches) if holes+niches else None
   surface(full.difference(allcuts) if allcuts is not None else full,0)
   surface(backfull.difference(unary_union(holes)) if holes else backfull,'back',True)
   if roof_level is None:
    side(list(orient(full,sign=1).exterior.coords),'back',0,True)
   else:
    side([(-f.length/2,z0),(f.length/2,z0)],'back',0)
    for j in range(len(front_top)-1):
     # Top follows two independently evaluated roof-under curves, not a horizontal cut.
     faces.append((index(at(*back_top[j+1],'back')),index(at(*back_top[j],'back')),index(at(*front_top[j],0)),index(at(*front_top[j+1],0))))
   for h in holes:side(list(orient(h,sign=-1).exterior.coords),'back',0)
   for h in niches:
    surface(h,-recess)
    side(list(orient(h,sign=-1).exterior.coords),-recess,0)
  self.b.add(vertices,faces,'warm white plaster',label+'/continuous-ring-with-reveals')

 def profile_column(self,xy,z0,z1,radius,label,material='aged red timber'):
  h=z1-z0
  self.b.lathe(xy,[(z0,radius*.92),(z0+.10,radius),(z0+h*.20,radius*1.04),(z0+h*.72,radius*.96),(z1-.09,radius*.85),(z1,radius*.84)],material,12,label)

 def curved_arm(self,f,u,d,z,halfspan,thick,depth,mat,label,radial=False):
  xs=np.linspace(-halfspan,halfspan,9)
  low=[(x,z+.16*(abs(x)/halfspan)**2) for x in xs]
  high=[(x,z+.16*(abs(x)/halfspan)**2+thick) for x in xs[::-1]]
  poly=Polygon(low+high)
  mapper=(lambda x,zz,dd:f.point(u-dd,zz,d+x)) if radial else (lambda x,zz,dd:f.point(u+x,zz,d+dd))
  self.b.prism(poly,-depth/2,depth/2,mapper,mat,label)

 def dougong(self,f,u,z,size,label):
  # Deep visible U-bottom paired arms; small real bearing blocks, not stacked cubes.
  for k,span in enumerate([.27,.38,.49]):
   zz=z+k*.17*size;d=.04+k*.16*size
   self.curved_arm(f,u,d,zz,span*size,.105*size,.17*size,'dark bracket timber',label+f'/lateral-U{k}')
   self.curved_arm(f,u,d+.11,zz+.05*size,span*.88*size,.105*size,.15*size,'dark bracket timber',label+f'/radial-U{k}',True)
   for side in (-1,1):f.box(u+side*span*.72*size,zz+.17*size,.13*size,.13*size,.18*size,d,'dark bracket timber',label+f'/bearing{k}')
  f.box(u,z-.09*size,.19*size,.25*size,.23*size,.03,'dark bracket timber',label+'/seat')

 def railing(self,ring,base,level):
  # Fangta has straight open horizontal rails, not Longhua meander panels.
  for i,xy in enumerate(ring):
   self.profile_column(xy,base,base+.98,.062,f'L{level}/gallery-corner{i}','weathered railing')
   self.b.lathe(xy,[(base+.97,.075),(base+1.02,.075),(base+1.065,.035)],'worn pale wood',10,f'L{level}/postcap{i}')
  for edge,f in enumerate(self.facades(ring,f'L{level}/gallery')):
   width=f.length+.12
   for j,height in enumerate([.18,.39,.60,.89]):
    f.box(0,base+height,width,.055 if j<3 else .085,.065 if j<3 else .095,0,'weathered railing',f'four-horizontal-rail-{j+1}')
   for u in [-f.length/6,f.length/6]:
    f.box(u,base+.49,.075,.98,.075,0,'worn pale wood','two-intermediate-rail-posts')
   self.rail_precision.append({'level':level,'edge':edge,'horizontal_rails':4,'intermediate_posts':2,'scope':'Visible2017horizontalbarconfiguration; rear repetition and metric spacing estimated.'})

 def porch(self):
  c=self.c['global_estimates'];v=self.c['levels'][0];ring=self.ring*(c['porch_column_square_side_m']/6)
  locations=[(f'corner{i}',xy) for i,xy in enumerate(ring)]
  for edge,f in enumerate(self.facades(ring,'ground-porch')):
   for j,u in enumerate(c['porch_intermediate_post_offsets_m']):locations.append((f'edge{edge}-middle{j}',f.point(u,0)[:2]))
  assert len(locations)==12
  for name,xy in locations:
   ztop=self.roof_under_at(v,xy)-.22
   self.b.lathe(xy,[(.22,.23),(.28,.24),(.42,.20)],'grey stone base',16,'ground-porch/'+name+'/stone-foot')
   self.profile_column(xy,.40,ztop+.04,c['porch_column_radius_m'],'ground-porch/'+name+'/round-column','dark porch timber')
   self.b.box([*xy,ztop+.08],[.32,.32,.18],'dark bracket timber',label='ground-porch/'+name+'/capital')
   self.porch_records.append({'label':name,'xy_enu':list(map(float,xy)),'column_bottom':.40,'column_top':ztop+.04,'capital_top':ztop+.17,'roof_underside':self.roof_under_at(v,xy),'support_scope':'Capital-to-substrate joined by explicit cross-bearing beam; no claimed architectural survey.'})
  for edge,f in enumerate(self.facades(ring,'ground-porch')):
   # Four endpoint/intermediate columns per face and a continuous curved header.
   verts=[];faces=[];us=sorted({-f.length/2,f.length/2,*c['porch_intermediate_post_offsets_m'],*[float(x) for x in np.linspace(-f.length/2,f.length/2,17)]})
   for u in us:
    z=self.roof_under_at(v,f.point(u,0))
    verts.extend([f.point(u,z-.25,-.10),f.point(u,z-.25,.10),f.point(u,z+.025,.10),f.point(u,z+.025,-.10)])
   for j in range(len(us)-1):
    for k in range(4):faces.append((j*4+k,j*4+(k+1)%4,(j+1)*4+(k+1)%4,(j+1)*4+k))
   faces.extend([(3,2,1,0),tuple((len(us)-1)*4+k for k in range(4))])
   xyz=np.asarray(verts);tris=[(q[0],q[k],q[k+1]) for q in faces for k in range(1,len(q)-1)]
   if sum(float(np.dot(xyz[a],np.cross(xyz[b],xyz[c]))) for a,b,c in tris)<0:faces=[tuple(reversed(q)) for q in faces]
   self.b.add(verts,faces,'dark porch timber',f'ground-porch/continuous-roof-bearing-header{edge}')

 def structure(self):
  levels=self.c['levels'];global_c=self.c['global_estimates']
  self.b.plan_prism(Polygon(self.ring*global_c['stone_base_scale']),0,global_c['stone_base_top'],'grey stone base','estimated-low-porch-plinth-no-invented-stair-flight')
  self.b.plan_prism(Polygon(self.ring*1.025),.20,global_c['core_plinth_top'],'grey platform edge','visible-core-stone-plinth')
  for v in levels:
   level=v['level'];F=v['floor_base'];C=v['roof_finished_crown'];ring=self.ring*v['wall_scale'];facs=self.facades(ring,f'L{level}/wall')
   nextF=levels[level]['floor_base'] if level<9 else C-.12
   size=max(.70,1.0-(level-1)*.035)
   visible_top=self.roof_under_at(v,facs[0].point(0,0,.52))-.56*size-.10
   through={}
   for i,f in enumerate(facs):
    width=v['opening_width'];height=min(v['opening_height_preferred'],visible_top-F-.30);bottom=F+.03 if level==1 else F+.13
    if height<.95:raise ValueError('Insufficient visible Fangta doorway height')
    shape=np.asarray(cusped_opening_profile(width,height),float);shape[:,1]*=height/shape[:,1].max();shape[:,1]+=bottom;shape=Polygon(shape)
    assert shape.is_valid;through[i]=[shape]
    self.apertures.append({'level':level,'model_edge_id':i,'source_edge_id':i,'type':'through-cusped-door','bottom_m':bottom,'width_m':width,'height_m':height,'geographic_phase_verified':False,'policy':'One middle doorway in every three-bay face perprimarydescription; noalternatingblindpanels.'})
   self.wall_ring(v['wall_scale'],F,nextF+.015,through,{},v['wall_thickness'],0,f'L{level}',v if level==9 else None)
   for i,xy in enumerate(ring):self.profile_column(xy,F,visible_top+.11,v['column_radius'],f'L{level}/red-corner-column{i}')
   for i,f in enumerate(facs):
    f.box(0,F+.055,f.length,.11,.11,.035,'aged red timber','lower-frame-band')
    f.box(0,visible_top-.025,f.length,.20,.16,.045,'aged red timber','upper-three-bay-beam')
    for u in [-f.length/6,f.length/6]:f.box(u,(F+visible_top)/2,.14,visible_top-F,.11,.035,'aged red timber','three-bay-upright')
    for bay in [-1,1]:
     # A horizontal transom in each white side bay; it never covers the middle opening.
     f.box(bay*f.length/3,F+(visible_top-F)*.58,f.length/3-.13,.085,.09,.04,'aged red timber','side-bay-transom')
    for j,u in enumerate(np.linspace(-f.length/2,f.length/2,5)):
     support_z=self.roof_under_at(v,f.point(float(u),0,.52))-.56*size
     self.dougong(f,float(u),support_z,size,f'L{level}/eave-dougong{j}-edge{i}')
   if level>=2:
    gallery=self.ring*v['balcony_scale'];self.b.plan_prism(Polygon(gallery),F-.22,F+.02,'grey platform edge',f'L{level}/gallery-slab')
    self.railing(gallery,F+.035,level)
    previous=levels[level-2]
    for f in self.facades(self.ring*previous['wall_scale'],f'L{level}/continuous-core-bearing'):
     f.box(0,F-.29,f.length,.12,.10,.035,'aged red timber','red-bearing-band-over-white-core')
    for f in self.facades(gallery,f'L{level}/gallery-edge'):
     f.box(0,F-.065,f.length,.10,.055,.015,'worn pale wood','weathered-platform-lip')
     for u in [-f.length/3,0,f.length/3]:
      self.curved_arm(f,u,-.13,F-.39,.27,.085,.15,'dark bracket timber',f'L{level}/gallery-under-U',False)
      self.curved_arm(f,u,-.23,F-.38,.30,.085,.14,'dark bracket timber',f'L{level}/gallery-under-cross',True)
    self.assembly.append({'level':level,'previous_roof_crown':previous['roof_finished_crown'],'floor_slab_bottom':F-.22,'nominal_inner_roof_to_slab_clearance_m':F-.22-previous['roof_finished_crown'],'core_to_slab_overlap_m':.235,'scope':'Scalarassemblydesignonly; actualexportedcontactchecksremainseparate.'})
  self.porch()

 def roof_point(self,v,edge,s,t):
  scale_inner=v['wall_scale']*.945 if v['level']<9 else .075
  inner=self.ring*scale_inner;outer=self.ring*v['roof_scale']
  a,b=inner[edge],inner[(edge+1)%4];c,d=outer[edge],outer[(edge+1)%4]
  xy=(a*(1-s)+b*s)*(1-t)+(c*(1-s)+d*s)*t
  C=v['roof_finished_crown']-.132
  z=C-v['roof_center_drop']*t-v['roof_radial_sag']*4*t*(1-t)+v['roof_corner_lift']*t*t*abs(2*s-1)**v['corner_curve_power']
  return np.array([*xy,z])

 def roof_counts(self,v,edge):
  outerlength=np.linalg.norm((self.ring[(edge+1)%4]-self.ring[edge])*v['roof_scale'])
  radial=np.linalg.norm(self.roof_point(v,edge,.5,1)[:2]-self.roof_point(v,edge,.5,0)[:2])
  return max(8,round(outerlength/v['tile_lane_width_m'])),max(3,math.ceil(radial/v['tile_course_length_m']))

 def underlayer_drop(self,v):
  return .020*(max(self.roof_counts(v,e)[1] for e in range(4))-1)+.010

 def roof_under_at(self,v,point):
  # Invert the planar radial patch on the matching source face; used to seat
  # bracket tops under the real sloped substrate, not a fictitious flat eave.
  p=np.asarray(point[:2]);inner_scale=v['wall_scale']*.945 if v['level']<9 else .075
  inner=self.ring*inner_scale;outer=self.ring*v['roof_scale'];candidates=[]
  for e in range(4):
   a,b=inner[e],inner[(e+1)%4];c,d=outer[e],outer[(e+1)%4]
   tangent=(b-a)/np.linalg.norm(b-a);normal=np.array([-tangent[1],tangent[0]])
   t=float(normal@(p-a)/(normal@(c-a)))
   aa=a*(1-t)+c*t;bb=b*(1-t)+d*t;denominator=float(np.dot(bb-aa,bb-aa))
   if denominator<=1e-16:continue  # square opposite patches can collapse outside their radial domain
   s=float((p-aa)@(bb-aa)/denominator)
   if -.0001<=s<=1.0001:candidates.append((abs(min(t,0))+abs(max(t-1,0)),e,s,t))
  if not candidates:raise ValueError('Roof support lies outside parameter faces')
  _,e,s,t=min(candidates);return float(self.roof_point(v,e,s,t)[2]-self.underlayer_drop(v)-.055)

 def roof_mesh(self,v):
  level=v['level'];vs=[];fs=[];lookup={}
  def ind(p):
   key=tuple(round(float(x),10) for x in p)
   if key not in lookup:lookup[key]=len(vs);vs.append(key)
   return lookup[key]
  ns=16;nt=10
  for edge in range(4):
   ids=[[ind(self.roof_point(v,edge,j/ns,i/nt)-[0,0,self.underlayer_drop(v)]) for j in range(ns+1)] for i in range(nt+1)]
   for i in range(nt):
    for j in range(ns):fs.append((ids[i][j],ids[i][j+1],ids[i+1][j+1],ids[i+1][j]))
  self.shell(vs,fs,.055,'roof underlayer',f'L{level}/continuous-curved-roof')
  if level==9:
   cap_bottom=v['roof_finished_crown']-.132-self.underlayer_drop(v)-.055-.020
   self.b.plan_prism(Polygon(self.ring*.077),cap_bottom,v['roof_finished_crown'],'roof underlayer','top-roof-solid-center-interlocked-with-annulus')

 def tile_strip(self,v,edge,s0,s1,t0,t1,zoffset,kind,mat,label):
  ss=np.linspace(s0,s1,3 if kind=='pan' else 5);vs=[]
  for t in [t0,t1]:
   for k,s in enumerate(ss):
    q=k/(len(ss)-1);p=self.roof_point(v,edge,float(s),t)
    profile=.026*(2*q-1)**2 if kind=='pan' else .041*math.sin(math.pi*q)
    p[2]+=(.030 if kind=='pan' else .082)+profile+zoffset;vs.append(p)
  n=len(ss);fs=[(j,j+1,n+j+1,n+j) for j in range(n-1)]
  self.shell(vs,fs,.012,mat,label)

 def ridge_seat(self,v,corner):
  """Narrow solid grey hip base; the pan/cap courses and continuous roof retain their explicit equations.

  Each foot is evaluated on one of the two real adjacent roof faces. The feet
  embed20mm below their substrate tops. A tapered crest overlaps the existing
  ridge lower skin. Beyond t=1 the original decorative extension may cantilever.
  """
  previous=(corner-1)%4;foot_width=.095;top_ratio=.30
  samples=sorted({0.,1.,*[float(t) for t in np.linspace(0,1,25)],
                  *[float(t) for t in np.linspace(.04,1.10,20) if t<1]})
  vertices=[];faces=[];minimum_foot_to_crest=1e9
  for t in samples:
   center=self.roof_point(v,corner,0,t)
   right_end=self.roof_point(v,corner,1,t);left_end=self.roof_point(v,previous,0,t)
   ds_right=min(.35,foot_width/np.linalg.norm(right_end[:2]-center[:2]))
   ds_left=min(.35,foot_width/np.linalg.norm(left_end[:2]-center[:2]))
   left=self.roof_point(v,previous,1-ds_left,t)
   right=self.roof_point(v,corner,ds_right,t)
   left[2]-=self.underlayer_drop(v)+.020
   right[2]-=self.underlayer_drop(v)+.020
   uplift=.18*(max(0.,(t-.82)/.28)**3)
   ridge_z=center[2]+.08+uplift
   top_left=center.copy();top_right=center.copy();top_center=center.copy()
   top_left[:2]+=(left[:2]-center[:2])*top_ratio
   top_right[:2]+=(right[:2]-center[:2])*top_ratio
   top_left[2]=ridge_z-.020;top_right[2]=ridge_z-.020;top_center[2]=ridge_z-.015
   minimum_foot_to_crest=min(minimum_foot_to_crest,top_center[2]-max(left[2],right[2]))
   bottom_center=center.copy();bottom_center[2]-=self.underlayer_drop(v)+.020
   vertices.extend([left,bottom_center,right,top_right,top_center,top_left])
  width=6
  for j in range(len(samples)-1):
   for k in range(width):
    a=j*width+k;b=j*width+(k+1)%width;c=(j+1)*width+(k+1)%width;d=(j+1)*width+k
    faces.append((a,b,c,d))
  # The bottom has a real center crease. Split each end into two quads,
  # triangulated explicitly; a fan across this concave profile would be wrong.
  cap_triangles=[(0,1,5),(1,4,5),(1,2,3),(1,3,4)]
  faces.extend(tuple(reversed(tri)) for tri in cap_triangles)
  faces.extend(tuple((len(samples)-1)*width+k for k in tri) for tri in cap_triangles)
  xyz=np.asarray(vertices,float);triangles=[(f[0],f[k],f[k+1]) for f in faces for k in range(1,len(f)-1)]
  signed=sum(float(np.dot(xyz[a],np.cross(xyz[b],xyz[c]))) for a,b,c in triangles)/6
  if signed<0:faces=[tuple(reversed(f)) for f in faces]
  self.b.add(vertices,faces,'tile 1',f"L{v['level']}/continuous-grey-ridge-seat{corner}")
  self.ridge_seat_records.append({'level':v['level'],'corner':corner,'radial_t_range':[0,1],'sections':len(samples),'nominal_each_face_foot_width_m':foot_width,'foot_embed_below_substrate_top_m':.020,'crest_below_unchanged_ridge_center_m':.015,'minimum_constructed_foot_to_crest_m':minimum_foot_to_crest,'scope':'Solid hipbase bridgesadjacentactualrooffaces; t>1ornamentmaycantilever. Finiteactualcontactmustbeseparatelychecked.'})

 def roof_details(self,v):
  level=v['level'];caps=0;pans=0;pair_count=0
  for edge in range(4):
   cols,rows=self.roof_counts(v,edge);overlap=min(.025,.10/rows)
   for col in range(cols):
    for row in range(rows):
     t0=row/rows;t1=min(1,(row+1)/rows+overlap);off=-row*.020
     mix=((level*73856093)^(edge*19349663)^(col*83492791)^(row*2654435761))%3
     self.tile_strip(v,edge,(col+.025)/cols,(col+.975)/cols,t0,t1,off,'pan',f'tile {mix}',f'L{level}/pan/e{edge}/c{col}/r{row}');pans+=1
     if col<cols-1:
      self.tile_strip(v,edge,(col+1-.16)/cols,(col+1+.16)/cols,t0,t1,off,'cap',f'tile {mix}',f'L{level}/cover/e{edge}/c{col}/r{row}');caps+=1
     if row<rows-1:pair_count+=1
    # Actual rounded pan/cover ends at the eave and exposed separate round rafters.
    s=(col+.5)/cols;end=self.roof_point(v,edge,s,1);end[2]+=.032-(rows-1)*.020
    tangent=self.roof_point(v,edge,s,.99)-self.roof_point(v,edge,s,1);tangent/=np.linalg.norm(tangent)
    self.b.tube([end-.018*tangent,end+.055*tangent],.055,f'tile {col%3}',8,f'L{level}/round-tile-end')
    points=[self.roof_point(v,edge,s,t)-[0,0,self.underlayer_drop(v)+.10] for t in [.08,.35,.65,1.01]]
    self.b.tube(points,.045,'dark bracket timber',6,f'L{level}/separate-rafter')
   # Document exact construction law; audit finishedFloat32lap points below.
   samples=[]
   for row in range(rows-1):
    t=(row+1)/rows+overlap/2
    upper=self.roof_point(v,edge,.5,t)[2]+.030-row*.020
    lower=self.roof_point(v,edge,.5,t)[2]+.030-(row+1)*.020
    samples.append(float(np.float32(upper-.012)-np.float32(lower)))
   self.roof_records.append({'level':level,'edge':edge,'rows':rows,'columns':cols,'overlap_parameter':overlap,'vertical_course_step_m':.020,'tile_skin_m':.012,'analytic_float32_lap_clearance_samples_m':samples,'substrate_drop_m':self.underlayer_drop(v),'pan_baseline_m':.030,'cover_baseline_m':.082,'analytic_min_cover_to_pan_clearance_m':.014,'actual_triangle_surface_lap_check_pending':True})
  # One continuous hip at each source corner, not duplicated by adjacent faces.
  for corner in range(4):
   points=[]
   for t in np.linspace(.04,1.10,20):
    uplift=.18*(max(0.,(t-.82)/.28)**3)
    points.append(self.roof_point(v,corner,0,float(t))+[0,0,.08+uplift])
   self.b.tube(points,.045,'tile 1',8,f'L{level}/continuous-upturned-corner-ridge{corner}')
   self.ridge_seat(v,corner)
   bell=self.roof_point(v,corner,0,.95)-[0,0,.35]
   self.b.tube([bell+[0,0,.13],bell+[0,0,.26]],.014,'iron finial',5,f'L{level}/bell-hanger{corner}')
   # Simplified solid exterior bell silhouette; no claimed internal bell cavity.
   self.b.lathe(bell[:2],[(bell[2]-.12,.10),(bell[2]-.10,.12),(bell[2]+.01,.075),(bell[2]+.08,.035)],'aged bell bronze',10,f'L{level}/bell{corner}')

 def annular_hoop(self,z,radius,inner,height,label):
  n=48;outer=[(radius*math.cos(i*math.tau/n),radius*math.sin(i*math.tau/n)) for i in range(n)]
  hole=[(inner*math.cos(i*math.tau/n),inner*math.sin(i*math.tau/n)) for i in reversed(range(n))]
  self.b.plan_prism(Polygon(outer,[hole]),z-height/2,z+height/2,'iron finial',label)

 def finial(self):
  # Fangta's photographed iron rings have real holes; no solid Longhua-style belly.
  self.b.lathe((0,0),[(34.77,.51),(34.90,.62),(35.14,.58),(35.53,.43),(35.70,.32)],'iron finial',32,'finial/overturned-bowl')
  self.b.lathe((0,0),[(35.55,.30),(35.65,.53),(35.78,.55),(35.89,.39)],'iron finial',32,'finial/exposure-dish')
  self.b.lathe((0,0),[(35.60,.10),(40.78,.085),(41.10,.06)],'iron finial',16,'finial/central-spindle')
  c=self.c['global_estimates']
  for i,(z,radius) in enumerate(zip(c['finial_ring_centers_z'],c['finial_ring_outer_radii_m'])):
   inner=radius-c['finial_hoop_radial_width_m'];height=c['finial_hoop_height_m']
   self.annular_hoop(z,radius,inner,height,f'finial/open-annular-ring-{i+1}')
   for j in range(4):
    angle=j*math.pi/2;axis=np.array([math.cos(angle),math.sin(angle),0.]);a=axis*.075+[0,0,z];b=axis*(inner+.025)+[0,0,z]
    self.b.tube([a,b],.025,'iron finial',8,f'finial/ring{i+1}-radial-spoke{j}')
   self.finial_records.append({'ring':i+1,'center_z':z,'outer_radius_m':radius,'inner_hole_radius_m':inner,'height_m':height,'radial_spokes':4,'style':'Actualannularvoid; thicknessesandspokesareestimated,notmeasuredphotogrammetry.'})
  self.annular_hoop(40.65,.49,.39,.075,'finial/upper-ornament-open-yoke')
  for j in range(6):
   angle=j*math.tau/6;axis=np.array([math.cos(angle),math.sin(angle),0.])
   points=[axis*r+[0,0,z] for r,z in [(.08,40.56),(.31,40.73),(.49,40.65),(.60,40.88)]]
   self.b.tube(points,.035,'iron finial',8,f'finial/schematic-yoke-arm{j}')
  self.b.lathe((0,0),[(40.83,.10),(41.01,.17),(41.16,.10),(41.30,.07)],'iron finial',24,'finial/dark-neck')
  self.b.lathe((0,0),[(41.25,.075),(41.36,.16),(41.53,.18),(41.66,.09),(41.81,.13),(41.94,.085),(42.02,.025),(42.65,.006)],'dull gold bottle',24,'finial/small-golden-gourd-and-tip')
  top=self.c['levels'][-1]
  for corner in range(4):
   end=self.roof_point(top,corner,0,.86)+[0,0,.10]
   self.b.tube([np.array([0.,0.,40.67]),end],.018,'iron finial',6,f'finial/four-stay-cables{corner}')

 def audit(self):
  failures=[];records=[];points=[]
  for part in self.b.parts:
   v=np.asarray(part['vertices'],dtype=np.float32).astype(float);t=np.asarray(part['triangles'],dtype=np.int64);points.append(v)
   cross=np.cross(v[t[:,1]]-v[t[:,0]],v[t[:,2]]-v[t[:,0]])
   _,inverse=np.unique(v,axis=0,return_inverse=True);welded=inverse[t]
   counts=Counter(tuple(sorted((int(a),int(b)))) for tri in welded for a,b in zip(tri,np.roll(tri,-1)))
   volume=float(np.einsum('ij,ij->',v[t[:,0]],np.cross(v[t[:,1]],v[t[:,2]]))/6)
   bad=sum(x!=2 for x in counts.values());zero=int(np.sum(np.linalg.norm(cross,axis=1)<=1e-9))
   if bad or zero or volume<=0:failures.append({'label':part['label'],'nonmanifold_edges':bad,'zero_triangles':zero,'signed_volume':volume})
   records.append({'label':part['label'],'material':part['material'],'triangles':len(t),'volume_m3':volume})
  pts=np.concatenate(points);assert abs(pts[:,2].max()-42.65)<1e-4
  return {'schema':'fangta-numeric-geometry-v10','passed':not failures,'failures':failures,'source_geometry_sha256':sha(HERE/'geometry-input.json'),'calibration_sha256':sha(HERE/'calibration.json'),'parts':len(records),'triangles':sum(r['triangles'] for r in records),'part_records':records,'bbox_enu_m':[pts.min(0).tolist(),pts.max(0).tolist()],'openings':self.apertures,'roof_design_and_lap_samples':self.roof_records,'assembly_nominal_clearances':self.assembly,'top_storey_wall_roof_join':self.walltop_records,'ridge_seats':self.ridge_seat_records,'porch_columns':self.porch_records,'open_finial_rings':self.finial_records,'model_square_ring_enu':self.ring.tolist(),'source_owner_ring_enu_unchanged':self.owner_ring.tolist(),'rail_precision_union':self.rail_precision,'topology_check':'exact FLOAT32 position welding per part; no cross-component welding','actual_overlapping_tile_triangle_test_passed':False,'native_visual_passed':False,'browser_passed':False,'height_measured':False,'opening_geographic_phase_verified':False,'limits':'Closed part checks do not prove absence of intersections across components or visual accuracy.'}

 def build(self,output):
  if output.exists():raise ValueError('Use a new output directory; never overwrite a frozen model run')
  self.structure()
  for level in self.c['levels']:
   if level['roof_center_drop']<=4*level['roof_radial_sag']:raise ValueError('Eave center would turn outward into a trough')
   self.roof_mesh(level);self.roof_details(level)
  self.finial();qa=self.audit();output.mkdir(parents=True)
  write(output/'geometry-report.json',qa)
  if not qa['passed']:raise ValueError('Geometry audit failed: '+str(qa['failures'][:12]))
  photos=json.loads((HERE/'references/photo-register.json').read_text())['photos']
  copyright='Model CC-BY-SA-4.0; photo references: '+ '; '.join(p['author']+' '+p['license'].replace(' ','-') for p in photos)+'; source footprint © OpenStreetMap contributors via Overture Maps Foundation ODbL-1.0; no photograph pixels embedded.'
  metadata={'model_revision':self.c['model_revision'],'id':self.g['id'],'name':'兴圣教寺塔（松江方塔）','copyright':copyright,'license':'CC-BY-SA-4.0','source_geometry_sha256':sha(HERE/'geometry-input.json'),'calibration_sha256':sha(HERE/'calibration.json'),'ground_base_m':0,'height_measured':False,'height_nominal_m':42.65,'height_basis':self.c['height_policy'],'source_boundary':self.g['geometry'],'source_anchor':self.g['anchor'],'model_square_ring_enu':self.ring.tolist(),'opening_alignment':None,'embedded_photos':False,'appearance_epoch':self.c['appearance_epoch'],'source_photos':[{'author':p['author'],'license':p['license'],'source':p['description_page'],'sha256':p['sha256'],'embedded_as_texture':False} for p in photos],'uncertainty':self.c['uncertainty']}
  raw=output/'songjiang-fangta-pagoda-raw.glb';self.b.save(raw,metadata)
  if raw.stat().st_size>=100_000_000:raise ValueError('Raw violates strict single-file limit')
  record={'id':self.g['id'],'raw':{'file':raw.name,'bytes':raw.stat().st_size,'sha256':sha(raw)},'triangles':qa['triangles'],'parts':qa['parts'],'embedded_images':0,'ground_base_m':0,'height_estimate_m':42.65,'height_measured':False,'alignment':None,'geometry_qa_passed':True,'native_visual_passed':False,'browser_passed':False,'raw_within_preferred60MB':raw.stat().st_size<60_000_000,'source_geometry_sha256':sha(HERE/'geometry-input.json'),'limitations':self.c['uncertainty']}
  write(output/'asset-metadata.json',record);print(json.dumps(record,ensure_ascii=False,indent=2))

if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,default=HERE/'output-v1');args=ap.parse_args();Pagoda().build(args.output)
