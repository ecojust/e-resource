"""Original Grosvenor House historic high-rise exterior, Shanghai. MIT.

The 2020 garden photograph guides the terraced silhouette, pale vertical strips,
deep crown grooves and low glass entrance shelter. Coarse map geometry does not
identify the heights of its southern steps; the main wall / low shelter split
below is explicitly an author interpretation, not surveyed source attribution.
"""
import argparse,json,math
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from common.photo_architecture import Builder,Facade,facade_ring

ID='huangpu-grosvenor-house'
SOURCE=[[-36.836629309851624,-14.44824692294231],[-45.044035168342674,-6.381525266969918],[-34.09343605436925,4.890164740347272],[-22.380632141494406,11.194258950865404],[18.22999574564109,11.1942589508654],[30.487313979352002,8.149864659582171],[35.93984744654057,4.375716353431706],[46.50543960525292,-6.420045317396937],[35.70891441294333,-16.986382489407085],[25.296807259090787,-5.484350347817697],[11.508281127944818,-.9994931296495198],[10.30991741413595,-4.7995128415802615],[4.363833293786576,-4.978179379233726],[4.273749832471603,-2.0050538065582066],[.16664373872160865,-2.2164101992845455],[.2244274513628679,-7.028300482832202],[-19.88215535259785,-7.809791582275718],[-19.971639636250636,-4.837599633266801],[-22.944983211104038,-4.926463090703536],[-34.75348242506116,-16.748727390768973]]
P={'local_origin_wgs84':[121.45728030428835,31.221260424588685],
 'global_heading_deg':32.69139103346206,
 'axes':'x southeast along central back wall, y northeast; garden facade faces local -y; z up',
 'documented_storeys_including_basement':18,'documented_basements':1,'documented_height_m':78.,
 'secondary_storey_account':{'above_ground':18,'below_ground':3,'conflict_resolved':False},
 'model_above_ground_floor_layers':17,'model_below_ground_layers':0,
 'height_endpoints_verified':False,'model_selected_architectural_top_m':78.,
 'floor_pitch_design_m':4.1,'terrace_roof_design_m':[53.3,57.4,61.5,65.6,69.7],
 'main_plan_inset_design_m':.30,'central_tower_projection_design_m':.75,
 'central_tower_face_width_design_m':15.,'entrance_shelter_width_design_m':18.,
 'entrance_shelter_depth_design_m':4.6,'ordinary_window_recess_design_m':.32,
 'crown_groove_rear_depth_design_m':.58,
 'all_plan_dimensions_estimated':True,'all_floor_layer_datums_estimated':True,
 'source_south_step_height_attribution_verified':False,
 'entrance_shelter_depth_reason':'Conservative 4.6m design depth keeps the separately identified foreground map source clear. It is an author placement constraint, not a measured real canopy depth.',
 'height_interpretation':'The official 18 layers includes one basement; the model uses seventeen estimated above-ground layers and a non-occupied architectural crown, omits all underground construction and chooses 78m as its maximum. The source does not define height endpoints, and secondary 18-above/3-below wording conflicts.'}
PALETTE={
 'warm brown brick':{'color':[.48,.36,.265],'roughness':.91},
 'brick horizontal band':{'color':[.42,.305,.22],'roughness':.9},
 'pale vertical stone':{'color':[.82,.80,.715],'roughness':.73},
 'window sill stone':{'color':[.55,.49,.395],'roughness':.82},
 'recessed glass':{'color':[.15,.235,.24],'roughness':.28,'metallic':.14},
 'dark window frame':{'color':[.23,.28,.255],'roughness':.59},
 'roof closure estimate':{'color':[.32,.345,.31],'roughness':.92},
 'dark shelter metal':{'color':[.115,.15,.145],'roughness':.58,'metallic':.32},
 'shelter roof glass':{'color':[.185,.305,.315],'roughness':.22,'metallic':.22},
 'crown recessed brick':{'color':[.31,.225,.16],'roughness':.95},
 'ground stone':{'color':[.43,.435,.375],'roughness':.86},
}


