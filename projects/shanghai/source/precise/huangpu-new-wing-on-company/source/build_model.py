"""New Wing On Company: original photo-informed exterior geometry, MIT.

The two Suicasmo 2025 views and New Wing Mansion view were actually inspected.
The north-cut front tower, stepped vertical window groups, broad pale cornices,
deep low wedge and rounded southeast end are distinct from Old Wing On across
the street. Dimensions and floor datums below are author interpretations.
"""
import argparse
import json
import math
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union

from common.photo_architecture import Builder, Facade, facade_ring

ID='huangpu-new-wing-on-company'
PALETTE={
 'warm yellow brick':{'color':[.56,.48,.32],'roughness':.93},
 'light brick pier':{'color':[.64,.565,.405],'roughness':.89},
 'brick spandrel':{'color':[.50,.43,.305],'roughness':.94},
 'pale stone band':{'color':[.77,.755,.66],'roughness':.86},
 'green granite':{'color':[.18,.245,.22],'roughness':.48},
 'entry stone':{'color':[.54,.51,.39],'roughness':.82},
 'roof':{'color':[.34,.355,.33],'roughness':.96},
 'recessed glass':{'color':[.15,.225,.235],'roughness':.32,'metallic':.12},
 'window frame':{'color':[.57,.61,.58],'roughness':.55,'metallic':.2},
 'iron':{'color':[.16,.18,.17],'roughness':.72,'metallic':.25},
 'thermometer cream':{'color':[.79,.79,.68],'roughness':.76},
 'thermometer inset':{'color':[.26,.27,.23],'roughness':.8},
}
P={
 'all_plan_dimensions_estimated':True,
 'local_axes':'x ENE, y NNW, z up; placement rotation is separately documented',
 'local_origin_wgs84':[121.47443219384867,31.236886904148918],
 'global_heading_deg':-15.763307672,
 'front_cut_a_xy':[-18.6,27.5], 'front_cut_b_xy':[-5.7,34.8],
 'front_body_depth_design_m':24.,
 'front_high_body_plan_interpretation':'Near-right-angled quadrilateral aligned to the photographed northeast street face; the coarse-map angle and documented rectangular upper plan are not reconciled by survey.',
 'podium_seventh_roof_design_m':23.4,
 'rear_eighth_roof_design_m':26.6,
 'front_thirteenth_roof_design_m':42.6,
 'upper_tower_seven_layer_roof_design_m':65.7,
 'crown_lower_top_design_m':68.3,
 'selected_architectural_top_m':72.,
 'documented_total_height_m':72.,
 'documented_height_endpoint_defined':False,
 'model_selects_72m_as_solid_architectural_top':True,
 'modern_antenna_mast_included':False,
 'front_layer_datums_m':[0.,4.2,7.4,10.6,13.8,17.,20.2,23.4,26.6,29.8,33.,36.2,39.4,42.6],
 'upper_layer_datums_m':[42.6,45.9,49.2,52.5,55.8,59.1,62.4,65.7],
 'layer_interpretation':'13 lower + 7 upper + 2 top service stages is an author allocation of the documented 22 storeys, not verified floor plans.',
 'rear_documented_storeys':8,
 'tower_central_window_axes':3,
 'tower_side_single_axes':2,
 'northeast_continuous_bay_spacing_design_m':3.,
 'thermometer_stem_design_width_m':.48,
 'thermometer_major_minor_tick_design_widths_m':[1.65,1.15],
 'north_entry_opening_design_width_m':4.8,
 'north_entry_opening_design_height_m':7.0,
 'window_bays_and_hidden_elevations_estimated':True,
 'bridge_old_wing_on_and_neighboring_buildings_excluded':True,
 'modern_advertisements_commercial_text_and_temperature_readout_excluded':True,
}

FRONT_A=np.array(P['front_cut_a_xy'],float)
FRONT_B=np.array(P['front_cut_b_xy'],float)
T=(FRONT_B-FRONT_A)/np.linalg.norm(FRONT_B-FRONT_A)
N=np.array([-T[1],T[0]])
C=(FRONT_A+FRONT_B)/2
FRONT_WIDTH=float(np.linalg.norm(FRONT_B-FRONT_A))


