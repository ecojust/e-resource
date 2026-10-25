"""Focused, asset-free checks for sourced gabled/skillion closed shells.

Run: python source/city/check_roof_geometry.py
Or audit qualified source inputs and write a reproducible report:
  python source/city/check_roof_geometry.py --qualified qualified-roofs.json \
      --report geometry-validation.json
No model/source-data files are created or modified.
"""
import argparse
from collections import defaultdict
import copy
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import unittest

import numpy as np
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

from roof_geometry import MeshData, RoofGeometryError, append_roof_shell, build_roof_shell


RECTANGLE = [(0., 0.), (12., 0.), (12., 8.), (0., 8.)]


def triangles(shell):
    for mesh in (shell.roof, shell.walls):
        for offset in range(0, len(mesh.indices), 3):
            indices = mesh.indices[offset:offset + 3]
            yield [mesh.positions[i] for i in indices], [mesh.normals[i] for i in indices]


def check_shell(test, shell, ring, base, height):
    footprint = Polygon(ring)
    edges = defaultdict(list)
    top_projection = []
    # Shift origin before volume summation for stable tests far from (0,0,0).
    reference = np.array([ring[0][0], base, ring[0][1]], dtype=float)
    volume = 0.
    for points, normals in triangles(shell):
        a, b, c = np.asarray(points, dtype=float)
        cross = np.cross(b - a, c - a)
        test.assertGreater(np.linalg.norm(cross), 0, 'no degenerate triangle')
        geometric = cross / np.linalg.norm(cross)
        for normal in normals:
            test.assertAlmostEqual(np.linalg.norm(normal), 1., places=10)
            test.assertGreater(np.dot(geometric, normal), 1 - 1e-9, 'normal follows outward winding')
        if geometric[1] > 1e-8:
            top_projection.append(Polygon([(x, z) for x, y, z in points]))
        volume += np.dot(a - reference, np.cross(b - reference, c - reference)) / 6
        for point in points:
            test.assertTrue(np.isfinite(point).all())
            test.assertGreaterEqual(point[1], base)
            test.assertLessEqual(point[1], height)
            test.assertLessEqual(footprint.distance(Point(point[0], point[2])), 1e-8)
        for a, b in zip(points, points[1:] + points[:1]):
            a, b = tuple(a), tuple(b)
            key = tuple(sorted((a, b)))
            edges[key].append(1 if (a, b) == key else -1)
    for edge, uses in edges.items():
        test.assertEqual(len(uses), 2, f'closed shell edge {edge}: {uses}')
        test.assertEqual(sum(uses), 0, f'edge orientation {edge}')
    test.assertGreater(volume, 0, 'positive signed volume means outward shell')
    test.assertAlmostEqual(unary_union(top_projection).symmetric_difference(footprint).area, 0., places=8)
    all_points = shell.roof.positions + shell.walls.positions
    test.assertEqual(min(point[1] for point in all_points), base)
    test.assertEqual(max(point[1] for point in all_points), height)
    return volume