def main_plan():
 # Removing the southern map steps from the tall bar is an interpretation.
 # Their source-level building ownership is retained in the placement audit;
 # they are not automatically declared to be surveyed canopy footprints.
 pruned=Polygon(SOURCE[:11]+[SOURCE[17],SOURCE[18],SOURCE[19]])
 p=orient(pruned.buffer(-P['main_plan_inset_design_m'],join_style=2),1.)
 assert Polygon(SOURCE).covers(p)
 # The central photographed pale tower projects in front of the main wall.
 tmp=Builder(PALETTE)
 face=min((f for f in facade_ring(tmp,p) if f.n[1]<-.8 and f.length>20),key=lambda f:abs(f.center[0]+4.2))
 width=P['central_tower_face_width_design_m'];d=P['central_tower_projection_design_m']
 pts=[face.point(-width/2,0)[:2],face.point(width/2,0)[:2],face.point(width/2,0,d)[:2],face.point(-width/2,0,d)[:2]]
 projection=Polygon(pts)
 p=orient(p.union(projection),1.)
 return p,face.center[:2],face.t[:2],face.n[:2]


def wall(f,prev,nxt,lo,hi,holes,material='warm brown brick',thickness=.40):
 # Miter the independent closed wall solids along their plan corners. This
 # avoids overlapping square-ended strips at oblique source boundary turns.
 t,n=f.t[:2],f.n[:2]
 def inside(point,other):
  axes=np.array([n,other]);return point-n*thickness if abs(np.linalg.det(axes))<1e-10 else np.linalg.solve(axes,np.array([n@point-thickness,other@point-thickness]))
 left=(inside(f.a[:2],prev.n[:2])-f.a[:2])@t/thickness
 right=(inside(f.b[:2],nxt.n[:2])-f.b[:2])@t/thickness
 def mapper(u,z,d):return f.point(u-d*(left+(u+f.length/2)/f.length*(right-left)),z,d)
 shape=box(-f.length/2,lo,f.length/2,hi)
 if holes:shape=shape.difference(unary_union(holes))
 f.builder.prism(shape,-thickness,0,mapper,material,f.label+'/opened-mitered-wall')


def window(f,shape,lod,label,cols=4,rows=3,depth=.32):
 inner=shape.buffer(-.065,join_style=2)
 f.prism(inner,-depth-.028,-depth,'recessed glass',label+'-recessed-glass')
 x0,z0,x1,z1=shape.bounds;bars=[]
 if not lod:
  for i in range(1,cols):
   x=x0+(x1-x0)*i/cols;bars.append(box(x-.023,z0,x+.023,z1))
  for i in range(1,rows):
   z=z0+(z1-z0)*i/rows;bars.append(box(x0,z-.023,x1,z+.023))
 panes=inner.difference(unary_union(bars)) if bars else inner
 f.prism(shape.buffer(-.018,join_style=2).difference(panes),-depth+.04,-depth+.12,'dark window frame',label+'-frame')
 f.box((x0+x1)/2,z0-.055,x1-x0+.15,.12,.27,.025,'window sill stone',label+'-sill')


