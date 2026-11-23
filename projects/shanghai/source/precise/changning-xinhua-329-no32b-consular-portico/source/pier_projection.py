"""Project three measured paint outlines onto the visible facets of the west shaft."""
from collections import defaultdict

import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union
from photo_architecture import pieces


def paint_number(builder, readings, eye, ray_matrix, material):
    shaft = next(p for p in builder.parts if p['label'] == 'west column/smooth shaft')
    vertices = np.asarray(shaft['vertices'])
    image = (vertices - eye) @ np.linalg.inv(ray_matrix).T
    pixels = image[:, :2] / image[:, 2, None]
    for glyph, reading in zip('32乙', readings, strict=True):
        outline = Polygon(reading['original_pixel_outline'], reading['cutouts'])
        faces = defaultdict(list)
        planes = {}
        for indices in shaft['triangles']:
            indices = list(indices)
            a, b, c = vertices[indices]
            normal = np.cross(b - a, c - a)
            normal /= np.linalg.norm(normal)
            if np.dot(normal, eye - a) <= 0:
                continue
            triangle = Polygon(pixels[indices])
            if not outline.intersects(triangle):
                continue
            plane = np.dot(normal, a)
            key = tuple(np.round([*normal, plane], 7))
            planes[key] = normal, plane
            faces[key].append(triangle)
        coverage = []
        count = 0
        for key, polygons in faces.items():
            normal, plane = planes[key]

            def ring_to_world(ring):
                rays = np.c_[ring.coords, np.ones(len(ring.coords))] @ ray_matrix.T
                t = (plane - np.dot(normal, eye)) / (rays @ normal)
                return (eye + t[:, None] * rays)[:, [0, 2]]

            def surface(x, z, relief):
                y = (plane - normal[0] * x - normal[2] * z) / normal[1]
                return x, y - relief, z

            for cut in pieces(outline.intersection(unary_union(polygons))):
                coverage.append(cut)
                if cut.area < .01:
                    continue
                patch = Polygon(ring_to_world(cut.exterior), [ring_to_world(r) for r in cut.interiors])
                count += 1
                builder.prism(patch, .00025, .00165, surface, material,
                              f'west column/hand-painted {glyph} facet {count}')
        visible = unary_union(coverage).area / outline.area
        if visible < .9999:
            raise ValueError(f'Only {visible:.4%} of the measured {glyph} reaches the shaft')
