"""Renovated south terrace of the Bank of Communications warehouse on Guangfu Road.

The entrance is the origin. The studio roof plan supplies the boundary; the
house layout supplies its elevation. Handrail dimensions are fitted to the
2025 photographs. The higher roof structures belong to the main building.
"""
import json
import math
from pathlib import Path

import numpy as np
from shapely.geometry import Point, Polygon
from shapely.geometry.polygon import orient


SOURCE = Path(__file__).parent
MEASUREMENTS = SOURCE.parent / 'measurements'
PAVING = 'Guanger terrace | jointed stone paving'
STEEL = 'Guanger terrace | dark metal handrail'
BEZEL = 'Guanger terrace | flush light surround'
LENS = 'Guanger terrace | inset light disc'
LAMP = 'Guanger terrace | lamp centre'

def finish(rgb, roughness, metal=0.0):
    srgb = np.asarray(rgb) / 255
    linear = np.where(srgb <= .04045, srgb / 12.92, ((srgb+.055)/1.055)**2.4)
    return dict(color=linear.tolist(), roughness=roughness, metallic=metal)

PALETTE = {
    PAVING: dict(color=[1.,1.,1.], roughness=.86, metallic=0.,
                 texture=str(SOURCE / 'roof-terrace-paving.png')),
    STEEL: finish((56, 59, 61), .54, .44),
    BEZEL: finish((77, 80, 82), .66, .2),
    LENS: finish((149, 151, 150), .56, .08),
    LAMP: finish((214, 205, 169), .34, .10),
}

def terrace_layout(layout):
    survey = json.loads((MEASUREMENTS / 'roof-terrace-survey.json').read_text())
    fit = json.loads((MEASUREMENTS / 'roof-terrace-fit.json').read_text())
    transform = np.asarray(layout.get('plan_pixel_to_xy', fit['plan_pixel_to_xy']))
    if transform.shape != (2,3):
        raise ValueError('The warehouse roof plan needs a 2 by 3 pixel-to-metre matrix')
    def at(p):
        return transform @ [*p,1.]
    inner = np.asarray([at(p) for p in survey['roof_plan_edges']['inner_south']])
    west, east = (at(p) for p in survey['roof_plan_edges']['southern_paved_field_back_line'])
    field = orient(Polygon([*inner, east, west]), sign=1.0)
    return field, inner, fit

def add_terrace(b, lod, layout):
    """Add the surveyed continuous paved field, wall rail and seven visible flush lights."""
    field, inner, fit = terrace_layout(layout)
    z = float(layout['roof_deck_z'])
    far = lod is True or lod == 'lod'
    b.palette.update(PALETTE)
    b.plan_prism(field, z-.065, z, PAVING, 'South terrace | riverfront paving')
    # The UV axes follow the rectilinear roof plan. Giving the skirt a small
    # separate offset keeps the atlas defined on each of its narrow edges.
    tangent = np.asarray(fit['plan_pixel_to_xy'])[:,0]
    tangent = tangent / np.linalg.norm(tangent)
    inward = np.array([-tangent[1], tangent[0]])
    b.parts[-1]['texcoords'] = [
        ((np.dot([x,y], tangent)+36+.43*(h-z))/72,
         (np.dot([x,y], inward)+4+.31*(h-z))/32)
        for x,y,h in b.parts[-1]['vertices']
    ]

    arcs = np.r_[0., np.cumsum(np.linalg.norm(np.diff(inner, axis=0), axis=1))]
    def rail_point(s, offset, height):
        i = min(max(0, np.searchsorted(arcs,s,side='right')-1),len(inner)-2)
        vector = (inner[i+1]-inner[i])/(arcs[i+1]-arcs[i])
        centre = inner[i]+(s-arcs[i])*vector
        normal = np.array([-vector[1],vector[0]])
        return [*(centre+normal*offset),z+height]
    # The flag pedestal interrupts the rail at the central raised parapet.
    # Its shaft and masonry are part of the existing facade.
    flag = float(np.interp(0.,inner[:,0],arcs))
    height = fit['handrail_z_above_deck_m']
    pitch = fit['bracket_pitch_m']
    start = fit['support_stations_south_arc_from_west_m'][0]
    bracket_stations = sorted(start+i*pitch for i in range(-75,76))
    for side, left, right in [('west',.14,flag-.59),('east',flag+.59,arcs[-1]-.14)]:
        points = [left,*(n for n in arcs if left<n<right),right]
        b.tube([rail_point(s,.145,height) for s in points],.026,STEEL,
               sides=6 if far else 12,label=f'South terrace | {side} handrail')
        for index,s in enumerate(t for t in bracket_stations if left+.05<t<right-.05):
            low = height-fit['bracket_drop_m']
            points = [rail_point(s,-.022,low),rail_point(s,.146,low),
                      rail_point(s,.146,height-.014)]
            b.tube(points,.018,STEEL,sides=5 if far else 8,
                   label=f'South terrace | {side} rail bracket {index+1:02}')

    for i, centre in enumerate(fit['light_centres_xy'],1):
        centre = np.array(centre)
        plate = orient(Polygon(centre+np.asarray(fit['light_plate_corner_offsets_xy'])),sign=1)
        if not field.covers(plate):
            raise ValueError(f'Roof light {i} is outside the measured paved field')
        b.plan_prism(plate,z-.004,z+.006,BEZEL,f'South terrace | light {i} outer plate')
        # The circular insert sits flush in its square cover in photos 38 and 40.
        for radius,lo,hi,material,name in [(.298,.006,.009,LENS,'disc'),(.026,.009,.013,LAMP,'point')]:
            circle = orient(Point(centre).buffer(radius,quad_segs=4 if far else 9),sign=1)
            b.plan_prism(circle,z+lo,z+hi,material,f'South terrace | light {i} {name}')
