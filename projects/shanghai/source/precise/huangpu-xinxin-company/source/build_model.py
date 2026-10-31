"""Original photo-informed Xinxin south shop-front exterior, MIT.

The 2013/2022/2024/2025 south and oblique photographs were actually viewed.
Only the photographed south commercial part and short side returns are modeled;
the cut at local y=-8m is an author scope boundary, not a surveyed party wall.
Northern hotel, courtyard and interiors remain outside this candidate.
"""
import argparse
import json
import math
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon, box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from common.photo_architecture import Builder, Facade, facade_ring

ID='huangpu-xinxin-company'
PALETTE={
 'warm cream plaster':{'color':[.72,.695,.60],'roughness':.87},
 'pale raised trim':{'color':[.81,.785,.69],'roughness':.82},
 'recessed panel':{'color':[.675,.65,.56],'roughness':.91},
 'shop granite':{'color':[.56,.515,.45],'roughness':.71},
 'recessed glass':{'color':[.13,.19,.21],'roughness':.30,'metallic':.12},
 'dark window frame':{'color':[.17,.18,.16],'roughness':.55,'metallic':.25},
 'gallery shadow wall':{'color':[.54,.53,.47],'roughness':.92},
 'black railing':{'color':[.075,.09,.085],'roughness':.60,'metallic':.35},
 'roof stone':{'color':[.47,.48,.44],'roughness':.95},
 'neutral scope cut':{'color':[.51,.53,.51],'roughness':.98},
}
P={
 'local_origin_wgs84':[121.47222314008322,31.237338603109322],
 'global_heading_deg':-14.444157472676181,
 'local_axes':'x ENE, y NNW, z up; south front at negative y',
 'author_frame_scope_cut_y_m':-8.,'model_frame_scope_cut_y_m':15.219429812778612,'scope_cut_is_surveyed_dividing_wall':False,
 'all_plan_dimensions_estimated':True,'all_layer_datums_estimated':True,
 'source_plan_area_m2_estimated':3965.1463656165315,
 'wall_inset_from_coarse_map_design_m':.65,
 'south_main_bays_design':13,'side_return_bays_design':7,
 'main_window_bottoms_design_m':[5.30,9.70,14.10,18.50,22.75],
 'main_window_heights_design_m':[3.05,3.05,3.05,3.05,2.15],
 'main_wall_top_design_m':25.6,'gallery_roof_top_design_m':29.2,
 'gallery_cornice_top_design_m':29.55,'roof_guard_top_design_m':30.45,
 'corner_pavilion_roof_top_design_m':33.35,
 'central_tower_lower_roof_design_m':34.0,
 'central_tower_upper_roof_design_m':37.5,
 'gallery_setback_design_m':2.15,
 'floor_interpretation':'Ground shop level + five window rows + upper gallery gives seven authored layers. The official sixth-floor balcony is not reconciled to this visual allocation by measured floor plans.',
 'documented_height_description':'more than thirty metres; measurement endpoint unspecified',
 'south_front_photo_window_bays_count_is_estimate':True,
 'current_visible_tower_is_not_claimed_original_1925_tower':True,
 'north_hotel_courtyard_and_true_dividing_line_unmodeled':True,
}
SOURCE_PLAN=[[25.933164160278917,-34.045829045669805],[22.06458256220468,-38.84224958840131],[-21.600823727139378,-38.6548612849901],[-25.77704991331637,-34.419198138334366],[-25.777049913316393,35.10013412649815],[-22.161880397553013,38.90891660735379],[21.99703664837903,38.59448971988469],[25.678844448900698,34.486153025381356]]
SCOPE=box(-100,-100,100,P['author_frame_scope_cut_y_m'])

def south_plan():
 return orient(Polygon(SOURCE_PLAN).buffer(-.65,join_style=2).intersection(SCOPE),sign=1.)

