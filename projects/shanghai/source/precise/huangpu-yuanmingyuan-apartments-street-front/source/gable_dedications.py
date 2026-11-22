"""Street-facing stone tablets above the two gables at 115 Yuanmingyuan Road.

The hand-drawn inscription contours use original camera observations. All
coordinates are metres in the east facade's X-north, Y-inward, Z-up frame.
"""

from functools import lru_cache
import json
from pathlib import Path

import numpy as np
from shapely import constrained_delaunay_triangles
from shapely.geometry import Point, Polygon, box
from shapely.geometry.polygon import orient

from east_photo_plane import CAMERAS
from wing_casements import finish

SHELL = "Yuanming warm grey tablet surround"
FIELD = "Yuanming buff gable inscription field"
COPING = "Yuanming weathered grey tablet coping"
SOUTH_SCRIPT = "Yuanming grey shallow AD inscription"
NORTH_SCRIPT = "Yuanming dark shallow 1904 inscription"
WORN_SCRIPT = "Yuanming worn date curl"
PALETTE = {
    SHELL: finish([155, 145, 130], .86),
    FIELD: finish([150, 133, 113], .90),
    COPING: finish([107, 107, 93], .82),
    WORN_SCRIPT: finish([112, 105, 102], .76),
    SOUTH_SCRIPT: finish([118, 115, 120], .63),
    NORTH_SCRIPT: finish([62, 58, 61], .77),
}

OBS = json.loads((Path(__file__).resolve().parents[1] / 'measurements/gable-dedication-traces.json').read_bytes())
MATRIX = CAMERAS['2014_oblique']
EYE = -np.linalg.solve(MATRIX[:, :3], MATRIX[:, 3])


def point_on_stone(wing, u, v, y):
    """Transfer an orthophoto point from the street wall plane to the stone relief."""
    start, top = (-12., 26.) if wing == 'south' else (2.3, 26.3)
    on_wall = np.array([start + u / 100., 0., top - v / 100.])
    return EYE + ((y - EYE[1]) / -EYE[1]) * (on_wall - EYE)


def bounds(wing, observed, y):
    l, t, r, b = observed
    a = point_on_stone(wing, l, b, y)
    c = point_on_stone(wing, r, t, y)
    return a[0], a[2], c[0], c[2]


def contour(path, segments):
    """Sample hand-traced lines and cubic Bezier curves written in local photo pixels."""
    tokens = iter(path.split())
    result = []
    def xy():
        return np.array([float(next(tokens)), float(next(tokens))])
    for command in tokens:
        if command in ('M', 'L'):
            result.append(xy())
        elif command == 'C':
            a = result[-1]
            b, c, d = xy(), xy(), xy()
            for t in np.linspace(0, 1, segments + 1)[1:]:
                result.append((1-t)**3*a + 3*(1-t)**2*t*b + 3*(1-t)*t*t*c + t**3*d)
        elif command != 'Z':
            raise ValueError(f'Unsupported hand-trace command {command}')
    return np.asarray(result)


@lru_cache(maxsize=2)
def inscription_transform(wing):
    field = OBS['measurements'][wing]['field']
    axes, observations = [], []
    for (x, z), (u, v) in zip(((0, 0), (405, 0), (405, 246), (0, 246)), field):
        axes.extend([[x, z, 1, 0, 0, 0, -u*x, -u*z], [0, 0, 0, x, z, 1, -v*x, -v*z]])
        observations.extend([u, v])
    return np.r_[np.linalg.solve(axes, observations), 1].reshape(3, 3)


def letter(wing, glyph, lod):
    paths = OBS['hand_traces'][glyph]
    transform = inscription_transform(wing)
    loops = []
    for path in paths:
        raw = contour(path, 3 if lod else 7)
        image = np.column_stack([raw, np.ones(len(raw))]) @ transform.T
        coords = image[:, :2] / image[:, 2:]
        loops.append([point_on_stone(wing, u, v, -.089)[[0, 2]] for u, v in coords])
    shape = Polygon(loops[0], loops[1:])
    if not shape.is_valid:
        raise ValueError(f'Invalid traced contour {wing} {glyph}')
    return orient(shape, sign=1)


def plate(builder, shape, rear, front, material, label):
    builder.prism(shape, -rear, -front, lambda x, z, d: (x, -d, z), material, label)


