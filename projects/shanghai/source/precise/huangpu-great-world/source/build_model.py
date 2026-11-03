"""Original photo-informed Great World exterior, local ENU metres.

Plans: source1519 + source497 registration. Heights, details and roof pavilion
positions are photographic estimates; see model-parameters.json. The unknown
current courtyard canopy is deliberately outside this model's scope.
"""
import argparse,json,math
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,Point,LineString,box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from common.photo_architecture import Builder,Facade,opening,facade_ring
from world_geometry import perimeter_mapper,rectangular_shell,regular_polygon,band,stone_column,balustrade,pediment

ID='huangpu-great-world'
ROOT=Path(__file__).resolve().parent
PARAMS=json.loads((ROOT/'model-parameters.json').read_text())
PALETTE={'warm stone':{'color':[.73,.65,.51],'roughness':.85},'pale dressed stone':{'color':[.74,.72,.65],'roughness':.78},'carved pale stone':{'color':[.74,.72,.65],'roughness':.78},'roof zinc':{'color':[.30,.32,.31],'roughness':.74},'recessed glass':{'color':[.10,.15,.17],'roughness':.28,'metallic':.18},'bronze window frame':{'color':[.16,.12,.09],'roughness':.57},'red roof letters':{'color':[.54,.065,.045],'roughness':.6},'pavilion dark gray roof':{'color':[.24,.25,.24],'roughness':.80},'tower pale gray cap':{'color':[.65,.64,.59],'roughness':.80}}


def geometric_rail(b,a,c,z,detail=True):
 f=Facade(b,a,c,'corner entrance geometric stone railing');length=f.length
 f.box(0,z+.12,length,.15,.28,.25,'pale dressed stone','bottom rail');f.box(0,z+.96,length,.16,.32,.25,'pale dressed stone','handrail')
 count=max(2,round(length/.95));w=length/count
 for j in range(count):
  u=-length/2+w*(j+.5)
  if j%2==0:
   shape=Polygon([(u-w*.44,z+.54),(u,z+.19),(u+w*.44,z+.54),(u,z+.89)]);cut=Polygon([(u-w*.31,z+.54),(u,z+.29),(u+w*.31,z+.54),(u,z+.79)])
  else:
   shape=Point(u,z+.54).buffer(.34,resolution=12 if detail else 6);cut=Point(u,z+.54).buffer(.25,resolution=12 if detail else 6)
  f.prism(shape.difference(cut),.15,.31,'pale dressed stone','open diamond and circular fret')


def tower_core(b,poly,bottom,top,lod,label):
 # Bounded outer core with real recessed windows, never an invented interior.
 for i,f in enumerate(facade_ring(b,poly,label)):
  h=top-bottom;w=f.length*.60;shape=opening(0,bottom+.35,w,h-.72)
  f.wall(bottom,top,[shape],.25,'warm stone');f.window(shape,2,2 if lod else 3,trim=False,label='recessed tower core glazing')
 b.plan_prism(poly,bottom,bottom+.18,'pale dressed stone',label+' floor');b.plan_prism(poly,top-.18,top,'roof zinc',label+' ceiling')


