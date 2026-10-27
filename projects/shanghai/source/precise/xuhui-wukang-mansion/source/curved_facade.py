"""Curved counterpart to Facade, in the same centred (u, z, outward d) frame.

The caller supplies an open, ordered CCW footprint polyline. Positive d is its
right-hand side. Path vertices use mitred offsets, so neighbouring strips meet
exactly; a dense smooth input path produces a smooth-looking façade. Absolute
depth should remain small relative to the curve radius to avoid offset folds.

wall/window/beam retain Facade's API. Boxes, sills, bands and rails follow the
curve. Prism strips are <= 0.30 m wide and also split at every path vertex.
Introduced interior cut caps are removed; actual outer edges and hole reveals
remain. This helper authors geometry only and does not infer building layout.
"""

import math

import numpy as np
from shapely.geometry import LineString, Point, box as rect

from common.photo_architecture import Facade


class CurvedFacade(Facade):
    MAX_STRIP_WIDTH = .30

    def __init__(self, builder, ordered_ccw_path_xy, label='curved-facade'):
        path = np.asarray(ordered_ccw_path_xy, dtype=float)
        if (path.ndim != 2 or path.shape[1] != 2 or len(path) < 2
                or not np.isfinite(path).all()):
            raise ValueError('CurvedFacade needs at least two finite XY points')
        delta = np.diff(path, axis=0)
        lengths = np.linalg.norm(delta, axis=1)
        if np.any(lengths < 1e-9):
            raise ValueError('CurvedFacade path has repeated adjacent points')
        if np.linalg.norm(path[-1]-path[0]) < 1e-9 or not LineString(path).is_simple:
            raise ValueError('CurvedFacade requires an open, non-intersecting path')

        tangents = delta / lengths[:, None]
        normals = np.column_stack((tangents[:, 1], -tangents[:, 0]))
        offsets = np.empty_like(path)
        offsets[0], offsets[-1] = normals[0], normals[-1]
        for i in range(1, len(path)-1):
            denominator = 1. + float(np.dot(normals[i-1], normals[i]))
            if denominator < 1e-6:
                raise ValueError('CurvedFacade path has a reversing tangent')
            offsets[i] = (normals[i-1] + normals[i]) / denominator

        self.builder, self.label = builder, label
        self.path = path.copy()
        self.length = float(lengths.sum())
        self._lengths, self._tangents = lengths, tangents
        self._offsets = offsets
        self._stations = np.r_[0., np.cumsum(lengths)] - self.length/2
        self.a, self.b = np.r_[path[0], 0.], np.r_[path[-1], 0.]
        self.center = self.point(0., 0.)
        mid = self._segment(0.)
        # Compatibility descriptors only: geometry methods never use one fixed
        # midpoint basis to approximate an entire curved component.
        self.t = np.r_[tangents[mid], 0.]
        self.n = np.r_[normals[mid], 0.]
        self.audit = {'prism_calls': 0, 'strips': 0,
                      'removed_internal_cap_triangles': 0,
                      'max_strip_width_m': 0.}

    def _segment(self, u):
        return int(np.clip(np.searchsorted(self._stations, u, side='right')-1,
                           0, len(self._lengths)-1))

    def point(self, u, z, d=0):
        if not np.isfinite([u, z, d]).all():
            raise ValueError('CurvedFacade coordinates must be finite')
        if u < self._stations[0]:
            xy = self.path[0] + self._tangents[0]*(u-self._stations[0])
            normal = self._offsets[0]
        elif u > self._stations[-1]:
            xy = self.path[-1] + self._tangents[-1]*(u-self._stations[-1])
            normal = self._offsets[-1]
        else:
            i = self._segment(u)
            fraction = (u-self._stations[i])/self._lengths[i]
            xy = self.path[i]*(1-fraction) + self.path[i+1]*fraction
            normal = self._offsets[i]*(1-fraction) + self._offsets[i+1]*fraction
        return np.array([xy[0]+normal[0]*d, xy[1]+normal[1]*d, z])

    def _cuts(self, low, high):
        """Cuts include polyline corners and support short endpoint extensions."""
        knots = [low, *(u for u in self._stations if low < u < high), high]
        cuts = [float(low)]
        for a, b in zip(knots, knots[1:]):
            count = max(1, math.ceil((b-a)/self.MAX_STRIP_WIDTH))
            cuts.extend(float(a+(b-a)*i/count) for i in range(1, count+1))
        return cuts

    def prism(self, poly, back, front, material='limestone', label='wall'):
        if not np.isfinite([back, front]).all() or front <= back:
            raise ValueError('Curved prism must have positive finite thickness')
        if poly.is_empty:
            return
        if not poly.is_valid:
            raise ValueError('Invalid curved wall polygon')
        x0, z0, x1, z1 = poly.bounds
        cuts = self._cuts(x0, x1)
        self.audit['prism_calls'] += 1
        for index, (left, right) in enumerate(zip(cuts, cuts[1:])):
            clipped = poly.intersection(rect(left, z0-1., right, z1+1.))
            if clipped.is_empty or clipped.area <= 1e-12:
                continue
            mapped_parameters = {}

            def mapper(u, z, d):
                xyz = self.point(u, z, d)
                mapped_parameters[tuple(map(float, xyz))] = (u, z, d)
                return xyz

            first_part = len(self.builder.parts)
            self.builder.prism(clipped, back, front, mapper, material,
                               f'{self.label}/{label}/strip-{index:03d}')
            for part in self.builder.parts[first_part:]:
                parameters = [mapped_parameters[tuple(v)] for v in part['vertices']]
                keep = []
                for triangle in part['triangles']:
                    coordinates = [parameters[i] for i in triangle]
                    zs = [p[1] for p in coordinates]
                    remove = False
                    for cut in (left, right):
                        if (x0 < cut < x1
                                and all(abs(p[0]-cut) < 1e-9 for p in coordinates)
                                and poly.contains(Point(cut, (min(zs)+max(zs))/2))):
                            remove = True
                            break
                    if remove:
                        self.audit['removed_internal_cap_triangles'] += 1
                    else:
                        keep.append(triangle)
                part['triangles'] = keep
            self.audit['strips'] += 1
            self.audit['max_strip_width_m'] = max(
                self.audit['max_strip_width_m'], right-left)

    def box(self, u, z, w, h, depth=.3, d=0,
            material='carved pale stone', label='trim'):
        if not np.isfinite([u, z, w, h, depth, d]).all():
            raise ValueError('Curved box dimensions must be finite')
        if min(w, h, depth) <= 0:
            return
        self.prism(rect(u-w/2, z-h/2, u+w/2, z+h/2),
                   d-depth/2, d+depth/2, material, label)

    def line(self, a, b, radius=.04, material='wrought iron', sides=8, label='rail'):
        a, b = np.asarray(a, float), np.asarray(b, float)
        if a.shape not in ((2,), (3,)) or b.shape != a.shape:
            raise ValueError('Curved rail endpoints must both be (u,z) or (u,z,d)')
        if not np.isfinite([a, b]).all():
            raise ValueError('Curved rail endpoints must be finite')
        if abs(a[0]-b[0]) < 1e-12:
            parameters = [a, b]
        else:
            cuts = self._cuts(min(a[0], b[0]), max(a[0], b[0]))
            if b[0] < a[0]:
                cuts.reverse()
            parameters = [a+(b-a)*(u-a[0])/(b[0]-a[0]) for u in cuts]
        self.builder.tube([self.point(*p) for p in parameters], radius,
                          material, sides, self.label+'/'+label)
