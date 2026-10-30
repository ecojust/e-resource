"""Photo-informed Pacific Hotel / Hua'an Building main historic exterior. MIT.

The 2013-12-05 Livelikerw photograph was visually inspected. No photo pixels are
embedded. All plan dimensions, floor datums, bay counts, ornament and unseen
faces are author estimates. The documented 工-shaped plan is interpreted as an
H, not as an extrusion of the frozen map's coarse rectangular feature.
"""
import argparse
import json
import math
from pathlib import Path

import numpy as np
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

from common.photo_architecture import Builder, Facade, facade_ring, opening

ID = 'huangpu-pacific-hotel'
PALETTE = {
    'pale limestone': {'color': [.67, .65, .59], 'roughness': .86},
    'rusticated limestone': {'color': [.61, .60, .55], 'roughness': .89},
    'carved pale stone': {'color': [.73, .71, .65], 'roughness': .81},
    'granite plinth': {'color': [.29, .28, .26], 'roughness': .84},
    'portico granite': {'color': [.43, .35, .29], 'roughness': .83},
    'roof': {'color': [.37, .38, .36], 'roughness': .94},
    'recessed glass': {'color': [.105, .15, .17], 'roughness': .27, 'metallic': .18},
    'bronze window frame': {'color': [.22, .20, .16], 'roughness': .63, 'metallic': .15},
    'dark spandrel': {'color': [.19, .23, .23], 'roughness': .79},
    'red bronze trim': {'color': [.28, .13, .095], 'roughness': .66, 'metallic': .2},
    'clock dial': {'color': [.54, .65, .66], 'roughness': .55},
    'clock iron': {'color': [.075, .10, .10], 'roughness': .61, 'metallic': .35},
    'aged gold dome': {'color': [.52, .44, .24], 'roughness': .51, 'metallic': .58},
    'cupola red': {'color': [.30, .14, .12], 'roughness': .74},
}
P = {
    'all_plan_dimensions_estimated': True,
    'plan_description': '工/H interpretation; no surveyed historical footprint',
    'plan_width_m': 42., 'plan_depth_m': 36.,
    'left_wing_xy': [-21., -18., -10., 18.],
    'right_wing_xy': [10., -18., 21., 18.],
    'connector_xy': [-10., -14., 10., 12.],
    'front_central_recess_m': 4., 'rear_central_recess_m': 6.,
    'design_layer_datums_m': [0., 4.2, 7.5, 11.1, 14.7, 18.3, 21.9, 25.5, 29.16, 33.16],
    'central_body_roof_m': 29.16, 'wing_attic_top_m': 33.16,
    'main_tower_center_xy': [0., -11.],
    'main_tower_base_m': 29.16, 'main_tower_top_m': 38.16,
    'tower_design_height_m': 9.,
    'tower_height_equation_is_interpretation': True,
    'tower_lower_column_count_estimated': 8,
    'tower_open_lantern_column_count_estimated': 8,
    'lower_clock_center_m': 33.4, 'clock_radius_m_estimated': .81,
    'front_wing_bays_estimated': 3, 'front_central_bays_estimated': 7,
    'balustrade_balconies': 3,
    'modern_northern_hotel_building_included': False,
}


def wall(f, prev, nxt, lo, hi, holes, material, thickness=.46):
    """Close each wall with mitred ends, including the concave H-plan corners."""
    t, n = f.t[:2], f.n[:2]
    def inside(pt, other_n):
        return np.linalg.solve(np.array([n, other_n]),
                               np.array([n @ pt-thickness, other_n @ pt-thickness]))
    left = (inside(f.a[:2], prev.n[:2])-f.a[:2]) @ t / thickness
    right = (inside(f.b[:2], nxt.n[:2])-f.b[:2]) @ t / thickness
    def mapper(u, z, d):
        shift = left+(u+f.length/2)/f.length*(right-left)
        return f.point(u-d*shift, z, d)
    surface = box(-f.length/2, lo, f.length/2, hi)
    if holes:
        surface = surface.difference(unary_union(holes))
    f.builder.prism(surface, -thickness, 0, mapper, material,
                    f.label+'/closed-mitred-wall')


