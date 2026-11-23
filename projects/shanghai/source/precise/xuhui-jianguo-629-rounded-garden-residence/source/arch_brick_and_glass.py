"""The three red masonry piers and the independent narrow glazed registers."""
import json
import math
from pathlib import Path

from shapely.geometry import Polygon, box

from materials import BLOCK, BRICK, DARK, FRAME, GLASS, MID_GLASS, MORTAR, TRIM, paint


RIM = 'Jianguo 629 | pressed glass edge'
PALETTE = {RIM: paint((154, 164, 157), .32)}
OBSERVATIONS = json.loads((Path(__file__).resolve().parents[1] / 'measurements' /
                           'brick-and-glass-photo-observations.json').read_text())


def layout_from_photo(photo_to_xz, face_y=0.0, storey_height=3.30):
    """Convert the six measured components using the caller's photo-to-wall function."""
    def point(uv):
        xyz = photo_to_xz(*uv)
        return (float(xyz[0]), float(xyz[-1]))

    def average(points, dimension):
        return sum(point(p)[dimension] for p in points) / len(points)

    levels = []
    for entry in OBSERVATIONS['rows']:
        pier = entry['pier']
        u = [average(pair, 0) for pair in zip(pier['base'], pier['shoulders'])]
        foot = average(pier['base'], 1)
        shoulder = average(pier['shoulders'], 1)
        crown = point(pier['crown'])[1] if entry['id'] != 'upper' else shoulder
        glass = entry['glass']
        tl, tr, br, bl = glass['corners']
        levels.append({'id': entry['id'],
                       'pier': [min(u), max(u), foot, shoulder, max(shoulder, crown)],
                       'strip': [average([tl, bl], 0), average([tr, br], 0),
                                 average([bl, br], 1), average([tl, tr], 1)],
                       'brick_bottom': average(glass['cap_base'], 1),
                       'brick_top': average(glass['cap_top'], 1),
                       'courses': glass['rows']})
    return {'levels': levels, 'face_y': face_y, 'course_height': storey_height / 52.0}


def pier_outline(pier, segments=18):
    x0, x1, z0, shoulder, crown = pier
    if crown <= shoulder + .0005:
        return box(x0, z0, x1, shoulder)
    # The shallow curve belongs to the top edge of a planar panel.
    p = [(x0, z0), (x1, z0)]
    for i in range(segments + 1):
        t = i / segments
        p.append((x1 + (x0 - x1) * t, shoulder + (crown - shoulder) * 4 * t * (1 - t)))
    return Polygon(p)


def opening_profiles(layout):
    """Return individual red fields and clear strip holes for a wall builder."""
    layout = layout.get('brick_and_glass', layout)
    return [{'id': row['id'], 'pier': pier_outline(row['pier']),
             'strip': box(row['strip'][0], row['strip'][2], row['strip'][1], row['strip'][3])}
            for row in layout['levels']]


def _face(b, shape, face_y, back_y, material, label):
    b.prism(shape, -back_y, -face_y, lambda x, z, out: (x, -out, z), material, label)


def _brick(b, shape, face_y, back_y, label, course_height):
    _face(b, shape, face_y, back_y, BRICK, label)
    # The shared image is six stretcher lengths across and eighteen courses high.
    part = b.parts[-1]
    if 'texcoords' not in part:
        return
    coords = [None] * len(part['vertices'])
    for i0, i1, i2 in part['triangles']:
        a, c, d = (part['vertices'][i] for i in (i0, i1, i2))
        ux, uy, uz = [c[j] - a[j] for j in range(3)]
        vx, vy, vz = [d[j] - a[j] for j in range(3)]
        nx, ny, nz = uy*vz-uz*vy, uz*vx-ux*vz, ux*vy-uy*vx
        for i in (i0, i1, i2):
            x, y, z = part['vertices'][i]
            if abs(nz) > math.hypot(nx, ny):
                s, t = x, y
            else:
                length = math.hypot(nx, ny)
                s, t = (-ny*x + nx*y) / length, z
            coords[i] = [s / (6 * course_height * 3.4), t / (18 * course_height)]
    part['texcoords'] = coords


def _glass_units(b, rect, num_rows, wall_y, label, lod):
    x0, z0, x1, z1 = rect.bounds
    unit_width, unit_height = (x1-x0)/3, (z1-z0)/num_rows
    _face(b, rect, wall_y+.095, wall_y+.13, MORTAR, label + ' joints')
    for r in range(num_rows):
        for c in range(3):
            joint = min(unit_width, unit_height)*.045
            x, z = x0+c*unit_width, z0+r*unit_height
            outline = box(x+joint, z+joint, x+unit_width-joint, z+unit_height-joint)
            child = label + f' {r+1}-{c+1}'
            if lod:
                _face(b, outline, wall_y+.078, wall_y+.094, BLOCK, child)
            else:
                # A small optical border, as seen between the pale grout and the darker glass.
                inset = outline.buffer(-min(unit_width, unit_height)*.054, join_style=2)
                _face(b, outline.difference(inset), wall_y+.077, wall_y+.094, RIM, child+' rim')
                _face(b, inset, wall_y+.080, wall_y+.094, BLOCK, child+' glass')


def _single_light(b, rect, wall_y, label, material):
    inner = rect.buffer(-.029, join_style=2)
    _face(b, rect.difference(inner), wall_y+.074, wall_y+.108, FRAME, label+' sash')
    _face(b, inner, wall_y+.111, wall_y+.12, material, label+' single light')


def add_brick_and_glass(b, layout, lod=False, glazing='2019-published'):
    """Add the red brick piers and narrow registers. Select the 2017 glass separately."""
    if glazing not in ('2019-published', '2017-photographed'):
        raise ValueError('Unknown photographic glazing state')
    for key, value in PALETTE.items():
        b.palette.setdefault(key, value)
    layout = layout.get('brick_and_glass', layout)
    wall_y = layout.get('face_y', 0.0)
    for row in layout['levels']:
        name = 'Garden ' + row['id']
        panel = pier_outline(row['pier'], 8 if lod else 18)
        _brick(b, panel, wall_y+.025, wall_y+.16, name+' | central brick pier', layout['course_height'])
        x0, x1, z0, z1 = row['strip']
        area = box(x0, z0, x1, z1)
        _face(b, area.buffer(.042, join_style=2).difference(area),
              wall_y-.020, wall_y+.025, TRIM, name+' | strip border')
        _face(b, area, wall_y+.138, wall_y+.16, DARK, name+' | strip backing')
        red_low, red_high = row['brick_bottom'], row['brick_top']
        _brick(b, box(x0, red_low, x1, red_high), wall_y+.064, wall_y+.134,
               name+' | strip brick panel', layout['course_height'])
        for tag, low, high, n, material in [('lower', z0, red_low, row['courses'][1], MID_GLASS),
                                             ('upper', red_high, z1, row['courses'][0], GLASS)]:
            rect = box(x0, low, x1, high)
            if glazing == '2019-published':
                _glass_units(b, rect, n, wall_y, name+' '+tag, lod)
            else:
                _single_light(b, rect, wall_y, name+' '+tag, material)