class RoofGeometryChecks(unittest.TestCase):
    def test_rectangular_roofs_have_exact_volume_and_closed_outward_shell(self):
        for shape, direction in [('gabled', {'ridge_unit': (1., 0.)}),
                                 ('skillion', {'down_slope_unit': (0., 1.)})]:
            with self.subTest(shape=shape):
                shell = build_roof_shell([RECTANGLE], base=3, height=17, roof_height=4,
                                        roof_shape=shape, **direction)
                volume = check_shell(self, shell, RECTANGLE, 3, 17)
                self.assertAlmostEqual(volume, 12 * 8 * (17 - 3 - 4 / 2), places=8)
                self.assertEqual(shell.stats['eave_height'], 13)
                self.assertEqual(shell.stats['roof_triangles'], 4 if shape == 'gabled' else 2)
                # No horizontal roof cap is left at total height under a slope.
                upward = [normal for normal in shell.roof.normals if normal[1] > 0]
                self.assertTrue(all(normal[1] < 1 for normal in upward))

    def test_zero_eave_height_is_a_closed_wedge(self):
        for shape, direction in [('gabled', {'ridge_unit': (1., 0.)}),
                                 ('skillion', {'down_slope_unit': (0., 1.)})]:
            with self.subTest(shape=shape):
                shell = build_roof_shell([RECTANGLE], base=5, height=9, roof_height=4,
                                        roof_shape=shape, **direction)
                self.assertAlmostEqual(check_shell(self, shell, RECTANGLE, 5, 9), 12 * 8 * 2, places=8)
                self.assertEqual(shell.stats['eave_height'], 5)
        shell = build_roof_shell([RECTANGLE], base=0, height=4, roof_height=4,
                                roof_shape='gabled', ridge_unit=(1., 0.))
        check_shell(self, shell, RECTANGLE, 0, 4)

    def test_decimal_zero_eave_roundoff_is_bounded_by_ulps(self):
        for shape, direction in [('gabled', {'ridge_unit': (1., 0.)}),
                                 ('skillion', {'down_slope_unit': (0., 1.)})]:
            shell = build_roof_shell([RECTANGLE], base=7.2, height=9.2, roof_height=2,
                                    roof_shape=shape, **direction)
            check_shell(self, shell, RECTANGLE, 7.2, 9.2)
            self.assertEqual(shell.stats['eave_height'], 7.2)
            with self.assertRaises(RoofGeometryError):
                build_roof_shell([RECTANGLE], base=7.2, height=9.2, roof_height=2 + 1e-9,
                                 roof_shape=shape, **direction)

    def test_rotation_clockwise_and_large_offset(self):
        angle = math.radians(31)
        c, s = math.cos(angle), math.sin(angle)
        def rotate(point):
            x, z = point
            return (x * c - z * s + 100000., x * s + z * c - 200000.)
        ring = [rotate(point) for point in reversed(RECTANGLE)]
        for shape, direction in [('gabled', {'ridge_unit': (c, s)}),
                                 ('skillion', {'down_slope_unit': (-s, c)})]:
            shell = build_roof_shell([ring + ring[:1]], base=2, height=14, roof_height=3,
                                    roof_shape=shape, **direction)
            volume = check_shell(self, shell, ring, 2, 14)
            self.assertAlmostEqual(volume, 12 * 8 * (12 - 1.5), places=6)

    def test_near_rectangular_clip_keeps_oblique_footprint_and_ridge_height(self):
        ring = [(0., 0.), (12., .2), (11.8, 8.), (-.3, 7.8)]
        for shape, direction in [('gabled', {'ridge_unit': (.8, .6)}),
                                 ('skillion', {'down_slope_unit': (.6, -.8)})]:
            shell = build_roof_shell([ring], base=0, height=12, roof_height=3,
                                    roof_shape=shape, **direction)
            check_shell(self, shell, ring, 0, 12)
            self.assertAlmostEqual(shell.stats['footprint_area_m2'], Polygon(ring).area)

    def test_direction_reversal_semantics(self):
        kwargs = dict(base=0, height=12, roof_height=4)
        a = build_roof_shell([RECTANGLE], roof_shape='gabled', ridge_unit=(1., 0.), **kwargs)
        b = build_roof_shell([RECTANGLE], roof_shape='gabled', ridge_unit=(-1., 0.), **kwargs)
        self.assertEqual(set(a.roof.positions), set(b.roof.positions), 'ridge axes are 180-degree equivalent')
        a = build_roof_shell([RECTANGLE], roof_shape='skillion', down_slope_unit=(0., 1.), **kwargs)
        b = build_roof_shell([RECTANGLE], roof_shape='skillion', down_slope_unit=(0., -1.), **kwargs)
        def top_at(shell, x, z):
            return max(y for xx, y, zz in shell.roof.positions if xx == x and zz == z)
        self.assertEqual((top_at(a, 0, 0), top_at(a, 0, 8)), (12, 8))
        self.assertEqual((top_at(b, 0, 0), top_at(b, 0, 8)), (8, 12))

    def test_collinear_and_duplicate_input_vertices_preserve_closed_shell(self):
        ring = [(0., 0.), (4., 0.), (12., 0.), (12., 0.), (12., 8.), (0., 8.), (0., 0.)]
        shell = build_roof_shell([ring], base=0, height=9, roof_height=2,
                                roof_shape='gabled', ridge_unit=(1., 0.))
        check_shell(self, shell, RECTANGLE, 0, 9)

    def test_append_uses_existing_mesh_offsets_and_rejects_atomically(self):
        roof, walls = MeshData(), MeshData()
        roof.vertices([(1., 2., 3.)], (0., 1., 0.))
        walls.vertices([(1., 2., 3.), (4., 5., 6.)], (1., 0., 0.))
        stats = append_roof_shell(roof, walls, [RECTANGLE], base=0, height=9, roof_height=2,
                                 roof_shape='gabled', ridge_unit=(1., 0.))
        self.assertGreaterEqual(min(roof.indices), 1)
        self.assertGreaterEqual(min(walls.indices), 2)
        self.assertEqual(stats['height'], 9)
        self.assertLess(max(roof.indices), len(roof.positions))
        before = copy.deepcopy((roof, walls))
        with self.assertRaises(RoofGeometryError):
            append_roof_shell(roof, walls, [RECTANGLE], base=0, height=9, roof_height=10,
                              roof_shape='gabled', ridge_unit=(1., 0.))
        self.assertEqual((roof, walls), before)

    def test_invalid_sources_fail_explicitly(self):
        valid = dict(rings=[RECTANGLE], base=0, height=9, roof_height=2,
                     roof_shape='gabled', ridge_unit=(1., 0.))
        changes = [
            {'roof_height': 0}, {'roof_height': -1}, {'roof_height': 10},
            {'height': 0}, {'height': float('inf')}, {'base': float('nan')},
            {'ridge_unit': None}, {'ridge_unit': (0., 0.)}, {'ridge_unit': (2., 0.)},
            {'ridge_unit': (float('nan'), 0.)}, {'down_slope_unit': (1., 0.)},
            {'roof_shape': 'hipped'}, {'rings': [RECTANGLE, [(1, 1), (2, 1), (2, 2), (1, 2)]]},
            {'rings': [[(0, 0), (4, 4), (0, 4), (4, 0)]]},
            {'rings': [[(0, 0), (float('inf'), 0), (2, 3)]]},
            {'rings': [[(0, 0), (1, 1), (2, 2)]]},
        ]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(RoofGeometryError):
                build_roof_shell(**(valid | change))