def window(f, shape, lod, label, columns=2, rows=2, sill=True):
    if lod:
        f.prism(shape.buffer(-.065, join_style=2), -.34, -.31,
                'recessed glass', label+'-glass')
        x0, z0, x1, _ = shape.bounds
        # Identical protruding sill bounds in both variants.
        if sill:
            f.box((x0+x1)/2, z0-.07, x1-x0+.30, .14, .60, .10,
                  'carved pale stone', label+'-sill')
    elif sill:
        f.window(shape, columns, rows, 'bronze window frame', False,
                 'recessed glass', label)
    else:
        # A strip's horizontal members and sill are supplied once below.
        f.prism(shape.buffer(-.09, join_style=2), -.34, -.32,
                'recessed glass', label+'-glass')
        inner = shape.buffer(-.09, join_style=2)
        f.prism(shape.buffer(-.025, join_style=2).difference(inner),
                -.27, -.16, 'bronze window frame', label+'-frame')


def cornice(builder, plan, z, projection, lod, label, dentils=True):
    """Three continuous mitred rings preserve deep, shadowed photo silhouette."""
    for dz, height, reach in [(-.25, .16, projection*.60),
                              (-.07, .20, projection),
                              (.10, .14, projection*.92)]:
        ring = plan.buffer(reach, join_style=2).difference(plan.buffer(-.12, join_style=2))
        builder.plan_prism(ring, z+dz-height/2, z+dz+height/2,
                           'carved pale stone', label+'-profile')
    if dentils:
        for f in facade_ring(builder, plan, label):
            # Main and LOD retain dentil scale; LOD drops alternate teeth.
            for u in np.arange(-f.length/2+.24, f.length/2-.14, .68 if lod else .34):
                f.box(float(u), z-.43, .15, .22, projection*.52, projection*.28,
                      'carved pale stone', 'dentil')


def column(builder, xy, lo, hi, radius, lod, label, material='carved pale stone'):
    h = hi-lo
    profile = [(lo, radius*1.30), (lo+.07*h, radius*1.30),
               (lo+.11*h, radius), (hi-.15*h, radius*.91),
               (hi-.11*h, radius*1.19), (hi-.06*h, radius*1.40),
               (hi, radius*1.40)]
    builder.lathe(tuple(xy), profile, material, 10 if lod else 20, label)


def balcony(builder, cx, ywall, width, z, lod, label):
    front = ywall-1.22
    builder.box((cx, ywall-.55, z), (width+.36, 1.5, .22),
                'carved pale stone', label=label+'-projecting-slab')
    builder.box((cx, front, z+.91), (width+.36, .30, .18),
                'carved pale stone', label=label+'-top-rail')
    builder.box((cx, front, z+.20), (width+.24, .24, .22),
                'carved pale stone', label=label+'-bottom-rail')
    for x in np.linspace(cx-width/2+.18, cx+width/2-.18, 6 if lod else 10):
        builder.lathe((float(x), front),
                      [(z+.29, .065), (z+.41, .105), (z+.60, .08),
                       (z+.75, .052), (z+.82, .075)],
                      'carved pale stone', 8 if lod else 12, label+'-baluster')
    for x in [cx-width/2, cx+width/2]:
        builder.box((x, front, z+.53), (.22, .30, .76),
                    'carved pale stone', label=label+'-end-post')
        builder.box((x, (front+ywall)/2, z+.91), (.24, ywall-front, .18),
                    'carved pale stone', label=label+'-return-rail')
        builder.box((x, (front+ywall)/2, z+.46), (.15, ywall-front, .58),
                    'pale limestone', label=label+'-solid-side-return')
        # Closed tapered consoles; silhouettes survive simplification.
        poly = Polygon([(ywall-.99, z-.11), (ywall+.10, z-.11),
                        (ywall+.10, z-1.0), (ywall-.20, z-.92)])
        builder.prism(poly, x-.12, x+.12, lambda y, z_, d: (d, y, z_),
                      'carved pale stone', label+'-console')


