"""Photo-derived brass plate, two fastenings and visible marks at 123 East Nanjing Road.

Adapted from Shwangtianyuan's August 2022 photograph under CC BY-SA 4.0.
The full credit, licence and original-pixel contours accompany this module.
"""
import json
from math import cos, pi, sin
from pathlib import Path

import numpy as np
from shapely import Polygon, constrained_delaunay_triangles, orient_polygons

from photo_plane import position

PALETTE = {
    "Satin ochre brass": {"color": [.38, .242, .114], "roughness": .51, "metallic": .60},
    "Dark bronze plaque lettering": {"color": [.074, .047, .024], "roughness": .56, "metallic": .36},
    "Aged brass fastenings": {"color": [.18, .11, .053], "roughness": .60, "metallic": .52},
}
DATA = json.loads((Path(__file__).resolve().parents[1] / "measurements/nanjing-123-plaque.json").read_bytes())


def add_solid(builder, polygons, front_y, back_y, material, label):
    points, faces = [], []
    for rings in polygons:
        projected = [[position(u, v, front_y)[[0, 2]] for u, v in ring] for ring in rings]
        shape = orient_polygons(Polygon(projected[0], projected[1:]))
        if not shape.is_valid:
            raise ValueError(f"Invalid traced region in {label}")
        index = {}
        for ring in (shape.exterior, *shape.interiors):
            for xy in list(ring.coords)[:-1]:
                if xy not in index:
                    index[xy] = len(index)
        offset, count = len(points), len(index)
        points.extend((x, y, z) for y in (front_y, back_y) for x, z in index)
        for tri in constrained_delaunay_triangles(shape).geoms:
            corners = list(orient_polygons(tri).exterior.coords)[:3]
            a, b, c = (offset + index[q] for q in corners)
            faces.extend(((a, b, c), (a+count, c+count, b+count)))
        for ring in (shape.exterior, *shape.interiors):
            ids = [index[q]+offset for q in ring.coords]
            for a, b in zip(ids, ids[1:]):
                faces.extend(((a, a+count, b+count), (a, b+count, b)))
    builder.add(np.asarray(points), np.asarray(faces), material, label)


def add_street_number(builder, lod):
    add_solid(builder, [[DATA["outline"]]], -.130, -.113, "Satin ochre brass", "Clipped brass address plate")
    sides = 8 if lod else 14
    for i, dot in enumerate(DATA["fastenings"], 1):
        u, v = dot["center"]
        r = dot["radius_px"]
        ring = [(u+r*cos(2*pi*j/sides), v+r*sin(2*pi*j/sides)) for j in range(sides)]
        add_solid(builder, [[ring]], -.1318, -.130, "Aged brass fastenings", f"Round side fastening {i}")
    for row in DATA["lettering"]:
        add_solid(builder, row["lod" if lod else "full"], -.1306, -.130, "Dark bronze plaque lettering",
                  f"Photographed street plate mark {row['glyph']}")
