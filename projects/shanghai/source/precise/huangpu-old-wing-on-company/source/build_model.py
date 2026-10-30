"""Old Wing On Company: original photo-informed exterior candidate, MIT geometry.

The 2011 tower close view, 2013 east facade, 2025 northeast corner and 2025
north facade were inspected. The six-storey body, curved northeast entrance,
two long iron galleries, oculus band and separate northern two-storey roof
pavilion guide the geometry. Every model dimension, bay count, relief profile,
rear wall and seventh-storey boundary is an author estimate, not a survey.
Reference photograph pixels, commercial signs and neighboring buildings are absent.
"""
import argparse
import json
import math
from pathlib import Path

import numpy as np
from shapely.geometry import MultiPoint, Point, Polygon, box
from shapely.ops import unary_union

from common.photo_architecture import Builder, Facade, facade_ring, opening

ID = 'huangpu-old-wing-on-company'
PALETTE = {
    'cream stone': {'color': [.74, .715, .635], 'roughness': .85},
    'carved pale stone': {'color': [.82, .79, .71], 'roughness': .79},
    'rusticated stone': {'color': [.69, .67, .60], 'roughness': .88},
    'cornice shadow stone': {'color': [.59, .58, .525], 'roughness': .91},
    'base stone': {'color': [.52, .52, .46], 'roughness': .85},
    'roof': {'color': [.43, .44, .41], 'roughness': .93},
    'recessed glass': {'color': [.105, .16, .15], 'roughness': .27, 'metallic': .17},
    'bronze window frame': {'color': [.14, .18, .16], 'roughness': .60, 'metallic': .18},
    'iron': {'color': [.085, .105, .095], 'roughness': .65, 'metallic': .30},
    'pale globe': {'color': [.85, .86, .81], 'roughness': .45},
}
P = {
    'all_plan_dimensions_estimated': True,
    'design_width_east_west_m': 66., 'design_depth_north_south_m': 94.,
    'main_roof_design_m': 30., 'northeast_corner_radius_design_m': 12.4,
    'northeast_corner_circle_center_xy': [20.6, 34.6],
    'northeast_curve_facets': 5,
    'design_layer_datums_m': [0., 5., 10., 15., 20., 25.5, 30.],
    'north_street': 'Nanjing Road', 'east_street': 'Zhejiang Road',
    'seventh_storey_estimated_xy': [8., -44., 33., -22.],
    'seventh_storey_roof_design_m': 34.4,
    'seventh_storey_boundaries_not_measured': True,
    'gallery_floor_datums_design_m': [5., 25.5],
    'northeast_corner_balcony_floor_datums_design_m': [10., 15., 20.],
    'northeast_corner_crown_top_design_m': 32.5,
    'northeast_crown_curved_moulding_rise_design_m': 1.7,
    'tower_upper_pediment_rise_design_m': 1.4,
    'tower_name_in_official_chapter': '倚云阁',
    'tower_common_name_variant': '绮云阁',
    'tower_center_xy_estimated': [-12.5, 42.5],
    'tower_is_separate_from_northeast_curved_entrance': True,
    'tower_solid_base_datums_design_m': [30., 34.],
    'tower_open_pavilion_datums_design_m': [34., 39., 43.4],
    'tower_architectural_top_design_m': 45.8,
    'tower_modern_photo_mast_top_design_m': 54.,
    'tower_total_height_has_no_verified_source_measurement': True,
    'tower_modern_mast_is_not_claimed_original': True,
    'continuous_ground_arcade_included': False,
    'commercial_signs_included': False,
    'new_wing_on_and_connecting_bridges_included': False,
    'invented_courtyard_included': False,
}


def closed_wall(f, prev, nxt, lo, hi, holes, material='cream stone', thickness=.46):
    t, n = f.t[:2], f.n[:2]
    def inner(pt, other):
        return np.linalg.solve(np.array([n, other]), np.array([n@pt-thickness, other@pt-thickness]))
    left = (inner(f.a[:2], prev.n[:2])-f.a[:2])@t/thickness
    right = (inner(f.b[:2], nxt.n[:2])-f.b[:2])@t/thickness
    def mapper(u, z, d):
        return f.point(u-d*(left+(u+f.length/2)/f.length*(right-left)), z, d)
    shape = box(-f.length/2, lo, f.length/2, hi)
    if holes:
        shape = shape.difference(unary_union(holes))
    f.builder.prism(shape, -thickness, 0, mapper, material, f.label+'/closed-mitred-wall')


