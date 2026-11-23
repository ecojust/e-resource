"""The visible pale bend, its dark wall opening, and the exposed run under the eave."""
import json
import math
from pathlib import Path

import numpy as np
from register_court import Camera


PALE = '325 garden | weathered pale wall tubing'
SLEEVE = '325 garden | pale connector sleeve'
MOUTH = '325 garden | dark opening around the sleeve'
PALETTE = {
    PALE: {'color': [.55, .50, .37], 'roughness': .79},
    SLEEVE: {'color': [.51, .48, .37], 'roughness': .83},
    MOUTH: {'color': [.055, .045, .027], 'roughness': .94},
}
CONTROLS = Path(__file__).resolve().parents[1] / 'measurements/wall-conduit-observations.json'


def _mouth(b, centre, outer, inner, sides):
    """Closed annular section around an actual open centre, on the Y=0 wall."""
    cx, _, cz = centre
    profile = [(outer, -.003), (outer, -.016), (outer-.004, -.022),
               (inner, -.021), (inner, -.002)]
    vertices = []
    for i in range(sides):
        angle = math.tau*i/sides
        for radius, y in profile:
            vertices.append((cx + radius*math.cos(angle), y, cz + radius*math.sin(angle)))
    width = len(profile)
    faces = [(i*width+j, ((i+1)%sides)*width+j,
              ((i+1)%sides)*width+(j+1)%width, i*width+(j+1)%width)
             for i in range(sides) for j in range(width)]
    b.add(vertices, faces, MOUTH, 'Courtyard wall / dark rim at photographed penetration')


def add_wall_conduit(b, lod=False):
    """Add the two photographed portions. Their projected gap is occupied by the pole."""
    for key, material in PALETTE.items():
        b.palette.setdefault(key, material)
    data = json.loads(CONTROLS.read_text())
    camera = Camera('fayhoo')
    mouth = data['mouth']
    centre = camera.wall(mouth['pixel'], -.012)
    _mouth(b, centre, mouth['outer_radius_m'], mouth['inner_radius_m'], 12 if lod else 24)
    bent, horizontal = data['visible_centerlines']
    # The lower part descends out of the wall; toward the soffit it stands further off.
    depths = np.interp(np.arange(len(bent)), [0, 1, 3, 7, 10, 14, len(bent)-1],
                       [.002, -.048, -.083, -.10, -.12, -.18, -.224])
    points = [camera.wall(pixel, depth) for pixel, depth in zip(bent, depths)]
    # One segment continues into the sleeve, so the two cut ends do not show a light leak.
    sides = 8 if lod else 16
    b.tube(points[:4], .035, SLEEVE, sides, 'Courtyard wall / pale sleeve leaving the wall')
    b.tube(points[2:], .023, PALE, sides, 'Courtyard wall / low curved run to the near edge of the pole')
    # Set the upper section against the sloped soffit and keep the whole round section
    # beneath it. Solve ray/plane instead of measuring this foreshortened height by eye.
    line = []
    epsilon = .019
    for pixel in horizontal:
        ray = camera.ray(pixel)
        c = camera.c
        distance = (3.685 - .032*c[0] - c[2] - epsilon) / (ray[2] + .032*ray[0])
        p = c + ray*distance
        # The photographed soffit projects .43 m, so the tubing remains inside its edge.
        line.append(camera.wall(pixel, np.clip(p[1], -.37, -.065)))
    b.tube(line, .020, PALE, sides, 'Courtyard wall / visible line beyond the pole')