def inset_field(wing, inset):
    return Polygon([point_on_stone(wing, u, v, -.089)[[0, 2]]
                    for u, v in OBS['measurements'][wing]['field']]).buffer(inset, join_style=2)


def moulding(builder, wing, area, profile, label, material=COPING):
    # Both the profile and its soffit appear in this low-angle view. Fit the four
    # physical bounds to the four observed silhouette limits while keeping the
    # estimated bearing depth and the face profile independent.
    is_lower = 'lower' in label
    depth_multiplier = .77 if is_lower else .80
    rear = -.055 if is_lower else -.030
    profile = [(part, y * depth_multiplier, inset) for part, y, inset in profile]
    initial = bounds(wing, area, profile[0][1])
    def build_rings(parameters):
        l, bottom, r, top = parameters
        rings = []
        for proportion, y, endset in profile:
            z = bottom + (top - bottom) * proportion
            rings.append([(l + endset, y, z), (r - endset, y, z),
                          (r - endset, rear, z), (l + endset, rear, z)])
        return rings
    x0,z1 = (-12.,26.) if wing=='south' else (2.3,26.3)
    def residual(parameters):
        xyz = np.asarray(build_rings(parameters)).reshape(-1, 3)
        front = EYE + (-EYE[1] / (xyz[:, 1] - EYE[1]))[:, None] * (xyz - EYE)
        uv = np.column_stack([(front[:,0]-x0)*100, (z1-front[:,2])*100])
        return np.r_[uv.min(axis=0),uv.max(axis=0)] - np.asarray(area)
    parameters = np.asarray(initial)
    step = 1.e-5
    for _ in range(5):
        difference = residual(parameters)
        if max(abs(difference)) < .001:
            break
        jacobian = np.column_stack([(residual(parameters + axis * step) - difference) / step
                                    for axis in np.eye(4)])
        parameters -= np.linalg.solve(jacobian, difference)
    if max(abs(residual(parameters))) > .30 or parameters[3] - parameters[1] < .045:
        raise ValueError(f"Unresolved stone sill silhouette in {wing}")
    rings = build_rings(parameters)
    points = sum(rings, [])
    faces = [(3, 2, 1, 0)]
    for i in range(len(rings)-1):
        a, b = 4*i, 4*(i+1)
        for j in range(4):
            faces.append((a+j, a+(j+1)%4, b+(j+1)%4, b+j))
    faces.append(tuple(range(len(points)-4, len(points))))
    builder.add(points, faces, material, label)


def sloping_bezel(builder, outside, inside, outer_y, inner_y, label):
    ring = orient(outside.difference(inside), sign=1)
    facets, points, indices = [], [], {}
    inner_border = inside.boundary
    thickness = .009
    def vertex(x, z, back):
        key = (float(x), float(z), back)
        if key not in indices:
            y = inner_y if inner_border.distance(Point(x, z)) < 1.e-7 else outer_y
            indices[key] = len(points)
            points.append((x, y + (thickness if back else 0.), z))
        return indices[key]
    for tri in constrained_delaunay_triangles(ring).geoms:
        coords = list(orient(tri, sign=1).exterior.coords)[:3]
        facets.append(tuple(vertex(x, z, False) for x, z in coords))
        facets.append(tuple(vertex(x, z, True) for x, z in reversed(coords)))
    for boundary in (ring.exterior, *ring.interiors):
        coords = list(boundary.coords)
        for a, b in zip(coords, coords[1:]):
            facets.append((vertex(*a, True), vertex(*b, True),
                           vertex(*b, False), vertex(*a, False)))
    builder.add(points, facets, SHELL, label)


