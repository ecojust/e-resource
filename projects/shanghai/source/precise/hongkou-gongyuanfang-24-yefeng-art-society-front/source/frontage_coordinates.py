"""Intersect original photograph pixels with the flat wall and curved bay of No. 24."""
import json
from math import sqrt
from pathlib import Path

import numpy as np

MEASUREMENTS = Path(__file__).resolve().parents[1] / 'measurements'
STUDY = json.loads((MEASUREMENTS / 'two-cameras-and-curved-sill.json').read_bytes())
FRONT_CAMERA = np.asarray(STUDY['front'])
GABLE_CAMERA = np.asarray(STUDY['oblique_wall'])
CX, CY = STUDY['curved_sill']['circle_center']
SILL_RADIUS = STUDY['curved_sill']['radius']
WALL_RADIUS = SILL_RADIUS - STUDY['curved_sill']['inward_wall_offset_from_stone_edge']
CUT_BOTTOM = -5.334


def intersect_plane(u, v, axis, value, camera=FRONT_CAMERA):
    """Return XYZ for a pixel and one known coordinate (X=0, Y=1, Z=2)."""
    eq = camera[:2] - np.array([[u], [v]]) * camera[2]
    other = [k for k in range(3) if k != axis]
    point = np.zeros(3)
    point[axis] = value
    point[other] = np.linalg.solve(eq[:, other], -eq[:, 3] - value * eq[:, axis])
    return point


def facade_point(u, v, face_y=0., camera=FRONT_CAMERA):
    return intersect_plane(u, v, 1, face_y, camera)


def bay_y(x, radius=WALL_RADIUS):
    return CY - sqrt(radius * radius - (x - CX) ** 2)


def bay_point(u, v, radius=WALL_RADIUS):
    """First intersection with the outward circular segment of the red-brick bay."""
    a = facade_point(u, v)
    step = facade_point(u, v, 1.) - a
    origin = a[:2] - [CX, CY]
    roots = np.roots([step[:2] @ step[:2], 2 * origin @ step[:2], origin @ origin - radius ** 2])
    front = [a + z.real * step for z in roots if abs(z.imag) < 1e-7 and (a + z.real * step)[1] < CY]
    if not front:
        raise ValueError(f'Pixel {(u,v)} misses the curved frontage')
    return min(front, key=lambda p: p[1])


def project(point, camera=FRONT_CAMERA):
    pixel = camera @ [*point, 1.]
    return pixel[:2] / pixel[2]
