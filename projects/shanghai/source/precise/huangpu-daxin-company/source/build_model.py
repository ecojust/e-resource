"""Original Daxin / The Sun Company historic main-block exterior. MIT.

Observed 2016 and 2025 southwest photographs guide the south/west facades.
All dimensions, layer datums, north/east closures and unseen roof are estimates.
Modern north B and east C buildings, advertisements and interiors are excluded.
"""
import argparse,json,math
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,box,Point
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from common.photo_architecture import Builder,facade_ring,opening
ID='huangpu-daxin-company'
PALETTE={
 'cream glazed tile':{'color':[.64,.585,.46],'roughness':.72},
 'pale ceramic trim':{'color':[.82,.805,.73],'roughness':.66},
 'tile rib':{'color':[.70,.64,.51],'roughness':.74},
 'recessed glass':{'color':[.17,.23,.25],'roughness':.32,'metallic':.12},
 'steel window frame':{'color':[.30,.32,.30],'roughness':.55,'metallic':.25},
 'black granite':{'color':[.085,.095,.095],'roughness':.48},
 'recessed gallery':{'color':[.49,.47,.40],'roughness':.88},
 'roof closure estimate':{'color':[.42,.45,.43],'roughness':.95},
 'plain rear estimate':{'color':[.59,.57,.49],'roughness':.9},
}
SOURCE=[[-27.41538132746998,28.34483246364317],[26.531379128962726,28.344832463643172],[27.563215782625267,-23.769728664810117],[26.530733632685806,-25.602209301182278],[21.516613361372844,-28.456431983297353],[-14.136603951359849,-29.247521954470848],[-21.15683196232215,-27.84848410454567],[-25.534874416921358,-24.53189539043875],[-26.962254933010602,-22.02415086269954]]
P={'local_origin_wgs84':[121.47027547958102,31.237025440662855], 'global_heading_deg':-15.35035407206028,
 'axes':'x ENE, y NNW, z up; southwest is negative x and negative y',
 'all_plan_dimensions_estimated':True,'all_layer_datums_estimated':True,
 'documented_storeys':10,'documented_height_m':42.3,'documented_height_endpoint_verified':False,
 'author_selected_maximum_top_m':42.3,'main_block_roof_design_m':33.0,
 'gallery_roof_design_m':36.6,'gallery_guard_top_design_m':37.18,
 'corner_roof_design_m':40.55,'corner_parapet_design_m':41.85,
 'upper_window_bottoms_design_m':[5.05,9.05,13.05,17.05,21.05,25.05,29.05],
 'upper_window_height_design_m':2.65,'ordinary_window_recess_design_m':.34,
 'gallery_rear_setback_design_m':2.,'ground_entry_recess_design_m':1.05,
 'south_gallery_open_bays':3,'west_gallery_open_bays_estimated':4,
 'north_limit_m':28.34483246364317,'facade_smoothing':'Eight planar facets approximate the southwest rounded street corner within the coarse source polygon.',
 'height_interpretation':'The documented 42.3m lacks a measurement endpoint; choosing it for the model maximum and allocating floors is an author interpretation, not a surveyed reconstruction.'}

def plan():
 # Rounded street corner follows the source envelope without copying neighboring buildings.
 start=np.array([-26.33,-18.8]);control=np.array([-26.33,-28.42]);end=np.array([-13.8,-28.53])
 arc=[((1-t)**2*start+2*t*(1-t)*control+t*t*end).tolist() for t in np.linspace(0,1,9)]
 points=[[-26.80,27.73],*arc,[21.25,-27.85],[26.05,-25.1],[26.95,-23.6],[25.94,27.73]]
 p=orient(Polygon(points),1.);assert p.is_valid and Polygon(SOURCE).buffer(.015).covers(p)
 return p

def wall(f,prev,nxt,lo,hi,holes,mat,thick=.42):
 t,n=f.t[:2],f.n[:2]
 def inside(p,other):
  axes=np.array([n,other]);return p-n*thick if abs(np.linalg.det(axes))<1e-10 else np.linalg.solve(axes,np.array([n@p-thick,other@p-thick]))
 left=(inside(f.a[:2],prev.n[:2])-f.a[:2])@t/thick;right=(inside(f.b[:2],nxt.n[:2])-f.b[:2])@t/thick
 def mapper(u,z,d):return f.point(u-d*(left+(u+f.length/2)/f.length*(right-left)),z,d)
 shape=box(-f.length/2,lo,f.length/2,hi)
 if holes:shape=shape.difference(unary_union(holes))
 f.builder.prism(shape,-thick,0,mapper,mat,f.label+'/opened-solid-wall')