def local(u,d):
    return C+T*u-N*d


def rectangle(u0,u1,d0,d1):
    return Polygon([local(u0,d0),local(u0,d1),local(u1,d1),local(u1,d0)])


def podium_plan():
    # The rounded east/southeast end is photo-supported. The broad extents are
    # an inset author interpretation of the coarse frozen map, not 1400m² fitted.
    a=np.array([23.5,-2.5]);c1=np.array([30.,-14.2]);c2=np.array([26.6,-23.8]);d=np.array([17.1,-23.8])
    curve=[((1-t)**3*a+3*(1-t)**2*t*c1+3*(1-t)*t*t*c2+t**3*d).tolist() for t in np.linspace(0,1,13)]
    return Polygon([[-18.6,-18.8],[-18.6,27.5],[-5.7,34.8],*curve,[-12.8,-23.8]])


def wall(f,prev,nxt,lo,hi,holes,material,thickness=.40):
    t,n=f.t[:2],f.n[:2]
    def inner(p,other):
        return np.linalg.solve(np.array([n,other]),np.array([n@p-thickness,other@p-thickness]))
    left=(inner(f.a[:2],prev.n[:2])-f.a[:2])@t/thickness
    right=(inner(f.b[:2],nxt.n[:2])-f.b[:2])@t/thickness
    def mapper(u,z,d):
        return f.point(u-d*(left+(u+f.length/2)/f.length*(right-left)),z,d)
    shape=box(-f.length/2,lo,f.length/2,hi)
    if holes:shape=shape.difference(unary_union(holes))
    f.builder.prism(shape,-thickness,0,mapper,material,f.label+'/closed-window-wall')


def window(f,shape,lod,label,glass_depth=.32,cols=2,rows=3):
    inner=shape.buffer(-.075,join_style=2)
    f.prism(inner,-glass_depth-.025,-glass_depth,'recessed glass',label+'-glass')
    if not lod:
        x0,z0,x1,z1=shape.bounds
        bars=[box(x0+(x1-x0)*k/cols-.025,z0,x0+(x1-x0)*k/cols+.025,z1) for k in range(1,cols)]
        bars += [box(x0,z0+(z1-z0)*k/rows-.023,x1,z0+(z1-z0)*k/rows+.023) for k in range(1,rows)]
        panes=inner.difference(unary_union(bars)) if bars else inner
        f.prism(shape.buffer(-.025,join_style=2).difference(panes),-.26,-.16,'window frame',label+'-steel-grid')
    x0,z0,x1,z1=shape.bounds
    # Tiny sills preserve facade scale without classical architraves.
    f.box((x0+x1)/2,z0-.045,x1-x0+.10,.09,.18,.015,'pale stone band',label+'-sill')


def roof_band(b,plan,z,height,label,reach=.25,exclude=None):
    ring=plan.buffer(reach,join_style=2).difference(plan.buffer(-.35,join_style=2))
    slab=plan.buffer(-.32,join_style=2)
    if exclude is not None:
        ring=ring.difference(exclude);slab=slab.difference(exclude)
    b.plan_prism(ring,z-height,z,'pale stone band',label+'-wide-flat-band')
    b.plan_prism(slab,z-.16,z-.04,'roof',label+'-roof-slab')


