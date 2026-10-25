"""Source-parameter roof shells in metres: X east, Y up, Z south.

This module does not infer eligibility, height, bearing or roof type. Callers
must qualify a single simple footprint and resolve source direction semantics.
In particular, Overture ridge bearings and OSM downslope bearings are not
interchangeable. A gabled roof assumes a centred, symmetric ridge; a skillion
is one plane. Neither adds overhangs, dormers or a guessed roof dimension.

``height`` is the absolute top Y, already including ``roof_height``. ``base``
is absolute bottom Y. The returned roof mesh includes the downward-facing base
cap, matching build_district_models.Mesh.polygon; walls reach the roof profile.
No flat cap is inserted under the pitched roof.
"""
from dataclasses import dataclass, field
import math

import mapbox_earcut
import numpy as np
from shapely.geometry import LineString, Polygon
from shapely.ops import split

VERSION = 'source-roof-geometry-v1'


class RoofGeometryError(ValueError):
    """An unsupported/invalid input; no caller mesh has been modified."""


@dataclass
class MeshData:
    positions: list = field(default_factory=list)
    normals: list = field(default_factory=list)
    indices: list = field(default_factory=list)

    def vertices(self, points, normal):
        offset = len(self.positions)
        self.positions.extend(points)
        self.normals.extend([normal] * len(points))
        return offset


@dataclass
class RoofShell:
    roof: MeshData
    walls: MeshData
    stats: dict


def _finite(value, label):
    try:
        if isinstance(value, bool):
            raise ValueError()
        value = float(value)
    except (ValueError, TypeError, OverflowError) as exc:
        raise RoofGeometryError(f'{label}: expected a finite number') from exc
    if not math.isfinite(value):
        raise RoofGeometryError(f'{label}: expected a finite number')
    return value


def _unit(value, label):
    if not isinstance(value, (list, tuple, np.ndarray)) or len(value) != 2:
        raise RoofGeometryError(f'{label}: an explicit XZ unit vector is required')
    x, z = (_finite(v, label) for v in value)
    length = math.hypot(x, z)
    if abs(length - 1) > 1e-6:
        raise RoofGeometryError(f'{label}: expected length 1, got {length}')
    return x / length, z / length


def _signed_area(ring):
    # Shift before the cross products: city tiles may have a large local offset.
    ox, oz = ring[0]
    return sum((a[0] - ox) * (b[1] - oz) - (b[0] - ox) * (a[1] - oz)
               for a, b in zip(ring, ring[1:] + ring[:1])) / 2


def _clean_ring(values):
    ring = []
    for point in values:
        if len(point) != 2:
            raise RoofGeometryError('footprint: points must be local (x, z) pairs')
        point = tuple(_finite(value, 'footprint') for value in point)
        if not ring or point != ring[-1]:
            ring.append(point)
    if len(ring) > 1 and ring[0] == ring[-1]:
        ring.pop()
    # Remove only exactly collinear intermediate points. This changes no line
    # or footprint area, and avoids earcut omitting a vertex only on the floor.
    changed = True
    while changed and len(ring) > 3:
        changed = False
        for i, b in enumerate(ring):
            a, c = ring[i - 1], ring[(i + 1) % len(ring)]
            ab = (b[0] - a[0], b[1] - a[1])
            bc = (c[0] - b[0], c[1] - b[1])
            if ab[0] * bc[1] - ab[1] * bc[0] == 0 and ab[0] * bc[0] + ab[1] * bc[1] >= 0:
                ring.pop(i)
                changed = True
                break
    if len(ring) < 3 or _signed_area(ring) == 0:
        raise RoofGeometryError('footprint: fewer than three non-collinear vertices')
    if _signed_area(ring) < 0:
        ring.reverse()
    return ring


def _cross(a, b, c):
    ab = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    ac = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    return (ab[1] * ac[2] - ab[2] * ac[1],
            ab[2] * ac[0] - ab[0] * ac[2],
            ab[0] * ac[1] - ab[1] * ac[0])


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _face(mesh, points, normal):
    """A convex wall profile, with its single original bottom boundary edge."""
    unique = []
    for point in points:
        if not unique or point != unique[-1]:
            unique.append(point)
    if len(unique) > 1 and unique[0] == unique[-1]:
        unique.pop()
    if len(unique) < 3:
        return
    offset = mesh.vertices(unique, normal)
    for i in range(1, len(unique) - 1):
        cross = _cross(unique[0], unique[i], unique[i + 1])
        if _dot(cross, cross) == 0:
            continue  # A zero-eave-height edge may meet the base directly.
        if _dot(cross, normal) <= 0:
            raise RoofGeometryError('wall: invalid profile orientation')
        mesh.indices.extend((offset, offset + i, offset + i + 1))