def window(f, shape, lod, label, rows=3, surround=.10):
    if not lod:
        f.window(shape, 2, rows, 'bronze window frame', False, 'recessed glass', label)
        # The common helper appends a generic rectangular sill. Replace it
        # once below so the circular oculi do not acquire false sills.
        assert f.builder.parts[-1]['label']==f.label+'/'+label+'-sill'
        f.builder.parts.pop()
    else:
        f.prism(shape.buffer(-.07, join_style=2), -.34, -.31, 'recessed glass', label+'-glass')
    if surround:
        f.prism(shape.buffer(surround, join_style=2).difference(shape), -.025, .085,
                'carved pale stone', label+'-surround')
    x0, z0, x1, z1 = shape.bounds
    if z0 > .20 and label!='round-oculus':
        f.box((x0+x1)/2, z0-.065, x1-x0+.22, .13, .35, .05,
              'carved pale stone', label+'-sill')


def column(b, xy, lo, hi, radius, lod, label, ionic=True):
    b.lathe(tuple(xy), [(lo, radius*1.42), (lo+.12, radius*1.42),
                        (lo+.27, radius), (hi-.31, radius*.90),
                        (hi-.20, radius*1.22), (hi-.08, radius*1.42),
                        (hi, radius*1.42)],
            'carved pale stone', 12 if lod else 20, label)
    if ionic:
        b.box((xy[0], xy[1], hi-.045), (radius*3.25, radius*2.9, .16),
              'carved pale stone', label=label+'-simplified-capital')


def cornice(b, plan, z, reach, lod, label, dentils=False):
    for dz, h, p in [(-.23, .14, reach*.65), (-.07, .17, reach), (.09, .14, reach*.9)]:
        ring = plan.buffer(p, join_style=2).difference(plan.buffer(-.10, join_style=2))
        b.plan_prism(ring, z+dz-h/2, z+dz+h/2, 'carved pale stone', label+'-profile')
    if dentils:
        for f in facade_ring(b, plan, label):
            for u in np.arange(-f.length/2+.24, f.length/2-.12, .85 if lod else .43):
                f.box(float(u), z-.38, .18, .20, reach*.65, reach*.27,
                      'carved pale stone', 'dentil')


def railing(f, lo, hi, z, depth, lod, label, stone=False, globes=False):
    mat = 'carved pale stone' if stone else 'iron'
    f.box((lo+hi)/2, z+1.0, hi-lo, .14 if stone else .065, .25 if stone else .065,
          depth, mat, label+'-top-rail')
    f.box((lo+hi)/2, z+.13, hi-lo, .15 if stone else .055, .20 if stone else .055,
          depth, mat, label+'-bottom-rail')
    for u in np.arange(lo+.19, hi-.10, .65 if lod else .36):
        if stone:
            xy = f.point(float(u), 0, depth)[:2]
            f.builder.lathe(tuple(xy), [(z+.24, .060), (z+.37, .10), (z+.62, .075),
                                       (z+.82, .045), (z+.91, .075)],
                            mat, 8 if lod else 12, label+'-baluster')
        else:
            f.box(float(u), z+.55, .042, .86, .042, depth, mat, label+'-picket')
            if not lod:
                diamond = Polygon([(u-.11, z+.53), (u, z+.73), (u+.11, z+.53), (u, z+.33)])
                f.prism(diamond.difference(diamond.buffer(-.022)), depth-.022, depth+.022,
                        mat, label+'-diamond')
    for u in [lo, hi]:
        f.box(u, z+.56, .17 if stone else .075, 1.12, .21 if stone else .075,
              depth, mat, label+'-post')
        if globes:
            xy = f.point(u, 0, depth)[:2]
            f.builder.lathe(tuple(xy), [(z+1.10, .075), (z+1.43, .06)],
                            'iron', 8, label+'-globe-post')
            f.builder.lathe(tuple(xy), [(z+1.43, .05), (z+1.49, .13), (z+1.60, .16),
                                       (z+1.72, .10), (z+1.75, .035)],
                            'pale globe', 8 if lod else 12, label+'-simplified-globe')


