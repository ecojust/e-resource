#!/usr/bin/env python3
"""Detailed Ba Jin main house: original photo-informed exterior, estimated metric fit."""
import json, hashlib, math, sys
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE / 'common'))
from photo_architecture import Builder, Facade, opening

D = json.loads((HERE / 'design-input.json').read_text())
W, DEPTH = D['frame']['width_m'], D['frame']['depth_m']
H = D['dimensions_C']
PAL = {
    'spatial pebbledash base': {'color': [.39, .36, .31], 'roughness': .95},
    'unobserved side surface': {'color': [.43, .42, .39], 'roughness': .95},
    'estimated plain tile roof': {'color': [.24, .20, .17], 'roughness': .9},
    'white trim': {'color': [.82, .81, .75], 'roughness': .83},
    'green painted frame': {'color': [.045, .16, .13], 'roughness': .75},
    'spatial glass': {'color': [.18, .26, .27], 'roughness': .38},
    'recess backing': {'color': [.15, .14, .12], 'roughness': .95},
    'stone plinth': {'color': [.55, .54, .50], 'roughness': .92},
}


def construct():
    roof_case, height_case = "B", "C"
    from build_palette import palette
    b = Builder(palette(PAL))
    half = W / 2
    y0, y1 = -DEPTH / 2, DEPTH / 2
    roofhalf = half + H['roof_overhang']
    bayhalf = H['entry_bay_width'] / 2
    northfront = y1 + H['entry_bay_projection']
    transition_start = y1 - D['roof_cases'][roof_case]['north_transition_depth_m']

    from roof_planar import prepare_roof, add_roof
    roof = prepare_roof(W, DEPTH, H)
    south_profile = roof['south_profile']
    roof_z = roof['height']
    north_profile = lambda x: roof_z(x,y1)

    b.features=[]
    from facade_details import window as detailed_window, feature, extras
    def window(f,shape,label,cols=2,rows=3,sill=True):
        return detailed_window(b,f,shape,label,cols,rows,sill)

    # Garden elevation uses its actual observed 4-bay rhythm. These are real
    # apertures, with simple separate frame/glass, not painted rectangles.
    south = Facade(b, (-half, y0), (half, y0), 'south-garden')
    garden_holes = []
    xcs = [-4.65, -1.55, 1.55, 4.65]
    for i, x in enumerate(xcs):
        width = 2.55 if i in (0, 3) else 2.28
        garden_holes.append((opening(x, .30, width, 2.85), f'ground-bay-{i+1}', 3, 3))
        garden_holes.append((opening(x, 4.75, 2.48, 1.82), f'upper-bay-{i+1}', 4, 3))
    attic = opening(0., 8.47, 5.03, 1.98, arch=1.72, segments=24)
    garden_holes.append((attic, 'wide-arched-attic', 6, 3))
    vents = [opening(x, 7.88, .145, .29) for x in np.linspace(-2.48, 2.48, 10)]
    outline = Polygon([(-half, .30), (half, .30), (half, H['garden_eave']),
                       (H['roof_knee_x'], H['garden_roof_knee']), (0., H['garden_ridge']),
                       (-H['roof_knee_x'], H['garden_roof_knee']), (-half, H['garden_eave'])])
    south.wall(.30, H['garden_ridge'], holes=[s[0] for s in garden_holes] + vents,
               thickness=.28, material='spatial pebbledash base', outline=outline)
    for shape, label, cols, rows in garden_holes:
        window(south, shape, label, cols, rows)
    for i, shape in enumerate(vents):
        south.prism(shape, -.32, -.30, 'recess backing', f'documented-vent-{i+1}-back')
    # Unobserved sides have no invented window rows. Their wall/roof junction
    # is a pressure-test hypothesis, explicitly distinct from visible fronts.
    for x, reverse, label in [(-half, True, 'west-unobserved'), (half, False, 'east-unobserved')]:
        f = Facade(b, (x, y1-.28 if reverse else y0+.28), (x, y0+.28 if reverse else y1-.28), label)
        f.wall(.30, H['garden_eave'], thickness=.28, material='unobserved side surface')

    # North facade: stepped central bay with separately recessed portal.
    # The top is not a copy of the photographed southern gable.
    north = Facade(b, (half, y1), (-half, y1), 'north-shoulders')
    topxs = [-half,-H['roof_knee_x'],-bayhalf,0.,bayhalf,H['roof_knee_x'],half]
    north_outline = Polygon([(-half,.30),(half,.30)]+[(x,roof_z(x,y1)) for x in reversed(topxs)])
    north.prism(north_outline.difference(box(-bayhalf, .29, bayhalf, H['garden_ridge']+.01)),
                -.28, 0., 'spatial pebbledash base', 'unmeasured-shoulders')
    entry = Facade(b, (bayhalf, northfront), (-bayhalf, northfront), 'north-entry-bay')
    arch = opening(0., .30, H['porch_arch_width'], H['porch_arch_top']-.30,
                   arch=1.74, segments=28)
    entry_holes = [
        (opening(-2.95, 1.12, 1.0, 1.45), 'lower-left-shuttered-window', 2, 3),
        (opening(2.95, 1.12, 1.0, 1.45), 'lower-right-shuttered-window', 2, 3),
        (opening(0., 5.16, 1.82, 2.02), 'central-upper-window', 1, 2),
        (opening(-2.45, 8.12, 1.04, 1.05), 'left-attic-window', 2, 2),
        (opening(0., 8.05, 2.18, 1.11), 'middle-attic-window', 2, 1),
        (opening(2.45, 8.12, 1.04, 1.05), 'right-attic-window', 2, 2),
    ]
    entry.wall(.30, H['entry_eave'], holes=[arch]+[r[0] for r in entry_holes],
               thickness=.28, material='spatial pebbledash base')
    for shape, label, cols, rows in entry_holes:
        window(entry, shape, label, cols, rows)
    # Stone-coloured arch ring, lowered side parapets and actual inner room.
    ring = arch.buffer(.22, join_style=2).difference(arch).intersection(box(-3, D['north_entry_revision']['arch_leg_bottom_m'], 3, 4.2))
    entry.prism(ring, -.015, .065, 'white trim', 'arch-surround')

    entry.box(0, 4.30, H['entry_bay_width']+.05, .13, .18, .03, 'white trim', 'north-storey-stringcourse')
    for x in (-1.52, 1.52):
        rev=D['north_entry_revision']
        entry.box(math.copysign((rev['low_wall_inner_u_m']+rev['low_wall_outer_u_m'])/2,x),
                  .77,rev['low_wall_outer_u_m']-rev['low_wall_inner_u_m'],.94,.28,-.11,
                  'spatial pebbledash base','portal-low-side-wall')
        rev=D['north_entry_revision']
        entry.box(math.copysign((rev['coping_inner_u_m']+rev['coping_outer_u_m'])/2,x),
                  (rev['coping_bottom_m']+rev['coping_top_m'])/2,
                  rev['coping_outer_u_m']-rev['coping_inner_u_m'],
                  rev['coping_top_m']-rev['coping_bottom_m'],.39,.00,
                  'white trim','portal-low-side-coping')
    backface = Facade(b, (bayhalf, northfront-H['porch_recess']), (-bayhalf, northfront-H['porch_recess']), 'portal-inner-back')
    innerdoor = opening(0, .30, 1.48, 2.55)
    innerwindows = [opening(x, 1.28, 1.17, 1.28) for x in (-1.47,1.47)]
    backface.prism(box(-2.15,.30,2.15,3.68).difference(unary_union([innerdoor]+innerwindows)),
                   -.16,0,'spatial pebbledash base','actual-recess-backwall')
    window(backface, innerdoor, 'entry-door', 3, 4, False)
    backface.prism(box(-.66,.34,.66,1.08),-.14,-.06,'green painted frame','entry-door-lower-panel')
    for i, win in enumerate(innerwindows):
        window(backface, win, f'porch-back-window-{i}', 2, 3, False)
    for x in (-2.13,2.13):
        b.box((x,northfront-H['porch_recess']/2-.04,1.95),(.18,H['porch_recess']-.08,3.30),
              'spatial pebbledash base',label='porch-estimated-return')
    b.box((0,northfront-H['porch_recess']/2-.04,3.64),(4.15,H['porch_recess']-.08,.12),
          'white trim',label='porch-estimated-ceiling')
    # The projected bay is only 0.18m beyond the shoulders, less than its
    # wall thickness. Its end caps already form the return surfaces: adding
    # another return prism would duplicate those exposed faces. Lift only
    # the wall top vertices to the one hip plane, including its rear edge.
    for part in b.parts:
        if part['label']=='north-entry-bay/continuous-open-wall':
            part['vertices']=[(x,y,roof_z(x,y) if abs(z-H['entry_eave'])<1e-8 else z) for x,y,z in part['vertices']]

    roof_manifest = add_roof(b,roof)
    extras(b,W,DEPTH,H,roof)
    feature(b,entry,arch,'arched-portal','open recessed portal',(-.28,0),(-1.27,-1.24))
    b.features[-1]['expected_closure']={'material':'spatial glass or green painted frame at rear entry door; inner pebble wall outside rear openings','plane_depth_m':-H['porch_recess'],'recess_clear_depth_interval_m':[-H['porch_recess']+.02,-.29]}
    for i,vent in enumerate(vents):feature(b,south,vent,f'documented-vent-{i+1}','vent',(-.28,0),(-.32,-.30))

    # Compact building plinth and necessary entrances; no whole garden plane.
    footprint = box(-half,y0,half,y1).union(box(-bayhalf,y1,bayhalf,northfront))
    b.plan_prism(footprint, 0, .30, 'stone plinth', 'main-plinth')
    # Single stepped solids prevent overlapping coplanar stair side faces.
    south_steps=Polygon([(y0-1.14,0),(y0,0),(y0,.30),(y0-.56,.30),
                         (y0-.56,.20),(y0-.85,.20),(y0-.85,.10),(y0-1.14,.10)])
    b.prism(south_steps,-4.275,4.275,lambda y,z,x:(x,y,z),'stone plinth','garden-entry-single-stepped-solid')
    # The north staircase is one boundary shell with nested tier footprints.
    # Horizontal differences form exposed treads; no stacked internal caps.
    from north_steps import add_north_steps
    add_north_steps(b,northfront,D['north_entry_revision'])
    return b, roof, roof_manifest
