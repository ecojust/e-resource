"""No.19 terrace, from the two faces of the 2015 Fayhoo courtyard photograph.

Local X comes toward the garden. The long balustrade runs in +Y. The last
cross-section falls behind a foreground tree. The cloudy sky reflections,
towels, foliage and planters in the photograph are outside this model.
"""
import math
from pathlib import Path
import json

import numpy as np
from shapely import constrained_delaunay_triangles
from shapely.geometry import Polygon

MEASUREMENTS = Path(__file__).resolve().parents[1] / 'measurements/terrace-sections.json'
STONE = 'No.19 terrace | ivory cast stone'
CAP = 'No.19 terrace | pale cement moulding'
FASCIA = 'No.19 terrace | white rendered fascia'
UNDER = 'No.19 terrace | warm shadowed render'
DECK = 'No.19 terrace | grey walking surface'


def _paint(rgb, roughness):
    def linear(byte):
        c = byte / 255
        return c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4
    return {'color': [linear(v) for v in rgb], 'roughness': roughness}


PALETTE = {STONE: _paint((218, 214, 205), .85), CAP: _paint((228, 223, 213), .82),
           FASCIA: _paint((213, 209, 201), .88), UNDER: _paint((198, 191, 172), .9),
           DECK: _paint((153, 150, 142), .92)}


def _signed_shell(b, vertices, faces, material, label):
    vertices = np.asarray(vertices, dtype=float)
    relative = vertices - vertices[0]
    volume6 = sum(np.dot(relative[f[0]], np.cross(relative[f[i]], relative[f[i + 1]]))
                  for f in faces for i in range(1, len(f) - 1))
    if volume6 < 0:
        faces = [list(reversed(f)) for f in faces]
    b.add(vertices, faces, material, label)


def _cornice(b, section, left, end, material, label):
    # A closed L in plan. Every section is mitred at its projected arris.
    # The native end faces need triangulation because the bead profile is concave.
    n = len(section)
    vs = ([(left, y, z) for x, y, z in section] + list(section) +
          [(x, end, z) for x, y, z in section])
    faces = [(k*n+i, k*n+(i+1)%n, (k+1)*n+(i+1)%n, (k+1)*n+i)
             for k in range(2) for i in range(n)]
    for offset, axis in [(0, 1), (2*n, 0)]:
        planar = [(p[axis], p[2]) for p in section]
        poly = Polygon(planar)
        if not poly.is_valid or poly.area < 1e-7:
            raise ValueError(f'Invalid {label} section')
        index = {p: j for j, p in enumerate(planar)}
        for tri in constrained_delaunay_triangles(poly).geoms:
            ids = [index[p] for p in list(tri.exterior.coords)[:3]]
            # Outside at the start reverses the cross-section perimeter, while
            # the terminating cap follows it. The two projected planes differ.
            if tri.exterior.is_ccw != poly.exterior.is_ccw:
                ids.reverse()
            faces.append(tuple(offset+i for i in (reversed(ids) if offset == 0 else ids)))
    _signed_shell(b, vs, faces, material, label)


def _segment(b, x0, x1, y0, y1, z0, z1, material, label):
    b.box(((x0+x1)/2, (y0+y1)/2, (z0+z1)/2),
          (x1-x0, y1-y0, z1-z0), material, label=label)


