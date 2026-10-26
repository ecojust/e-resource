#!/usr/bin/env python3
"""Photograph-informed 208–212 teahouse; real open masonry, timber gallery and tiled roof.
Raw generation only. No network, Blender, production paths or automatic registration.
"""
import argparse, hashlib, json, math, sys
from pathlib import Path
from collections import Counter
import numpy as np
from shapely.geometry import Polygon, box as rect
from shapely.ops import unary_union
from shapely import affinity
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'common'))
from photo_architecture import Builder,Facade,opening,pieces
from sign_lettering import add_facade_lettering

P={
 'lime mortar':{'color':[.42,.43,.40],'roughness':.96},
 'grey brick 0':{'color':[.43,.46,.44],'roughness':.91},
 'grey brick 1':{'color':[.38,.41,.40],'roughness':.94},
 'grey brick 2':{'color':[.48,.49,.45],'roughness':.94},
 'orange brick':{'color':[.43,.22,.13],'roughness':.89},
 'warm stone':{'color':[.37,.38,.34],'roughness':.93},
 'lime plaster':{'color':[.71,.72,.66],'roughness':.95},
 'rear uncertain plaster':{'color':[.62,.63,.59],'roughness':.96},
 'dark recess':{'color':[.065,.061,.048],'roughness':.95},
 'old timber':{'color':[.21,.16,.103],'roughness':.84},
 'timber highlight':{'color':[.36,.29,.21],'roughness':.87},
 'dark timber':{'color':[.12,.085,.055],'roughness':.87},
 'quiet glass':{'color':[.20,.25,.23],'roughness':.32,'metallic':.12},
 'slate 0':{'color':[.20,.22,.21],'roughness':.94},
 'slate 1':{'color':[.245,.25,.23],'roughness':.92},
 'slate 2':{'color':[.18,.195,.18],'roughness':.94},
 'roof backing':{'color':[.13,.14,.13],'roughness':.96},
 'green letters':{'color':[.11,.42,.29],'roughness':.56},
 'muted gold':{'color':[.56,.42,.21],'roughness':.61,'metallic':.23},
 'lantern yellow':{'color':[.83,.60,.13],'roughness':.78},
 'lantern ribs':{'color':[.51,.35,.10],'roughness':.85},
 'old iron':{'color':[.16,.16,.13],'roughness':.81,'metallic':.2},
}

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
class TeaHouse:
 def __init__(self):
  self.g=json.loads((HERE/'geometry-input.json').read_text());self.c=json.loads((HERE/'calibration.json').read_text());self.b=Builder(P)
  a,b=self.g['front_edge']['endpoints_local_east_north_m'];self.f=Facade(self.b,b,a,'observed-southeast-front')
  assert np.dot(self.f.n[:2],self.g['front_edge']['outward_normal_east_north'])>.99999
  self.W=self.f.length;self.plan=Polygon(self.g['polygon_local_east_north'])
  self.local=np.array([self.coords([*p,0]) for p in self.g['polygon_local_east_north']]);self.D=-self.local[:,1].min()
  self.centers=[-self.W/3,0,self.W/3];self.holes=[];self.appearances=[];self.lettering=[]
 def coords(self,p):
  v=np.asarray(p)-self.f.center;return np.array([v@self.f.t,v@self.f.n,v[2]])
 def point(self,u,d,z):return self.f.point(u,z,d)
 def box(self,u,d,z,w,dep,h,mat,label):self.f.box(u,z,w,h,dep,d,mat,label)
 def planar(self,poly):return Polygon([self.point(u,d,0)[:2] for u,d in poly.exterior.coords])
 def lathe(self,u,d,z,profile,mat,label,segments=16):
  center=self.point(u,d,0)[:2];self.b.lathe(center,[(z+h,r) for h,r in profile],mat,segments,label)
 def glass_grid(self,u,bottom,width,height,cols,rows,d,label):
  shape=rect(u-width/2,bottom,u+width/2,bottom+height);inner=shape.buffer(-.055,join_style=2)
  bars=[]
  for k in range(1,cols):
   x=u-width/2+width*k/cols;bars.append(rect(x-.022,bottom,x+.022,bottom+height))
  for k in range(1,rows):
   z=bottom+height*k/rows;bars.append(rect(u-width/2,z-.025,u+width/2,z+.025))
  panes=inner.difference(unary_union(bars));frame=shape.difference(panes)
  self.f.prism(frame,d-.065,d+.005,'dark timber',label+'-unified-frame')
  # Frame-front to glass-front20mm; no large dark tunnel or buried crossing glass.
  for i,p in enumerate(pieces(panes.buffer(-.002,join_style=2))):self.f.prism(p,d-.028,d-.015,'quiet glass',label+f'-pane-{i}')
 def structure(self):
  self.b.plan_prism(self.plan,.0,.16,'warm stone','exact-original-footprint-floor')
  # Only the known front is ornamented. Side/rear wall feet remain the exact source outline.
  ring=self.plan.difference(self.plan.buffer(-.28,join_style=2))
  frontcut=self.planar(rect(-self.W/2-.3,-.42,self.W/2+.3,.2))
  remaining=ring.difference(frontcut)
  self.b.plan_prism(remaining,.16,6.45,'rear uncertain plaster','conservative-side-rear-continuous-shell')
  for i,u in enumerate(self.centers):
   bottom=.94 if i!=1 else .16
   h=opening(u,bottom,1.91,3.25-bottom,arch=.91,segments=32);self.holes.append(h)
  wall=rect(-self.W/2,.16,self.W/2,3.67).difference(unary_union(self.holes))
  self.f.prism(wall,-.32,0,'lime mortar','three-real-arched-openings-wall')
  # Shallow individual visible brick skins over continuous load-bearing mortar.
  # Joints are only 7mm recessed; they never extend through the wall.
  for row,z0 in enumerate(np.arange(.18,3.67,.095)):
   offset=.14 if row%2 else 0.
   for col,x0 in enumerate(np.arange(-self.W/2-.28+offset,self.W/2,.28)):
    brick=rect(x0+.004,z0+.004,x0+.276,min(z0+.091,3.67)).intersection(wall)
    for pp in pieces(brick):self.f.prism(pp,.001,.008,f'grey brick {(row*11+col*7)%3}',f'front-brick-{row}-{col}')
  for i,(u,hole) in enumerate(zip(self.centers,self.holes)):
   # Radial voussoir wedges are actual brick solids, with thin mortar gaps.
   spring=3.25-.91
   for k in range(23):
    t0=k*math.pi/23+.006;t1=(k+1)*math.pi/23-.006
    pts=[(u+r*math.cos(t),spring+r*math.sin(t)) for r,ts in [(1.16,(t0,t1)),(.965,(t1,t0))] for t in ts]
    self.f.prism(Polygon(pts),.015,.11,'orange brick',f'arch-{i}-voussoir-{k}')
   for side in [-1,1]:
    self.box(u+side*1.045,.035,spring-.035,.32,.20,.12,'orange brick',f'arch-{i}-spring-cap')
   if i!=1:
    self.box(u,-.11,.96,1.95,.39,.10,'warm stone',f'arch-{i}-sill')
    self.glass_grid(u,1.03,1.76,1.27,4,2,-.13,f'observed-side-arch-{i}-lower-window')
    # Semicircular dark head retains real arched reveal. No storefront goods or people baked in.
    head=hole.intersection(rect(u-1,2.30,u+1,3.3)).buffer(-.025,join_style=2)
    self.f.prism(head,-.17,-.15,'dark recess',f'arch-{i}-recessed-curved-head')
    self.f.prism(hole.buffer(-.025,join_style=2).difference(hole.buffer(-.09,join_style=2)),-.18,-.10,'dark timber',f'arch-{i}-curved-timber-perimeter')
   else:
    # An actual central passage, side jamb and one inward-open wooden leaf.
    self.f.prism(hole.buffer(-.025,join_style=2).difference(hole.buffer(-.09,join_style=2)),-.18,-.10,'dark timber','main-door-frame')
    self.box(u,-2.35,1.68,1.85,.08,3.03,'dark recess','limited-interior-occlusion-backstop-not-front-fill')
    self.box(u-1.02,-.55,1.34,.075,.88,2.30,'old timber','main-inward-open-door-leaf')
    for z in [.35,.85,1.65,2.35]:self.box(u-1.06,-.55,z,.04,.80,.05,'timber highlight','door-leaf-rail')
  # Continuous courses cross piers only; the real openings remain unfilled.
  for z in [1.18,2.28]:
   strip=wall.intersection(rect(-self.W/2,z-.035,self.W/2,z+.035))
   self.f.prism(strip,.011,.045,'orange brick','visible-orange-horizontal-course')
  # Steps stay within this building entrance, not a guessed street paving patch.
  for i,(d,z) in enumerate([(.24,.04),(.07,.10)]):self.box(0,d,z,2.0,.30,.08,'warm stone',f'central-threshold-step-{i}')
  self.b.plan_prism(self.plan,3.58,3.70,'old timber','upper-floor-slab')
  upper=rect(-self.W/2+.28,3.70,self.W/2-.28,6.39)
  upper_holes=[rect(u-.69,3.82,u+.69,5.88) for u in self.centers]
  self.f.prism(upper.difference(unary_union(upper_holes)),-1.45,-1.17,'lime plaster','gallery-rear-wall-three-inferred-joinery-bays')
  for i,u in enumerate(self.centers):self.glass_grid(u,3.82,1.38,2.06,4,5,-1.19,f'upper-recess-joinery-{i}')
 def gallery(self):
  # Four full turned posts support three open gallery bays, not a window-textured wall.
  for i,u in enumerate(np.linspace(-self.W/2+.14,self.W/2-.14,4)):
   prof=[(0,.115),(.12,.15),(.20,.105),(.80,.085),(1.05,.115),(1.16,.12),(1.24,.087),(1.44,.087),(1.50,.14),(1.63,.15),(1.72,.09),(2.52,.085),(2.60,.13),(2.72,.13)]
   self.lathe(u,-.08,3.70,prof,'timber highlight',f'gallery-main-turned-post-{i}',20)
  for z,w,h in [(3.90,self.W-.20,.10),(4.70,self.W-.15,.105),(6.39,self.W+.25,.16)]:self.box(0,-.08,z,w,.19,h,'old timber','gallery-continuous-timber-rail')
  for bay in range(3):
   x0=-self.W/2+.20+bay*(self.W-.28)/3;x1=-self.W/2+.08+(bay+1)*(self.W-.28)/3
   for j,u in enumerate(np.linspace(x0+.10,x1-.10,12)):
    profile=[(0,.022),(.08,.036),(.15,.023),(.29,.022),(.34,.043),(.43,.043),(.49,.022),(.64,.023),(.70,.036),(.75,.022)]
    self.lathe(float(u),-.08,3.95,profile,'timber highlight',f'gallery-bay-{bay}-turned-spindle-{j}',12)
  # Exposed floor joists and under-eave rafters are visible from this narrow street.
  for i,u in enumerate(np.arange(-self.W/2+.18,self.W/2,.24)):
   self.box(float(u),-.40,3.56,.07,1.44,.12,'dark timber',f'gallery-exposed-floor-joist-{i}')
   self.b.tube([self.point(u,-1.10,6.48),self.point(u,.57,6.15)],.045,'old timber',8,f'roof-visible-rafter-{i}')
  for u in [-self.W/2+.14,self.W/2-.14]:
   for direction in [-1,1]:
    if abs(u+direction*.35)<self.W/2:self.b.tube([self.point(u,-.08,5.96),self.point(u+direction*.35,-.08,6.35)],.055,'old timber',8,'gallery-diagonal-bracket')
 def roof(self):
  ridge=-self.D/2;front=.62;back=-self.D-.35
  def z(d):
   den=(front-ridge) if d>=ridge else (ridge-back)
   f=abs(d-ridge)/den
   return 8.0-1.64*f+.15*f**5
  # Closed backing extruded across frontage; true dual pitched sections.
  ds=np.linspace(back,front,33)
  profile=Polygon([(d,z(d)) for d in ds]+[(d,z(d)-.09) for d in ds[::-1]])
  self.b.prism(profile,-self.W/2-.23,self.W/2+.23,lambda d,z,u:self.point(-u,d,z),'roof backing','continuous-two-pitch-roof-backing')
  # v2: close the inferred two side gables up to the actual roof underside.
  # The wall feet and edge directions come from the unchanged source polygon;
  # no unseen side window or decorative gable is invented.
  source_ring=self.g['polygon_local_east_north']
  for edge_index in (0,2):
   side=Facade(self.b,source_ring[(edge_index+1)%4],source_ring[edge_index],f'inferred-side-gable-{edge_index}')
   us=np.linspace(-side.length/2,side.length/2,33)
   top=[]
   for u in us:
    d=self.coords(side.point(float(u),0,0))[1]
    top.append((float(u),max(6.451,float(z(d)-.09))))
   shape=Polygon([(-side.length/2,6.45),(side.length/2,6.45)]+top[::-1])
   side.prism(shape,-.28,0,'rear uncertain plaster','conservative-solid-roof-closure')
  # Short overlapping semicylindrical cover tiles. Never continuous giant ribs.
  for side,(d0,d1) in enumerate([(back,ridge),(ridge,front)]):
   steps=max(1,round(abs(d1-d0)/.25))
   for j in range(steps):
    a=d0+(d1-d0)*j/steps;b=d0+(d1-d0)*(j+1)/steps
    for i,u in enumerate(np.arange(-self.W/2-.20,self.W/2+.20,.19)):
     # Real 18.5mm shingle step across the original35mm lap. Opposite
     # pitch halves use opposite ramp directions so the upslope tile covers
     # the downslope tile. No change to roof backing, pitch or gables.
     def lifted(d,aa=a,bb=b,which=side):
      fraction=(d-aa)/(bb-aa)
      return z(d)+.0185*(fraction if which==1 else 1-fraction)
     # The last back-pitch tile ends at the ridge, under its unchanged cap;
     # it must not overlap the first tile of the other pitch on the same skin.
     lap=0. if side==0 and j==steps-1 else .035
     self.tile(float(u),float(a),float(b),lifted,.068,.015,'slate '+str((i*3+j+side)%3),f'roof-tile-{side}-{j}-{i}',end_overlap=lap,vertical_shell=True)
  self.b.tube([self.point(-self.W/2-.28,ridge,8.09),self.point(self.W/2+.28,ridge,8.09)],.10,'slate 1',14,'roof-ridge-round-cap')
  # Small tiled canopy above the ground floor, confirmed under the gallery rail.
  for i,u in enumerate(np.arange(-self.W/2-.12,self.W/2+.12,.18)):
   self.tile(float(u),-.08,.46,lambda d:3.68-.32*(d+.08),.064,.014,'orange brick',f'ground-mini-canopy-tile-{i}')
 def tile(self,u,a,b,z,r,t,mat,label,end_overlap=.035,vertical_shell=False):
  vs=[];segments=8
  for d in [a,b+end_overlap]:
   for layer,radius in enumerate([r,r-t]):
    for th in np.linspace(0,math.pi,segments+1):
     # Constant vertical shell thickness keeps both lap skins separated even
     # at their curved shoulders; concentric radial shells would intersect
     # there after a mere18.5mm vertical lift. Canopy tiles retain old geometry.
     x=(r if vertical_shell else radius)*math.cos(th)
     height=r*math.sin(th)-layer*t if vertical_shell else radius*math.sin(th)
     vs.append(self.point(u+x,d,z(d)+height+.01))
  n=segments+1;faces=[]
  for k in range(segments):
   faces.extend([(k,k+1,2*n+k+1,2*n+k),(n+k,3*n+k,3*n+k+1,n+k+1),
                 (k,n+k,n+k+1,k+1),(2*n+k,2*n+k+1,3*n+k+1,3*n+k)])
  faces.extend([(0,2*n,3*n,n),(segments,n+segments,3*n+segments,2*n+segments)])
  vs=np.asarray(vs);vol=sum(np.dot(vs[f[0]],np.cross(vs[f[j]],vs[f[j+1]]))/6 for f in faces for j in range(1,len(f)-1))
  if vol<0:faces=[tuple(reversed(f)) for f in faces]
  self.b.add(vs,faces,mat,label)
 def signs_lanterns(self):
  font=HERE/'fonts/TeahouseSubset.otf'
  # Visible street-facing vertical board. Font outlines approximate the observed calligraphic lettering.
  self.box(-self.W/2+.22,.90,5.04,.64,.13,3.38,'old timber','vertical-sign-real-thickness')
  self.box(-self.W/2+.22,.978,5.04,.54,.025,3.27,'dark timber','vertical-sign-inner-board')
  for i,ch in enumerate('江南第一茶樓'):
   # 一 has a natural glyph bbox938x148 units. Do not stretch this
   # horizontal stroke into the square used by the other full Han glyphs.
   glyph_height=.43*148/938 if ch=='一' else .43
   self.lettering.append(add_facade_lettering(self.f,ch,-self.W/2+.22,6.36-i*.51,.43,glyph_height,.995,1.027,'green letters',label='observed-green-sign',font=font))
  # Small concealed mounts: their existence/placement is construction estimate,
  # not a claim of photograph-resolved fasteners. They attach the relocated
  # board to the existing gallery post without moving any building surface.
  for z_mount in (4.02,6.10):
   self.box(-self.W/2+.22,.40,z_mount,.075,1.0,.075,'dark timber','vertical-sign-concealed-mount-estimate')
  self.box(0,-1.07,6.10,3.5,.10,.35,'dark timber','upper-horizontal-sign-board')
  self.lettering.append(add_facade_lettering(self.f,'朱家角俱樂部茶樓',0,6.10,3.15,.24,-1.012,-.995,'muted gold',label='upper-sign-visible-wording-approximate',font=font))
  for i,u in enumerate(self.centers):
   # The photograph has one hanging yellow lantern per bay on both storeys.
   for z,d,size in [(2.95,.47,.28),(5.74,.12,.23)]:
    profile=[(0,.12),(.10,size*.95),(.40,size),(.66,size*.93),(.75,.12)]
    self.lathe(u,d,z-.37,profile,'lantern yellow',f'lantern-{i}-{z}',20)
    self.b.tube([self.point(u,d,z+.38),self.point(u,d,z+.63)],.011,'old iron',6,'lantern-hanger')
    for k in range(10):
     a=math.tau*k/10;points=[]
     for h,r in profile:points.append(self.point(u+(r+.006)*math.cos(a),d+(r+.006)*math.sin(a),z-.37+h))
     self.b.tube(points,.007,'lantern ribs',6,'lantern-rib')
 def audit(self):
  failures=[];triangles=0;allv=[];per=[]
  for part in self.b.parts:
   v=np.asarray(part['vertices'],dtype=np.float32).astype(float);t=np.asarray(part['triangles']);triangles+=len(t);allv.append(v)
   cross=np.cross(v[t[:,1]]-v[t[:,0]],v[t[:,2]]-v[t[:,0]])
   edges=Counter(tuple(sorted((int(a),int(b)))) for tri in t for a,b in zip(tri,np.roll(tri,-1)))
   volume=float(np.einsum('ij,ij->',v[t[:,0]],np.cross(v[t[:,1]],v[t[:,2]]))/6)
   bad=sum(n!=2 for n in edges.values());zero=int(np.sum(np.linalg.norm(cross,axis=1)<1e-9))
   if bad or zero or volume<=0:failures.append({'label':part['label'],'nonmanifold_edges':bad,'zero_triangles':zero,'volume':volume})
   per.append({'label':part['label'],'material':part['material'],'triangles':len(t),'volume_m3':volume})
  points=np.concatenate(allv)
  return {'passed':not failures,'parts':len(per),'triangles':triangles,'float32_closed_positive_parts':len(per)-len(failures),'failures':failures,'bbox_enu_m':[points.min(0).tolist(),points.max(0).tolist()], 'part_records':per,'real_front_voids':3,'upper_open_gallery':True,'photo_embedded_images':0,'non_target_geometry_claim':'No city feature is changed by this standalone builder. Target/27 retained neighbors are bound in geometry-input.json.'}
 def build(self,out):
  self.structure();self.gallery();self.roof();self.signs_lanterns();qa=self.audit()
  out.mkdir(parents=True,exist_ok=True)
  (out/'geometry-report.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
  if not qa['passed']:raise ValueError('Geometry QA failed: '+str(qa['failures'][:8]))
  metadata={'id':self.g['id'],'name':self.g['name_zh'],'source_geometry_sha256':sha(HERE/'geometry-input.json'),'calibration_sha256':sha(HERE/'calibration.json'),'copyright':'Photo-informed geometry: CC BY-SA 3.0; reference photograph Fayhoo, Wikimedia Commons; footprint Overture / East Asian Buildings CC BY4.0; aggregate ODbL1.0; font SIL OFL1.1','license':'CC-BY-SA-3.0','ground_base_m':0,'photo_textures_embedded':False,'appearance_epoch':'2016 photograph (EXIF); Commons page states2013, unresolved','height_measured':False,'roof_and_rear_estimated':True,'source_photo_sha256':sha(HERE/'photos/commons-33172025.jpg')}
  path=out/'qingpu-beidajie-208-212-raw.glb';self.b.save(path,metadata)
  result={'id':self.g['id'],'raw':{'file':path.name,'bytes':path.stat().st_size,'sha256':sha(path)},'triangles':qa['triangles'],'parts':qa['parts'],'geometry_qa_passed':True,'visual_acceptance':False,'browser_passed':False,'native_not_generated':True,'ground_base_m':0,'front_azimuth_deg':self.g['front_edge']['outward_azimuth_deg'],'recommended_orthographic_azimuth_deg':self.g['front_edge']['outward_azimuth_deg']+15,'recommended_elevation_deg':15,'total_model_height_m':qa['bbox_enu_m'][1][2], 'license':metadata['license'],'photo_images':0,'limitations':self.c['limitations']}
  assert path.stat().st_size<100000000
  (out/'asset-metadata.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
  print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=HERE/'output');a=p.parse_args();TeaHouse().build(a.output)