def outer_band(b,plan,z0,z1,reach,label,material='pale raised trim',inner=.35):
 outside=plan.buffer(reach,join_style=2).intersection(SCOPE)
 band=outside.difference(plan.buffer(-inner,join_style=2))
 # North clipping is a neutral scope cut, without a fictitious rear cornice.
 band=band.intersection(box(-100,-100,100,-8.02))
 b.plan_prism(band,z0,z1,material,label)
 return outside

def miter_wall(f,prev,nxt,lo,hi,holes,material,thickness=.4):
 # General corner-miter construction adapted from the cited geometry helper use.
 t,n=f.t[:2],f.n[:2]
 def inner(p,other):
  axes=np.array([n,other])
  return p-n*thickness if abs(np.linalg.det(axes))<1e-10 else np.linalg.solve(axes,np.array([n@p-thickness,other@p-thickness]))
 left=(inner(f.a[:2],prev.n[:2])-f.a[:2])@t/thickness
 right=(inner(f.b[:2],nxt.n[:2])-f.b[:2])@t/thickness
 def mapper(u,z,d):return f.point(u-d*(left+(u+f.length/2)/f.length*(right-left)),z,d)
 shape=box(-f.length/2,lo,f.length/2,hi)
 if holes:shape=shape.difference(unary_union(holes))
 f.builder.prism(shape,-thickness,0,mapper,material,f.label+'/closed-opened-wall')

def framed_window(f,shape,lod,label,depth=.32,cols=3,rows=3):
 inside=shape.buffer(-.085,join_style=2)
 f.prism(inside,-depth-.025,-depth,'recessed glass',label+'-glass')
 x0,z0,x1,z1=shape.bounds
 bars=[]
 if not lod:
  bars += [box(x0+(x1-x0)*k/cols-.026,z0,x0+(x1-x0)*k/cols+.026,z1) for k in range(1,cols)]
  bars += [box(x0,z0+(z1-z0)*k/rows-.024,x1,z0+(z1-z0)*k/rows+.024) for k in range(1,rows)]
 panes=inside.difference(unary_union(bars)) if bars else inside
 f.prism(shape.buffer(-.025,join_style=2).difference(panes),-depth+.035,-depth+.14,'dark window frame',label+'-frame')
 f.box((x0+x1)/2,z0-.055,x1-x0+.14,.11,.23,.035,'pale raised trim',label+'-sill')

def wall_panels(f,u,bottom,width,height,lod,label):
 if height<.32:return
 for k in [-1,1]:
  center=u+k*width*.235;w=width*.39
  outer=box(center-w/2,bottom,center+w/2,bottom+height)
  f.prism(outer,.018,.05,'recessed panel',label+'-panel')
  for inset,depth in ([(0,.13),(.105,.10)] if not lod else [(0,.12)]):
   frame=outer.buffer(-inset,join_style=2).difference(outer.buffer(-inset-.045,join_style=2))
   f.prism(frame,.055,depth,'pale raised trim',label+'-rectangular-moulding')

def balcony_railing(f,u,width,lod,label):
 z0,z1=25.78,26.76
 members=[box(u-width/2,z0,u+width/2,z0+.065),box(u-width/2,z1-.065,u+width/2,z1)]
 members += [box(u-width/2,z0,u-width/2+.055,z1),box(u+width/2-.055,z0,u+width/2,z1)]
 for x in [u-width*.29,u,u+width*.29]:members.append(box(x-.019,z0,x+.019,z1))
 if not lod:
  for x in [u-width*.25,u+width*.25]:
   diamond=Polygon([(x,z0+.15),(x+.18,(z0+z1)/2),(x,z1-.15),(x-.18,(z0+z1)/2)])
   members.append(diamond.exterior.buffer(.020,join_style=2))
   stem=box(x-.021,z0+.10,x+.021,z1-.10);members.append(stem)
 f.prism(unary_union(members),.46,.51,'black railing',label+'-iron-panel')

def corbel(f,u,label):
 profile=Polygon([(-.16,24.28),(.53,25.34),(.53,25.60),(-.16,25.60)])
 f.builder.prism(profile,-.13,.13,lambda d,z,v:f.point(u-v,z,d),'pale raised trim',f.label+'/'+label)

