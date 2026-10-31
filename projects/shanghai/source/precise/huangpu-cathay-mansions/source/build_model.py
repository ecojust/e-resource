"""Original Cathay Mansions historic main-block exterior, Shanghai. MIT.

South garden 2006 and northwest street 2019 photographs guide the model.
The frozen source footprint establishes only an estimated map envelope. Every
dimension, floor datum and unseen east/roof detail is an author interpretation.
No photographs or their pixels are embedded in any delivered model.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon, box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from common.photo_architecture import Builder, Facade, facade_ring

ID = 'huangpu-cathay-mansions'
P = {
 'local_origin_wgs84': [121.4562656354953,31.222458278353752],
 'global_heading_deg': -12.528888829615887,
 'axes': 'x ENE along south garden facade; y NNW toward Changle Road; z up',
 'documented_storey_height_alternatives': [{'storeys':14,'height_m':57.0},{'storeys':13,'height_m':65.0}],
 'model_selected_architectural_top_m':57.0,
 'main_roof_design_m':52.10,
 'crown_floor_design_m':52.10,
 'ordinary_window_recess_design_m':.30,
 'all_plan_dimensions_estimated':True,
 'all_floor_layer_datums_estimated':True,
 'height_endpoints_verified':False,
 'main_floor_window_bottoms_design_m':[.55,4.45,*[8.55+4*i for i in range(10)],48.65],
 'main_floor_window_heights_design_m':[2.95,2.95,*[2.90 for i in range(10)],2.45],
 'south_projecting_bay_centers_design_m':[-20.,20.],
 'south_bay_vertical_range_design_m':[8.05,44.15],
 'north_wing_ranges_design_m':[[-22.10,-11.45,6.65,15.56],[10.95,23.55,6.65,15.56]],
 'main_plan_range_design_m':[-32.60,-10.95,31.95,6.65],
 'photographed_features':'Brown brick / pale stepped surrounds; south stacked polygonal bays; pale upper storey and central small crown; two north projections, deep setbacks and broad/narrow window groups.',
 'height_interpretation':'Official account gives 14 storeys/57m and an alternative 13 storeys/65m without endpoints. The model chooses a 57m maximum, 13 layers in the main bar and one central rooftop layer, all author interpretations rather than a survey.'
}
SOURCE = [[-32.82142631387234,7.321224398713261],[-22.419563822617356,7.099888428700691],[-22.58519210694998,8.70406381901618],[-22.439153290110596,8.671610531632206],[-22.530579657562498,16.007078041501188],[-11.021982077862882,16.06263791039213],[-10.911207918297961,7.154360771880869],[10.500780177909007,7.099356856583521],[10.390006840680247,16.00763769558277],[24.00111394959605,16.117669666110164],[24.11212795668315,7.210471834232653],[32.411240661140056,6.9335826169227595],[32.47418017522211,-3.531434047416538], [32.68764296542285,-3.5788705401661955],[32.52138450594609,-11.379905054393465],[-33.319539750960494,-11.379905054393461]]
PALETTE = {
 'brown brick':{'color':[.31,.225,.16],'roughness':.91},
 'warm brick variation':{'color':[.375,.285,.205],'roughness':.9},
 'pale dressed stone':{'color':[.79,.775,.675],'roughness':.75},
 'recessed glass':{'color':[.13,.21,.23],'roughness':.28,'metallic':.18},
 'pale window frame':{'color':[.72,.73,.65],'roughness':.61},
 'lower stone base':{'color':[.57,.555,.475],'roughness':.8},
 'roof closure estimate':{'color':[.35,.37,.33],'roughness':.93},
 'dark metal':{'color':[.12,.15,.145],'roughness':.62,'metallic':.3},
 'recessed carved stone':{'color':[.61,.60,.51],'roughness':.88},
}


def plan():
 p=box(*P['main_plan_range_design_m'])
 for x0,x1,y0,y1 in P['north_wing_ranges_design_m']:
  p=p.union(box(x0,y0,x1,y1))
 p=orient(p,1.)
 assert Polygon(SOURCE).covers(p)
 return p


def wall(f,lo,hi,holes,material='brown brick',thickness=.38):
 shape=box(-f.length/2,lo,f.length/2,hi)
 if holes:shape=shape.difference(unary_union(holes))
 f.prism(shape,-thickness,0,material,'real-opened-wall')


def surround(f,shape,label):
 """Stepped pale voussoir-like window edging visible in the street photo."""
 x0,z0,x1,z1=shape.bounds
 outer=shape.buffer(.17,join_style=2)
 outer=outer.union(box(x0-.27,z0+.16,x0+.04,z0+.58))
 outer=outer.union(box(x1-.04,z0+.16,x1+.27,z0+.58))
 outer=outer.union(box(x0-.27,z1-.55,x0+.04,z1-.16))
 outer=outer.union(box(x1-.04,z1-.55,x1+.27,z1-.16))
 f.prism(outer.difference(shape),-.012,.115,'pale dressed stone',label+'-stepped-pale-surround')
 f.box((x0+x1)/2,z0-.105,x1-x0+.39,.15,.34,.08,'pale dressed stone',label+'-projecting-sill')


def window(f,shape,lod,label,depth=.30,columns=3,rows=3,trim=True):
 inner=shape.buffer(-.073,join_style=2)
 f.prism(inner,-depth-.03,-depth,'recessed glass',label+'-recessed-glass')
 x0,z0,x1,z1=shape.bounds;bars=[]
 if not lod:
  bars += [box(x0+(x1-x0)*i/columns-.024,z0,x0+(x1-x0)*i/columns+.024,z1) for i in range(1,columns)]
  bars += [box(x0,z0+(z1-z0)*i/rows-.022,x1,z0+(z1-z0)*i/rows+.022) for i in range(1,rows)]
 panes=inner.difference(unary_union(bars)) if bars else inner
 f.prism(shape.buffer(-.022,join_style=2).difference(panes),-depth+.045,-depth+.12,'pale window frame',label+'-frame')
 if trim:surround(f,shape,label)


def carvings(f,u,z,width,lod,label):
 """A small geometric swag panel, not a traced source image."""
 f.box(u,z,width,.76,.055,.025,'recessed carved stone',label+'-recessed-panel')
 if not lod:
  # Closed tapered folded ribbons give the shallow relief actual thickness.
  for side in [-1,1]:
   poly=Polygon([(u+side*.05,z-.17),(u+side*(width*.33),z+.07),(u+side*(width*.40),z+.20),(u+side*(width*.28),z+.12),(u+side*.04,z-.05)])
   f.prism(orient(poly,1.),.065,.13,'pale dressed stone',label+'-geometric-swag')
  f.box(u,z+.03,.12,.36,.09,.10,'pale dressed stone',label+'-central-drop')


def build(lod=False):
 b=Builder(PALETTE);p=plan();ff=facade_ring(b,p,'historic-main')
 features={'parameters':P,'source_plan_xy':SOURCE,'design_plan_xy':list(map(list,p.exterior.coords[:-1])),
  'window_openings':0,'south_bay_columns':2,'north_projecting_wings':2,'facades':[],
  'recess_probes':[],'bay_faces':[],'photos_embedded':False}
 heights=P['main_floor_window_heights_design_m'];bottoms=P['main_floor_window_bottoms_design_m']
 def add_probe(f,u,z,depth,group,material='recessed glass'):
  features['recess_probes'].append({'group':group,'point':f.point(u,z).tolist(),'normal':f.n.tolist(),'depth':depth,'material':material})
 for f in ff:
  south=f.n[1]<-.9;west=f.n[0]<-.9;north=f.n[1]>.9;east=f.n[0]>.9
  wingtip=north and f.center[1]>15
  notch=abs(f.n[0])>.9 and f.center[1]>7
  if south:
   specs=[(x-f.center[0],3.10,4) for x in np.arange(-30.,30.01,5.)]
  elif f.length>16 and (west or east):
   specs=[(-5.7,3.7,4),(0.,1.25,1),(5.7,3.7,4)]
  elif wingtip:
   specs=[(-f.length*.28,1.48,1),(0.,2.20,2),(f.length*.28,1.48,1)]
  elif notch:
   specs=[(-f.length*.25,2.75,3),(f.length*.25,2.75,3)]
  elif f.length>18:
   specs=[(-7.7,3.15,3),(-2.6,3.15,3),(2.6,3.15,3),(7.7,3.15,3)]
  else:
   specs=[(-f.length*.30,min(2.8,f.length*.27),3),(0.,1.05,1),(f.length*.30,min(2.8,f.length*.27),3)]
  holes=[]
  for k,(u,width,cols) in enumerate(specs):
   for floor,(z,h) in enumerate(zip(bottoms,heights)):
    isbay=south and any(abs(f.point(u,0)[0]-x)<.1 for x in P['south_projecting_bay_centers_design_m'])
    if isbay and 2<=floor<=10:continue
    w=width
    # The cream ground has tall, narrower individual window openings.
    if floor<2 and not south:w*=.92
    shape=box(u-w/2,z,u+w/2,z+h);holes.append(shape)
    window(f,shape,lod,f'window-{k}-floor-{floor}',columns=cols,rows=4 if floor<12 else 3)
    features['window_openings']+=1
    if (floor in [4,10] and k==0 and (south or wingtip or notch)) or (floor==7 and west and f.length>16):
     add_probe(f,u+w*.11,z+.37,.30,('south-flat' if south else 'north-wing-tip' if wingtip else 'north-notch-side' if notch else 'west-wide')+f'-{floor}')
   if south and f.point(u+2.45,0)[0]<31.75:
    # Long white verticals and floor grid are a photo-led south-side feature.
    f.box(u+2.45,28.0,.16,47.6,.11,.025,'pale dressed stone','south-long-pale-vertical')
   elif wingtip and abs(u)<.1:
    for sign in [-1,1]:f.box(u+sign*1.36,29.0,.19,45.9,.13,.035,'pale dressed stone','north-wing-central-vertical-strip')
  if south:
   for x in P['south_projecting_bay_centers_design_m']:
    u=x-f.center[0];holes.append(box(u-1.95,8.05,u+1.95,44.15))
  wall(f,0,8.03,holes,'pale dressed stone' if south or west else 'lower stone base')
  wall(f,8.03,48.02,holes)
  wall(f,48.02,52.10,holes,'pale dressed stone' if south else 'brown brick')
  for z,h,d in [(7.78,.30,.24),(8.10,.14,.13),(47.96,.24,.22),(51.83,.22,.23),(52.20,.22,.25)]:
   f.box(0,z,f.length-.03,h,.38,d-.19,'pale dressed stone','continuous-stone-cornice')
  if south:
   for z in [11.78+4*i for i in range(9)]:
    stripe=box(-f.length/2,z-.085,f.length/2,z+.085)
    gaps=[box(x-f.center[0]-1.95,8.0,x-f.center[0]+1.95,44.2) for x in P['south_projecting_bay_centers_design_m']]
    f.prism(stripe.difference(unary_union(gaps)),.015,.08,'pale dressed stone','south-horizontal-floor-joint')
   # Photo-visible pale descenders link the small central crown to the upper
   # two storeys. Their proportions are estimated; every existing opening is
   # explicitly subtracted so the relief cannot cover its recessed glazing.
   for x in [-2.5,2.5]:
    u=x-f.center[0]
    accent=box(u-.47,43.80,u+.47,52.10).difference(unary_union(holes))
    f.prism(accent,.018,.145,'pale dressed stone','south-central-upper-pale-descender')
    for sign in [-1,1]:
     line=box(u+sign*.31-.025,44.20,u+sign*.31+.025,51.70).difference(unary_union(holes))
     f.prism(line,.15,.19,'pale dressed stone','south-central-upper-relief-line')
   for x in [-5.,0.,5.]:carvings(f,x-f.center[0],51.58,2.3,lod,'south-central-top-relief')
  if wingtip or north and f.length>18 or west and f.length>16:
   for u,_,_ in specs:
    carvings(f,u,47.15,min(2.,f.length/4),lod,'upper-shallow-swag')
  if wingtip:
   # Taller stepped central head is restrained, not the neighboring Grosvenor crown.
   head=Polygon([(-2.9,52.31),(2.9,52.31),(2.9,53.05),(1.7,53.05),(1.7,53.65),(-1.7,53.65),(-1.7,53.05),(-2.9,53.05)])
   f.prism(head,-.32,.075,'pale dressed stone','north-wing-small-stepped-head')
   carvings(f,0.,52.85,1.6,lod,'wing-head-swag')
  features['facades'].append({'label':f.label,'a':f.a.tolist(),'b':f.b.tolist(),'normal':f.n.tolist(),'length':f.length,'window_groups':[[float(u),float(w),c] for u,w,c in specs], 'south':bool(south),'north_wing_tip':bool(wingtip),'north_notch_side':bool(notch),'photo_guided':bool(south or west or north or notch),'east_details_estimated':bool(east and not notch)})
  # Sparse shallow closed brick courses, just sufficient to avoid a flat paint
  # effect at native inspection distance. No brick texture or tiny tiled mesh.
  if not lod and not south:
   for z in np.arange(8.25,47.8,1.):
    stripe=box(-f.length/2+.15,z,f.length/2-.15,z+.028)
    shape=stripe.difference(unary_union([q.buffer(.32,join_style=2) for q in holes]))
    if not shape.is_empty:f.prism(shape,.008,.023,'warm brick variation','subtle-brick-course')

 # South faceted projecting bay columns. The main wall has a matching tall
 # cutout; three glazed faces per floor and shallow side returns are geometric.
 for bi,x in enumerate(P['south_projecting_bay_centers_design_m']):
  poly=orient(Polygon([(x-1.95,-10.95),(x-1.95,-11.32),(x-1.26,-12.26),(x+1.26,-12.26),(x+1.95,-11.32),(x+1.95,-10.95)]),1.)
  bfs=facade_ring(b,poly,f'south-projecting-bay-{bi}')
  for f in bfs:
   if f.n[1]>.9:continue # Open connection into the main bar; no hidden wall.
   holes=[]
   if f.length>.7:
    w=f.length-.30
    for floor in range(9):
     z=8.55+4*floor;shape=box(-w/2,z,w/2,z+2.90);holes.append(shape)
     window(f,shape,lod,f'bay-window-{floor}',columns=3 if f.length>2 else 1,trim=False)
     features['window_openings']+=1
     if floor==6:add_probe(f,w*.14,z+.36,.30,'south-bay-front' if f.n[1]<-.9 else 'south-bay-oblique')
   wall(f,8.05,44.15,holes,'pale dressed stone',.30)
   for z in [8.12+4*i for i in range(10)]:f.box(0,z,f.length-.018,.21,.36,.035,'pale dressed stone','bay-floor-projecting-belt')
   features['bay_faces'].append({'label':f.label,'normal':f.n.tolist(),'length':f.length})
  for z in [8.05+4*i for i in range(10)]:b.plan_prism(poly,z,z+.13,'pale dressed stone',f'south-bay-{bi}-horizontal-closure')
  front=next(f for f in bfs if f.n[1]<-.9)
  crest=Polygon([(-1.4,44.15),(1.4,44.15),(1.4,44.42),(.75,44.42),(.45,44.70),(-.45,44.70),(-.75,44.42),(-1.4,44.42)])
  front.prism(crest,-.24,.10,'pale dressed stone','bay-small-stepped-crest')

 b.plan_prism(p,0,.18,'lower stone base','main-ground-slab')
 b.plan_prism(p,51.94,52.10,'roof closure estimate','main-roof-follows-notched-footprint')
 # A small, centred, set-back upper floor is visible above the garden facade.
 crown=box(-7.40,-8.50,7.40,4.80)
 for f in facade_ring(b,crown,'central-rooftop-crown'):
  n=3 if f.length>14 else 2;pitch=f.length/n;holes=[]
  for k in range(n):
   u=-f.length/2+(k+.5)*pitch;shape=box(u-1.20,52.85,u+1.20,55.18);holes.append(shape)
   window(f,shape,lod,f'crown-window-{k}',columns=3,trim=False);features['window_openings']+=1
   if f.n[1]<-.9 and k==1:add_probe(f,u+.19,53.33,.30,'central-crown-window')
  wall(f,52.1,56.25,holes,'pale dressed stone')
  f.box(0,56.35,f.length+.04,.24,.49,.055,'pale dressed stone','crown-upper-cornice')
  f.box(0,56.69,f.length-.60,.62,.30,-.03,'pale dressed stone','crown-plain-parapet')
  for u in [-f.length/2+.22,f.length/2-.22]:f.box(u,56.57,.43,.86,.40,.01,'pale dressed stone','crown-end-upright')
  if f.n[1]<-.9:
   for u in [-4.8,0,4.8]:carvings(f,u,55.77,2.3,lod,'crown-geometric-relief')
 b.plan_prism(crown,56.05,56.25,'roof closure estimate','central-crown-roof')
 # Two modest service flues, estimated from visible northwest roof hardware.
 for i,(x,y) in enumerate([(-18.5,12.0),(17.5,12.0)]):
  b.box((x,y,53.30),(1.10,1.0,2.40),'roof closure estimate',label=f'roof-flue-{i}-estimated')
  b.box((x,y,54.55),(1.35,1.25,.18),'dark metal',label=f'roof-flue-{i}-cap-estimated')
 # Garden-side entrance: recessed glazing within the existing centre ground
 # opening plus a small shelter, kept below and outside the brick grid.
 south=next(f for f in ff if f.n[1]<-.9)
 u=-south.center[0]
 south.box(u,3.72,7.6,.25,1.48,.65,'pale dressed stone','garden-entry-shallow-canopy')
 for sign in [-1,1]:south.box(u+sign*3.25,1.83,.40,3.66,.55,.70,'pale dressed stone','garden-entry-canopy-pier')
 features.update(author_parts=len(b.parts),all_dimensions_estimated=True,
  north_gaps_preserved=True,adjacent_low_hall_and_other_compound_blocks_modeled=False)
 meta={'id':ID,'name':'华懋公寓历史主楼外观候选','status':'exterior-candidate-with-estimated-geographic-placement',
  'current_address':'长乐路109号','address_conflict_note':'Historic-building list gives 109; one official narrative prints 189. The candidate retains the listed 109 identity; the discrepancy is unresolved.',
  'documented_storey_height_alternatives':P['documented_storey_height_alternatives'],
  'documented_storeys':14,'documented_height_m':57.0,'height_endpoints_verified':False,
  'model_selected_architectural_top_m':57.0,'model_main_bar_layers':13,'model_rooftop_layers':1,
  'floor_layer_allocation_is_author_interpretation':True,'all_plan_dimensions_estimated':True,'all_floor_layer_datums_estimated':True,
  'south_and_northwest_photo_guided':True,'east_elevation_photo_verified':False,'unseen_roof_is_author_closure':True,
  'north_projection_configuration_source_and_photo_guided':True,'closed_courtyard_claimed':False,
  'adjacent_low_hall_and_other_compound_blocks_modeled':False,'original_1929_state_claimed':False,
  'commercial_signs_modeled':False,'interiors_modeled':False,'photos_embedded':False,'map_replacement':False,
  'scope_kind':'historic-main-block-exterior','local_origin_wgs84':P['local_origin_wgs84'],
  'global_heading_deg':P['global_heading_deg'],'source_footprint_id':'f6e4b883-ed86-4c90-aa96-2c717ff043c5',
  'geometry_license':'MIT','model_units':'metres','author_axes':'x ENE, y NNW, z up','gltf_axes':'x ENE, y up, z SSE',
  'scope':'Photo-informed present exterior of Cathay Mansions historic main block / Jinbei building, not Cathay Hotel, Grosvenor House or the whole Jinjiang compound. Two open north recesses and the central north gap remain open; garden, adjoining low hall, other compound buildings, signs and interiors excluded. All dimensions and floor layers are estimates.',
  'height_interpretation':P['height_interpretation']}
 return b,meta,features


def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--lod',action='store_true');a=p.parse_args()
 b,meta,features=build(a.lod);a.out.mkdir(parents=True,exist_ok=True)
 role='lod' if a.lod else 'raw';record=b.save(a.out/(ID+'-'+role+'.glb'),meta)
 a.out.joinpath(role+'-features.json').write_text(json.dumps(features,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:v for k,v in record.items() if k!='part_summary'},ensure_ascii=False))
if __name__=='__main__':main()