def window(f,shape,lod,label,depth=.34,cols=3,rows=4,trim=True):
 inner=shape.buffer(-.065,join_style=2);f.prism(inner,-depth-.028,-depth,'recessed glass',label+'-recessed-glass')
 x0,z0,x1,z1=shape.bounds;bars=[]
 if not lod:
  bars += [box(x0+(x1-x0)*i/cols-.023,z0,x0+(x1-x0)*i/cols+.023,z1) for i in range(1,cols)]
  bars += [box(x0,z0+(z1-z0)*i/rows-.021,x1,z0+(z1-z0)*i/rows+.021) for i in range(1,rows)]
 panes=inner.difference(unary_union(bars)) if bars else inner
 f.prism(shape.buffer(-.018,join_style=2).difference(panes),-depth+.035,-depth+.11,'steel window frame',label+'-steel-frame')
 if trim:f.box((x0+x1)/2,z0-.055,x1-x0+.10,.11,.17,.015,'tile rib',label+'-sill')

def tile_panel(f,u,z,w,h,lod,label):
 # Original shallow ribs suggest the photographed vertical ceramic detailing;
 # no photo texture or claim of tile-by-tile measured reproduction.
 if h<=.1:return
 f.box(u,z,w,h,.035,.012,'cream glazed tile',label+'-panel')
 if not lod:
  for x in np.linspace(u-w/2+.12,u+w/2-.12,max(2,int(w/.32))):f.box(float(x),z,.035,h,.055,.038,'tile rib',label+'-tile-rib')

def pierced_band(f,u,w,z0,z1,lod,label):
 outer=box(u-w/2,z0,u+w/2,z1);holes=[]
 n=max(2,int(w/.78))
 for k in range(n):
  x=u-w/2+w*(k+.5)/n;size=min(.48,w/n-.16)
  holes.append(box(x-size/2,z0+.15,x+size/2,z1-.15))
  if not lod and k%2==0:holes[-1]=holes[-1].union(box(x-.11,z0+.06,x+.11,z1-.06))
 f.prism(outer.difference(unary_union(holes)),.025,.18,'pale ceramic trim',label+'-true-pierced-frieze')

def crown_fin(f,u,z,lod,label):
 shape=Polygon([(u-.18,z),(u+.18,z),(u+.06,z+.58),(u-.05,z+.50)])
 f.prism(shape,-.06,.20,'pale ceramic trim',label+'-angular-crest')