def main_tower(b,lod,features,probes):
 c=PARAMS['tower_center_enu_m'];detail=not lod
 # First arched rooftop tier: genuine annular arch openings and an inset core.
 poly=regular_polygon(c,5.12,12);b.plan_prism(poly.buffer(.18,join_style=2),20.22,20.58,'pale dressed stone','tower base terrace joins main roof');inner=regular_polygon(c,2.74,12)
 tower_core(b,inner,20.4,25.75,lod,'tower arch-tier inset core')
 for i,f in enumerate(facade_ring(b,poly,'tower arched colonnade')):
  hole=opening(0,20.7,f.length-.67,4.69,.86,18 if detail else 10)
  f.wall(20.4,25.9,[hole],.32,'warm stone');f.prism(hole.buffer(.14,join_style=2).difference(hole),.015,.18,'pale dressed stone','raised arch moulding')
  # Capitals and shafts stand at the arch piers; side arches remain open.
  for u in [-f.length/2+.16]:
   p=f.point(u,0,.10);stone_column(b,p[:2],20.55,24.7,.19,detail,'tower arch pier column')
  if i==2:
   probes.append({'label':'tower arch opening beside core','kind':'void','origin':f.point(0,22.8,.65).tolist(),'direction':(-f.n).tolist(),'max_distance':1.15})
 band(b,poly,25.87,.25,.40,.3,label='arched tower projecting cornice')
 b.plan_prism(poly.buffer(-.26,join_style=2),25.72,26.08,'pale dressed stone','continuous arched-tier ceiling beneath cornice cap')
 for level,(bottom,top,r,core_r) in enumerate([(26.12,30.75,4.35,2.4),(30.98,35.12,3.67,1.96)]):
  ring=regular_polygon(c,r);core=regular_polygon(c,core_r)
  tower_core(b,core,bottom,top-.08,lod,f'tower straight tier {level+1} inset core')
  b.plan_prism(ring.buffer(.22,join_style=2),bottom-.15,bottom+.10,'pale dressed stone',f'tower tier {level+1} floor')
  for j,p in enumerate(list(ring.exterior.coords)[:-1]):stone_column(b,p,bottom+.10,top-.20,.24 if level==0 else .20,detail,f'tower tier {level+1} open column')
  band(b,ring,top-.21,.37,.38,.30,label=f'tower tier {level+1} capital cornice')
  b.plan_prism(ring.buffer(-.26,join_style=2),top-.34,top+.12,'pale dressed stone',f'continuous straight-tier {level+1} ceiling beneath cornice cap')
  for f in facade_ring(b,ring,'tower low rail'):
   f.box(0,bottom+.64,f.length-.3,.10,.13,0,'pale dressed stone','upper low guardrail')
   if detail:
    for u in np.linspace(-f.length/2+.4,f.length/2-.4,max(2,round(f.length/.65))):f.box(u,bottom+.39,.075,.45,.11,0,'pale dressed stone','low guardrail stanchion')
 ring=regular_polygon(c,2.68);b.plan_prism(ring.buffer(.12,join_style=2),35.2,35.45,'pale dressed stone','small lantern base joins lower terrace');tower_core(b,ring,35.3,37.55,lod,'upper small hexagonal lantern')
 band(b,ring,37.47,.23,.27,.25,label='small lantern cornice')
 ring=regular_polygon(c,1.75);b.plan_prism(ring.buffer(.12,join_style=2),37.5,37.8,'pale dressed stone','upper lantern base joins lower cap');tower_core(b,ring,37.65,41.05,lod,'slender upper lantern')
 band(b,ring,40.97,.18,.20,.2,label='slender lantern cornice')
 b.lathe(c,[(41.02,1.93),(41.43,1.65),(42.15,.88),(42.9,.40),(43.8,.065)],'tower pale gray cap',12,'twelve-sided tapered tower cap')
 b.lathe(c,[(43.78,.055),(46.4,.035)],'aged brass',8,'slender estimated tower finial')
 features['main_tower']={'center_enu_m':c,'main_roof_m':20.4,'tip_m':43.8,'finial_m':46.4,'open_arcade_tiers':3,'inset_windowed_cores':True,'first_rooftop_tier':'12 arched bays around a near-round crown; independent of six-vertex mapped base','next_two_tiers':'straight columns with recessed core','geometry_not_surveyed':True}


def pavilion(b,p,lod,index):
 c=p['center_enu_m'];r=p['radius_m'];levels=p['levels'];n=10 if not lod else 8
 z=20.4
 for tier in range(levels):
  top=z+(3.6 if levels==2 else 3.5);outer=regular_polygon(c,r,n,0)
  core=regular_polygon(c,r*.45,n,0);tower_core(b,core,z,top-.22,lod,f'roof pavilion {index} inset core {tier}')
  b.plan_prism(outer.buffer(.16),z-.08,z+.20,'pale dressed stone',f'roof pavilion {index} platform')
  for v in list(outer.exterior.coords)[:-1]:stone_column(b,v,z+.20,top-.20,.18,not lod,f'roof pavilion {index} open column')
  band(b,outer,top-.28,.30,.25,.25,label=f'roof pavilion {index} cornice')
  b.plan_prism(outer.buffer(-.21,join_style=2),top-.30,top-.02,'pale dressed stone',f'roof pavilion {index} continuous tier ceiling')
  z=top
 b.lathe(c,[(z-.05,r*1.08),(z+.18,r*1.07),(z+.55,r*.97),(z+1.05,r*.67),(z+1.33,r*.12),(z+1.46,.04)],'pavilion dark gray roof',32 if not lod else 16,f'roof pavilion {index} shallow dome')


