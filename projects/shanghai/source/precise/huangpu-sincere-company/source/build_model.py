"""Photo-informed Sincere Company historic exterior candidate; original MIT geometry.

The 2010 southwest photograph, 2013 Moxing Tower photograph and 2024 southeast
corner photograph were visually inspected. No image pixels or commercial signs
are embedded. All dimensions/bay counts/ornamental profiles are author estimates.
The 100 x 68 m design is not the frozen map polygon or a surveyed footprint.
"""
import argparse
import json
import math
from pathlib import Path

import numpy as np
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

from common.photo_architecture import Builder, Facade, facade_ring, opening

ID = 'huangpu-sincere-company'
PALETTE = {
    'cream stone': {'color': [.72, .69, .60], 'roughness': .85},
    'carved pale stone': {'color': [.79, .76, .67], 'roughness': .80},
    'rusticated stone': {'color': [.66, .64, .56], 'roughness': .89},
    'cornice shadow stone': {'color': [.57, .56, .50], 'roughness': .91},
    'base stone': {'color': [.43, .43, .39], 'roughness': .88},
    'roof': {'color': [.43, .44, .41], 'roughness': .92},
    'recessed glass': {'color': [.10, .14, .15], 'roughness': .28, 'metallic': .18},
    'bronze window frame': {'color': [.15, .155, .14], 'roughness': .61, 'metallic': .15},
    'iron': {'color': [.095, .105, .095], 'roughness': .66, 'metallic': .25},
    'clock dial': {'color': [.74, .75, .68], 'roughness': .72},
    'clock iron': {'color': [.07, .08, .07], 'roughness': .65, 'metallic': .25},
}
P = {
    'all_plan_dimensions_estimated': True,
    'design_width_m': 100., 'design_depth_m': 68.,
    'design_plan_xy': [[-44., -34.], [42., -34.], [50., -26.], [50., 34.],
                       [-50., 34.], [-50., -28.]],
    'southwest_corner_cut_m': 6., 'southeast_corner_cut_m': 8.,
    'south_street': 'Nanjing Road', 'east_street': 'Zhejiang Road',
    'design_layer_datums_m': [0., 4.5, 8.7, 13., 17.4, 21.8, 26.2, 30.6],
    'main_roof_design_m': 30.6, 'northeast_low_wing_roof_design_m': 21.8,
    'northeast_low_wing_authored_xy': [20., -8., 50., 34.],
    'northeast_step_photo_guided_but_bounds_unmeasured': True,
    'arcade_design_depth_m': 3.2,
    'primary_street_pier_width_design_m': 1.24,
    'primary_street_pier_front_design_m': .54,
    'primary_street_cross_storey_column_radius_design_m': .36,
    'main_middle_cornice_reach_design_m': 1.0,
    'ordinary_window_surround_width_design_m': .08,
    'ordinary_window_surround_front_design_m': .05,
    'tower_name': 'Moxing Tower / 摩星塔',
    'tower_center_xy_estimated': [43., -27.],
    'tower_outward_bearing_enu': [0.7071067811865476, -0.7071067811865476],
    'tower_design_stage_datums_m': [30.6, 33.8, 38.3, 42.1, 46.1, 47.3, 51.3],
    'tower_stage_forms': ['stepped clock base', 'large square arched pavilion',
                         'small chamfered square arched pavilion', 'open circular columned pavilion'],
    'tower_total_top_design_m': 51.3,
    'tower_total_height_has_no_verified_source_measurement': True,
    'tower_pole_design_length_m': 4.,
    'clock_center_design_m': 32.20, 'clock_radius_design_m': 1.08,
    'modern_commercial_signs_included': False,
    'courtyard_invented': False, 'separate_northern_building_included': False,
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


def win(f, shape, lod, label, rows=2, trim=True):
    # Ordinary rectangular openings stay quieter than the principal arches.
    # Hero corner windows and curved opening surrounds keep the stronger trim.
    fine_trim = (trim and label in {'lower-window', 'middle-window', 'upper-window'}
                 and shape.equals(box(*shape.bounds))
                 and (abs(f.n[0]) > .9 or abs(f.n[1]) > .9))
    if not lod:
        f.window(shape, 2, rows, 'bronze window frame', trim and not fine_trim,
                 'recessed glass', label)
    else:
        f.prism(shape.buffer(-.065, join_style=2), -.34, -.31, 'recessed glass', label+'-glass')
        x0, z0, x1, _ = shape.bounds
        f.box((x0+x1)/2, z0-.07, x1-x0+.30, .14, .60, .10,
              'carved pale stone', label+'-sill')
        if trim and not fine_trim:
            f.prism(shape.buffer(.16, join_style=2).difference(shape), -.025, .105,
                    'carved pale stone', label+'-surround')
    if fine_trim:
        f.prism(shape.buffer(P['ordinary_window_surround_width_design_m'], join_style=2).difference(shape),
                -.015, P['ordinary_window_surround_front_design_m'], 'cream stone', label+'-fine-surround')


def column(b, xy, lo, hi, radius, lod, label, ionic=False):
    h = hi-lo
    b.lathe(tuple(xy), [(lo, radius*1.32), (lo+.12, radius*1.32),
                        (lo+.24, radius), (hi-.34, radius*.91),
                        (hi-.22, radius*1.20), (hi-.09, radius*1.36),
                        (hi, radius*1.36)], 'carved pale stone', 12 if lod else 20, label)
    if ionic:
        b.box((xy[0], xy[1], hi-.06), (radius*3.3, radius*2.9, .17),
              'carved pale stone', label=label+'-simplified-capital')


def cornice(b, plan, z, reach, lod, label, dentils=False):
    for dz, height, projection in [(-.24, .15, reach*.62), (-.08, .16, reach), (.08, .13, reach*.90)]:
        ring = plan.buffer(projection, join_style=2).difference(plan.buffer(-.12, join_style=2))
        b.plan_prism(ring, z+dz-height/2, z+dz+height/2, 'carved pale stone', label+'-profile')
    if dentils:
        for f in facade_ring(b, plan, label):
            for u in np.arange(-f.length/2+.23, f.length/2-.12, .86 if lod else .43):
                f.box(float(u), z-.38, .18, .19, reach*.65, reach*.25,
                      'carved pale stone', 'dentil')


def railing(f, lo, hi, z, depth, lod, label, stone=False):
    material = 'carved pale stone' if stone else 'iron'
    f.box((lo+hi)/2, z+.94, hi-lo, .14 if stone else .07, .24 if stone else .07,
          depth, material, label+'-top-rail')
    f.box((lo+hi)/2, z+.16, hi-lo, .18 if stone else .06, .20 if stone else .06,
          depth, material, label+'-bottom-rail')
    for u in np.arange(lo+.20, hi-.11, .66 if lod else .38):
        if stone:
            xy = f.point(float(u), 0, depth)[:2]
            f.builder.lathe(tuple(xy), [(z+.25, .065), (z+.39, .10), (z+.60, .075),
                                       (z+.80, .05), (z+.86, .075)],
                            material, 8 if lod else 12, label+'-stone-baluster')
        else:
            f.box(float(u), z+.54, .045, .76, .045, depth, material, label+'-iron-picket')
            if not lod:
                diamond = Polygon([(u-.13, z+.51), (u, z+.73), (u+.13, z+.51), (u, z+.29)])
                f.prism(diamond.difference(diamond.buffer(-.025)), depth-.023, depth+.023,
                        material, label+'-iron-diamond')
    for u in [lo, hi]:
        f.box(u, z+.52, .18 if stone else .08, 1.04, .22 if stone else .08,
              depth, material, label+'-end-post')


def balcony(f, center, width, z, lod, label, stone=False, projection=.88):
    f.box(center, z-.10, width+.34, .20, projection+.42, projection/2-.04,
          'carved pale stone', label+'-slab')
    railing(f, center-width/2, center+width/2, z, projection-.12, lod, label, stone)
    for u in [center-width/2, center+width/2]:
        f.box(u, z+.94, .18 if stone else .07, .14 if stone else .07, projection,
              projection/2-.12, 'carved pale stone' if stone else 'iron', label+'-return-rail')
        f.box(u, z-.48, .22, .57, .40, .16, 'carved pale stone', label+'-console')


def curved_pediment(f, u, spring, width, rise, lod, label, broken=True):
    radius = width/2
    seg = 12 if lod else 28
    ranges = [(0., math.pi*.43), (math.pi*.57, math.pi)] if broken else [(0., math.pi)]
    for start, stop in ranges:
        aa = np.linspace(start, stop, seg)
        outer = [(u+radius*math.cos(a), spring+rise*math.sin(a)) for a in aa]
        inner = [(u+(radius-.22)*math.cos(a), spring+(rise-.20)*math.sin(a)) for a in aa[::-1]]
        f.prism(Polygon(outer+inner), -.01, .32, 'carved pale stone', label+'-arched-moulding')
    for side in [-1, 1]:
        f.box(u+side*(radius-.45), spring-.04, .95, .20, .56, .15,
              'carved pale stone', label+'-spring-block')


def facade_bays(f):
    cut_se = f.n[0] > .4 and f.n[1] < -.4
    cut_sw = f.n[0] < -.4 and f.n[1] < -.4
    n = 1 if cut_se or cut_sw else max(3, round((f.length-1.8)/4.05))
    margin = .9
    pitch = (f.length-2*margin)/n
    centers = [-f.length/2+margin+(k+.5)*pitch for k in range(n)]
    return centers, pitch, min(2.65, pitch-.85), cut_se, cut_sw


def build(lod=False):
    b = Builder(PALETTE)
    plan = Polygon(P['design_plan_xy'])
    low_region = box(*P['northeast_low_wing_authored_xy'])
    high_plan = plan.difference(low_region)
    low_roof = plan.intersection(low_region)
    es = facade_ring(b, plan, 'main-body')
    opening_count = 0
    arcade_holes = []
    balcony_count = 0
    primary_pier_clearances = []
    se_facade = None
    # Street-level outer arcade: actual arched voids, floor and rear glazing.
    for j, f in enumerate(es):
        centers, pitch, width, cut_se, cut_sw = facade_bays(f)
        is_street = f.n[1] < -.1 or abs(f.n[0]) > .9
        holes = []
        for u in centers:
            w = 5.4 if cut_se else (4.2 if cut_sw else min(3.12, pitch-.62))
            shape = opening(u, 0. if is_street else .30, w, 4.02 if is_street else 3.72,
                            arch=1.12 if is_street else 0., segments=12 if lod else 24)
            holes.append(shape)
            if is_street:
                arcade_holes.append({'center_xy': f.point(u, 0).tolist()[:2], 'normal': f.n.tolist(),
                                     'clear_width_design_m': w, 'back_glass_depth_design_m': 3.54})
                f.prism(shape.buffer(.16, join_style=2).difference(shape).intersection(
                    box(-f.length/2, 0, f.length/2, 4.5)), -.01, .16,
                    'rusticated stone', 'arcade-arch-surround')
            else:
                win(f, shape, lod, 'estimated-rear-ground-window')
                opening_count += 1
        closed_wall(f, es[j-1], es[(j+1) % len(es)], 0., 4.5, holes,
                    'base stone', .50)
    back_plan = plan.buffer(-P['arcade_design_depth_m'], join_style=2)
    back_edges = facade_ring(b, back_plan, 'arcade-rear')
    for j, f in enumerate(back_edges):
        centers, pitch, width, cut_se, cut_sw = facade_bays(f)
        holes = []
        for u in centers:
            shape = opening(u, .22, min(2.95, pitch-.35), 3.65)
            holes.append(shape)
            win(f, shape, lod, 'recessed-shop-window', rows=2, trim=False)
            opening_count += 1
        closed_wall(f, back_edges[j-1], back_edges[(j+1) % len(back_edges)], .18, 4.5,
                    holes, 'cream stone', .40)
    # Floors stop clear of outer wall edges; no coincident whole-footprint plinth.
    floor_ring = plan.buffer(-.025, join_style=2).difference(plan.buffer(-3.16, join_style=2))
    b.plan_prism(floor_ring, .08, .18, 'roof', 'walk-through-arcade-floor')
    b.plan_prism(plan.buffer(-.49, join_style=2), 4.31, 4.49, 'roof', 'arcade-soffit')
    # Lower two design layers: varied groups of giant columns and tall arches.
    for j, f in enumerate(es):
        centers, pitch, width, cut_se, cut_sw = facade_bays(f)
        if cut_se:
            se_facade = f
        holes = []
        col_positions = set()
        if cut_sw:
            # The photographed southwest cut is the broad rusticated sign pier.
            for z in np.arange(4.76, 30.38, .60):
                f.box(0, float(z), f.length-.22, .51, .15, .045,
                      'rusticated stone', 'southwest-horizontal-stone-course')
        elif cut_se:
            shape = opening(0, 4.84, 4.8, 7.55, arch=1.62, segments=16 if lod else 28)
            holes.append(shape)
            win(f, shape, lod, 'southeast-grand-arched-opening', rows=4)
            opening_count += 1
            for u in [-3.62, 3.62]:
                column(b, f.point(u, 0, .43)[:2], 4.65, 12.73, .42, lod,
                       'southeast-giant-ionic-column', True)
                f.box(u, 12.8, 1.54, .31, 1.10, .35, 'carved pale stone', 'corner-capital-block')
            curved_pediment(f, 0, 12.91, 8.8, 2.48, lod, 'southeast-large-semicircular-pediment', False)
            balcony(f, 0, 9.3, 4.50, lod, 'southeast-stone-balcony', True, 1.15)
            balcony(f, 0, 3.8, 8.70, lod, 'southeast-center-iron-balcony', False, 1.05)
            balcony_count += 2
            shield = Point(0, 12.66).buffer(.38, quad_segs=10 if lod else 20)
            f.prism(shield, .10, .24, 'carved pale stone', 'corner-simplified-oval-cartouche')
        else:
            street = f.n[1] < -.9 or abs(f.n[0]) > .9
            primary_street = f.n[1] < -.9 or f.n[0] < -.9
            for k, u in enumerate(centers):
                xy = f.point(u, 0)[:2]
                low_east = f.n[0] > .9 and xy[1] > -8
                giant = street and not low_east and k % 7 in (2, 3, 4)
                if giant:
                    shape = opening(u, 4.86, width+.20, 7.63, arch=.95, segments=12 if lod else 24)
                    holes.append(shape)
                    win(f, shape, lod, 'two-storey-column-bay', rows=4)
                    opening_count += 1
                    col_positions.update([round(u-pitch/2, 6), round(u+pitch/2, 6)])
                    balcony(f, u, width+.18, 8.70, lod, 'lower-stone-balcony', True)
                    balcony_count += 1
                else:
                    for lo, hi in [(4.5, 8.7), (8.7, 13.)]:
                        shape = opening(u, lo+.53, width, hi-lo-1.10,
                                        arch=.72 if low_east else 0., segments=12 if lod else 24)
                        holes.append(shape)
                        win(f, shape, lod, 'lower-window', rows=2)
                        opening_count += 1
                        if street and lo == 4.5:
                            curved_pediment(f, u, hi-.39, width+.62, .62, lod, 'broken-window-pediment')
            for u in col_positions:
                radius = P['primary_street_cross_storey_column_radius_design_m'] if primary_street else .265
                column(b, f.point(u, 0, .30)[:2], 4.68, 12.68, radius, lod,
                       'lower-cross-storey-ionic-column', True)
            # Wider stone piers break the long street elevation into sections.
            if street:
                for k in range(0, len(centers)+1, 7):
                    u = -f.length/2+.9+k*pitch
                    pier_top = 21.55 if f.n[0] > .9 and f.point(u, 0)[1] > -8 else 30.255
                    pier_width = P['primary_street_pier_width_design_m'] if primary_street else 1.0
                    pier_depth, pier_center = (.58, .25) if primary_street else (.31, .10)
                    joint_width = pier_width+.04 if primary_street else 1.08
                    joint_depth, joint_center = (.62, .24) if primary_street else (.38, .15)
                    if primary_street:
                        # Group divisions adjoin ordinary windows, not the tall
                        # three-bay arches. Check the widest horizontal joint.
                        clearance = min(abs(u-c)-width/2-joint_width/2 for c in centers)
                        assert clearance > .03, (f.label, u, clearance)
                        primary_pier_clearances.append(float(clearance))
                    f.box(u, (4.705+pier_top)/2, pier_width, pier_top-4.705, pier_depth, pier_center,
                          'rusticated stone', 'three-part-elevation-projecting-pier')
                    if not lod:
                        for z in np.arange(4.9, pier_top-.45, .60):
                            f.box(u, float(z), joint_width, .08, joint_depth, joint_center,
                                  'carved pale stone', 'projecting-pier-horizontal-joint')
        closed_wall(f, es[j-1], es[(j+1) % len(es)], 4.5, 13., holes)
    # Middle layers include the eastern wing's large upper arched windows.
    for lo, hi in [(13., 17.4), (17.4, 21.8)]:
        for j, f in enumerate(es):
            centers, pitch, width, cut_se, cut_sw = facade_bays(f)
            holes = []
            if not cut_sw and not (cut_se and lo == 13.):
                for u in ([-3., 0., 3.] if cut_se else centers):
                    xy = f.point(u, 0)[:2]
                    low_east = f.n[0] > .9 and xy[1] > -8
                    w = 1.76 if cut_se else (width+.27 if low_east else width)
                    shape = opening(u, lo+.58, w, 3.15,
                                    arch=1.14 if low_east else 0., segments=12 if lod else 24)
                    holes.append(shape)
                    win(f, shape, lod, 'low-wing-large-arch' if low_east else 'middle-window', rows=2)
                    opening_count += 1
                    if f.n[1] < -.9 and lo == 13. and int(round(u/pitch)) % 3 == 0:
                        balcony(f, u, w+.20, lo+.50, lod, 'upper-iron-balcony', False, .60)
                        balcony_count += 1
            closed_wall(f, es[j-1], es[(j+1) % len(es)], lo, hi, holes)
            f.beam(hi-.11, .16, .19, 'carved pale stone', label='middle-storey-belt')
    # Actual upper footprint omits the NE region, creating a full terrace step.
    upper_edges = facade_ring(b, high_plan, 'high-roof-body')
    for lo, hi in [(21.8, 26.2), (26.2, 30.6)]:
        for j, f in enumerate(upper_edges):
            centers, pitch, width, cut_se, cut_sw = facade_bays(f)
            holes = []
            if not cut_sw and not cut_se:
                for u in centers:
                    shape = opening(u, lo+.65, width, 2.95)
                    holes.append(shape)
                    win(f, shape, lod, 'upper-window', rows=2)
                    opening_count += 1
                    if lo == 21.8:
                        f.box(u, hi-.55, width+.36, .19, .34, .12,
                              'carved pale stone', 'upper-window-lintel')
            elif cut_se:
                # Modern advertising conceals this area in both close photos.
                # Only a plain closed transition is authored behind that zone.
                f.box(0, (lo+hi)/2, f.length-.36, hi-lo-.25, .13, .04,
                      'cream stone', 'unresolved-sign-obscured-corner-transition')
            closed_wall(f, upper_edges[j-1], upper_edges[(j+1) % len(upper_edges)], lo, hi, holes)
        b.plan_prism(high_plan.buffer(-.49, join_style=2), hi-.20, hi-.015,
                     'roof', 'high-body-estimated-floor')
    for z in [8.7, 13., 17.4, 21.8]:
        b.plan_prism(plan.buffer(-.49, join_style=2), z-.19, z-.015,
                     'roof', 'main-estimated-floor')
    b.plan_prism(low_roof.buffer(-.025, join_style=2), 21.62, 21.8,
                 'roof', 'northeast-lower-roof-terrace')
    cornice(b, plan, 4.47, .38, lod, 'street-arcade-cornice')
    cornice(b, plan, 13.0, P['main_middle_cornice_reach_design_m'], lod,
             'strong-middle-dentil-cornice', True)
    shadow_band = plan.buffer(.38, join_style=2).difference(plan.buffer(-.12, join_style=2))
    b.plan_prism(shadow_band, 12.52, 12.76, 'cornice shadow stone', 'main-cornice-subdued-under-band')
    cornice(b, low_roof, 21.72, .40, lod, 'low-wing-roof-cornice')
    cornice(b, high_plan, 30.48, .62, lod, 'high-body-crowning-cornice')
    # Sparse roof posts and balls are photograph-guided, spacing is estimated.
    for f in facade_ring(b, high_plan, 'roof-ornament'):
        if f.n[1] < -.9 or f.n[0] < -.9:
            for u in np.arange(-f.length/2+2., f.length/2-1., 11.5):
                xy = f.point(float(u), 0, -.04)[:2]
                b.lathe(tuple(xy), [(30.6, .10), (31.12, .07), (31.18, .14),
                                    (31.31, .18), (31.44, .12), (31.47, .025)],
                        'carved pale stone', 8 if lod else 12, 'roof-ball-finial')
    # Moxing Tower: stepped clock base, two square arched pavilions, round lantern.
    tx, ty = P['tower_center_xy_estimated']
    tangent = np.array([1., 1.])/math.sqrt(2)
    inward = np.array([-1., 1.])/math.sqrt(2)
    outward = -inward
    def xy(u, v):
        return np.array([tx, ty])+tangent*u+inward*v
    def tower_plan(width, chamfer=0.):
        h = width/2
        pts = [(-h, -h), (h, -h), (h, h), (-h, h)] if not chamfer else [
            (-h+chamfer, -h), (h-chamfer, -h), (h, -h+chamfer), (h, h-chamfer),
            (h-chamfer, h), (-h+chamfer, h), (-h, h-chamfer), (-h, -h+chamfer)]
        return Polygon([xy(u, v) for u, v in pts])
    front = Facade(b, xy(-6, -2.75), xy(6, -2.75), 'moxing-stepped-clock-base')
    step_outline = Polygon([(-6, 30.6), (6, 30.6), (6, 31.22), (4.85, 31.22),
                            (4.85, 31.79), (3.55, 31.79), (3.55, 33.64),
                            (-3.55, 33.64), (-3.55, 31.79), (-4.85, 31.79),
                            (-4.85, 31.22), (-6, 31.22)])
    front.prism(step_outline, -5.5, 0, 'cream stone', 'closed-stepped-clock-podium')
    front.box(0, 33.68, 7.34, .24, 5.80, -2.62,
              'carved pale stone', 'clock-base-crowning-belt')
    zc, r = P['clock_center_design_m'], P['clock_radius_design_m']
    circle = Point(0, zc).buffer(r, quad_segs=16 if lod else 32)
    ring = Point(0, zc).buffer(r+.12, quad_segs=16 if lod else 32).difference(circle)
    front.prism(circle, .015, .060, 'clock dial', 'round-clock-dial')
    front.prism(ring, .010, .12, 'clock iron', 'clock-outer-rim')
    for k in range(12):
        a = k*math.tau/12
        front.line((.84*math.sin(a), zc+.84*math.cos(a), .10),
                    (.99*math.sin(a), zc+.99*math.cos(a), .10),
                    .026, 'clock iron', 6, 'illustrative-clock-marker')
    for a, length in [(-math.pi/3, .57), (math.pi/3, .83)]:
        front.line((0, zc, .13), (length*math.sin(a), zc+length*math.cos(a), .13),
                   .034, 'clock iron', 6, 'illustrative-10-10-clock-hand')
    front.prism(Point(0, zc).buffer(.075, quad_segs=8), .10, .17, 'clock iron', 'clock-center')
    tower_openings = []
    stage_column_count = []
    for stage, lo, hi, width, chamfer, radius in [
            (1, 33.8, 38.3, 6.40, 0., .25),
            (2, 38.3, 42.1, 4.75, .55, .19)]:
        tp = tower_plan(width, chamfer)
        fs = facade_ring(b, tp, f'moxing-square-stage-{stage}')
        columns = 0
        for j, f in enumerate(fs):
            holes = []
            if f.length > 2.5:
                w = 2.5 if stage == 1 else 1.74
                shape = opening(0, lo+.35, w, hi-lo-1.03, arch=w*.44,
                                segments=12 if lod else 24)
                holes.append(shape)
                f.prism(shape.buffer(.17, join_style=2).difference(shape), .01, .17,
                        'carved pale stone', 'arched-through-opening-surround')
                tower_openings.append({'stage': stage, 'normal_enu': f.n.tolist(),
                                       'center_enu': f.point(0, lo+(hi-lo)/2).tolist()})
                for u in [-f.length/2+.42, f.length/2-.42]:
                    column(b, f.point(u, 0, .23)[:2], lo+.20, hi-.48, radius,
                           lod, f'moxing-stage-{stage}-external-column')
                    columns += 1
                railing(f, -w/2+.08, w/2-.08, lo+.35, -.03, lod,
                        f'moxing-stage-{stage}-opening-railing')
            closed_wall(f, fs[j-1], fs[(j+1) % len(fs)], lo+.12, hi-.24,
                        holes, 'cream stone', .31)
        b.plan_prism(tp.buffer(.26, join_style=2), lo, lo+.15,
                     'carved pale stone', f'moxing-stage-{stage}-floor')
        b.plan_prism(tp.buffer(.34, join_style=2), hi-.24, hi,
                     'carved pale stone', f'moxing-stage-{stage}-roof')
        cornice(b, tp, hi-.10, .37, lod, f'moxing-stage-{stage}-dentil-cornice', True)
        stage_column_count.append(columns)
    b.lathe((tx, ty), [(42.1, 1.85), (42.28, 1.92), (42.39, 1.72)],
            'carved pale stone', 16 if lod else 32, 'moxing-circular-lantern-floor')
    for a in np.linspace(0, math.tau, 8, endpoint=False):
        column(b, (tx+1.52*math.cos(a), ty+1.52*math.sin(a)), 42.37, 45.91,
               .18, lod, 'moxing-open-round-pavilion-column')
    b.lathe((tx, ty), [(45.88, 1.77), (46.00, 2.04), (46.16, 2.04),
                       (46.27, 1.85)], 'carved pale stone', 16 if lod else 32,
            'moxing-round-pavilion-entablature')
    cap = [(46.16, 1.85)]
    for a in np.linspace(.12, math.pi/2-.10, 7 if lod else 13):
        cap.append((46.16+1.14*math.sin(a), 1.85*math.cos(a)))
    cap.append((47.30, .09))
    b.lathe((tx, ty), cap, 'carved pale stone', 16 if lod else 32,
            'moxing-low-curved-cap')
    b.lathe((tx, ty), [(47.25, .12), (51.25, .035), (51.30, .018)],
            'iron', 8, 'moxing-thin-pole-design-top-51-3')
    # Pole crossbar stays below the authored top; no measured antenna claim.
    b.tube([(tx-.62, ty, 51.08), (tx+.62, ty, 51.08)], .025, 'iron', 6,
           'moxing-pole-small-crossbar')
    if not lod:
        for z in np.arange(47.6, 50.95, .21):
            b.tube([(tx-.12, ty, float(z)), (tx+.12, ty, float(z))], .018,
                   'iron', 5, 'estimated-pole-rung')
    # Preserve each closed author solid; normalize globally reversed winding.
    for part in b.parts:
        vertices = np.array(part['vertices'])
        triangles = np.array(part['triangles'])
        volume = np.einsum('ij,ij->i', vertices[triangles[:, 0]],
                           np.cross(vertices[triangles[:, 1]], vertices[triangles[:, 2]])).sum()/6
        assert abs(volume) > 1e-10, part['label']
        if volume < 0:
            part['triangles'] = [(int(a), int(c), int(bb)) for a, bb, c in triangles]
    metadata = {
        'id': ID, 'name': 'Sincere Company historic exterior / 先施公司与摩星塔',
        'status': 'standalone-exterior-candidate-not-geographically-registered',
        'all_plan_dimensions_estimated': True, 'height_endpoints_verified': False,
        'documented_main_building_height': 'more than 30 metres; no exact endpoint verified',
        'documented_floor_history': 'original 5, later 2 added, 7 total; design window layers unmeasured',
        'documented_street_lengths_m': {'Nanjing_Road': 66, 'Zhejiang_Road': 61},
        'design_plan_m': [100, 68], 'frozen_map_coarse_bounds_approx_m': [106, 75],
        'scope_conflict_unresolved': '66/61 m street elevations, frozen map 106/75 m and photographed western extension scope not reconciled; 100/68 m is an author design',
        'northeast_lower_wing': 'photo-guided true roof step; boundaries and 21.8 m datum estimated',
        'main_roof_design_m': 30.6, 'tower_top_design_m': 51.3,
        'tower_total_height_verified': False, 'tower_name': 'Moxing Tower / 摩星塔',
        'tower_is_not_yongan_qiyunge': True,
        'clock_time_illustrative': '10:10',
        'photo_references': ['Pyzhou 2010-05-07 GFDL 1.2+',
                             'Livelikerw 2013-12-19 CC BY-SA 3.0',
                             'Chainwit. 2024-04-24 CC BY 4.0'],
        'photos_embedded': False, 'map_replacement': False,
        'rear_elevations_and_roof_junctions_estimated': True,
        'commercial_advertising_and_neighboring_buildings_included': False,
        'copyright': 'Original code and geometry MIT; reference photographs not embedded',
    }
    features = {
        'parameters': P, 'author_parts': len(b.parts), 'window_openings': opening_count,
        'ground_arcade_openings': arcade_holes, 'ground_arcade_opening_count': len(arcade_holes),
        'primary_street_pier_min_window_clearance_design_m': min(primary_pier_clearances),
        'primary_street_pier_width_and_projection_checked': True,
        'balcony_count_design_estimate': balcony_count,
        'southeast_cross_storey_columns': 2, 'southeast_semicircular_pediment': True,
        'southwest_corner_is_broad_un_towered_chamfer': True,
        'tower_square_stage_through_arches': tower_openings,
        'tower_square_stage_column_counts_design': stage_column_count,
        'tower_round_stage_column_count_design': 8,
        'tower_open_stage_count': 3, 'clock_face_count': 1,
        'all_decorative_profiles_simplified_and_unmeasured': True,
        'northeast_upper_footprint_cutout_xy': P['northeast_low_wing_authored_xy'],
        'full_roof_and_rear_are_estimated_without_invented_courtyard': True,
    }
    return b, metadata, features


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--lod', action='store_true')
    args = parser.parse_args()
    builder, metadata, features = build(args.lod)
    args.out.mkdir(parents=True, exist_ok=True)
    stem = ID+('-lod' if args.lod else '-raw')
    result = builder.save(args.out/(stem+'.glb'), metadata)
    (args.out/(stem+'-features.json')).write_text(json.dumps(features, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'part_summary'}))


if __name__ == '__main__':
    main()
