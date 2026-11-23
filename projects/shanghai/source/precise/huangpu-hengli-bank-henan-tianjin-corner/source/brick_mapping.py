"""Metre-based projection for the original 32 m square brick-bond image."""
from math import hypot

STREET_EDGES = {
    'Tianjin': ((-15.8184, 0.), (0., 0.)),
    'Chamfer': ((0., 0.), (2.8775, 3.2731)),
    'Henan': ((2.8775, 3.2731), (.8376, 32.4104)),
}
BRICK = 'Hengli dark fired brick'


def brick_uv(label, vertex):
    start, end = STREET_EDGES[label.split('/')[0]]
    vx, vy = end[0]-start[0], end[1]-start[1]
    along = ((vertex[0]-start[0])*vx+(vertex[1]-start[1])*vy)/hypot(vx,vy)
    return ((along+.70)/32., (vertex[2]+.25)/32.)