def balcony(f, u, width, z, lod, label, stone=False, projection=1.15, globes=False):
    f.box(u, z-.13, width+.24, .26, projection+.42, projection/2-.07,
          'carved pale stone', label+'-slab')
    railing(f, u-width/2, u+width/2, z, projection-.10, lod, label, stone, globes)
    for uu in [u-width/2, u+width/2]:
        f.box(uu, z+1.0, .14 if stone else .065, .14 if stone else .065, projection,
              projection/2-.10, 'carved pale stone' if stone else 'iron', label+'-return')
    for uu in np.linspace(u-width/2+.25, u+width/2-.25, max(2, round(width/2.8))):
        # Tapered bracket, not a claimed full sculptural replica.
        bracket = Polygon([(-.20,z-.24),(.20,z-.24),(.17,z-.74),(.02,z-1.02),(-.14,z-.74)])
        f.prism(Polygon([(a+uu,zz) for a,zz in bracket.exterior.coords]), -.04, .62,
                'carved pale stone', label+'-simplified-bracket')


def pediment(f, u, z, width, lod, label, curved, rise=.62):
    if curved:
        aa = np.linspace(0, math.pi, 14 if lod else 28)
        outer = [(u+width/2*math.cos(a), z+rise*math.sin(a)) for a in aa]
        inner = [(u+(width/2-.15)*math.cos(a), z+(rise-.17)*math.sin(a)) for a in aa[::-1]]
        f.prism(Polygon(outer+inner), .02, .27, 'carved pale stone', label+'-curved-moulding')
    else:
        outer = Polygon([(u-width/2,z),(u,z+.67),(u+width/2,z),(u+width/2-.20,z-.06),
                         (u,z+.46),(u-width/2+.20,z-.06)])
        f.prism(outer, .02, .27, 'carved pale stone', label+'-triangular-moulding')
    f.box(u,z-.09,width+.12,.16,.47,.12,'carved pale stone',label+'-base')
    for uu in [u-width/2+.14,u+width/2-.14]:
        f.box(uu,z-.31,.23,.41,.32,.13,'carved pale stone',label+'-console')
    if not lod:
        medallion = Point(u,z+.03).buffer(.13,quad_segs=10)
        f.prism(medallion,.10,.29,'carved pale stone',label+'-simplified-cartouche')


def body_plan():
    cx,cy=P['northeast_corner_circle_center_xy'];r=P['northeast_corner_radius_design_m']
    pts=[(-30.,-47.),(30.,-47.),(33.,-44.),(33.,cy)]
    pts += [(cx+r*math.cos(a),cy+r*math.sin(a)) for a in np.linspace(0,math.pi/2,6)[1:]]
    pts += [(-30.,47.),(-33.,44.),(-33.,-44.)]
    return Polygon(pts)


def facade_kind(f):
    curved = f.n[0]>.1 and f.n[1]>.1
    north = f.n[1]>.999
    east = f.n[0]>.999
    return north,east,curved,north or east or curved


def bay_data(f):
    north,east,curved,street=facade_kind(f)
    if curved:
        return [0.],f.length, min(2.8,f.length-.65)
    n=max(1,round((f.length-1.2)/(3.65 if street else 4.6)))
    pitch=(f.length-1.2)/n
    centers=[-f.length/2+.6+(k+.5)*pitch for k in range(n)]
    return centers,pitch,min(2.50,pitch-.83)



