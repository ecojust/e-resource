"""Curved Flemish-bond parapet on the upper terrace of No.51, viewed from its garden."""
import math

import numpy as np

X_MIN, X_MAX = -4.36, 4.28
BASE, CAP_BASE, CAP_TOP = 8.74, 9.72, 9.80
BACK = .24
SHORT, LONG = .128, .257
PERIOD = SHORT + LONG
COURSE = .0653
FIRST_BED = 8.794
JOINT = .009
BRICK = tuple(f'Terrace parapet | grey face brick, tone {i + 1}' for i in range(5))
MORTAR = 'Terrace parapet | light grey pointing'
CAP = 'Terrace parapet | pale continuous coping'

def finish(rgb):
    value = np.asarray(rgb, dtype=float) / 255
    color = np.where(value <= .04045, value / 12.92, ((value + .055) / 1.055) ** 2.4)
    return {'color': color.tolist(), 'roughness': .89, 'metallic': 0.}

PALETTE = {**{key: finish((r, r + 4, r + 5)) for key, r in zip(BRICK, (116, 122, 127, 132, 137))},
           MORTAR: finish((188, 191, 190)), CAP: finish((186, 189, 187))}

def front(x):
    return -.4987440735 - .0025217623 * x + .04703376129 * x * x

def arc(x):
    """Signed distance along the measured front, relative to X=0."""
    a, b = -.0025217623, 2 * .04703376129
    def primitive(t):
        return (t * math.hypot(1., t) + math.asinh(t)) / (2 * b)
    return primitive(a + b * x) - primitive(a)

def x_from_arc(s):
    x = s
    for _ in range(4):
        x -= (arc(x) - s) / math.hypot(1., -.0025217623 + 2 * .04703376129 * x)
    return x

def strip(x0, x1, contour, count=1):
    """A closed swept solid. The contour runs counterclockwise in its local Y,Z plane."""
    xs = np.linspace(x0, x1, count + 1)
    vertices = [(x, front(x) + y, z) for x in xs for y, z in contour]
    n = len(contour)
    faces = [tuple(range(n - 1, -1, -1)), tuple(count * n + k for k in range(n))]
    for i in range(count):
        for j in range(n):
            k = (j + 1) % n
            faces.append((i * n + j, i * n + k, (i + 1) * n + k, (i + 1) * n + j))
    return vertices, faces

def collect(group, geom):
    vertices, faces = group
    points, indices = geom
    offset = len(vertices)
    vertices.extend(points)
    faces.extend(tuple(offset + j for j in face) for face in indices)

def add_parapet(b, lod=False):
    coarse = lod is True or lod == 'lod'
    sides = 34 if coarse else 76
    v, f = strip(X_MIN, X_MAX, [(.006, BASE), (BACK, BASE), (BACK, CAP_BASE), (.006, CAP_BASE)], sides)
    b.add(v, f, MORTAR, 'Upper terrace | curved brick bed and estimated inner face')
    limits = arc(X_MIN), arc(X_MAX)
    for row in range(15):
        bed_lo = FIRST_BED + (row - 1) * COURSE
        lo = max(BASE, bed_lo + JOINT / 2)
        hi = bed_lo + COURSE - JOINT / 2
        start = arc(.15) - (row % 2) * PERIOD / 2
        groups = {m: ([], []) for m in BRICK}
        first = math.floor((limits[0] - start) / PERIOD)
        last = math.floor((limits[1] - start) / PERIOD)
        for repeat in range(first, last + 1):
            origin = start + repeat * PERIOD
            for k, (left, right) in enumerate(((origin, origin + SHORT), (origin + SHORT, origin + PERIOD))):
                left_end = left <= limits[0]; right_end = right >= limits[1]
                s0 = max(left + JOINT / 2, limits[0]); s1 = min(right - JOINT / 2, limits[1])
                if s1 - s0 < .004:
                    continue
                x0, x1 = x_from_arc(s0), x_from_arc(s1)
                variation = ((row * 109 + repeat * 73 + k * 37) % 19) / 18
                y = -.0007 - .0014 * variation
                back = BACK + .001 if left_end or right_end else .016
                contour = [(y, lo), (back, lo), (back, hi), (y, hi)]
                if not coarse:
                    edge = .0017
                    contour = [(y + edge, lo), (back, lo), (back, hi), (y + edge, hi), (y, hi - edge), (y, lo + edge)]
                geom = strip(x0, x1, contour, 1 if coarse or k == 0 else 2)
                mat = BRICK[(row * 17 + repeat * 13 + k * 11 + repeat // 4) % len(BRICK)]
                if coarse:
                    collect(groups[mat], geom)
                else:
                    unit = 'header' if k == 0 else 'stretcher'
                    b.add(*geom, mat, f'Upper terrace | course {row + 1:02d} {unit} {repeat - first + 1:02d}')
        if coarse:
            for mat, (v, f) in groups.items():
                if v:
                    b.add(v, f, mat, f'Upper terrace | course {row + 1:02d} {mat}')
    v, f = strip(X_MIN, X_MAX, [(-.024, CAP_BASE), (BACK + .018, CAP_BASE),
                                 (BACK + .018, CAP_TOP), (-.022, CAP_TOP), (-.030, CAP_TOP - .008),
                                 (-.030, CAP_BASE + .009)], sides)
    b.add(v, f, CAP, 'Upper terrace | continuous pale coping above the Flemish bond')