def octagonal_box(cx,cy,width,depth,cut):
 x0,x1=cx-width/2,cx+width/2;y0,y1=cy-depth/2,cy+depth/2
 return Polygon([(x0+cut,y0),(x1-cut,y0),(x1,y0+cut),(x1,y1-cut),(x1-cut,y1),(x0+cut,y1),(x0,y1-cut),(x0,y0+cut)])

def hipped_cap(b,plan,z0,z1,label,lod):
 # A low truncated hip, rather than a dome or a tall historical spire.
 p=orient(plan,1.);lo=list(p.exterior.coords[:-1]);c=np.array(p.centroid.coords[0]);hi=[(c+(np.array(q)-c)*.74).tolist() for q in lo]
 vertices=[(*q,z0) for q in lo]+[(*q,z1) for q in hi];n=len(lo)
 faces=[tuple(reversed(range(n))),tuple(n+i for i in range(n))]
 faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 b.add(vertices,faces,'roof stone',label)

def open_tower_stage(b,plan,bottom,top,label,lod):
 facades=facade_ring(b,plan,label);rays=[]
 for i,f in enumerate(facades):
  n=3 if abs(f.n[1])>.8 else 2
  centers=np.linspace(-f.length/2+.55,f.length/2-.55,n+1)
  holes=[]
  for j in range(n):holes.append(box(centers[j]+.36,bottom+.25,centers[j+1]-.36,top-.42))
  miter_wall(f,facades[i-1],facades[(i+1)%len(facades)],bottom,top,holes,'warm cream plaster',.48)
  for j,u in enumerate(centers):
   f.box(float(u),top-.43,.85,.20,.65,.03,'pale raised trim','stepped-capital-bottom')
   f.box(float(u),top-.21,1.02,.22,.79,.10,'pale raised trim','stepped-capital-top')
  if f.n[1]<-.8:
   h=holes[0];u=(h.bounds[0]+h.bounds[2])/2;rays.append({'label':label,'point':f.point(u,(bottom+top)/2).tolist(),'normal':f.n.tolist(),'clear_depth_m':float(plan.bounds[3]-plan.bounds[1])+.2})
 b.plan_prism(plan.buffer(.36,join_style=2),top,top+.25,'pale raised trim',label+'-wide-roof')
 b.plan_prism(plan.buffer(.18,join_style=2),top+.25,top+.35,'roof stone',label+'-upper-roof-slab')
 return rays