def _pier(b, box, side_ribs, front_ribs, name, far):
    x0, x1, y0, y1, bottom, top = box
    _segment(b, x0+.007, x1-.009, y0+.011, y1-.007, bottom, top-.037, STONE,
             f'terrace.{name}.pier-core')
    # Each broad reed runs up one face. A low round crown produces the small
    # changes in silhouette across the pier, also visible above the side towel.
    for face, count, low, high in [('side', side_ribs, x0, x1), ('front', front_ribs, y0, y1)]:
        if not count:
            continue
        pitch = (high-low)/count
        steps = 5 if far else 12
        for i in range(count):
            start = low + pitch*i
            ztop = top + (.009 if i%3 == 1 else -.005 if i%3 == 2 else 0.)
            # Closed rectangular core with shallow curved outward face/swept crown.
            vs = []
            for level, radius in [(bottom, .72), (bottom+.019, 1.),
                                  (ztop-.044, 1.), (ztop-.015, .84), (ztop, .52)]:
                for j in range(steps+1):
                    f = j/steps
                    s = start+pitch*(.011+.978*f)
                    crown = math.sin(math.pi*f)**.74
                    d = .002+.024*radius*crown
                    z = level - (.021*(1-crown) if level >= ztop-.015 else 0)
                    vs.append((s, y0-d, z) if face == 'side' else (x1+d, s, z))
                vs.extend([(start+.989*pitch, y0+.016, level), (start+.011*pitch, y0+.016, level)]
                          if face=='side' else [(x1-.016, start+.989*pitch, level), (x1-.016, start+.011*pitch, level)])
            k = steps+3
            fs = [tuple(reversed(range(k))), tuple(range(4*k, 5*k))]
            fs += [(a*k+j, a*k+(j+1)%k, (a+1)*k+(j+1)%k, (a+1)*k+j)
                   for a in range(4) for j in range(k)]
            _signed_shell(b, vs, fs, STONE, f'terrace.{name}.{face}-reed.{i+1:02}')


def _spindle(b, center, profile, name, far):
    # The photographs show flat, rectangular pale stocks, a rounded shoulder,
    # narrow neck and projecting capital. A small bevel preserves the stock.
    x, y = center
    vs = []
    for z, w, depth in profile:
        a, c = w/2, depth/2
        fillet = min(a, c)*.22
        loop = [(-a+fillet,-c), (a-fillet,-c), (a,-c+fillet), (a,c-fillet),
                (a-fillet,c), (-a+fillet,c), (-a,c-fillet), (-a,-c+fillet)]
        vs.extend((x+dx, y+dy, z) for dx, dy in loop)
    n = len(profile)
    faces = [tuple(reversed(range(8))), tuple(range((n-1)*8, n*8))]
    faces.extend((k*8+j,k*8+(j+1)%8,(k+1)*8+(j+1)%8,(k+1)*8+j)
                 for k in range(n-1) for j in range(8))
    b.add(vs, faces, STONE, f'terrace.spindle.{name}')


def add_terrace(b, lod=False):
    """Add the photographed corner and the open, visible section of its railing."""
    d = json.loads(MEASUREMENTS.read_text())
    far = lod is True or lod in ('far','low','lod','distant')
    b.palette.update(PALETTE)
    end = d['front_cut_y']
    for row in d['returns']:
        sec = row['section_xyz']
        if far:
            sec = [sec[i] for i in row['lod_vertices']]
        _cornice(b, sec, row['start_x'], end, {'cap': CAP,'fascia': FASCIA,'shade': UNDER}[row['finish']],
                 'terrace.return.'+row['name'])
    _segment(b, .011, 1.916, -.007, end, 7.390, 7.460, DECK, 'terrace.deck')
    for pier in d['piers']:
        _pier(b, pier['box'], pier['side_reeds'], pier['front_reeds'], pier['key'], far)
    profile = d['spindle_profile_z_width_depth']
    if far:
        profile = [profile[i] for i in d['lod_spindle_profile']]
    for name, row in d['runs'].items():
        for i, pos in enumerate(row['center_positions']):
            center = (pos, row['plane']) if name=='side' else (row['plane'], pos)
            p = profile if name=='side' else [(z, dy, dx) for z, dx, dy in profile]
            _spindle(b, center, p, f'{name}.{i+1:02}', far)
        for z0, z1, width, finish, label in d['handrail_layers']:
            a,c = row['rail_extents']; v=row['plane']; h=width/2
            limits=(a,c,v-h,v+h) if name=='side' else (v-h,v+h,a,c)
            _segment(b,*limits,z0,z1,CAP if finish=='cap' else STONE,f'terrace.hand.{name}.{label}')