def author_facade_clearance(b, plan, lod):
    """Check authored ornament projections against every main-body aperture.

    This is an implementation check of estimated geometry, not measured history.
    Balcony rails/porticoes intentionally in front of glazing are outside this
    pier/pediment check. Exact meshes and complete GLBs are checked separately.
    """
    checked_parts=0; checked_openings=0; intersections=[]; pediment_gaps=[]
    for f in facade_ring(b,plan,'main-body'):
        north,east,curve,street=facade_kind(f)
        centers,pitch,width=bay_data(f); holes=[]
        for layer,(lo,hi) in enumerate(zip(P['design_layer_datums_m'][:-1],P['design_layer_datums_m'][1:])):
            for k,u in enumerate(centers):
                if layer==0:shape=opening(u,.24,min(width+.35,pitch-.48),4.20)
                elif layer==4:shape=opening(u,20.48,width,2.23)
                else:shape=opening(u,lo+.58,width,hi-lo-1.18)
                holes.append(shape)
                if layer==4 and street:holes.append(Point(u,24.04).buffer(.57,quad_segs=20))
                if street and not curve and layer in (1,2,3) and k%3==1:
                    z=hi-.34
                    next_bottom=20.48 if layer==3 else hi+.58
                    pediment_gaps.append({'facade':f.label,'layer':layer+1,'u':float(u),
                        'horizontal_base_above_current_opening_m':z-.09-.08-shape.bounds[3],
                        'highest_pediment_below_next_opening_m':next_bottom-(z+(.62 if (k//3+layer)%2==0 else .67)),
                        'side_console_horizontal_clearance_m':(width+.76)/2-.14-.23/2-width/2})
        checked_openings+=len(holes)
        selected=[p for p in b.parts if p['label'].startswith(f.label+'/') and any(
            key in p['label'] for key in ['facade-grouping-pilaster','pilaster-stone-course',
              'pilaster-capital','gallery-heavy-console','alternating-window-pediment',
              'north-tower-axis-giant-pier'])]
        for part in selected:
            xyz=np.asarray(part['vertices']); uv=np.column_stack(((xyz-f.center)@f.t,xyz[:,2]))
            projection=MultiPoint(uv).convex_hull
            for hole in holes:
                area=projection.intersection(hole).area
                if area>1e-8:intersections.append({'part':part['label'],'intersection_area_m2':area})
            checked_parts+=1
    assert not intersections,intersections[:5]
    assert all(p['horizontal_base_above_current_opening_m']>.08 and
               p['highest_pediment_below_next_opening_m']>.14 and
               p['side_console_horizontal_clearance_m']>.12 for p in pediment_gaps)
    sill_parts=[p for p in b.parts if p['label'].endswith('-sill')]
    signatures=[tuple(sorted(tuple(round(v,9) for v in xyz) for xyz in p['vertices'])) for p in sill_parts]
    duplicate_sills=len(signatures)-len(set(signatures))
    round_sills=sum('round-oculus-sill' in p['label'] for p in sill_parts)
    assert duplicate_sills==0 and round_sills==0
    return {'scope':'Author implementation check; all dimensions and profiles remain estimates',
            'checked_pier_and_pediment_parts':checked_parts,'checked_main_body_apertures':checked_openings,
            'positive_area_intersections_with_apertures':intersections,
            'duplicate_exact_window_sill_parts':duplicate_sills,'round_oculus_rectangular_sill_parts':round_sills,
            'window_sill_parts':len(sill_parts),'ordinary_pediment_clearances':pediment_gaps,
            'min_pediment_base_above_opening_m':min(p['horizontal_base_above_current_opening_m'] for p in pediment_gaps),
            'min_pediment_top_below_next_opening_m':min(p['highest_pediment_below_next_opening_m'] for p in pediment_gaps),
            'min_pediment_side_console_clearance_m':min(p['side_console_horizontal_clearance_m'] for p in pediment_gaps),
            'balcony_rails_and_porticoes_not_part_of_this_no_occlusion_check':True}

def build(lod=False):
    b=Builder(PALETTE);plan=body_plan();es=facade_ring(b,plan,'main-body')
    window_count=0;oculus_count=0;window_probes=[];gallery_segments=[];pier_clearances=[]
    north_f=next(f for f in es if facade_kind(f)[0])
    curve_fs=[f for f in es if facade_kind(f)[2]]
    tx,ty=P['tower_center_xy_estimated']
    # Continuous masonry facades with genuine polygon-cut openings and recessed glazing.
    for j,f in enumerate(es):
        north,east,curve,street=facade_kind(f);centers,pitch,width=bay_data(f)
        for layer,(lo,hi) in enumerate(zip(P['design_layer_datums_m'][:-1],P['design_layer_datums_m'][1:])):
            holes=[]
            for k,u in enumerate(centers):
                if layer==0:
                    shape=opening(u,.24,min(width+.35,pitch-.48),4.20)
                elif layer==4:
                    shape=opening(u,20.48,width,2.23)
                else:
                    shape=opening(u,lo+.58,width,hi-lo-1.18)
                holes.append(shape)
                window(f,shape,lod,'ground-shopfront' if layer==0 else 'main-window',
                       rows=3 if layer in (1,2,3) else 2, surround=.08 if street else .06)
                window_count+=1
                if layer==0 and street:
                    window_probes.append({'center_enu':f.point(u,2.17).tolist(),
                                          'outward_normal_enu':f.n.tolist(),'glass_front_m':-.32 if not lod else -.31})
                if layer==4 and street:
                    circle=Point(u,24.04).buffer(.57,quad_segs=10 if lod else 20)
                    holes.append(circle);window(f,circle,lod,'round-oculus',rows=1,surround=.16)
                    oculus_count+=1;window_count+=1
                    if not lod:
                        # Small paired curls indicate photographed ornamental borders.
                        for side in [-1,1]:
                            curl=Point(u+side*.79,24.04).buffer(.12,quad_segs=8)
                            f.prism(curl,.01,.17,'carved pale stone','oculus-simplified-scroll')
                if street and not curve and layer in (1,2,3) and k%3==1:
                    pediment(f,u,hi-.34,width+.76,lod,'alternating-window-pediment',(k//3+layer)%2==0)
                if street and layer in (1,2,3) and not lod:
                    # Geometric low-relief spandrels; actual sculpture is not reconstructed.
                    diamond=Polygon([(u-.38,lo+.22),(u,lo+.08),(u+.38,lo+.22),(u,lo+.36)])
                    f.prism(diamond,.015,.075,'carved pale stone','simplified-spandrel-diamond')
            closed_wall(f,es[j-1],es[(j+1)%len(es)],lo,hi,holes,
                        'base stone' if layer==0 else 'cream stone',.48)
        if street:
            for z in [5.,25.5]:
                balcony(f,0.,f.length-.06,z,lod,'continuous-iron-gallery',projection=1.30,globes=z==25.5)
                gallery_segments.append({'facade':f.label,'floor_m':z,'outward_normal_enu':f.n.tolist(),
                                         'endpoints_xy':[f.a[:2].tolist(),f.b[:2].tolist()]})
            # Narrow grouping piers do not cover the window apertures.
            group_us=([-f.length/2+.11,f.length/2-.11] if curve else
                      [-f.length/2+.6+k*pitch for k in range(0,len(centers)+1,3)])
            for u in group_us:
                if abs(u)>f.length/2-.09:continue
                pw=.30 if curve else min(.78,pitch-width-.20)
                clearance=min(abs(u-c)-width/2-(pw+.04)/2 for c in centers)
                assert clearance>.06
                pier_clearances.append(float(clearance))
                f.box(u,15.10,pw,19.90,.28,.10,'rusticated stone','facade-grouping-pilaster')
                f.box(u,23.93,pw+.18,.36,.40,.20,'carved pale stone','pilaster-capital')
                f.box(u,24.75,pw+.28,.62,.71,.28,'carved pale stone','gallery-heavy-console')
                if not lod:
                    for z in np.arange(5.45,23.0,.54):
                        f.box(u,float(z),pw+.04,.045,.30,.105,'carved pale stone','pilaster-stone-course')
        else:
            for z in [5.,10.,15.,20.,25.5]:f.beam(z,.16,.14,'carved pale stone',label='estimated-rear-belt')
    # Floor plates are set behind facade masonry, preserving visible window reveals.
    for z in P['design_layer_datums_m'][1:]:
        b.plan_prism(plan.buffer(-.49,join_style=2),z-.20,z-.015,'roof','estimated-main-floor')
    cornice(b,plan,5.,.42,lod,'first-gallery-belt')
    cornice(b,plan,25.42,.72,lod,'heavy-sixth-storey-gallery-cornice',True)
    cornice(b,plan,29.91,.67,lod,'main-roof-cornice')
    b.plan_prism(plan.difference(plan.buffer(-.34,join_style=2)),30.,30.65,
                 'cream stone','estimated-low-roof-parapet')
    # Curved balconies on the northeast corner are distinct from the remote tower.
    for f in curve_fs:
        for z in [10.,15.,20.]:
            balcony(f,0.,f.length-.07,z,lod,'northeast-curved-balcony',stone=z==10.,projection=1.12)
        for u in [-f.length/2+.12,f.length/2-.12]:
            column(b,f.point(u,0,.20)[:2],5.26,9.58,.17,lod,'northeast-lower-paired-pilaster')
    # Northeast entrance portico: shallow arched canopy with paired supports.
    center=np.array(P['northeast_corner_circle_center_xy']);n=np.array([1.,1.])/math.sqrt(2)
    t=np.array([-1.,1.])/math.sqrt(2);arcfront=center+n*P['northeast_corner_radius_design_m']
    entry=Facade(b,arcfront-t*5.4,arcfront+t*5.4,'northeast-entrance')
    canopy=Polygon([(-5.1,4.73),(-3.8,4.73),(-2.8,5.12),(-1.4,5.77),(0,6.05),
                    (1.4,5.77),(2.8,5.12),(3.8,4.73),(5.1,4.73),(5.1,4.39),
                    (3.5,4.39),(2.5,4.78),(1.2,5.35),(0,5.58),(-1.2,5.35),
                    (-2.5,4.78),(-3.5,4.39),(-5.1,4.39)])
    entry.prism(canopy,-.05,2.15,'carved pale stone','arched-projecting-entrance-canopy')
    for u in [-4.25,-3.69,3.69,4.25]:
        column(b,entry.point(u,0,1.62)[:2],.12,4.50,.18,lod,'entrance-paired-ionic-column')
    # Broad upper curved corner crest, with simple blind central relief.
    for f in curve_fs:
        f.wall(30.65,31.18,(),.38,'cream stone')
        f.beam(31.17,.20,.25,'carved pale stone',label='curved-corner-parapet-top')
    crown=Polygon([(-4.6,30.10),(-4.6,31.35),(-3.4,31.35),(-3.4,31.74),(-2.2,31.74),
                   (-2.2,32.18),(-.8,32.18),(0,32.5),(.8,32.18),(2.2,32.18),
                   (2.2,31.74),(3.4,31.74),(3.4,31.35),(4.6,31.35),(4.6,30.10)])
    entry.prism(crown,-1.40,-.90,'cream stone','separate-northeast-stepped-crown')
    pediment(entry,0,29.94,8.8,lod,'northeast-curved-crown-moulding',True,rise=1.7)
    # The north tower sits above a separate projecting three-bay facade group.
    hero_u=float((np.array([tx,47.,0.])-north_f.center)@north_f.t)
    for z in [10.,15.,20.]:
        balcony(north_f,hero_u,10.4,z,lod,'north-tower-axis-balcony',stone=z==10.,projection=1.20)
    north_centers,north_pitch,north_width=bay_data(north_f)
    north_gaps=[(a+bb)/2 for a,bb in zip(north_centers[:-1],north_centers[1:])]
    hero_piers=[min(north_gaps,key=lambda gap:abs(gap-desired)) for desired in [hero_u-5.85,hero_u+5.85]]
    for u in hero_piers:
        assert min(abs(u-c)-north_width/2-.73/2 for c in north_centers)>.07
        north_f.box(u,17.55,.73,15.30,.58,.22,'rusticated stone','north-tower-axis-giant-pier')
    # North entrance canopy and paired columns, separated from ordinary shop glazing.
    north_entry=Facade(b,(tx+5.3,47.),(tx-5.3,47.),'north-central-entrance')
    north_entry.prism(canopy,-.05,1.85,'carved pale stone','north-arched-entrance-canopy')
    for u in [-4.25,-3.69,3.69,4.25]:
        column(b,north_entry.point(u,0,1.40)[:2],.12,4.50,.18,lod,'north-entrance-paired-column')
    # Photo-visible local seventh-storey mass towards southeast, roof unseen and estimated.
    seventh=box(*P['seventh_storey_estimated_xy']);se=facade_ring(b,seventh,'southeast-seventh-storey')
    for j,f in enumerate(se):
        nwin=max(2,round((f.length-1.8)/3.7));pitch=(f.length-1.8)/nwin;holes=[]
        for k in range(nwin):
            u=-f.length/2+.9+(k+.5)*pitch;shape=opening(u,30.58,min(2.2,pitch-.66),3.15)
            holes.append(shape);window(f,shape,lod,'seventh-storey-window',rows=2);window_count+=1
        closed_wall(f,se[j-1],se[(j+1)%len(se)],30.,34.4,holes,'cream stone',.40)
    b.plan_prism(seventh.buffer(-.41,join_style=2),34.20,34.4,'roof','estimated-seventh-storey-roof')
    cornice(b,seventh,34.28,.42,lod,'seventh-storey-roof-cornice')
    # Solid (glazed) tower base does not count as one of the two open pavilions.
    towerbase=box(tx-5.0,ty-4.0,tx+5.0,ty+4.0);bs=facade_ring(b,towerbase,'tower-solid-base')
    for j,f in enumerate(bs):
        holes=[]
        for u in [-f.length*.22,f.length*.22]:
            shape=opening(u,30.52,1.76,2.78);holes.append(shape)
            window(f,shape,lod,'tower-base-recessed-window',rows=2);window_count+=1
        closed_wall(f,bs[j-1],bs[(j+1)%len(bs)],30.,34.,holes,'cream stone',.42)
    cornice(b,towerbase,33.94,.39,lod,'tower-base-cornice')
    tower_openings=[]
    for stage,lo,hi,w,d in [(1,34.,39.,9.0,7.2),(2,39.,43.4,7.1,5.7)]:
        tp=box(tx-w/2,ty-d/2,tx+w/2,ty+d/2);fs=facade_ring(b,tp,f'tower-open-pavilion-{stage}')
        for j,f in enumerate(fs):
            clear=f.length-(2.90 if stage==1 else 2.50)
            shape=opening(0,lo+.35,clear,hi-lo-1.04,arch=.12 if stage==1 else .25,segments=8 if lod else 16)
            closed_wall(f,fs[j-1],fs[(j+1)%len(fs)],lo+.13,hi-.27,[shape],'cream stone',.38)
            for u in [-clear/2-.31,clear/2+.31]:
                column(b,f.point(u,0,.17)[:2],lo+.25,hi-.52,.24 if stage==1 else .21,
                       lod,f'tower-stage-{stage}-external-column')
            railing(f,-clear/2+.06,clear/2-.06,lo+.36,.05,lod,f'tower-stage-{stage}-balustrade',stone=True)
            # The upper stage has curved pediments; lower stage has heavy straight entablature.
            if stage==2:
                pediment(f,0,hi-.22,f.length+.06,lod,'tower-upper-curved-pediment',True,rise=1.4)
            tower_openings.append({'stage':stage,'normal_enu':f.n.tolist(),
                                   'center_enu':f.point(0,lo+2.6).tolist(),
                                   'clear_width_design_m':clear})
        b.plan_prism(tp.buffer(.24,join_style=2),lo,lo+.16,'carved pale stone',f'tower-stage-{stage}-floor')
        b.plan_prism(tp.buffer(.37,join_style=2),hi-.27,hi-.03,'carved pale stone',f'tower-stage-{stage}-roof')
        cornice(b,tp,hi-.13,.47,lod,f'tower-stage-{stage}-cornice',True)
    # Low stepped central cap differs from Sincere's open circular lantern.
    b.box((tx,ty,43.76),(3.4,3.1,.72),'cream stone',label='tower-upper-central-plinth')
    b.box((tx,ty,44.16),(3.7,3.4,.16),'carved pale stone',label='tower-small-plinth-cornice')
    b.box((tx,ty,44.65),(2.10,1.95,.82),'cream stone',label='tower-small-square-cap')
    b.box((tx,ty,45.13),(2.45,2.28,.18),'carved pale stone',label='tower-cap-cornice')
    b.lathe((tx,ty),[(45.22,.92),(45.62,.37),(45.80,.16)],'carved pale stone',8 if lod else 16,
            'tower-architectural-top-design-45-8')
    b.lathe((tx,ty),[(45.76,.115),(53.94,.028),(54.,.016)],'iron',8,
            'modern-photo-mast-estimated-top-54')
    for z in np.arange(46.0,53.51,.52 if lod else .26):
        b.tube([(tx-.20,ty,float(z)),(tx+.20,ty,float(z))],.018,'iron',5,'simplified-modern-mast-rung')
    # Authored solids are closed individually; this does not assert a single Boolean-union solid.
    for part in b.parts:
        vertices=np.array(part['vertices']);triangles=np.array(part['triangles'])
        vol=np.einsum('ij,ij->i',vertices[triangles[:,0]],np.cross(vertices[triangles[:,1]],vertices[triangles[:,2]])).sum()/6
        assert abs(vol)>1e-10,part['label']
        if vol<0:part['triangles']=[(int(a),int(c),int(bb)) for a,bb,c in triangles]
    facade_review=author_facade_clearance(b,plan,lod)
    metadata={
        'id':ID,'name':'Old Wing On Company main building and rooftop pavilion / 老永安公司主楼与屋顶塔楼外观',
        'status':'standalone-exterior-candidate-not-geographically-registered',
        'all_plan_dimensions_estimated':True,'height_endpoints_verified':False,
        'documented_floor_count':'six storeys, locally seven; two-storey roof pavilion',
        'design_plan_m':[66.,94.], 'frozen_map_coarse_mrr_m':[94.636,66.671],
        'documented_site_area_m2':5681.5,'documented_floor_area_m2':30992.3,
        'main_roof_design_m':30.,'seventh_storey_roof_design_m':34.4,
        'tower_architectural_top_design_m':45.8,'tower_top_design_m':54.,
        'tower_modern_mast_top_design_m':54.,'tower_total_height_verified':False,
        'tower_official_name':'倚云阁','tower_common_variant':'绮云阁',
        'tower_solid_base_not_counted_as_open_storey':True,
        'tower_open_storeys':2,'tower_is_separate_from_northeast_curved_entrance':True,
        'tower_location_photo_guided_xy_unmeasured':[-12.5,42.5],
        'tower_modern_photo_mast_not_claimed_historically_original':True,
        'local_seventh_storey_boundary_rear_and_roof_estimated':True,
        'reference_photographs_embedded':False,'photos_embedded':False,
        'map_replacement':False,'continuous_ground_arcade_claimed':False,
        'new_wing_on_building_and_bridges_excluded':True,
        'commercial_signage_and_neighboring_buildings_included':False,
        'rear_elevations_and_roof_junctions_estimated':True,
        'copyright':'Original code and geometry MIT; reference photographs not embedded',
    }
    features={
        'facade_clearance_author_check':facade_review,
        'parameters':P,'design_plan_xy':[list(p) for p in plan.exterior.coords[:-1]],
        'author_parts':len(b.parts),'window_openings':window_count,'round_oculus_openings':oculus_count,
        'primary_pier_min_window_clearance_design_m':min(pier_clearances),
        'ordinary_window_surround_design_width_m':.08,
        'hero_north_pier_u_positions_design_m':hero_piers,
        'window_sills_are_single_and_round_oculi_have_no_rectangular_sill':True,
        'ground_shopfront_recess_probes':window_probes,
        'continuous_ground_arcade_opening_count':0,'iron_gallery_segments':gallery_segments,
        'two_continuous_street_iron_gallery_floors_m':[5.,25.5],
        'northeast_curved_balcony_floors_m':[10.,15.,20.],
        'tower_open_stage_count':2,'tower_pavilion_through_openings':tower_openings,
        'northeast_crown_and_north_tower_are_separate':True,
        'northeast_crown_top_design_m':32.5,
        'all_decorative_profiles_simplified_and_unmeasured':True,
        'rear_roof_and_seventh_storey_boundaries_estimated':True,
    }
    return b,metadata,features


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True);parser.add_argument('--lod',action='store_true')
    args=parser.parse_args();builder,metadata,features=build(args.lod);args.out.mkdir(parents=True,exist_ok=True)
    stem=ID+('-lod' if args.lod else '-raw');result=builder.save(args.out/(stem+'.glb'),metadata)
    (args.out/(stem+'-features.json')).write_text(json.dumps(features,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='part_summary'}))


if __name__=='__main__':main()