def _surface(mesh, ring, elevation, upward):
    indices = mapbox_earcut.triangulate_float64(
        np.asarray(ring, dtype=np.float64), np.asarray([len(ring)], dtype=np.uint32))
    if not len(indices):
        raise RoofGeometryError('surface: triangulation produced no faces')
    triangle_count = 0
    for i in range(0, len(indices), 3):
        a, b, c = (int(j) for j in indices[i:i + 3])
        triangle = [(ring[j][0], elevation(ring[j]), ring[j][1]) for j in (a, b, c)]
        cross = _cross(*triangle)
        if cross[1] == 0:
            raise RoofGeometryError('surface: degenerate projected triangle')
        if (cross[1] > 0) != upward:
            triangle[1], triangle[2] = triangle[2], triangle[1]
            cross = tuple(-value for value in cross)
        length = math.sqrt(_dot(cross, cross))
        normal = tuple(value / length for value in cross)
        offset = mesh.vertices(triangle, normal)
        mesh.indices.extend((offset, offset + 1, offset + 2))
        triangle_count += 1
    return triangle_count


def build_roof_shell(rings, *, base, height, roof_height, roof_shape,
                     ridge_unit=None, down_slope_unit=None):
    """Return ``RoofShell(roof, walls, stats)`` without mutating input meshes.

    ``rings`` is one local XZ exterior ring, with either winding and optional
    repeated closing point. Holes and multipart footprints must be qualified
    elsewhere, and are deliberately rejected here. A gabled roof requires
    ``ridge_unit``; skillion requires ``down_slope_unit``. No bearing conversion
    is performed. The supplied height includes the pitched roof.
    """
    base, height, roof_height = (_finite(v, name) for v, name in
                                 ((base, 'base'), (height, 'height'), (roof_height, 'roof_height')))
    available_height = height - base
    # Decimal source values can differ by a few binary ULPs when subtracting
    # (e.g. 9.2 - 7.2 < 2). Accept only arithmetic roundoff, not a dimensional
    # epsilon that could silently admit a roof below its declared base.
    height_roundoff = 4 * (math.ulp(base) + math.ulp(height) + math.ulp(roof_height))
    if height <= base or roof_height <= 0 or roof_height - available_height > height_roundoff:
        raise RoofGeometryError('height: require 0 < roof_height <= height - base')
    if roof_shape not in ('gabled', 'skillion'):
        raise RoofGeometryError('roof_shape: only gabled and skillion are supported')
    if len(rings) != 1:
        raise RoofGeometryError('footprint: exactly one exterior ring and no holes are supported')
    ring = _clean_ring(rings[0])
    footprint = Polygon(ring)
    if not footprint.is_valid or footprint.is_empty or not math.isfinite(footprint.area) or footprint.area <= 0:
        raise RoofGeometryError('footprint: expected a valid simple polygon')
    if roof_shape == 'gabled':
        if down_slope_unit is not None:
            raise RoofGeometryError('direction: gabled expects a ridge, not a downslope vector')
        ridge = _unit(ridge_unit, 'ridge_unit')
        direction = (-ridge[1], ridge[0])
    else:
        if ridge_unit is not None:
            raise RoofGeometryError('direction: skillion expects downslope, not a ridge vector')
        direction = _unit(down_slope_unit, 'down_slope_unit')

    xmin, zmin, xmax, zmax = footprint.bounds
    reference = (xmin + (xmax - xmin) / 2, zmin + (zmax - zmin) / 2)
    diagonal = math.hypot(xmax - xmin, zmax - zmin)
    tolerance = max(1e-10, diagonal * 1e-11)
    def projected(point):
        return (point[0] - reference[0]) * direction[0] + (point[1] - reference[1]) * direction[1]
    projections = [projected(point) for point in ring]
    minimum, maximum = min(projections), max(projections)
    span = maximum - minimum
    if span <= tolerance:
        raise RoofGeometryError('direction: footprint has no width along the slope')
    middle = minimum + span / 2
    eave = max(base, height - roof_height)

    def elevation(point):
        value = projected(point)
        if roof_shape == 'gabled':
            distance = abs(value - middle)
            if distance <= tolerance:
                return height
            fraction = min(1., max(0., distance / (span / 2)))
        else:
            fraction = min(1., max(0., (value - minimum) / span))
        if fraction <= 1e-13:
            return height
        if fraction >= 1 - 1e-13:
            return eave
        return height - roof_height * fraction

    intersections = {}
    roof_rings = [ring]
    if roof_shape == 'gabled':
        for i, (a, b) in enumerate(zip(ring, ring[1:] + ring[:1])):
            sa, sb = projections[i] - middle, projections[(i + 1) % len(ring)] - middle
            if sa * sb < 0:
                t = sa / (sa - sb)
                intersections[i] = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
        ridge_center = (reference[0] + direction[0] * middle, reference[1] + direction[1] * middle)
        extent = diagonal * 2
        line = LineString([(ridge_center[0] - ridge[0] * extent, ridge_center[1] - ridge[1] * extent),
                           (ridge_center[0] + ridge[0] * extent, ridge_center[1] + ridge[1] * extent)])
        pieces = [part for part in split(footprint, line).geoms if part.area > 0]
        if len(pieces) < 2:
            raise RoofGeometryError('ridge: line did not split footprint')
        known = ring + list(intersections.values())
        roof_rings = []
        for piece in pieces:
            if not isinstance(piece, Polygon) or piece.interiors:
                raise RoofGeometryError('ridge: unsupported split topology')
            points = []
            for point in list(piece.exterior.coords)[:-1]:
                # Use exactly the same edge/ridge crossing in roof and wall.
                nearest = min(known, key=lambda candidate: math.dist(point, candidate))
                if math.dist(point, nearest) > tolerance * 8:
                    raise RoofGeometryError('ridge: unexpected clipping vertex')
                points.append(nearest)
            roof_rings.append(_clean_ring(points))
        clipped_area = sum(Polygon(points).area for points in roof_rings)
        if abs(clipped_area - footprint.area) > max(1e-8, footprint.area * 1e-10):
            raise RoofGeometryError('ridge: clipping failed to preserve footprint area')

    roof, walls = MeshData(), MeshData()
    roof_triangles = sum(_surface(roof, points, elevation, True) for points in roof_rings)
    floor_triangles = _surface(roof, ring, lambda point: base, False)
    for i, (a, b) in enumerate(zip(ring, ring[1:] + ring[:1])):
        dx, dz = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dz)
        normal = (dz / length, 0., -dx / length)
        points = [(a[0], base, a[1]), (a[0], elevation(a), a[1])]
        if i in intersections:
            x, z = intersections[i]
            points.append((x, height, z))
        points.extend(((b[0], elevation(b), b[1]), (b[0], base, b[1])))
        _face(walls, points, normal)
    for mesh in (roof, walls):
        if not all(math.isfinite(value) for point in mesh.positions + mesh.normals for value in point):
            raise RoofGeometryError('geometry: non-finite output')
        if any(point[1] < base or point[1] > height for point in mesh.positions):
            raise RoofGeometryError('geometry: exceeded absolute height range')
    if max(point[1] for point in roof.positions) != height:
        raise RoofGeometryError('geometry: source top height not reached')
    return RoofShell(roof, walls, {
        'roof_shape': roof_shape, 'base': base, 'height': height,
        'roof_height': roof_height, 'eave_height': eave,
        'footprint_area_m2': footprint.area,
        'roof_triangles': roof_triangles, 'floor_triangles': floor_triangles,
        'wall_triangles': len(walls.indices) // 3,
        'assumption': 'centred symmetric ridge' if roof_shape == 'gabled' else 'single planar slope',
        'direction_semantics': 'ridge unit' if roof_shape == 'gabled' else 'downslope unit',
    })


def append_roof_shell(roof_mesh, wall_mesh, rings, **parameters):
    """Atomically append a valid shell to existing Mesh-compatible accumulators.

    The caller must NOT also call Mesh.polygon for this building: this function
    already supplies walls, roof and floor at the supplied absolute elevations.
    On rejected input neither mesh is modified; failures are explicit.
    """
    result = build_roof_shell(rings, **parameters)
    for mesh in (roof_mesh, wall_mesh):
        if not all(isinstance(getattr(mesh, name, None), list) for name in ('positions', 'normals', 'indices')):
            raise RoofGeometryError('target: expected Mesh lists positions/normals/indices')
        if len(mesh.positions) != len(mesh.normals):
            raise RoofGeometryError('target: position/normal lengths differ')
    for destination, source in ((roof_mesh, result.roof), (wall_mesh, result.walls)):
        offset = len(destination.positions)
        destination.positions.extend(source.positions)
        destination.normals.extend(source.normals)
        destination.indices.extend(index + offset for index in source.indices)
    return result.stats
