#!/usr/bin/env python3
"""Columbia Country Club: plan-backed spatial calibration stage.
All levels inferred from the published2018 plans/sections; no measured-height claim.
Draft intentionally excludes final surface maps, tile repetitions and carved microdetail.
"""
from pathlib import Path
import argparse,hashlib,json,math,sys
from collections import Counter
import numpy as np
from shapely.geometry import Polygon,Point,box as rect
from shapely.ops import unary_union
from shapely.geometry.polygon import orient
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'common'))
from photo_architecture import Builder,Facade,opening
P={'historic rough stucco':{'color':[.52,.49,.43],'roughness':.97},'east addition stucco':{'color':[.61,.60,.55],'roughness':.96},'stone trim':{'color':[.55,.52,.45],'roughness':.93},'terracotta roof':{'color':[.34,.13,.075],'roughness':.90},'aged timber':{'color':[.17,.087,.038],'roughness':.78},'glass shadow':{'color':[.12,.19,.19],'roughness':.28,'metallic':.20},'stone paving':{'color':[.48,.49,.46],'roughness':.92},'dark iron':{'color':[.065,.075,.072],'roughness':.6,'metallic':.45},'light interior':{'color':[.50,.48,.42],'roughness':.95}}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
class Club:
 def __init__(self):
  self.b=Builder(P);self.g=json.loads((HERE/'geometry-input.json').read_text());q=np.array(self.g['model_geometry_local_east_north_m']['coordinates'][0][:4]);v0=q[0]-q[3];v1=q[1]-q[2];self.angle=(math.atan2(v0[1],v0[0])+math.atan2(v1[1],v1[0]))/2
  self.R=np.array([[math.cos(self.angle),-math.sin(self.angle),0],[math.sin(self.angle),math.cos(self.angle),0],[0,0,1]])
  self.floor=.75;self.upper=5.4;self.eave=9.;self.features=[]
 def xy(self,x,y):return np.array([(x-377)/12,(310-y)/12])
 def xyz(self,x,y,z):return np.array([*self.xy(x,y),z])
 def poly(self,pts):return orient(Polygon([self.xy(x,y) for x,y in pts]),sign=1)
 def planbox(self,x0,y0,x1,y1):return self.poly([(x0,y0),(x1,y0),(x1,y1),(x0,y1)])
 def facade(self,a,b,label):return Facade(self.b,self.xy(*a),self.xy(*b),label)
 def box(self,c,s,m,label):self.b.box(c,s,m,label=label)
 def pane(self,f,u,bottom,w,h,arch,label):
  poly=opening(u,bottom,w,h,arch,20);inset=poly.buffer(-.085,join_style=2)
  f.prism(inset,-.24,-.21,'glass shadow',label+'/inset-glazing')
  f.prism(poly.difference(inset),-.22,-.06,'aged timber',label+'/real-frame')
  f.box(u,bottom+h*.43,w-.1,.065,.07,-.08,'aged timber',label+'/transom')
  f.box(u,bottom+h*.48,.07,h-.14,.07,-.08,'aged timber',label+'/mullion')
  self.features.append({'kind':'actual_wall_opening','label':label,'facade':f.label,'width_m':w,'height_m':h,'arch_rise_m':arch})
 def wall(self,a,b,bottom,top,holes=(),mat='historic rough stucco',label='wall'):
  f=self.facade(a,b,label);shapes=[opening(u,z,w,h,r,20) for u,z,w,h,r,name in holes];f.wall(bottom,top,shapes,.32,mat)
  for u,z,w,h,r,name in holes:self.pane(f,u,z,w,h,r,name)
  return f
 def outline_walls(self,pts,bottom,top,mat,label):
  poly=self.poly(pts);ps=list(poly.exterior.coords)
  for i,(a,b) in enumerate(zip(ps,ps[1:])):Facade(self.b,a,b,label+str(i)).wall(bottom,top,[],.28,mat)
 def hip(self,x0,y0,x1,y1,eave,ridge,label,axis='x',gable=False):
  # Independent Spanish low-pitch roof masses; no Chinese eave algorithm.
  a=self.xy(x0,y1);b=self.xy(x1,y0);xmin,xmax=a[0]-.38,b[0]+.38;ymin,ymax=a[1]-.38,b[1]+.38
  if axis=='x':
   end=min((ymax-ymin)*.45,(xmax-xmin)*.22);r0=[xmin+end,(ymin+ymax)/2,ridge];r1=[xmax-end,(ymin+ymax)/2,ridge]
   if gable:r0[0]=xmin;r1[0]=xmax
  else:
   end=min((xmax-xmin)*.45,(ymax-ymin)*.22);r0=[(xmin+xmax)/2,ymin+end,ridge];r1=[(xmin+xmax)/2,ymax-end,ridge]
   if gable:r0[1]=ymin;r1[1]=ymax
  vs=[[xmin,ymin,eave],[xmax,ymin,eave],[xmax,ymax,eave],[xmin,ymax,eave],r0,r1]
  fs=[(0,3,2,1)]
  if axis=='x':fs +=[(0,1,5,4),(1,2,5),(2,3,4,5),(3,0,4)]
  else:fs +=[(0,1,4),(1,2,5,4),(2,3,5),(3,0,4,5)]
  self.b.add(vs,fs,'terracotta roof',label+'/closed-hip-roof')
  self.b.tube([r0,r1],.11,'terracotta roof',10,label+'/ridge')
  self.features.append({'kind':'separate_roof_mass','label':label,'eave_m':eave,'ridge_m':ridge,'axis':axis,'gable':gable})
 def terrace(self):
  # Raised interior floor follows the plan; attached exterior terraces remain separate.
  main=[(58,210),(152,111),(175,133),(175,143),(270,143),(270,126),(299,126),(299,54),(382,54),(382,126),(415,126),(415,143),(513,143),(531,123),(558,146),(558,209),(697,209),(697,413),(511,413),(511,441),(172,441),(172,413),(74,413),(74,366),(58,366)]
  self.b.plan_prism(self.poly(main),0,self.floor,'stone paving','foundation/plan-shaped-raised-ground-floor')
  self.b.plan_prism(self.planbox(78,441,655,528),0,self.floor,'stone paving','south/attached-lower-terrace')
  for i in range(4):
   # Four inferred risers, calibratable from actual exterior views.
   self.b.plan_prism(self.planbox(282,528,403,550-i*5.5),0,(i+1)*self.floor/4,'stone paving',f'south/front-stair-{i}')
  self.b.plan_prism(self.planbox(176,365,511,441),self.upper-.24,self.upper,'stone paving','south/upper-terrace-slab')
  self.b.plan_prism(self.planbox(74,209,697,365),self.upper-.24,self.upper,'light interior','main/second-floor-slab')
  self.features.append({'kind':'terrace_recession','rear_gable_plan_y':365,'front_parapet_plan_y':441,'recession_m':76/12,'gable_axis_plan_x':342,'source':'upperplan fitted to ground axes; modern-Meipian03 spatial crosscheck'})
 def body(self):
  # Main central hall's rear wall is at y365; the southern arcade lies6.33m in front.
  for label,x0,x1,yfront in [('west-wing',74,176,413),('central-hall',176,511,365),('east-original-wing',511,610,413),('east-retained-addition',610,697,413)]:
   mat='east addition stucco' if 'addition' in label else 'historic rough stucco'
   width=(x1-x0)/12;front=[]
   if label=='west-wing':
    front=[(u,self.floor,1.82,3.85,.91,f'west-ground-arch-{j}') for j,u in enumerate([-2.45,0,2.45])]+[(u,6.2,1.45,2.05,0,f'west-upper-window-{j}') for j,u in enumerate([-2.35,0,2.35])]
   elif label=='central-hall':
    for j,x in enumerate([197,241,285,342,397,445,489]):
     u=(x-(x0+x1)/2)/12;front.append((u,5.42,1.8 if x==342 else 1.42,2.86 if x==342 else 2.0,.5 if x==342 else 0,f'central-upper-{j}'))
   elif label=='east-original-wing':
    front=[(0,self.floor,1.95,3.9,.55,'east-ground-curved-door'),(-2.5,2.1,.7,.75,0,'east-small-left'),(2.5,2.1,.7,.75,0,'east-small-right')]+[(u,6.2,1.35,2.1,.35 if j==1 else 0,f'east-upper-{j}') for j,u in enumerate([-2.3,0,2.3])]
   else:front=[(u,self.floor,1.45,3.75,.72,f'addition-ground-{j}') for j,u in enumerate([-2.25,0,2.25])]+[(u,6.1,1.35,2.0,0,f'addition-upper-{j}') for j,u in enumerate([-2.2,0,2.2])]
   self.wall((x0,yfront),(x1,yfront),self.floor,self.eave,front,mat,label+'/south')
   # North upper windows behind low projecting rooms. Ground circulation is open inward.
   north=[(u,6.25,1.35,1.95,0,label+f'/north-upper-{j}') for j,u in enumerate(np.linspace(-width/2+.9,width/2-.9,max(2,round(width/2.8))))]
   self.wall((x1,209),(x0,209),self.floor,self.eave,north,mat,label+'/north')
   self.wall((x0,209),(x0,yfront),self.floor,self.eave,[],mat,label+'/west')
   self.wall((x1,yfront),(x1,209),self.floor,self.eave,[],mat,label+'/east')
  self.hip(176,209,511,365,9.,12.,'main-long-hip')
  self.hip(74,209,176,413,9.,11.1,'west-long-wing',axis='y')
  self.hip(511,209,610,413,9.,11.5,'east-original-wing',axis='y',gable=True)
  self.hip(610,209,697,413,9.,10.9,'retained-east-addition',axis='y')
  # Short south triangular gable over the historically distinct east wing.
  f=self.facade((511,413),(610,413),'east-south-upper-gable');f.prism(Polygon([(-4.125,9.),(4.125,9.),(0,11.5)]),-.3,.02,'historic rough stucco','triangular-front-gable')
  for i,x in enumerate([177,510]):
   self.box(self.xyz(x,295,11.5),(1.15,1.45,5.0),'historic rough stucco',f'fireplace-chimney-{i}')
 def southern_arcade(self):
  f=self.facade((176,441),(511,441),'south-long-arcade');width=f.length;count=11;holes=[]
  for j in range(count):u=(j-(count-1)/2)*width/count;holes.append((u,self.floor,1.98,3.82,.99,f'south-arch-{j}'))
  self.wall((176,441),(511,441),self.floor,6.1,holes,'historic rough stucco','south-long-arcade')
  self.wall((176,365),(176,441),self.floor,5.4,[],'historic rough stucco','arcade-west-return')
  self.wall((511,441),(511,365),self.floor,5.4,[],'historic rough stucco','arcade-east-return')
  # Draft railing shows the real terrace level and continuous transparent-guard location.
  for j,u in enumerate(np.linspace(-width/2,width/2,14)):
   f.box(float(u),6.25,.035,.55,.04,-.08,'dark iron',f'glass-guard-post-{j}')
  f.box(0,6.52,width,.035,.04,-.08,'dark iron','glass-guard-top')
 def north_blocks(self):
  for label,pts in [('northwest-office',[(176,143),(270,143),(270,126),(299,126),(299,209),(176,209)]),('northeast-office',[(382,126),(415,126),(415,143),(513,143),(513,209),(382,209)])]:
   self.outline_walls(pts,self.floor,5.4,'historic rough stucco',label)
   self.b.plan_prism(self.poly(pts),5.15,5.4,'stone paving',label+'/flat-terrace-roof')
   self.outline_walls(pts,5.4,6.15,'historic rough stucco',label+'/parapet')
  # Central vestibule, lower than main rear upper facade; no invented second-story room.
  self.outline_walls([(299,126),(382,126),(382,209),(299,209)],self.floor,5.4,'historic rough stucco','central-north-vestibule')
  self.b.plan_prism(self.planbox(299,126,382,209),5.15,5.4,'stone paving','north-vestibule/flat-roof')
  # D-ended stair enclosures, with a curved rather than rectangular north front.
  for i,cx in enumerate([153,535]):
   radius=21;cy=145;points=[(cx-radius,209),(cx+radius,209),(cx+radius,cy)]
   points +=[(cx+radius*math.cos(a),cy-radius*math.sin(a)) for a in np.linspace(0,math.pi,25)[1:]]
   self.outline_walls(points,self.floor,9.5,'historic rough stucco',f'north-rounded-stair-{i}/')
   poly=self.poly(points);self.b.plan_prism(poly.buffer(.25),9.48,9.66,'terracotta roof',f'north-rounded-stair-{i}/curved-eave')
   # Low faceted cap follows the D outline rather than sharing the main twelve-metre ridge.
   coords=list(poly.buffer(.24).exterior.coords)[:-1];center=self.xy(cx,168);vs=[[x,y,9.65] for x,y in coords]+[[*center,10.0]];n=len(coords);faces=[tuple(reversed(range(n)))]+[(j,(j+1)%n,n) for j in range(n)];self.b.add(vs,faces,'terracotta roof',f'north-rounded-stair-{i}/independent-cap')
   self.features.append({'kind':'rounded_stair_turret','index':i,'eave_m':9.5,'cap_peak_m':10.0,'plan_center_x':cx})
 def north_portico(self):
  # Eight plan-supported columns, two pairs at each roof corner. Side arches
  # remain distinct from the north-facing entry; final photo-side sign unresolved.
  x0,x1,y0,y1=299,382,54,126
  for i,(x,y) in enumerate([(303,59),(311,59),(370,59),(378,59),(303,121),(311,121),(370,121),(378,121)]):
   xy=self.xy(x,y);self.b.lathe(xy,[(.75,.24),(.92,.28),(1.07,.19),(4.38,.19),(4.50,.30),(4.64,.30)],'stone trim',16,f'north-portico/column-{i}')
  for edge,(a,b) in enumerate([((382,54),(299,54)),((382,126),(382,54)),((299,54),(299,126))]):
   f=self.facade(a,b,'north-portico-face-'+str(edge));hole=opening(0,self.floor,f.length-.75,3.50,.62,24);f.wall(.75,5.8,[hole],.28,'historic rough stucco')
   f.box(0,5.84,f.length+.12,.16,.36,0,'stone trim','parapet-coping')
  self.b.plan_prism(self.planbox(x0,y0,x1,y1),4.65,5.1,'light interior','north-portico/single-ceiling-and-roof-slab')
  self.features.append({'kind':'north-portico','stone_columns':8,'three_open_faces':True,'side_face_sign_not_yet_placed':True})
 def central_mission_gable(self):
  f=self.facade((312,365),(372,365),'recessed-central-mission-gable')
  # Curved outline, standing on the back wall of the upper terrace.
  p=[(-2.5,9),(-2.5,9.55),(-1.7,9.55),(-1.25,9.70),(-.95,10.10),(-.85,10.65),(.85,10.65),(.95,10.10),(1.25,9.70),(1.7,9.55),(2.5,9.55),(2.5,9)]
  f.prism(Polygon(p),-.25,.08,'historic rough stucco','curved-parapet-silhouette')
  top=[f.point(u,z,.10) for u,z in p[1:-1]];self.b.tube(top,.09,'stone trim',8,'mission-gable/copings')
  center=self.xy(342,365);self.b.lathe(center,[(10.65,.26),(10.84,.30),(11.10,.18),(11.28,.26),(11.48,.12),(11.65,.08)],'stone trim',16,'mission-gable/central-urn')
  self.features.append({'kind':'mission-gable-location','plan_axis_x':342,'wall_y':365,'front_arcade_y':441,'model_recession_m':76/12})
 def build(self):
  self.terrace();self.body();self.southern_arcade();self.north_blocks();self.north_portico();self.central_mission_gable()
  for p in self.b.parts:
   vs=np.array(p['vertices']);ts=np.array(p['triangles']);volume=float(np.einsum('ij,ij->i',vs[ts[:,0]],np.cross(vs[ts[:,1]],vs[ts[:,2]])).sum()/6)
   if volume<0:p['triangles']=[tuple(reversed(t)) for t in p['triangles']]
   p['vertices']=(vs@self.R.T).tolist()
  return self

def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();assert not a.out.exists();m=Club().build();a.out.mkdir(parents=True)
 meta={'id':'columbia-country-club','name':'哥伦比亚乡村俱乐部','anchor':m.g['anchor'],'rotation_y':0,'ground_base_m':0,'axis':'glTF east/up/south','stage':'LOW-DETAIL SPATIAL CALIBRATION ONLY — not production asset','height_estimate_m':14.,'height_note':'Rounded starting levels inferred from independently scaled2018architect drawings; ±0.5–1m, not surveyed height','source_geometry_sha256':sha(HERE/'geometry-input.json'),'copyright':'Original authored geometry/code MIT; source footprint ©OpenStreetMap contributors / Overture ODbL-1.0; private reference pixels absent; no textures in this spatial draft'}
 r=m.b.save(a.out/'columbia-country-club-draft.glb',meta);write(a.out/'features.json',{'features':m.features,'counts':dict(Counter(x['kind'] for x in m.features))});write(a.out/'metadata.json',{**meta,'raw':{k:r[k] for k in ['file','bytes','sha256','triangles','parts','bounds_glb']}});print(json.dumps({k:r[k] for k in ['bytes','sha256','triangles','parts','bounds_glb']}))
if __name__=='__main__':main()