def audit_qualified(path):
    """Independently audit every qualified record without generating a GLB."""
    from build_district_models import cleaned_ring
    path = Path(path)
    contents = path.read_bytes()
    document = json.loads(contents)
    records = document['roofs']
    counts, passed, failures = defaultdict(int), 0, []
    seen = set()
    for item in records:
        key = item.get('key') or item['id']
        try:
            if key in seen:
                raise AssertionError('duplicate qualified source key')
            seen.add(key)
            if item['geometry']['type'] != 'Polygon':
                raise AssertionError('expected qualified single Polygon')
            rings = [cleaned_ring(ring, item['origin'], i == 0)
                     for i, ring in enumerate(item['geometry']['coordinates'])]
            direction = {name: item[name] for name in ('ridge_unit', 'down_slope_unit') if name in item}
            shell = build_roof_shell(rings, base=item['base'], height=item['height'],
                                    roof_height=item['roof_height'], roof_shape=item['roof_shape'], **direction)
            check_shell(unittest.TestCase(), shell, rings[0], item['base'], item['height'])
            passed += 1
            counts[item['roof_shape']] += 1
        except (AssertionError, ValueError, TypeError, IndexError, KeyError) as exc:
            failures.append({'key': key, 'roof_shape': item.get('roof_shape'), 'error': str(exc)})
    return {
        'input_qualification': str(path.resolve()),
        'input_qualification_sha256': hashlib.sha256(contents).hexdigest(),
        'input_qualification_complete': document.get('complete'),
        'qualified_records': len(records), 'passed_records': passed,
        'passed_by_shape': dict(sorted(counts.items())), 'failures': failures,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--qualified', type=Path, help='Run full shell checks on every qualified roof')
    parser.add_argument('--report', type=Path, help='Write validation JSON; does not write models or source data')
    args = parser.parse_args()
    loader = unittest.TestLoader()
    result = unittest.TextTestRunner(verbosity=2).run(loader.loadTestsFromTestCase(RoofGeometryChecks))
    module = Path(__file__).with_name('roof_geometry.py')
    report = {
        'schema_version': 1,
        'generated_utc': datetime.now(timezone.utc).isoformat(),
        'module': str(module.resolve()),
        'module_sha256': hashlib.sha256(module.read_bytes()).hexdigest(),
        'audit_script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'test_groups': loader.getTestCaseNames(RoofGeometryChecks),
        'test_group_count': result.testsRun,
        'test_groups_passed': result.wasSuccessful(),
        'checks': {
            'boundary_closure': 'Every exactly coordinate-welded shell edge occurs twice with opposite orientation.',
            'outward_normals': 'Every nondegenerate triangle agrees with its unit normals; shell signed volume is positive.',
            'source_height': 'All generated vertices stay within supplied absolute base/top; extrema equal both supplied values.',
            'footprint_area': 'Upward triangle projection union matches the input footprint to eight decimal places in square metres; vertices are within 1e-8m of the polygon.',
            'no_extra_roof_volume': 'Unit fixtures verify analytical roof volume and no retained flat top cap under pitched roofs.',
        },
        'precision_notice': 'Numerical tolerances verify generated mesh consistency only; they do not establish survey, source-footprint or architectural accuracy.',
    }
    if args.qualified:
        report['qualified_audit'] = audit_qualified(args.qualified)
    report['status'] = 'pass' if result.wasSuccessful() and not report.get('qualified_audit', {}).get('failures') else 'fail'
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({
        'status': report['status'], 'test_groups': report['test_group_count'],
        'qualified_records': report.get('qualified_audit', {}).get('qualified_records'),
        'passed_by_shape': report.get('qualified_audit', {}).get('passed_by_shape'),
        'report': str(args.report) if args.report else None,
    }, ensure_ascii=False))
    return 0 if report['status'] == 'pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