def build(lod=False):
    b = Builder(PALETTE)
    left, right, connector = (box(*P[k]) for k in
                              ['left_wing_xy', 'right_wing_xy', 'connector_xy'])
    plan = unary_union([left, right, connector])
    edges = facade_ring(b, plan, 'historic-H-body')
    count, strips, front_bays = 0, 0, []
    main_front = []
    for index, f in enumerate(edges):
        is_front = f.n[1] < -.9 and f.length > 8
        if is_front:
            main_front.append(f)
        n = (3 if f.length < 12 else 7) if is_front else max(1, int((f.length-1.2)/3.0))
        margin = 1.1 if f.length > 6 else .65
        pitch = (f.length-2*margin)/n
        centers = [-f.length/2+margin+(k+.5)*pitch for k in range(n)]
        w = min(2.25 if is_front and f.length < 12 else 1.8, pitch-.58)
        if is_front:
            front_bays.append({'center_xy': f.center[:2].tolist(), 'count': n})
        prev, nxt = edges[index-1], edges[(index+1) % len(edges)]
        for low, high in [(0., 4.2), (4.2, 7.5)]:
            holes = []
            for u in centers:
                shape = opening(u, low+.45, w, high-low-.85)
                holes.append(shape)
                window(f, shape, lod, 'granite-base-opening', rows=2)
                count += 1
            wall(f, prev, nxt, low, high, holes, 'granite plinth')
        # Five floor windows form one tall opening bordered by stone piers.
        # Dark real solids, recessed glazing and framing divide this opening.
        holes = []
        for u in centers:
            shape = opening(u, 7.78, w, 16.92)
            holes.append(shape)
            for level, (lo, hi) in enumerate(zip(P['design_layer_datums_m'][2:7],
                                                P['design_layer_datums_m'][3:8])):
                bottom, top = max(7.78, lo+.12), min(24.70, hi-.48)
                pane = opening(u, bottom, w, top-bottom)
                window(f, pane, lod, 'connected-tall-window', rows=2, sill=False)
                count += 1
                if level < 4:
                    f.box(u, hi-.22, w-.07, .48, .15, -.22,
                          'dark spandrel', 'recessed-dark-spandrel')
                if not lod:
                    f.box(u, bottom+.10, w-.03, .09, .11, -.12,
                          'red bronze trim', 'thin-window-transom')
                    f.box(u, (bottom+top)/2, .065, top-bottom, .12, -.16,
                          'bronze window frame', 'window-center-mullion')
                    f.box(u, top-.73, w-.04, .065, .12, -.16,
                          'bronze window frame', 'window-upper-transom')
            f.box(u, 7.71, w+.30, .14, .60, .10,
                  'carved pale stone', 'tall-strip-sill')
            for uu in [u-w/2-.17, u+w/2+.17]:
                f.box(uu, 16.30, .20, 17.44, .22, .055,
                      'carved pale stone', 'long-vertical-stone-pier-edge')
            f.box(u, 24.84, w+.40, .19, .32, .10,
                  'carved pale stone', 'tall-strip-lintel')
            if is_front and not lod:
                # Simplified shield relief between the top window and balcony.
                su = u-w/2-.17
                shield = Polygon([(su-.11, 23.33), (su+.11, 23.33),
                                  (su+.10, 22.99), (su, 22.83), (su-.10, 22.99)])
                f.prism(shield, .02, .17, 'carved pale stone', 'estimated-shield-relief')
            strips += 1
        wall(f, prev, nxt, 7.5, 25.5, holes, 'pale limestone')
        # Corner rustication: visible horizontal recessed joints, not texture.
        for side in [-1, 1]:
            quoin_width = min(1.15, max(.40, margin+(pitch-w)/2-.13))
            u = side*(f.length/2-quoin_width/2)
            for z in np.arange(7.76, 25.18, .58):
                f.box(u, float(z), quoin_width, .49, .24, .065,
                      'rusticated limestone', 'horizontal-rusticated-corner-block')
        upper_holes = []
        for u in centers:
            shape = opening(u, 26.02, min(w+ .15, pitch-.40), 2.45)
            upper_holes.append(shape)
            window(f, shape, lod, 'upper-column-storey-window', rows=2)
            count += 1
            if is_front:
                for offset in [-w/2-.25, w/2+.25]:
                    xy = f.point(u+offset, 0, .20)[:2]
                    column(b, xy, 25.91, 28.67, .20, lod,
                           'photo-guided-upper-engaged-column')
        wall(f, prev, nxt, 25.5, 29.16, upper_holes, 'pale limestone')
        f.beam(28.78, .20, .34, 'carved pale stone', label='upper-column-entablature')
    # Interior floor volumes and roofs follow the H outline, preserving recesses.
    for z in P['design_layer_datums_m'][1:9]:
        b.plan_prism(plan.buffer(-.48, join_style=2), z-.16, z,
                     'roof', 'estimated-H-floor-slab')
    b.plan_prism(plan, 0, .18, 'granite plinth', 'H-ground-plinth')
    cornice(b, plan, 7.48, .38, lod, 'base-to-main-cornice', False)
    cornice(b, plan, 25.45, .82, lod, 'deep-main-dentil-cornice')
    cornice(b, plan, 29.05, .34, lod, 'central-roof-cornice', False)
    # Only the two projecting wings carry the small-window attic layer.
    attic_count = 0
    for side, wing in [('left', left), ('right', right)]:
        es = facade_ring(b, wing, side+'-wing-attic')
        for j, f in enumerate(es):
            n = 3 if f.length < 12 else 9
            pitch = (f.length-2.4)/n
            holes = []
            for k in range(n):
                u = -f.length/2+1.2+(k+.5)*pitch
                shape = opening(u, 30.32, min(1.35, pitch-.60), 1.73)
                holes.append(shape)
                window(f, shape, lod, 'small-attic-window', rows=1)
                count += 1
                attic_count += 1
            wall(f, es[j-1], es[(j+1) % len(es)], 29.16, 33.16, holes,
                 'pale limestone')
            f.beam(29.39, .18, .20, 'carved pale stone', label='attic-lower-belt')
        b.plan_prism(wing.buffer(-.48, join_style=2), 32.94, 33.16,
                     'roof', side+'-attic-roof')
        cornice(b, wing, 32.96, .49, lod, side+'-attic-crowning-cornice', False)
    for cx, y, width in [(-15.5, -18., 3.), (0., -14., 3.4), (15.5, -18., 3.)]:
        balcony(b, cx, y, width, 22.45, lod, 'photo-guided-balustrade-balcony')
    # The low street entrance portico extends from the recessed central wall.
    b.box((0, -15.50, .13), (19.4, 3.9, .26), 'granite plinth', label='portico-step')
    b.box((0, -15.53, 4.10), (19.8, 3.96, .38),
          'portico granite', label='entrance-portico-entablature')
    b.box((0, -15.53, 4.35), (20.0, 4.04, .16),
          'carved pale stone', label='entrance-portico-cap')
    for x in [-8.8, -5.9, -2.95, 2.95, 5.9, 8.8]:
        column(b, (x, -17.07), .26, 3.91, .37, lod,
               'entrance-portico-column', 'portico granite')
        if not lod:
            for a in np.linspace(0, math.tau, 16, endpoint=False):
                b.tube([(x+.345*math.cos(a), -17.07+.345*math.sin(a), .75),
                        (x+.322*math.cos(a), -17.07+.322*math.sin(a), 3.3)],
                       .018, 'granite plinth', 5, 'estimated-portico-flute')
    # Principal roof clock tower: lower engaged columns, clock, open lantern.
    tx, ty = P['main_tower_center_xy']
    base = 29.16
    b.lathe((tx, ty), [(base, 2.70), (29.38, 2.70), (29.49, 2.39)],
            'carved pale stone', 8, 'clock-tower-octagonal-podium')
    b.lathe((tx, ty), [(29.46, 1.67), (32.56, 1.67)],
            'rusticated limestone', 8, 'clock-tower-closed-lower-core')
    for a in np.linspace(0, math.tau, 8, endpoint=False):
        xy = (tx+2.05*math.cos(a), ty+2.05*math.sin(a))
        column(b, xy, 29.53, 32.40, .23, lod,
               'clock-tower-lower-engaged-column')
    b.lathe((tx, ty), [(32.38, 2.37), (32.57, 2.53), (32.74, 2.53),
                       (32.88, 2.32)], 'carved pale stone', 16 if lod else 32,
            'lower-tower-projecting-entablature')
    b.lathe((tx, ty), [(32.78, 1.72), (34.38, 1.72)],
            'pale limestone', 16 if lod else 32, 'clock-drum')
    clock = Facade(b, (-2.15, ty-2.34), (2.15, ty-2.34), 'front-tower-clock')
    zc, radius = P['lower_clock_center_m'], P['clock_radius_m_estimated']
    circle = Point(0, zc).buffer(radius, quad_segs=16 if lod else 32)
    rim = Point(0, zc).buffer(radius+.16, quad_segs=16 if lod else 32).difference(circle)
    clock.prism(circle, -.04, .035, 'clock dial', 'blue-grey-round-dial')
    clock.prism(rim, -.08, .16, 'carved pale stone', 'raised-round-stone-frame')
    arch = Point(0, zc).buffer(radius+.31, quad_segs=16 if lod else 32)
    arch = arch.intersection(box(-2, zc+.13, 2, zc+1.2)).difference(
        Point(0, zc).buffer(radius+.20, quad_segs=16 if lod else 32))
    clock.prism(arch, -.05, .13, 'carved pale stone', 'clock-arched-crown')
    for k in range(12):
        a = k*math.tau/12
        clock.line((.61*math.sin(a), zc+.61*math.cos(a), .09),
                   (.73*math.sin(a), zc+.73*math.cos(a), .09),
                   .021, 'clock iron', 6, 'illustrative-hour-marker')
    for a, length in [(-math.pi/3, .46), (math.pi/3, .64)]:
        clock.line((0, zc, .115), (length*math.sin(a), zc+length*math.cos(a), .115),
                   .027, 'clock iron', 6 if lod else 8, 'illustrative-10-10-hand')
    clock.prism(Point(0, zc).buffer(.065, quad_segs=8), .10, .15,
                'clock iron', 'clock-hub')
    # Small shoulder ornaments are estimates from the photographic silhouette.
    for x in [-2.32, 2.32]:
        b.lathe((x, ty), [(29.43, .33), (29.63, .39), (30.16, .22),
                          (30.31, .25), (30.48, .12)],
                'carved pale stone', 8 if lod else 12, 'tower-shoulder-finial')
    b.lathe((tx, ty), [(34.30, 1.62), (34.47, 1.85), (34.62, 1.78)],
            'carved pale stone', 16 if lod else 32, 'open-lantern-floor')
    for a in np.linspace(0, math.tau, 8, endpoint=False):
        xy = (tx+1.34*math.cos(a), ty+1.34*math.sin(a))
        column(b, xy, 34.61, 36.26, .16, lod, 'open-upper-lantern-column')
    b.lathe((tx, ty), [(36.20, 1.65), (36.31, 1.82), (36.45, 1.82),
                       (36.54, 1.63)], 'carved pale stone', 16 if lod else 32,
            'upper-lantern-ring-entablature')
    # Hemispherical gold/bronze cap, small red octagonal cupola, final fixed top.
    dome = [(36.51, 1.62)]
    for theta in np.linspace(.08, math.pi/2-.08, 7 if lod else 15):
        dome.append((36.51+1.04*math.sin(theta), 1.62*math.cos(theta)))
    dome.append((37.55, .11))
    b.lathe((tx, ty), dome, 'aged gold dome', 16 if lod else 40,
            'gold-bronze-tower-dome')
    b.lathe((tx, ty), [(37.49, .23), (37.57, .26), (37.92, .26),
                       (38.01, .14)], 'cupola red', 8, 'small-red-octagonal-cupola')
    if not lod:
        for a in np.linspace(0, math.tau, 8, endpoint=False):
            b.box((tx+.245*math.cos(a), ty+.245*math.sin(a), 37.75),
                  (.055, .055, .25), 'carved pale stone', label='cupola-corner-moulding')
    b.lathe((tx, ty), [(38.00, .115), (38.10, .09), (38.16, .018)],
            'aged gold dome', 8, 'small-finial-at-design-top-datum')
    # The helper can emit a globally reversed tube cap orientation; normalize
    # each closed author part, preserving actual openings and semantic labels.
    for part in b.parts:
        v, triangles = np.array(part['vertices']), np.array(part['triangles'])
        volume = np.einsum('ij,ij->i', v[triangles[:, 0]],
                           np.cross(v[triangles[:, 1]], v[triangles[:, 2]])).sum()/6
        assert abs(volume) > 1e-10, part['label']
        if volume < 0:
            part['triangles'] = [(int(a), int(c), int(bb)) for a, bb, c in triangles]
    meta = {
        'id': ID, 'name': 'Pacific Hotel / Hua\u2019an Building main historical exterior',
        'status': 'standalone-exterior-candidate-not-geographically-registered',
        'source_photo_date': '2013-12-05', 'source_photo_author': 'Livelikerw',
        'source_photo_license': 'CC BY-SA 3.0; reference only, pixels not embedded',
        'photos_embedded': False, 'map_replacement': False,
        'all_plan_dimensions_estimated': True, 'height_endpoints_verified': False,
        'official_building_height_reference_m': 38.16,
        'official_roof_clock_tower_reference_m': 9.,
        'tower_base_plus_height_equation_is_interpretation': True,
        'height_floor_sources_unresolved': True,
        'floor_history_reference': 'Sources differ: original 8; ninth added before 1940; now 10. These counts and periods have not been independently reconciled.',
        'design_layer_counts': {'side_wings': 9, 'central_connector': 8},
        'chosen_top_design_datum_m': 38.16,
        'conflicting_gazetteer_references': ['38.16 m / 9 floors', '36.16 m / 8 floors'],
        'other_height_scope_reference_m': 40.1,
        'other_height_scope_reference_is_design_input': False,
        'height_scope_note': 'Chosen 38.16 m candidate top; 36.16 m and 40.1 m references have unresolved endpoint or scope differences and were not averaged or fitted.',
        'modern_northern_hotel_building_included': False,
        'neighboring_towers_included': False, 'modern_sign_letters_modeled': False,
        'copyright': 'Original code and geometry MIT; reference photo not embedded',
    }
    features = {
        'parameters': P, 'author_parts': len(b.parts),
        'estimated_window_openings': count, 'connected_vertical_window_strips': strips,
        'attic_window_openings': attic_count, 'front_bay_estimates': front_bays,
        'balustrade_balcony_count': 3, 'clock_face_count': 1,
        'clock_time_illustrative': '10:10', 'upper_lantern_is_open': True,
        'central_ninth_layer_omitted': True,
        'main_cornice_height_design_m': 25.45,
        'roof_clock_tower_two_stages': ['lower engaged-column core + clock', 'open eight-column lantern'],
        'unseen_faces_and_roof_junctions_estimated': True,
        'all_decorative_profiles_simplified_and_unmeasured': True,
    }
    return b, meta, features


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--lod', action='store_true')
    args = parser.parse_args()
    b, metadata, features = build(args.lod)
    args.out.mkdir(parents=True, exist_ok=True)
    stem = ID+('-lod' if args.lod else '-raw')
    result = b.save(args.out/(stem+'.glb'), metadata)
    (args.out/(stem+'-features.json')).write_text(json.dumps(features, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'part_summary'}))


if __name__ == '__main__':
    main()