def build(lod=False):
 b=Builder(PALETTE);p,center,tangent,normal=main_plan();cx=float(center[0])
 tower_front=center+normal*P['central_tower_projection_design_m']
 features={'parameters':P,'source_plan_xy':SOURCE,'design_plan_xy':list(map(list,p.exterior.coords[:-1])),
  'source_southern_steps_not_assumed_surveyed_canopy':True,'central_axis_plan_m':center.tolist(),
  'central_tower_front_plan_m':tower_front.tolist(),'window_openings':0,'crown_recesses':0,
  'terrace_levels':[],'facades':[],'probes':[],'photos_embedded':False}
 def probe(f,u,z,depth,group,material='recessed glass'):
  features['probes'].append({'group':group,'point':f.point(u,z).tolist(),'normal':f.n.tolist(),'depth':depth,'material':material})
 # Five altitude bands expose genuine terraces; no solid full-height slab
 # hides these setbacks. Widths and floor allocations are author estimates.
 halfwidths=[100.,34.5,26.5,18.5,10.0]
 tiers=[orient(p.intersection(box(cx-w,-100,cx+w,100)),1.) for w in halfwidths]
 tops=P['terrace_roof_design_m'];bottom=0.
 tower_faces=[]
 for tier,(poly,top) in enumerate(zip(tiers,tops)):
  ff=facade_ring(b,poly,f'terrace-band-{tier}')
  for i,f in enumerate(ff):
   tower=abs(np.dot(f.center[:2]-tower_front,normal))<.025 and np.dot(f.n[:2],normal)>.999 and f.length>14
   front=f.n[1]<-.12
   outer_accent=front and abs(f.center[0]-cx)>32 and f.length>7
   if tower:
    n=8;pitch=f.length/n;specs=[(-f.length/2+pitch*(k+.5),.92,1) for k in range(n)];tower_faces.append(f)
   elif outer_accent:
    n=3;pitch=f.length/n;specs=[(-f.length/2+pitch*(k+.5),min(1.55,pitch-.65),2) for k in range(n)]
   elif f.length>2.4:
    n=max(1,round(f.length/5.15));pitch=f.length/n
    specs=[(-f.length/2+pitch*(k+.5),min(3.65,pitch-.95),4) for k in range(n)]
   else:specs=[]
   holes=[]
   for k,(u,w,cols) in enumerate(specs):
    for floor in range(17):
     z=floor*4.1+.60;h=3.05 if floor==0 else 2.45
     if z<bottom+.15 or z+h>top-.30:continue
     shape=box(u-w/2,z,u+w/2,z+h);holes.append(shape)
     window(f,shape,lod,f'window-{k}-floor-{floor}',cols=cols,rows=3)
     features['window_openings']+=1
     if k==0 and ((tier==0 and floor in [4,10] and front and f.length>7) or tier>0 and front and f.length>7):
      probe(f,u+w*.11,z+.37,.32,('central-tower' if tower else 'outer-accent' if outer_accent else 'garden-wide')+f'-tier-{tier}-floor-{floor}')
   wall(f,ff[i-1],ff[(i+1)%len(ff)],max(.05,bottom),top,holes)
   if not tower and f.length>2.4:
    for floor in range(17):
     z=floor*4.1+3.58
     if bottom+.10<z<top-.15:f.box(0,z,f.length-.04,.095,.06,.015,'brick horizontal band','horizontal-brick-course')
   if outer_accent:
    for k in range(4):
     u=-f.length/2+f.length*k/3
     # Slightly shorten corner fins to stay within the identified main source.
     if k in [0,3]:u+=.20 if k==0 else -.20
     f.box(u,(bottom+top)/2,.24,top-bottom-.08,.17,.045,'pale vertical stone','outer-wing-long-pale-strip')
     if tier==0:f.box(u,top-.44,.45,1.20,.22,.065,'pale vertical stone','outer-wing-strip-stepped-head')
   f.box(0,top-.035,f.length-.06,.16,.35,.025,'window sill stone','terrace-edge-cornice')
   features['facades'].append({'label':f.label,'normal':f.n.tolist(),'a':f.a.tolist(),'b':f.b.tolist(),
       'height_range':[bottom,top],'tower':bool(tower),'front_photo_guided':bool(front),'rear_estimated':not front,'bays':len(specs)})
  upper=tiers[tier+1] if tier+1<len(tiers) else Polygon()
  roof=poly.buffer(-.065,join_style=2).difference(upper.buffer(.02,join_style=2))
  if not roof.is_empty:b.plan_prism(roof,top-.19,top-.035,'roof closure estimate',f'terrace-{tier}-exposed-roof')
  guard=poly.difference(poly.buffer(-.24,join_style=2)).difference(upper.buffer(.28,join_style=2))
  if not guard.is_empty:b.plan_prism(guard,top+.035,top+.80,'pale vertical stone',f'terrace-{tier}-open-plan-parapet')
  features['terrace_levels'].append({'roof_top_m':top-.035,'parapet_top_m':top+.80,'plan_xy':list(map(list,poly.exterior.coords[:-1]))})
  bottom=top
 b.plan_prism(p.buffer(-.065,join_style=2),0,.21,'ground stone','main-ground-closure')
 # The continuous narrow pale fins visually connect the entrance and crown.
 # They sit between the eight actual narrow-window columns, never over glass.
 tf=next(f for f in tower_faces if f.label.startswith('terrace-band-0'))
 for k in range(9):
  u=-tf.length/2+tf.length*k/8
  if k in [0,8]:u+=.13 if k==0 else -.13
  tf.box(u,34.98,.235,69.35,.20,.075,'pale vertical stone','central-continuous-pale-fin')
  tf.box(u,69.16,.52,1.16,.26,.105,'pale vertical stone','central-fin-top-stepped-head')
  if not lod:tf.box(u,34.92,.052,68.88,.24,.12,'pale vertical stone','central-fin-fine-rib')

 # Smaller set-back crown with eight deep, genuinely recessed vertical grooves.
 crown_width=12.40;crown_depth=6.40;back_center=tower_front-normal*.80
 crown=orient(Polygon([back_center+tangent*(-crown_width/2),back_center+tangent*(crown_width/2),
                      back_center+tangent*(crown_width/2)-normal*crown_depth,
                      back_center+tangent*(-crown_width/2)-normal*crown_depth]),1.)
 cff=facade_ring(b,crown,'central-crown')
 for i,f in enumerate(cff):
  front=np.dot(f.n[:2],normal)>.99;holes=[]
  if front:
   for k in range(8):
    u=-f.length/2+f.length*(k+.5)/8;w=.97
    shape=box(u-w/2,70.55,u+w/2,76.55);holes.append(shape)
    f.prism(shape.buffer(-.022,join_style=2),-.61,-.58,'crown recessed brick',f'crown-deep-groove-{k}-rear')
    features['crown_recesses']+=1
    if k in [2,5]:probe(f,u,73.2,.58,'crown-real-deep-groove','crown recessed brick')
  wall(f,cff[i-1],cff[(i+1)%len(cff)],69.7,77.10,holes,'pale vertical stone',.42)
  f.box(0,77.21,f.length-.04,.22,.35,.025,'pale vertical stone','crown-top-cap')
  if front:
   f.box(0,77.48,f.length-.75,.45,.30,-.035,'pale vertical stone','crown-upper-setback')
   for u in [-2.40,2.40]:f.box(u,77.56,.96,.88,.50,-.075,'pale vertical stone','crown-two-short-top-piers')
 b.plan_prism(crown.buffer(-.07,join_style=2),76.91,77.07,'roof closure estimate','unseen-crown-roof-closure')

 # Low glass entrance shelter observed in the garden photograph. Its position
 # and dimensions are estimates; it is not asserted to match a specific source
 # southern step. It remains low, independently supported and visibly glazed.
 shelter=Facade(b,tower_front-tangent*9.,tower_front+tangent*9.,'garden-entrance-shelter')
 # Local d is outward from the garden wall; the shelter projects southward.
 def shelter_point(u,z,d):return shelter.point(u,z,d)
 width=18.;depth=P['entrance_shelter_depth_design_m']
 canopy_plan=orient(Polygon([shelter_point(-9.,0,.12)[:2],shelter_point(9.,0,.12)[:2],
                            shelter_point(9.,0,depth)[:2],shelter_point(-9.,0,depth)[:2]]),1.)
 # Glass panels occupy genuine holes in the metal frame. They are modeled as
 # thin opaque glazing solids, with no hidden unperforated slab below them.
 rows=3;cols=6;roof_holes=[]
 for ix in range(cols):
  for iy in range(rows):
   u=-width/2+width*(ix+.5)/cols;d=.12+(depth-.12)*(iy+.5)/rows
   ww=width/cols-.17;dd=(depth-.12)/rows-.17
   roof_holes.append(Polygon([shelter_point(u-ww/2,0,d-dd/2)[:2],shelter_point(u+ww/2,0,d-dd/2)[:2],
                              shelter_point(u+ww/2,0,d+dd/2)[:2],shelter_point(u-ww/2,0,d+dd/2)[:2]]))
   b.box(shelter_point(u,4.045,d),(ww,dd,.08),'shelter roof glass',[shelter.t,shelter.n,[0,0,1]],label=f'shelter-glass-panel-{ix}-{iy}')
   if not lod:
    for side in [-1,1]:
     b.box(shelter_point(u+side*ww/2,4.12,d),(.055,dd,.12),'dark shelter metal',[shelter.t,shelter.n,[0,0,1]],label='shelter-real-thin-roof-rib')
 b.plan_prism(canopy_plan.difference(unary_union(roof_holes)),3.93,4.08,'dark shelter metal','low-entrance-roof-pierced-frame-matrix')
 for u in [-8.35,-2.8,2.8,8.35]:
  for d in [1.0,depth-.65]:
   b.box(shelter_point(u,1.95,d),(.38,.38,3.90),'pale vertical stone',label='shelter-independent-pier')
   b.box(shelter_point(u,.22,d),(.52,.52,.44),'ground stone',label='shelter-pier-plinth')
 features['shelter_plan_xy']=list(map(list,canopy_plan.exterior.coords[:-1]));features['shelter_glass_cells']=18
 features.update(author_parts=len(b.parts),main_above_ground_floor_layers=17,underground_modeled=False,
   neighboring_new_jinjiang_tower_modeled=False,western_low_apartments_modeled=False,
   main_front_five_fold_plan_estimated=True,roof_and_rear_estimated=True)
 meta={'id':ID,'name':'峻岭公寓历史高层主楼外观候选','status':'exterior-candidate-with-estimated-geographic-placement',
  'current_address':'茂名南路65－125号（名录范围）','official_narrative_address':'茂名南路59号',
  'address_correspondence_verified':False,'documented_storeys_including_basement':18,'documented_basements':1,
  'secondary_storey_account':P['secondary_storey_account'],'documented_height_m':78.,'height_endpoints_verified':False,
  'model_selected_architectural_top_m':78.,'model_above_ground_floor_layers':17,'model_below_ground_layers':0,
  'floor_layer_allocation_is_author_interpretation':True,'all_plan_dimensions_estimated':True,'all_floor_layer_datums_estimated':True,
  'garden_elevation_photo_guided':True,'rear_elevation_photo_verified':False,'unseen_roof_is_author_closure':True,
  'source_south_step_height_attribution_verified':False,'shelter_equals_specific_map_step_claimed':False,
  'shelter_depth_constrained_to_preserve_adjacent_source':True,
  'western_low_apartments_modeled':False,'neighboring_new_jinjiang_tower_modeled':False,
  'commercial_signs_modeled':False,'interiors_modeled':False,'underground_modeled':False,
  'photos_embedded':False,'map_replacement':False,'original_1934_state_claimed':False,
  'scope_kind':'historic-high-rise-main-block-exterior','local_origin_wgs84':P['local_origin_wgs84'],
  'global_heading_deg':P['global_heading_deg'],'source_footprint_id':'6fa0e0aa-bfd0-4d9e-a4bb-16e9088d530e',
  'geometry_license':'MIT','model_units':'metres','author_axes':P['axes'],'gltf_axes':'x southeast, y up, z southwest',
  'height_interpretation':P['height_interpretation'],
  'scope':'Photo-informed current exterior of the Grosvenor House historic high-rise / Jinjiang middle building. Seventeen estimated above-ground layers, stepped wing terraces, pale central verticals, recessed crown and low glass entrance shelter are modeled. All dimensions, floor datums, hidden rear/roof and main-wall versus low-shelter source-plan split are author interpretations. Western lower apartments, gardens, New Jinjiang tower, signs, interiors and underground construction excluded.'}
 return b,meta,features


def main():
 parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True);parser.add_argument('--lod',action='store_true');args=parser.parse_args()
 b,meta,features=build(args.lod);args.out.mkdir(parents=True,exist_ok=True);role='lod' if args.lod else 'raw'
 record=b.save(args.out/(ID+'-'+role+'.glb'),meta)
 (args.out/(role+'-features.json')).write_text(json.dumps(features,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:v for k,v in record.items() if k!='part_summary'},ensure_ascii=False))
if __name__=='__main__':main()