def build(lod=False):
    b=Builder(PALETTE);plan=podium_plan()
    side_direction=np.array([23.5,-2.5])-FRONT_B;side_direction/=np.linalg.norm(side_direction)
    side_normal=np.array([-side_direction[1],side_direction[0]])
    front=Polygon([FRONT_A,FRONT_A+side_direction*24,FRONT_B+side_direction*24,FRONT_B])
    assert plan.is_valid and front.is_valid and plan.buffer(.01).covers(front)
    upper=rectangle(-FRONT_WIDTH/2+3.05,FRONT_WIDTH/2-.65,1.25,20.0)
    center=rectangle(-FRONT_WIDTH/2+4.45,FRONT_WIDTH/2-2.05,.88,20.35)
    tower=unary_union([upper,center])
    assert front.covers(tower), 'Upper rectangular tower must remain within high base'
    crown1=rectangle(-3.5,5.9,2.2,17.5)
    crown2=rectangle(-2.4,4.8,3.4,14.5)
    crown2=crown2.buffer(-.65,join_style=2).buffer(.65,quad_segs=1)
    counter={'windows':0,'main_north_windows':0,'upper_center_windows':0,'side_narrow_windows':0,'ground_shopfronts':0}
    probes=[];feature_facades=[]
    def is_north(f):return bool(np.dot(f.n[:2],N)>.98)
    def mass(poly,datums,label,ground=False,upper_tier=False):
        fs=facade_ring(b,poly,label)
        crown=label in ('lower-pale-crown','upper-chamfered-crown')
        for i,f in enumerate(fs):
            prev,nxt=fs[i-1],fs[(i+1)%len(fs)]
            north=is_north(f)
            central=upper_tier and north and f.length>6
            count=3 if north and f.length>9 else max(1,int(round((f.length-.8)/3.15)))
            if upper_tier and f.length<.8:count=0
            if central:count=3
            if crown:count=1 if label=='upper-chamfered-crown' and north and f.length>4 else 0
            margin=1.25 if north and f.length>9 else min(.65,f.length*.14)
            gap=(f.length-2*margin)/count if count else 0
            centers=[-f.length/2+margin+gap*(k+.5) for k in range(count)]
            pier_us=[-f.length/2+margin+gap*k for k in range(count+1)] if count else []
            shared_ne=label in ('seven-storey-wedge','north-high-base') and float(f.n[:2]@side_normal)>.9999
            if shared_ne:
                ends=sorted(float((p-FRONT_B)@side_direction) for p in (f.a[:2],f.b[:2]))
                centers=[float((FRONT_B+side_direction*s-f.center[:2])@f.t[:2]) for s in np.arange(1.5,50.,3.) if ends[0]+.7<s<ends[1]-.7]
                pier_us=[float((FRONT_B+side_direction*s-f.center[:2])@f.t[:2]) for s in np.arange(0.,50.,3.) if ends[0]+.05<s<ends[1]-.05]
                count=len(centers);gap=3.
            for floor,(lo,hi) in enumerate(zip(datums,datums[1:])):
                openings=[]
                for j,u in enumerate(centers):
                    if ground and north and lo<7.4:
                        # North-cut entry spans the first two storeys. Its glass
                        # is deeply recessed; no fabricated shop sign is added.
                        continue
                    ww=min(2.12,gap*.64) if not upper_tier else min(1.58,gap*.72)
                    if ww<.50:continue
                    if ground and lo==0:
                        ww=min(gap*.78,2.65);bottom=.48;top=hi-.42
                        counter['ground_shopfronts']+=1
                    else:
                        bottom=lo+.48;top=hi-.65
                    if crown:
                        ww=1.10;bottom=lo+1.45;top=bottom+.82
                    shape=box(u-ww/2,bottom,u+ww/2,top)
                    openings.append(shape);counter['windows']+=1
                    if north and not upper_tier:counter['main_north_windows']+=1
                    if central:counter['upper_center_windows']+=1
                    window(f,shape,lod,f'floor-{floor}-bay-{j}',cols=2,rows=2 if ground and lo==0 else 3)
                    if len(probes)<80 and floor in (0,2,5) and j==0:
                        probes.append({'label':label,'point':f.point(u+.19,bottom+.31).tolist(),'normal':f.n.tolist(),'depth':.32})
                if ground and north and lo<7.4:
                    openings.append(box(-2.4,max(lo,0),2.4,min(hi,7.0)))
                wall(f,prev,nxt,lo,hi,openings,'green granite' if ground and lo==0 else 'warm yellow brick')
                if not lod and not crown and count and hi-lo>2.:
                    # Two shallow brick courses on the solid spandrel only.
                    for z in (lo+.16,lo+.31):
                        f.box(0,z,f.length-.14,.018,.015,.012,'brick spandrel','spandrel-course')
            # Vertical piers preserve the unbroken Art Deco emphasis and avoid
            # the dark glass openings. Short return edges are left undecorated.
            if not crown and count and f.length>3:
                for u in pier_us:
                    f.box(u,(datums[0]+datums[-1])/2,.22 if upper_tier else .18,datums[-1]-datums[0]-.16,.13,.045,'light brick pier','continuous-vertical-pier')
            feature_facades.append({'label':f.label,'a_xy':f.a[:2].tolist(),'b_xy':f.b[:2].tolist(),'outward_normal':f.n.tolist(),'layers':len(datums)-1,'bays':count,'north_cut':north})
        b.plan_prism(poly.buffer(-.37,join_style=2),datums[0],datums[0]+.12,'roof',label+'-base-floor')
        return fs
    levels=P['front_layer_datums_m']
    basefs=mass(plan,levels[:8],'seven-storey-wedge',ground=True)
    # Remove numerical corner slivers where the shared north cut is represented
    # by independently computed doubles. The 5mm joint is hidden by the high body.
    rear=plan.difference(front.buffer(.005,join_style=2)).simplify(.002,preserve_topology=True)
    # The eighth rear layer is a distinct lower mass. Its inner party wall is
    # not a public facade and is allowed to be hidden by the front body.
    mass(rear,[23.4,26.6],'rear-eighth-storey')
    frontfs=mass(front,levels[7:],'north-high-base')
    towerfs=mass(tower,P['upper_layer_datums_m'],'stepped-upper-tower',upper_tier=True)
    roof_band(b,plan,23.4,.65,'podium-seventh',exclude=front.buffer(.60,join_style=2))
    roof_band(b,rear,26.6,1.35,'rear-eighth',exclude=front.buffer(.35,join_style=2))
    roof_band(b,front,42.6,1.35,'front-thirteenth')
    roof_band(b,tower,65.7,1.35,'upper-tower')
    mass(crown1,[65.7,68.3],'lower-pale-crown')
    mass(crown2,[68.3,72.0],'upper-chamfered-crown')
    # Equipment crowns are pale concrete, not brick. Preserve their few actual
    # small openings and reduce their repetitive decorative layers.
    for part in b.parts:
        if part['label'].startswith(('lower-pale-crown','upper-chamfered-crown')) and part['material'] in ('warm yellow brick','light brick pier','brick spandrel'):
            part['material']='pale stone band'
    roof_band(b,crown1,68.3,.36,'crown-lower',.16)
    roof_band(b,crown2,72.0,.22,'crown-top',.12)
    # Deep north entrance behind the two-storey opening.
    f=next(f for f in basefs if is_north(f))
    entry_center=f.center[:2].tolist()
    entry=box(-2.4,.05,2.4,7.0)
    f.prism(entry,-1.30,-1.26,'recessed glass','deep-north-entry-glass')
    reveal=entry.buffer(.16,join_style=2).difference(entry).intersection(box(-3,0,3,7.5))
    f.prism(reveal,-.10,.22,'entry stone','north-entry-stone-reveal')
    for u in [-2.4,0,2.4]:f.box(u,3.5,.08,6.98,.10,-1.19,'window frame','north-entry-door-frame')
    for z in [2.7,5.2]:f.box(0,z,4.78,.08,.10,-1.19,'window frame','north-entry-transom')
    # The front-base northeast wall carries the conspicuous vertical scale;
    # no temperature value, numbers or commercial lettering are fabricated.
    side=max(frontfs,key=lambda q:float(q.n[:2]@T))
    thermo_u=0.;lo=12.;hi=39.4
    side.box(thermo_u,(lo+hi)/2,.48,hi-lo,.12,.20,'thermometer cream','thermometer-stem')
    side.box(thermo_u,(lo+hi)/2,.10,hi-lo-.45,.045,.285,'thermometer inset','thermometer-empty-channel')
    bulb=Point(thermo_u,lo-.4).buffer(.50,quad_segs=10 if lod else 20)
    side.prism(bulb,.13,.27,'thermometer cream','thermometer-bulb')
    for z in np.arange(lo+.1,hi,.90 if lod else .45):
        width=1.65 if round((z-lo)/.45)%2==0 else 1.15
        side.box(thermo_u,float(z),width,.045,.07,.19,'thermometer cream','thermometer-unlabelled-tick')
    # Roof safety rails stay below the selected 72m solid top. Tall modern
    # antenna rods are absent, so they cannot redefine the documented height.
    for f in facade_ring(b,crown1,'crown-low-rail'):
        if f.length<3:continue
        f.box(0,68.75,f.length-.3,.055,.055,-.12,'iron','top')
        for u in np.linspace(-f.length/2+.3,f.length/2-.3,max(2,int(f.length/1.6))):
            f.box(float(u),68.50,.045,.50,.045,-.12,'iron','post')
    metadata={'id':ID,'name':'新永安公司／七重天大厦历史外观候选',
      'status':'exterior-candidate-with-estimated-geographic-placement',
      'documented_front_storeys':22,'documented_rear_storeys':8,'documented_height_m':72.,
      'height_endpoints_verified':False,'selected_model_architectural_top_m':72.,
      'model_height_is_interpretation':True,'all_plan_dimensions_estimated':True,
      'documented_site_area_m2':1400.,'model_plan_area_m2_estimated':float(plan.area),
      'model_plan_does_not_rescale_map_to_documented_area':True,
      'current_address':'南京东路627号','gazetteer_address_variant':'南京东路727号',
      'indexed_year':'1933','gazetteer_year_variant':'1932','date_conflict_unresolved':True,
      'primary_facade':'northwest-facing short cut at northern end',
      'local_axes':P['local_axes'],'rear_roof_hidden_details_estimated':True,
      'floor_layer_allocation_is_author_interpretation':True,
      'high_base_quadrilateral_vs_documented_rectangular_plan_unresolved':True,
      'connecting_bridges_and_old_wing_on_excluded':True,'modern_tall_antenna_excluded':True,
      'thermometer_has_no_readout_or_numbers':True,'photos_embedded':False,
      'reference_photographs_embedded':False,'map_replacement':False,
      'interiors_modeled':False,'commercial_text_modeled':False,
      'copyright':'Original code and architectural geometry MIT; frozen map location/shape reference ODbL-1.0; no photograph pixels embedded'}
    features={'parameters':P,'author_parts':len(b.parts),'window_openings':counter['windows'],
      'main_north_windows':counter['main_north_windows'],'upper_center_windows':counter['upper_center_windows'],
      'ground_shopfronts':counter['ground_shopfronts'],'design_plan_xy':list(map(list,plan.exterior.coords[:-1])),
      'high_base_xy':list(map(list,front.exterior.coords[:-1])),
      'upper_tower_xy':list(map(list,tower.exterior.coords[:-1])),
      'podium_area_design_m2':float(plan.area),'high_base_area_design_m2':float(front.area),
      'rear_eighth_area_design_m2':float(rear.area),'facades':feature_facades,
      'window_recess_probe_candidates':probes,'north_entry_center_xy':entry_center,
      'rounded_southeast_end':True,'estimated_low_wedge_not_72m_extrusion':True,
      'modern_tall_antenna_included':False,'commercial_readouts_and_lettering_included':False}
    return b,metadata,features


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True);parser.add_argument('--lod',action='store_true')
    a=parser.parse_args();b,meta,features=build(a.lod);a.out.mkdir(parents=True,exist_ok=True)
    stem=ID+('-lod' if a.lod else '-raw');r=b.save(a.out/(stem+'.glb'),meta)
    (a.out/(stem+'-features.json')).write_text(json.dumps(features,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in r.items() if k!='part_summary'}))


if __name__=='__main__':main()