def raised(builder, shape, material, height, lod, name, pale=None):
    """A flat face, a cut bevel, connected sides and a rear face form one glyph mesh."""
    front, shoulder, rear = -.089 - height, -.089 - height + .003, -.0885
    inset = shape.buffer(-(.0018 if lod else .0026), join_style=2, mitre_limit=3)
    if inset.is_empty:
        raise ValueError(f'Bevel exceeds glyph width {name}')
    ring = shape.difference(inset)
    points, faces, index = [], [], {}
    def vertex(x, y, z):
        key = (float(x), float(y), float(z))
        if key not in index:
            index[key] = len(points)
            points.append(key)
        return index[key]
    def cap(geom, face_depth, reverse=False):
        triangles = constrained_delaunay_triangles(geom)
        for tri in triangles.geoms:
            coords = list(orient(tri, sign=1).exterior.coords)[:3]
            face = [vertex(x, face_depth(x, z), z) for x, z in coords]
            faces.append(tuple(reversed(face)) if reverse else tuple(face))
    inside_border = inset.boundary
    cap(inset, lambda x, z: front)
    cap(ring, lambda x, z: front if inside_border.distance(Point(x, z)) < 1e-7 else shoulder)
    cap(shape, lambda x, z: rear, reverse=True)
    for r in (shape.exterior, *shape.interiors):
        pairs = list(r.coords)
        for (x0, z0), (x1, z1) in zip(pairs, pairs[1:]):
            faces.append((vertex(x0,rear,z0), vertex(x1,rear,z1),
                          vertex(x1,shoulder,z1), vertex(x0,shoulder,z0)))
    builder.add(points, faces, material, name)
    if pale is not None:
        # Keep the closed relief intact beneath the lighter finish. The clipped
        # solid follows only the return stroke and preserves the date's counter.
        finish_domain = inset.intersection(pale)
        if not finish_domain.is_empty:
            plate(builder, finish_domain, front+.00015, front-.00075,
                  WORN_SCRIPT, name+" worn return")


def add_gable_dedications(builder, lod=False):
    for wing, body in OBS['measurements'].items():
        name = f'{"South" if wing == "south" else "North"} east gable'
        # Shoulder has a narrowed lower neck below the overhanging upper moulding.
        l, b, r, t = bounds(wing, body['shoulder'], -.084)
        w, h = r-l, t-b
        edge = [(.0, 1), (.018, .46), (.04, .18), (.075, .07), (.19, .07), (.24, 0)]
        shoulder = Polygon([(l+w*x, b+h*z) for x,z in edge] +
                           [(r-w*x, b+h*z) for x,z in reversed(edge)])
        plate(builder, shoulder, .006, -.081, SHELL, name + ' cut shoulders')
        moulding(builder, wing, body['upper'],
                 [(0,-.105,.095),(.14,-.116,.080),(.26,-.145,.046),
                  (.43,-.150,.046),(.51,-.127,.062),(.64,-.159,.035),
                  (.77,-.188,.012),(.92,-.200,0),(1,-.179,.008)],
                 name+' upper moulding')
        l, b, r, t = bounds(wing, body['bezel'], -.104)
        surround = box(l, b, r, t)
        field = inset_field(wing, 0.)
        plate(builder, surround, .008, -.066, SHELL, name+' backing block')
        plate(builder, field.buffer(.008, join_style=2), -.064, -.089, FIELD, name+' tablet field')
        # The outer arris stands in front of the band, and the inner reveal
        # returns to the field. Three strips receive daylight independently.
        edge = field.buffer(.026, join_style=2).intersection(surround)
        inner_edge = field.buffer(.012, join_style=2).intersection(surround)
        outer_edge = field.buffer(.072, join_style=2).intersection(surround)
        plate(builder, surround.difference(outer_edge), -.065, -.080, SHELL, name+' outer margin')
        sloping_bezel(builder, outer_edge, edge, -.080, -.120, name+' broad cut bevel')
        plate(builder, edge.difference(inner_edge), -.087, -.120, SHELL, name+' raised arris')
        sloping_bezel(builder, inner_edge, field, -.120, -.089, name+' inside bevel')
        moulding(builder, wing, body['lower'],
                 [(0,-.084,.043),(.20,-.107,.032),(.29,-.121,.026),
                  (.41,-.119,.030),(.52,-.146,.018),(.76,-.158,.009),
                  (.88,-.180,0),(1,-.171,.005)],
                 name+' lower sill')
        strokes = {symbol: letter(wing, symbol, lod) for symbol in body['glyphs']}
        faded_return = None
        if wing == 'north':
            # Both photographs show the curled pen stroke meeting the diagonal of 4.
            # Unite this patch so that its flat face and bevel are continuous.
            dark = strokes.pop('open-oval').union(strokes.pop('four'))
            curled_return = letter(wing, 'faint-loop-return', lod)
            faded_return = curled_return.difference(dark)
            strokes['joined oval and four'] = dark.union(curled_return)
        for symbol, shape in strokes.items():
            raised(builder, orient(shape, sign=1), SOUTH_SCRIPT if wing=='south' else NORTH_SCRIPT,
                   .012 if wing=='south' else .010, lod, name+' inscription '+symbol,
                   faded_return if symbol == 'joined oval and four' else None)