def build(lod=False):
 b=Builder(PALETTE);p=plan();ff=facade_ring(b,p,'historic-main');corner=orient(p.intersection(box(-50,-50,-7.,-9.2)),1.)
 features={'parameters':P,'source_plan_xy':SOURCE,'design_plan_xy':list(map(list,p.exterior.coords[:-1])),
  'high_corner_plan_xy':list(map(list,corner.exterior.coords[:-1])),'accent_bands':[],'facades':[],'window_openings':0,'gallery_openings':0,'crown_openings':0,'probes':[]}
 def probe(f,u,z,depth,label,mat='recessed glass'):
  features['probes'].append({'label':label,'point':f.point(u,z).tolist(),'normal':f.n.tolist(),'depth':depth,'material':mat})
 for i,f in enumerate(ff):
  south=f.n[1]<-.9;west=f.n[0]<-.9;north=f.n[1]>.9;east=f.n[0]>.9
  curved=f.length<8 and f.n[0]<-.10 and f.n[1]<-.10
  observed=south or west or curved
  count=1 if curved else max(1,round(f.length/(3.35 if observed else 4.1)))
  pitch=f.length/count;centers=[-f.length/2+pitch*(k+.5) for k in range(count)];holes=[]
  for k,u in enumerate(centers):
   width=min(2.58,pitch-.58);ground=box(u-width/2,.25,u+width/2,3.95);holes.append(ground)
   window(f,ground,lod,'ground-'+str(k),1.05 if observed else .45,2,2,False);features['window_openings']+=1
   if curved and i==3:probe(f,u+.13,2.2,1.05,'southwest-deep-shop-entry')
   for level,z in enumerate(P['upper_window_bottoms_design_m']):
    shape=box(u-width/2,z,u+width/2,z+2.65);holes.append(shape);window(f,shape,lod,f'window-{k}-{level}');features['window_openings']+=1
    if observed:tile_panel(f,u,z+3.34,width,1.12,lod,f'spandrel-{k}-{level}')
    if k==count//2 and level in [1,5] and (south or west or curved and i==3):probe(f,u+.16,z+.22,.34,f'{f.label}-window-{level}')
   if observed:
    for sign in [-1,1]:f.box(u+sign*(width/2+.12),18.35,.16,28.7,.18,.035,'tile rib','slender-vertical-pier')
  wall(f,ff[i-1],ff[(i+1)%len(ff)],0,33.,holes,'cream glazed tile' if observed else 'plain rear estimate')
  if (south or west) and f.length>20:
   axis=0 if south else 1;connection_low=-7. if south else -9.2;gallery_low=-3.7 if south else -5.8
   extent=max(f.a[axis],f.b[axis]);centres=[(connection_low+gallery_low)/2,extent-1.8]
   for value in centres:
    u=(value-f.center[axis])/f.t[axis];band=box(u-1.52,4.45,u+1.52,33.)
    f.prism(band.difference(unary_union(holes)),.006,.095,'pale ceramic trim','wide-vertical-stair-accent')
    for side in [-1,1]:
     line=box(u+side*1.40-.035,4.45,u+side*1.40+.035,33.)
     f.prism(line.difference(unary_union(holes)),.10,.14,'pale ceramic trim','accent-vertical-flute')
    features['accent_bands'].append({'face':f.label,'axis':axis,'center_axis':float(value),'u':float(u),'width':3.04,'range_z':[4.45,33.],'photo_guided':True})
  # Dark ground treatment and broad continuous south/west shelter.
  if observed:
   f.box(0,4.15,f.length-.04,.25,1.50,.75,'pale ceramic trim','projecting-continuous-canopy')
   f.box(0,3.98,f.length-.04,.09,1.46,.75,'black granite','canopy-dark-soffit')
   for k in range(count+1):
    if k in (0,count):continue
    f.box(-f.length/2+pitch*k,2.0,.26,3.75,.13,.02,'black granite','shop-granite-pier')
  features['facades'].append({'label':f.label,'a':f.a.tolist(),'b':f.b.tolist(),'normal':f.n.tolist(),'length':f.length,'bays':count,'photo_guided':bool(observed),'simplified_unseen':not observed})
 b.plan_prism(p,.0,.15,'black granite','main-ground-floor')
 b.plan_prism(p.difference(corner),32.88,33.,'roof closure estimate','lower-main-roof-under-gallery')
 # The two photographed street galleries have real large openings, pierced
 # ceramic friezes and an independently recessed rear wall.
 gallery_specs=[]
 south=next(f for f in ff if f.n[1]<-.9 and f.length>20)
 west=next(f for f in ff if f.n[0]<-.9 and f.length>20)
 for f,axis,lower,n in [(south,0,-3.7,3),(west,1,-5.8,4)]:
  pts=[f.a,f.b];lo=max(lower,min(q[axis] for q in pts));hi=max(q[axis] for q in pts)-3.6
  ua=(lo-f.center[axis])/f.t[axis];ub=(hi-f.center[axis])/f.t[axis];left,right=sorted([ua,ub]);width=right-left;step=width/n;holes=[]
  for k in range(n):
   u=left+(k+.5)*step;w=step-1.0;holes.append(box(u-w/2,33.50,u+w/2,35.58))
   # The balustrade is not a dark picture: stepped solid posts and openings.
   f.box(u,33.23,w,.24,.36,.03,'cream glazed tile','gallery-parapet-base')
   f.box(u,33.50,w,.12,.42,.06,'pale ceramic trim','gallery-parapet-cap')
   for x in np.linspace(u-w/2+.12,u+w/2-.12,max(2,int(w/1.25))):f.box(float(x),33.63,.18,.68,.36,.03,'pale ceramic trim','gallery-short-baluster')
   pierced_band(f,u,w,35.62,36.42,lod,'gallery-geometric-band')
   for x in np.arange(u-w/2+.18,u+w/2,.65):crown_fin(f,float(x),36.6,lod,'gallery-crest')
   # Door/window behind an actual clear 2m deep gallery.
   behind=box(u-w/2+.18,33.18,u+w/2-.18,35.55)
   glazing=box(u-.68,33.30,u+.68,35.42)
   f.prism(behind.difference(glazing),-2.24,-2.0,'recessed gallery','gallery-rear-wall')
   window(f,glazing,lod,'gallery-rear-glazing',2.30,2,3,False)
   if k==1:
    probe(f,u+w*.35,34.30,2.0,'gallery-real-setback','recessed gallery')
    probe(f,u+.16,34.30,2.30,'gallery-recessed-glazing')
   features['gallery_openings']+=1
  f.prism(box(left,33.,right,36.6).difference(unary_union(holes)).difference(box(left,35.62,right,36.42)), -.38,0,'cream glazed tile','upper-gallery-opened-wall')
  for k in range(n+1):
   u=left+k*step;f.box(u,34.95,.75,4.10,.48,.02,'cream glazed tile','gallery-wide-pier')
   f.box(u,36.6,.50,1.15,.19,.18,'pale ceramic trim','gallery-pier-stepped-head')
  f.box((left+right)/2,36.52,width,.16,2.52,-.98,'roof closure estimate','gallery-roof-slab')
  gallery_specs.append({'face':f.label,'local_u_range':[left,right],'openings':n,'floor':33.,'ceiling':36.6,'rear_depth':2.})
  # Wide vertical stair accents end in a real arched window and stepped head.
  connector_low=-7. if axis==0 else -9.2
  for j,(begin,end) in enumerate([(connector_low,lower),(hi,max(q[axis] for q in pts))]):
   ends=sorted([(begin-f.center[axis])/f.t[axis],(end-f.center[axis])/f.t[axis]]);mid=sum(ends)/2;w=ends[1]-ends[0]
   arch=opening(mid,33.38,min(1.98,w-.80),2.62,arch=.62,segments=20)
   f.prism(box(ends[0],33.,ends[1],37.40).difference(arch),-.40,.095,'pale ceramic trim','stair-accent-arched-upper-wall')
   window(f,arch,lod,'stair-accent-arched-window',.34,3,4);features['window_openings']+=1
   f.box(mid,37.43,w,.16,.46,.01,'pale ceramic trim','stair-head-first-step')
   f.box(mid,37.64,max(.8,w-.64),.26,.36,.02,'pale ceramic trim','stair-head-second-step')
   f.box(mid,37.88,max(.6,w-1.10),.22,.28,.03,'pale ceramic trim','stair-head-top-step')
   probe(f,mid+.19,34.10,.34,'stair-accent-arched-glass')

 # Simplified inner roof mass has no invented courtyard assertion. The roof
 # beyond these two visible galleries is explicitly an unseen author closure.
 upper_inner=p.buffer(-3.0,join_style=2).difference(corner.buffer(.015,join_style=2))
 b.plan_prism(upper_inner,33.,36.45,'plain rear estimate','estimated-inner-upper-roof-volume')
 b.plan_prism(upper_inner,36.45,36.6,'roof closure estimate','estimated-inner-upper-roof')
 # Taller southwest rounded corner: the photographed crown is not a four-column tower.
 cf=facade_ring(b,corner,'southwest-high-corner')
 crown_probes=[]
 for i,f in enumerate(cf):
  outer=f.n[0]<-.1 or f.n[1]<-.1;count=max(1,round(f.length/2.8));step=f.length/count;centers=[-f.length/2+step*(k+.5) for k in range(count)];holes=[]
  for k,u in enumerate(centers):
   width=min(2.1,step-.52)
   for j,(z,h) in enumerate([(33.20,2.5),(37.10,2.65)]):
    shape=box(u-width/2,z,u+width/2,z+h);holes.append(shape);window(f,shape,lod,f'high-window-{j}-{k}',.34,3,4);features['window_openings']+=1
   if outer:
    f.box(u+width/2+.13,37.10,.22,8.5,.22,.035,'pale ceramic trim','crown-vertical-blade')
    if not lod:f.box(u+width/2+.13,37.1,.055,8.5,.26,.08,'pale ceramic trim','crown-blade-flute')
   if outer and i==3:probe(f,u+.14,38.0,.34,'high-corner-window')
  wall(f,cf[i-1],cf[(i+1)%len(cf)],33.,40.55,holes,'cream glazed tile' if outer else 'plain rear estimate')
  crown_holes=[]
  for k,u in enumerate(centers):
   for sign in [-1,1]:
    w=min(.43,step*.19);x=u+sign*step*.21;shape=box(x-w/2,40.88,x+w/2,41.45);crown_holes.append(shape);features['crown_openings']+=1
    if outer and i==3 and sign==1:crown_probes.append({'label':'crown-small-through-opening','point':f.point(x,41.16).tolist(),'normal':f.n.tolist(),'clear_depth':1.25})
   f.box(u+step/2-.10,41.22,.29,2.16,.46,.04,'pale ceramic trim','crown-stepped-upright')
  wall(f,cf[i-1],cf[(i+1)%len(cf)],40.55,41.85,crown_holes,'pale ceramic trim',.36)
 b.plan_prism(corner,40.40,40.55,'roof closure estimate','corner-roof-under-perforated-parapet')
 # The central stack of projecting circular shelves occupies the rounded SW corner.
 arcfaces=[f for f in cf if f.n[0]<-.25 and f.n[1]<-.25];front=min(arcfaces,key=lambda f:abs(f.n[0]-f.n[1]));center=front.center[:2]+front.n[:2]*.21
 b.lathe(center,[(36.8,.50),(37.0,.60),(38.35,.60),(38.5,.45)],'pale ceramic trim',32,'southwest-central-rounded-drop')
 b.lathe(center,[(38.35,.14),(42.0,.14)],'pale ceramic trim',24,'southwest-central-vertical-spindle')
 for z in [39.,39.68,40.36,41.04,41.72]:b.lathe(center,[(z,.70),(z+.14,.70)],'pale ceramic trim',32,'southwest-stacked-projecting-round-shelf')
 b.lathe(center,[(41.86,.38),(42.05,.33),(42.22,.20),(42.30,.045)],'pale ceramic trim',32,'southwest-ornament-crown-cap')
 features.update(author_parts=len(b.parts),ornament_center_xy_m=center.tolist(),gallery_specs=gallery_specs,crown_probes=crown_probes,photos_embedded=False,north_east_and_inner_roof_estimated=True)
 assert max(q[1] for part in b.parts for q in part['vertices'])<=P['north_limit_m']+1e-8
 meta={'id':ID,'name':'大新公司历史主楼外观候选','status':'exterior-candidate-with-estimated-geographic-placement',
 'current_address':'南京东路830号','documented_storeys':10,'documented_height_m':42.3,'height_endpoints_verified':False,
 'model_selected_architectural_top_m':42.3,'all_plan_dimensions_estimated':True,'all_floor_layer_datums_estimated':True,
 'floor_layer_allocation_is_author_interpretation':True,'local_origin_wgs84':P['local_origin_wgs84'],'heading_deg':P['global_heading_deg'],
 'scope_kind':'historic-main-block-exterior-with-photo-guided-south-and-west-facades',
 'north_and_east_elevations_photo_verified':False,'unseen_roof_is_author_closure':True,'courtyard_configuration_verified':False,
 'modern_north_B_building_modeled':False,'modern_east_C_building_modeled':False,'commercial_signs_modeled':False,
 'interiors_modeled':False,'original_1936_state_claimed':False,'photos_embedded':False,'reference_photographs_embedded':False,
 'map_replacement':False,'geometry_license':'MIT','map_reference_license':'ODbL-1.0',
 'model_plan_area_m2_estimated':float(p.area),'documented_height_interpretation':P['height_interpretation'],
 'local_axes':P['axes'],'copyright':'Original code and geometry MIT; map shape/location reference ODbL-1.0; no photograph pixels embedded.'}
 return b,meta,features

def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--lod',action='store_true');a=p.parse_args();b,meta,features=build(a.lod);a.out.mkdir(parents=True,exist_ok=True);stem=ID+('-lod' if a.lod else '-raw');r=b.save(a.out/(stem+'.glb'),meta)
 (a.out/(stem+'-features.json')).write_text(json.dumps(features,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='part_summary'}))
if __name__=='__main__':main()