def roof_letters(b,a,c,lod):
 # Original stroke geometry for the three photographed characters, no font asset.
 f=Facade(b,a,c,'photographed rooftop 大世界 sign');scale=3.0
 strokes=[[[(-.43,.12),(.43,.12)],[(.03,.49),(-.02,.0),(-.19,-.28),(-.46,-.49)],[(-.01,.02),(.18,-.24),(.46,-.49)]],[[(-.47,.17),(.48,.17)],[(-.34,.49),(-.34,-.37),(.46,-.37)],[(-.04,.48),(-.04,-.05),(.24,-.05),(.24,.48)]],[[(-.37,.43),(.37,.43),(.37,-.03),(-.37,-.03),(-.37,.43)],[(-.37,.20),(.37,.20)],[(0,.43),(0,-.03)],[(-.04,-.05),(-.19,-.25),(-.44,-.39)],[(.04,-.05),(.20,-.25),(.44,-.39)],[(-.16,-.22),(-.16,-.49)],[(.17,-.23),(.17,-.49)]]]
 for j,paths in enumerate(strokes):
  center=(j-1)*3.45;shapes=[]
  for points in paths:shapes.append(LineString([(center+x*scale,23.2+y*scale) for x,y in points]).buffer(.14,cap_style=2,join_style=2))
  f.prism(unary_union(shapes),.10,.25,'red roof letters','original readable 大世界 strokes')
  for u in [center-.45,center+.45]:f.box(u,21.62,.055,1.95,.08,.06,'wrought iron','sign back support')