def build(lod=False):
 b=Builder(PALETTE);plan=south_plan();facades=facade_ring(b,plan,'south-scope');window_count=0;gallery_count=0;front_count=0;feature_facades=[];probes=[];open_rays=[]
 for i,f in enumerate(facades):
  north=f.n[1]>.8
  if north:
   miter_wall(f,facades[i-1],facades[(i+1)%len(facades)],0,29.2,[],'neutral scope cut',.45)
   feature_facades.append({'label':f.label,'normal':f.n.tolist(),'scope_cut':True,'windows':0});continue
  south=f.n[1]<-.8;n=13 if south else 7 if abs(f.n[0])>.8 else 1
  spacing=f.length/n;centers=[-f.length/2+spacing*(k+.5) for k in range(n)];holes=[]
  for k,u in enumerate(centers):
   width=min(2.72,spacing-.78) if n>1 else min(2.65,f.length-1.0)
   ground=box(u-width/2,.15,u+width/2,3.92);holes.append(ground)
   entry=south and abs(u)<5.5;framed_window(f,ground,lod,f'ground-{k}',1.45 if entry else .82,2,2)
   window_count+=1
   if south and abs(u)<.1:probes.append({'label':'main-entry','point':f.point(u+.22,2.).tolist(),'normal':f.n.tolist(),'depth':1.45})
   for level,(bottom,height) in enumerate(zip(P['main_window_bottoms_design_m'],P['main_window_heights_design_m'])):
    shape=box(u-width/2,bottom,u+width/2,bottom+height);holes.append(shape);framed_window(f,shape,lod,f'window-{k}-{level}',.32,3,3 if level<4 else 2)
    window_count+=1
    if south:front_count+=1
    if level<4:wall_panels(f,u,bottom+height+.19,width,P['main_window_bottoms_design_m'][level+1]-(bottom+height)-.40,lod,f'spandrel-{k}-{level}')
    if k==n//2 and level in [0,3]:probes.append({'label':f.label+'-window','point':f.point(u+.20,bottom+.21).tolist(),'normal':f.n.tolist(),'depth':.32})
   balcony_railing(f,u,spacing-.54,lod,f'gallery-{k}');gallery_count+=1
  miter_wall(f,facades[i-1],facades[(i+1)%len(facades)],0,25.6,holes,'warm cream plaster')
  for k in range(n+1):
   u=-f.length/2+spacing*k
   if k==0 or k==n:continue
   f.box(u,14.85,.45,21.6,.18,.04,'pale raised trim','long-straight-pier')
   if not lod:
    for d in [-.27,.27]:f.box(u+d,14.85,.052,21.6,.09,.055,'pale raised trim','pier-linear-moulding')
   corbel(f,u,'angular-balcony-bracket')
  for u in np.linspace(-f.length/2+.48,f.length/2-.48,n+1):
   f.box(float(u),27.28,.58,3.02,.48,-.02,'warm cream plaster','gallery-square-column')
   f.box(float(u),28.64,.78,.22,.64,.04,'pale raised trim','gallery-stepped-capital')
  f.box(0,4.32,f.length-.10,.72,.57,.09,'pale raised trim','ground-shop-fascia')
  feature_facades.append({'label':f.label,'normal':f.n.tolist(),'a':f.a.tolist(),'b':f.b.tolist(),'length':f.length,'bays':n,'south_main':bool(south),'window_rows':5,'scope_cut':False})
 # Floor/roof at the north limit are explicit scope closures, not invented hotel geometry.
 b.plan_prism(plan.intersection(box(-100,-100,100,-8.02)),0,.13,'shop granite','scope-ground-floor')
 for z,thickness in [(4.69,.12),(25.59,.18)]:b.plan_prism(plan.buffer(.56,join_style=2).intersection(box(-100,-100,100,-8.02)),z,z+thickness,'pale raised trim','front-floor-and-balcony-slab')
 outer_band(b,plan,25.34,25.58,.58,'deep-balcony-lip')
 # The hall is recessed behind a genuinely open three-sided gallery.
 hall=plan.buffer(-2.15,join_style=2).union(box(plan.bounds[0]+2.15,-12,plan.bounds[2]-2.15,-8)).intersection(plan).simplify(1e-7,preserve_topology=True)
 hallfaces=facade_ring(b,hall,'setback-hall')
 for i,f in enumerate(hallfaces):
  if f.n[1]>.8:continue
  n=max(1,int(f.length/3.4));holes=[]
  for u in np.linspace(-f.length/2+1.25,f.length/2-1.25,n):
   shape=box(float(u)-.92,26.10,float(u)+.92,28.49);holes.append(shape);framed_window(f,shape,lod,'setback-gallery-door',.32,2,2)
  miter_wall(f,hallfaces[i-1],hallfaces[(i+1)%len(hallfaces)],25.77,29.12,holes,'gallery shadow wall',.36)
 roof=plan.buffer(.52,join_style=2).intersection(box(-100,-100,100,-8.02))
 b.plan_prism(roof,29.12,29.2,'roof stone','gallery-roof')
 outer_band(b,plan,28.83,29.18,.65,'gallery-deep-cornice')
 outer_band(b,plan,29.18,29.40,.56,'gallery-upper-wide-band')
 outer_band(b,plan,29.40,29.55,.67,'gallery-top-edge')
 # Thin roof guards, not modern commercial signs or a fictitious antenna.
 for f in facade_ring(b,plan.buffer(-.12,join_style=2).intersection(SCOPE),'roof-guard'):
  if f.n[1]>.8:continue
  for z in [29.78,30.44]:f.box(0,z,f.length-.1,.04,.04,0,'black railing','horizontal-guard')
  for u in np.linspace(-f.length/2+.18,f.length/2-.18,max(2,int(f.length/2.2)+1)):
   f.box(float(u),30.02,.04,.86,.04,0,'black railing','guard-post')
 # Central paired-column south shop entry; all proportions are author estimates.
 south=next(f for f in facades if f.n[1]<-.8)
 for c in [-4.42,4.42]:
  for offset in [-.30,.30]:
   center=south.point(c+offset,0,.43)[:2]
   profile=[(.13,.30),(.28,.30),(.37,.24),(.47,.21),(3.50,.19),(3.58,.24),(3.78,.28),(3.92,.28)]
   b.lathe(center,profile,'pale raised trim',12 if lod else 24,'entry-paired-column')
   if not lod:
    for sign in [-1,1]:
     curve=[]
     for a in np.linspace(0,math.tau*1.1,22):
      radius=.11*(1-a/(math.tau*1.4));curve.append(south.point(c+offset+sign*(.18+radius*math.cos(a)),3.72+radius*math.sin(a),.44))
     b.tube(curve,.022,'pale raised trim',6,'entry-capital-scroll')
 # Two currently visible corner pavilions; roof type differs from unverified historic spires.
 for cx,label in [(-20.55,'southwest-corner'),(20.85,'southeast-corner')]:
  pavilion=octagonal_box(cx,-33.35,5.8,5.8,.8)
  b.plan_prism(pavilion.buffer(.18,join_style=2),29.55,29.90,'pale raised trim',label+'-base')
  ff=facade_ring(b,pavilion,label)
  for i,f in enumerate(ff):
   n=3 if f.length>3.5 else 1;centers=np.linspace(-f.length/2+.48,f.length/2-.48,n+1);holes=[]
   for j in range(n):
    shape=box(centers[j]+.12,30.17,centers[j+1]-.12,32.53);holes.append(shape);framed_window(f,shape,lod,'pavilion-window',.32,1,1)
   miter_wall(f,ff[i-1],ff[(i+1)%len(ff)],29.9,32.74,holes,'warm cream plaster',.32)
  b.plan_prism(pavilion.buffer(.25,join_style=2),32.74,32.92,'pale raised trim',label+'-projecting-eave')
  hipped_cap(b,pavilion.buffer(.23,join_style=2),32.92,33.35,label+'-low-hipped-cap',lod)
 # Open two-level south-middle tower, with unobstructed openings on all sides.
 lower=box(-5.25,-36.1,5.25,-28.3);upper=box(-4.0,-35.15,4.0,-29.25)
 b.plan_prism(lower,29.2,29.55,'roof stone','central-tower-base-floor')
 open_rays += open_tower_stage(b,lower,29.55,33.65,'central-open-lower',lod)
 open_rays += open_tower_stage(b,upper,34.0,37.15,'central-open-upper',lod)
 for f in facade_ring(b,lower,'central-terrace-guard'):
  if f.n[1]>.8:continue
  f.box(0,34.72,f.length-.4,.035,.035,-.10,'black railing','guard-top')
  for u in np.linspace(-f.length/2+.35,f.length/2-.35,max(2,int(f.length/1.5))):f.box(float(u),34.39,.035,.67,.035,-.10,'black railing','guard-post')
 metadata={'id':ID,'name':'新新公司南侧商店主楼临街外观候选','status':'partial-exterior-candidate-with-estimated-geographic-placement',
  'current_address':'南京东路720号','documented_front_storeys':7,'documented_height_description':P['documented_height_description'],
  'height_endpoints_verified':False,'model_selected_architectural_top_m':37.5,
  'all_plan_dimensions_estimated':True,'floor_layer_allocation_is_author_interpretation':True,
  'scope_cut_y_m':15.219429812778612,'author_frame_scope_cut_y_m':-8.,'scope_cut_is_surveyed_dividing_wall':False,'rear_cut_face_is_neutral_closure_not_real_elevation':True,
  'northern_hotel_modeled':False,'courtyard_modeled':False,'true_front_hotel_dividing_line_verified':False,
  'observed_current_south_tower_modeled':True,'tower_original_1925_identity_claimed':False,
  'documentary_1949_removal_vs_current_tower_unresolved':True,'unseen_historic_northeast_northwest_spires_modeled':False,
  'documented_site_area_m2':4280.,'model_plan_area_m2_estimated':float(plan.area),
  'model_plan_does_not_rescale_map_to_documented_area':True,
  'seven_layer_assignment_is_not_claimed_to_resolve_documented_sixth_floor_balcony':True,
  'southern_front_and_short_side_returns_only':True,'interiors_modeled':False,'neighbor_buildings_modeled':False,
  'commercial_advertising_text_modeled':False,'modern_roof_antenna_included':False,
  'photos_embedded':False,'reference_photographs_embedded':False,'map_replacement':False,
  'local_axes':P['local_axes'],'copyright':'Original code and geometry MIT; map shape/location reference ODbL-1.0; photograph pixels not embedded.'}
 features={'parameters':P,'author_parts':len(b.parts),'window_openings':window_count,'south_main_upper_windows':front_count,
  'gallery_railing_panels':gallery_count,'central_tower_is_open':True,'corner_pavilions':2,
  'source_plan_xy':SOURCE_PLAN,'design_plan_xy':list(map(list,plan.exterior.coords[:-1])),
  'recessed_hall_plan_xy':list(map(list,hall.exterior.coords[:-1])),'facades':feature_facades,
  'probe_candidates':probes,'open_tower_probe_candidates':open_rays,'north_hotel_unmodeled':True,
  'scope_cut_face_has_no_windows':True,'photos_embedded':False}
 # Rebase the authored source-centred frame to the south scope centroid. The
 # exact Mercator unit ratio preserves horizontal world coordinates; height is
 # unchanged. This also keeps the shared-map beacon on the modeled south part.
 offset=np.array([.08040842768440214,-23.219397263157248]);factor=1.0000021386931954
 def model_point(point):
  q=np.asarray(point,float).copy();q[:2]=(q[:2]-offset)*factor;return q.tolist()
 for part in b.parts:part['vertices']=[model_point(p) for p in part['vertices']]
 assert max(p[1] for part in b.parts for p in part['vertices'])<=15.219429812778612+1e-8, 'Geometry crosses north scope cap'
 for key in ['source_plan_xy','design_plan_xy','recessed_hall_plan_xy']:
  features[key]=[model_point(p) for p in features[key]]
 for f in features['facades']:
  for key in ['a','b']:
   if key in f:f[key]=model_point(f[key])
 for entry in features['probe_candidates']+features['open_tower_probe_candidates']:
  entry['point']=model_point(entry['point'])
  if 'depth' in entry:entry['depth']*=factor
  if 'clear_depth_m' in entry:entry['clear_depth_m']*=factor
 conversion={'source_author_origin_wgs84':[121.47216140297178,31.2375406392732],
             'model_origin_wgs84':P['local_origin_wgs84'],'offset_subtracted_xy_m':offset.tolist(),
             'horizontal_unit_ratio':factor,'height_scale':1.,
             'purpose':'Preserve world coordinates while centering the model/beacon on the authored south scope.'}
 metadata['coordinate_rebase']=conversion;features['coordinate_rebase']=conversion
 metadata['model_plan_area_m2_estimated']*=factor**2
 features['parameters_frame']='Design construction dimensions use source-author frame; all part vertices, feature polygons and probes use final south-centred model frame.'
 return b,metadata,features

def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--lod',action='store_true');a=p.parse_args()
 b,meta,features=build(a.lod);a.out.mkdir(parents=True,exist_ok=True);stem=ID+('-lod' if a.lod else '-raw');r=b.save(a.out/(stem+'.glb'),meta)
 (a.out/(stem+'-features.json')).write_text(json.dumps(features,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='part_summary'}))
if __name__=='__main__':main()