def build(lod=False):
 detail=not lod;b=Builder(PALETTE);features={};probes=[]
 original=PARAMS['plan_vertices_enu_m'];theater=Polygon(PARAMS['theater_exclusion_enu_m']);exclude=theater.buffer(.15,join_style=2)
 poly=orient(Polygon(original).difference(exclude),sign=1.)
 mapper,starts,outline=perimeter_mapper(poly);points=list(poly.exterior.coords);us=list(starts);zs=[0,20.4];holes=[];nwindows=0
 originaledges=[LineString([original[i],original[(i+1)%len(original)]]) for i in range(len(original))]
 rails=[];toweredges=[];decorated=[]
 for i,(aa,cc) in enumerate(zip(points,points[1:])):
  f=Facade(b,aa,cc,f'body edge {i}');mid=Point(f.center[:2]);source_i=min(range(len(original)),key=lambda j:originaledges[j].distance(mid));party=source_i==0;street=source_i>=5;tc=np.asarray(PARAMS['tower_center_enu_m']);istower=np.linalg.norm(f.center[:2]-tc)<6.1 and f.length>4.
  if party:continue
  if f.length<3:continue
  count=max(1,round((f.length-1.0)/(4.6 if street else 5.4)));margin=.80 if not istower else .53
  spacing=(f.length-2*margin)/count
  width=min(2.43 if street else 2.1,spacing-.84) if not istower else f.length-1.18
  if istower:count=1;spacing=f.length; toweredges.append(f)
  if width<.65:continue
  for j in range(count):
   u=-f.length/2+margin+spacing*(j+.5) if not istower else 0
   for floor,(bottom,height) in enumerate([(.48,5.15),(6.49,3.48),(11.19,3.48),(15.89,3.62)]):
    w=width if floor else min(width+.24,spacing-.45)
    hole=opening(u,bottom,w,height)
    # Actual cut in the continuous exterior shell; matching glazing is inset.
    hbounds=hole.bounds;global_hole=box(starts[i]+u+f.length/2-w/2,bottom,starts[i]+u+f.length/2+w/2,bottom+height);holes.append(global_hole);us.extend([global_hole.bounds[0],global_hole.bounds[2]]);zs.extend([bottom,bottom+height])
    f.window(hole,2 if floor else 3,3 if detail else 2,trim=street and not istower,label='ground storefront' if floor==0 else 'upper recessed window');nwindows+=1
    if street and not istower and floor>0:pediment(f,u,bottom+height,w,['flat','segment','triangle'][floor-1],detail)
    if len(probes)<2 and source_i in [9,20] and floor==1:probes.append({'label':f'body real window edge{source_i}','kind':'ray','origin':f.point(u+width*.17,bottom+height*.54,1).tolist(),'direction':(-f.n).tolist(),'material':'recessed glass','max_distance':2.0})
   if street and not istower:
    for side in [-1,1]:f.box(u+side*(width/2+.35),13.1,.19,13.7,.19,.06,'pale dressed stone','narrow facade pilaster')
  if street and not istower:
   for z in [6.2,10.9,15.6,20.4]:balustrade(b,aa,cc,z,detail,.43)
   decorated.append(source_i)
  elif istower:
   for z in [6.2,10.9,15.6,20.4]:geometric_rail(b,aa,cc,z,detail)
   for u in [-f.length/2+.26,f.length/2-.26]:
    xy=f.point(u,0,.35);stone_column(b,xy[:2],.16,6.08,.40,detail,'entrance lower compound capital column');stone_column(b,xy[:2],6.3,20.25,.39,detail,'entrance giant upper column')
 rectangular_shell(b,mapper,us,zs,holes,-.48,'warm stone','continuous four-storey U shell with actual windows',True)
 # One level main roof: capped perimeter and an inset dark roof field cannot be coplanar.
 b.plan_prism(poly.buffer(-.02,join_style=2),.0,.16,'dark stone','bounded U ground slab')
 roof=poly.buffer(-.46,join_style=2);b.plan_prism(roof,20.15,20.36,'roof zinc','inset main U roof below stone wall cap')
 for z,h,proj in [(0,.35,.08),(6.06,.22,.36),(10.77,.20,.32),(15.47,.20,.32),(20.17,.23,.45)]:band(b,poly,z,h,proj,.26,label='continuous main cornice',exclusion=exclude)
 # Under-floor slabs remain inside U; no interior floors are presented as surveyed.
 features['body']={'plan_area_m2':poly.area,'estimated_roof_m':20.4,'window_openings':nwindows,'continuous_periodic_shell':True,'roof_inset_m':.46,'roof_upper_z_m':20.36,'stone_wall_cap_z_m':20.4,'no_invented_courtyard_floor':True,'party_edge_source0_excluded_from_windows_and_projecting_decoration':True}
 main_tower(b,lod,features,probes)
 for i,p in enumerate(PARAMS['pavilions']):pavilion(b,p,lod,i+1)
 # Both signs face the two documented street wings; custom strokes are estimates.
 for source_i,sign_center in [(9,(-23.1,-6.1)),(20,(-29.0,39.0))]:
  a,c=original[source_i],original[(source_i+1)%len(original)];fa=Facade(b,c,a,'sign orientation');center=np.asarray(sign_center);v=(np.asarray(a)-np.asarray(c));v/=np.linalg.norm(v);roof_letters(b,center-v*4.2,center+v*4.2,lod)
 for z in [8.2,13.1,17.7]:probes.append({'label':f'window perimeter backstop regression z{z}','kind':'ray','origin':[49.42147692,-17.25521427,z],'direction':[-.83897032,-.54417718,0],'max_distance':1.7,'material':'recessed glass'})
 features['pavilions']=PARAMS['pavilions'];features['inscription']='大世界 only: readable original stroke construction; photo-visible text, estimated font/size';features['excluded_current_courtyard_canopy']=True
 meta={'id':ID,'name':'上海大世界｜四层U形主体、街角塔与屋顶亭','scope':PARAMS['scope'],'anchor':PARAMS['anchor'],'all_dimensions_estimated_except_map_plan':True,'source_register':'source-register.json','copyright':'Original geometry MIT; OpenStreetMap plan data ODbL-1.0; no photo pixels or third-party models embedded','variant':'lod' if lod else 'raw','height_m':46.4}
 return b,meta,features,probes

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--lod',action='store_true');p.add_argument('--out',type=Path,required=True);a=p.parse_args();b,m,f,r=build(a.lod);report=b.save(a.out,m);a.out.with_suffix('.features.json').write_text(json.dumps({'features':f,'probes':r},ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='part_summary'},ensure_ascii=False))
