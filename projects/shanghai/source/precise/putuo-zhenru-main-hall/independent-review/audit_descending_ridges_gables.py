#!/usr/bin/env python3
"""Actual v2 descending-ridge contacts and gable visibility; no geometry generation."""
from pathlib import Path
import sys
sys.dont_write_bytecode = True
import argparse, hashlib, json, math, time
from collections import defaultdict
import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from shapely.strtree import STRtree

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent
BASE = SOURCE.parent
sys.path.insert(0, str(BASE / 'independent-review'))
from actual_glb import loadraw, enu_tri, need, filemeta

FREEZE_SHA = '02929a28105be0fa9765a9d0e3105279c6e41f67d6aa7667c570cd405ea25056'
BASELINE_SHA = 'b9d4c8981740c19a22ced43d825e643b04fb42960cb113b13ae605e02e3106f9'
POSITIVE_EMBED = 0.00001

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def polygons(geometry):
    if geometry.is_empty:
        return []
    return [geometry] if geometry.geom_type == 'Polygon' else [p for p in getattr(geometry, 'geoms', []) if p.geom_type == 'Polygon']

def clip(vertices, plane):
    out = []
    if not vertices:
        return out
    for a, b in zip(vertices, vertices[1:] + vertices[:1]):
        fa, fb = float(plane @ [*a, 1]), float(plane @ [*b, 1])
        if fa >= 0:
            out.append(a)
        if (fa >= 0) != (fb >= 0):
            t = fa / (fa - fb)
            out.append([a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])])
    return out

class Scene:
    def __init__(self, path, rotation):
        self.raw = loadraw(path)
        self.rotation = rotation
        self.labels = defaultdict(list)
        for key in self.raw['parts']:
            self.labels[key[0]].append(key)
        self.cache, self.cell_cache, self.projection_cache = {}, {}, {}
        self.cell_diagnostics = {}
        self.rejected_interval_witnesses = []
        self.ray_cache = None

    def part(self, label):
        need(len(self.labels[label]) == 1, 'Missing/repeated required solid: ' + label)
        return self.raw['parts'][self.labels[label][0]]

    def triangles(self, label):
        if label not in self.cache:
            self.cache[label] = enu_tri(self.part(label)) @ self.rotation
        return self.cache[label]

    def directed_bytes(self, label):
        p = self.part(label)
        i = p['indices'].ravel()
        return np.concatenate([p['pos'][i], p['norm'][i]], axis=1).astype('<f4').tobytes()

    def yz_projection(self, label):
        if label not in self.projection_cache:
            t = self.triangles(label)
            p = [Polygon(tri[:, [1, 2]]) for tri in t]
            self.projection_cache[label] = unary_union([q for q in p if q.area > 1e-10])
        return self.projection_cache[label]

    def cells(self, label):
        """Overlay actual upward and downward facets to prove one vertical interval."""
        if label in self.cell_cache:
            return self.cell_cache[label]
        up, down = [], []
        for t in self.triangles(label):
            nz = np.cross(t[1] - t[0], t[2] - t[0])[2]
            if abs(nz) < 1e-11:
                continue
            poly = Polygon(t[:, :2])
            plane = np.linalg.solve(np.column_stack([t[:, :2], np.ones(3)]), t[:, 2])
            (up if nz > 0 else down).append((poly, plane))
        need(up and down, 'Solid lacks upper/lower heightfield: ' + label)
        upper_union = unary_union([p for p, _ in up])
        lower_union = unary_union([p for p, _ in down])
        need(abs(sum(p.area for p, _ in up) - upper_union.area) < 1e-7, 'Multiple upward intervals: ' + label)
        need(abs(sum(p.area for p, _ in down) - lower_union.area) < 1e-7, 'Multiple downward intervals: ' + label)
        need(upper_union.symmetric_difference(lower_union).area < 1e-7, 'Top/bottom footprint mismatch: ' + label)
        tree = STRtree([p for p, _ in down])
        rows = []
        excluded_cap_slivers = []
        for p, top in up:
            for j in tree.query(p, predicate='intersects'):
                q, bottom = down[int(j)]
                for cell in polygons(p.intersection(q)):
                    if cell.area <= 1e-12:
                        continue
                    verts = list(cell.exterior.coords[:-1])
                    minimum_thickness = min(float((top - bottom) @ [*xy, 1]) for xy in verts)
                    if minimum_thickness <= -1e-7:
                        steepness = max(float(np.linalg.norm(top[:2])), float(np.linalg.norm(bottom[:2])))
                        need(cell.area < 1e-7 and steepness > 10000, 'Substantial inverted vertical interval: ' + label)
                        excluded_cap_slivers.append({'area_m2': cell.area, 'bounds_m': list(cell.bounds), 'minimum_affine_thickness_m': minimum_thickness, 'maximum_surface_slope': steepness})
                        continue
                    rows.append({'polygon': cell, 'top': top, 'bottom': bottom})
        excluded_area = sum(q['area_m2'] for q in excluded_cap_slivers)
        need(abs(sum(r['polygon'].area for r in rows) - upper_union.area) < 1e-7 + excluded_area, 'Interior facet overlay incomplete: ' + label)
        self.cell_diagnostics[label] = {'actual_upward_projection_area_m2': upper_union.area, 'valid_interior_cell_area_m2': sum(r['polygon'].area for r in rows), 'excluded_nearly_vertical_cap_slivers': excluded_cap_slivers, 'excluded_sliver_area_m2': excluded_area, 'whole_solid_vertical_monotonicity_claimed': not excluded_cap_slivers}
        self.cell_cache[label] = rows
        return rows

    def interval(self, label, xy):
        """Independent actual triangle ray: require exactly one lower/upper crossing."""
        triangles = self.triangles(label)
        a = triangles[:, 0, :2]
        b, c, d = triangles[:, 1, :2] - a, triangles[:, 2, :2] - a, np.asarray(xy) - a
        det = b[:, 0] * c[:, 1] - b[:, 1] * c[:, 0]
        ix = np.flatnonzero(abs(det) > 1e-11)
        b, c, d, det, t = b[ix], c[ix], d[ix], det[ix], triangles[ix]
        u = (d[:, 0] * c[:, 1] - d[:, 1] * c[:, 0]) / det
        v = (b[:, 0] * d[:, 1] - b[:, 1] * d[:, 0]) / det
        keep = (u >= -1e-8) & (v >= -1e-8) & (u + v <= 1 + 1e-8)
        zs = t[:, 0, 2] + u * (t[:, 1, 2] - t[:, 0, 2]) + v * (t[:, 2, 2] - t[:, 0, 2])
        groups = []
        for height, sign in sorted(zip(zs[keep], np.sign(det[keep]))):
            if groups and abs(groups[-1][0] - height) < 1e-6:
                if groups[-1][1] != sign:
                    self.rejected_interval_witnesses.append({'label': label, 'xy_m': list(xy), 'reason': 'opposite coincident surface crossings'})
                    return None
            else:
                groups.append((float(height), float(sign)))
        if not (len(groups) == 2 and groups[0][1] == -1 and groups[1][1] == 1):
            self.rejected_interval_witnesses.append({'label': label, 'xy_m': list(xy), 'reason': 'not exactly one outward-oriented interval', 'actual_crossings_z_sign': groups})
            return None
        return groups[0][0], groups[1][0]

    def contact(self, left, right, restrict=None):
        a, b = self.cells(left), self.cells(right)
        tree = STRtree([r['polygon'] for r in b])
        regions, witnesses = [], []
        for ca in a:
            for j in tree.query(ca['polygon'], predicate='intersects'):
                cb = b[int(j)]
                common = ca['polygon'].intersection(cb['polygon'])
                if restrict is not None:
                    common = common.intersection(restrict)
                for poly in polygons(common):
                    if poly.area <= 1e-12:
                        continue
                    vertices = [list(x) for x in poly.exterior.coords[:-1]]
                    p1, p2 = ca['top'] - cb['bottom'], cb['top'] - ca['bottom']
                    p1, p2 = p1.copy(), p2.copy()
                    p1[2] -= POSITIVE_EMBED
                    p2[2] -= POSITIVE_EMBED
                    clipped = clip(clip(vertices, p1), p2)
                    if len(clipped) < 3:
                        continue
                    region = Polygon(clipped)
                    if region.area <= 1e-10:
                        continue
                    point = region.representative_point()
                    xy = [point.x, point.y]
                    ia, ib = self.interval(left, xy), self.interval(right, xy)
                    if ia is None or ib is None:
                        continue  # Reject this candidate witness; never bridge a ray cavity.
                    overlap = min(ia[1], ib[1]) - max(ia[0], ib[0])
                    need(overlap >= POSITIVE_EMBED - 1e-7, 'Affine clipped contact failed actual ray')
                    regions.append(region)
                    witnesses.append({'xy_m': xy, 'signed_interval_overlap_m': overlap, 'positive_cell_area_m2': region.area})
        contact = unary_union(regions)
        need(abs(sum(r.area for r in regions) - contact.area) < 1e-7, 'Contact regions overlap unexpectedly')
        return {'left': left, 'right': right, 'passed': contact.area > 1e-8 and bool(witnesses), 'strict_positive_contact_area_m2': contact.area, 'strict_interior_witness_count': len(witnesses), 'minimum_witness_overlap_m': min((w['signed_interval_overlap_m'] for w in witnesses), default=None), 'witnesses': witnesses, 'single_vertical_interval_verified_at_every_retained_witness': True}

    def prepare_rays(self):
        if self.ray_cache is not None:
            return
        data, lows, highs = [], [], []
        for key, p in self.raw['parts'].items():
            t = enu_tri(p) @ self.rotation
            data.append((key, t))
            lows.append(t.min(axis=(0, 1)))
            highs.append(t.max(axis=(0, 1)))
        self.ray_cache = (data, np.asarray(lows), np.asarray(highs))

    def ray(self, origin, direction):
        self.prepare_rays()
        data, low, high = self.ray_cache
        direction = np.asarray(direction, float)
        direction /= np.linalg.norm(direction)
        near = np.full(len(low), -np.inf)
        far = np.full(len(low), np.inf)
        valid = np.ones(len(low), bool)
        for axis in range(3):
            if abs(direction[axis]) < 1e-12:
                valid &= (origin[axis] >= low[:, axis] - 1e-8) & (origin[axis] <= high[:, axis] + 1e-8)
            else:
                q1, q2 = (low[:, axis] - origin[axis]) / direction[axis], (high[:, axis] - origin[axis]) / direction[axis]
                near = np.maximum(near, np.minimum(q1, q2))
                far = np.minimum(far, np.maximum(q1, q2))
        candidates = np.flatnonzero(valid & (far >= np.maximum(near, 0)))
        hits = []
        for i in candidates:
            key, t = data[int(i)]
            e1, e2 = t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]
            h = np.cross(np.broadcast_to(direction, e2.shape), e2)
            det = np.einsum('ij,ij->i', e1, h)
            ok = abs(det) > 1e-11
            inv = np.divide(1., det, out=np.zeros_like(det), where=ok)
            s = np.asarray(origin) - t[:, 0]
            u = inv * np.einsum('ij,ij->i', s, h)
            q = np.cross(s, e1)
            v = inv * (q @ direction)
            distance = inv * np.einsum('ij,ij->i', e2, q)
            good = ok & (u >= -1e-8) & (v >= -1e-8) & (u + v <= 1 + 1e-8) & (distance > 0)
            if good.any():
                hits.append({'distance_m': float(distance[good].min()), 'label': key[0], 'material': key[1]})
        return sorted(hits, key=lambda h: h['distance_m'])

def run(args):
    started = time.monotonic()
    lock = SOURCE / 'source-freeze.json'
    need(sha(lock) == FREEZE_SHA, 'Wrong frozen source revision')
    freeze = json.loads(lock.read_bytes())
    for entry in freeze['files']:
        actual = filemeta(SOURCE / entry['path'])
        need(all(actual[k] == entry[k] for k in ['bytes', 'sha256']), 'Frozen input changed: ' + entry['path'])
    calibration = json.loads((SOURCE / 'calibration.json').read_bytes())
    old_cal = json.loads((BASE / 'calibration.json').read_bytes())
    need(calibration['estimated'] == old_cal['estimated'] and calibration['orientation'] == old_cal['orientation'], 'Roof calibration changed')
    angle = math.radians(calibration['orientation']['model_x_axis_degrees_ccw_from_east'])
    rotation = np.array([[math.cos(angle), -math.sin(angle), 0], [math.sin(angle), math.cos(angle), 0], [0, 0, 1.]])
    old = Scene(BASE / 'run-v1/raw/putuo-zhenru-main-hall-raw.glb', rotation)
    new = Scene(args.raw, rotation)
    need(old.raw['raw']['sha256'] == BASELINE_SHA, 'Wrong baseline actual raw')
    structure = json.loads(args.structure_report.read_bytes())
    need(structure['structure_passed'] and structure['raw']['sha256'] == new.raw['raw']['sha256'], 'Missing new actual structure PASS')
    for field, name in [('source_geometry_sha256', 'geometry-input.json'), ('calibration_sha256', 'calibration.json')]:
        need(new.raw['doc']['extras'][field] == sha(SOURCE / name), 'New raw/source mismatch')
    need(new.raw['doc']['extras']['id'] == 'putuo-zhenru-main-hall', 'Wrong model')
    labels = [f'ridge/descending-gable-{sx}-{sy}' for sx in [-1, 1] for sy in [-1, 1]]
    fixed = [f'gable/{s}/closed-infill' for s in [-1, 1]] + ['ridge/continuous-main-ridge'] + [f'roof/field{i}/continuous-substrate' for i in range(4)] + [f'ridge/continuous-hip-{sx}-{sy}' for sx in [-1, 1] for sy in [-1, 1]]
    preserved = []
    for label in fixed:
        a, b = old.directed_bytes(label), new.directed_bytes(label)
        material = old.labels[label][0][1]
        need(a == b and old.raw['materials'][material] == new.raw['materials'][material], 'Required unchanged neighbor changed: ' + label)
        preserved.append({'label': label, 'directed_position_normal_sha256': hashlib.sha256(a).hexdigest(), 'material_equal': True, 'passed': True})
    fills, curtains, high_pitch, connections = [], [], [], []
    gg = calibration['estimated']['gable_half_length_m']
    br = calibration['estimated']['gable_break_run_m']
    for sx in [-1, 1]:
        fill = f'gable/{sx}/closed-infill'
        projection = new.yz_projection(fill)
        t = new.triangles(fill)
        n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
        normal_length = np.linalg.norm(n, axis=1)
        areas = {str(sign): float(normal_length[(n[:, 0] * sign / normal_length) > .99999].sum() / 2) for sign in [-1, 1]}
        fills.append({'label': fill, 'passed': projection.area > 10 and all(abs(v - projection.area) < 1e-5 for v in areas.values()), 'projected_fill_area_m2': projection.area, 'outward_inward_face_areas_m2': areas, 'major_side_face_normal_cosine_threshold': .99999, 'actual_local_bounds_m': [t.min(axis=(0, 1)).tolist(), t.max(axis=(0, 1)).tolist()], 'raw_directed_geometry_material_byte_exact': True})
        for sy in [-1, 1]:
            desc = f'ridge/descending-gable-{sx}-{sy}'
            before = old.yz_projection(desc).intersection(projection).area
            after = new.yz_projection(desc).intersection(projection).area
            curtains.append({'label': desc, 'passed': before > 1 and after < 1e-8, 'baseline_ridge_overlap_with_gable_yz_m2': before, 'new_ridge_overlap_with_gable_yz_m2': after, 'scope': 'Actual yz projection of the corresponding ridge versus unchanged gable fill; no camera guess or material recoloring.'})
            pitch = f'roof/field{0 if sy < 0 else 1}/continuous-substrate'
            # Explicitly restrict to the inner high-pitch half, away from the jump.
            if sx > 0:
                region = box(gg - .17, -br if sy < 0 else 0, gg - .005, 0 if sy < 0 else br)
            else:
                region = box(-gg + .005, -br if sy < 0 else 0, -gg + .17, 0 if sy < 0 else br)
            check = new.contact(desc, pitch, region)
            check['inner_high_pitch_restriction_bounds_m'] = list(region.bounds)
            high_pitch.append(check)
            connections.append(new.contact('ridge/continuous-main-ridge', desc))
            connections.append(new.contact(desc, f'ridge/continuous-hip-{sx}-{sy}'))

    native_path = BASE / 'run-v1/native/native-render-report.json'
    native = json.loads(native_path.read_bytes())
    need(native['source_glb_sha256'] == BASELINE_SHA, 'Native camera report is not baseline-bound')
    visibility = []
    gable = 'gable/-1/closed-infill'
    t = old.triangles(gable)
    normal = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
    indices = np.flatnonzero(normal[:, 0] / np.linalg.norm(normal, axis=1) < -.99999)
    # Select before inspecting new visibility: twelve largest actual exterior facets.
    indices = sorted(indices, key=lambda i: np.linalg.norm(normal[i]), reverse=True)[:12]
    targets = [t[i].mean(axis=0) for i in indices]
    for render in native['renders']:
        if render['camera']['name'] not in ['Full_hall_three_quarter', 'Historical_reference_rear_and_gable']:
            continue
        camera = render['camera']
        az, el = np.deg2rad([camera['azimuth_degrees'], camera['elevation_degrees']])
        direction_enu = np.array([-np.sin(az) * np.cos(el), -np.cos(az) * np.cos(el), -np.sin(el)])
        direction = direction_enu @ rotation
        rays = []
        for target in targets:
            origin = target - direction * 100
            before, after = old.ray(origin, direction), new.ray(origin, direction)
            need(before and after, 'Camera ray missed model')
            originally_curtain = before[0]['label'] in labels
            # Gable louvers are unchanged visible timber relief in front of the fill.
            exposed = after[0]['label'].startswith('gable/-1/')
            rays.append({'target_actual_gable_facet_center_local_m': target.tolist(), 'baseline_first_hit': before[0], 'new_first_hit': after[0], 'baseline_curtain_occlusion': originally_curtain, 'now_visible_gable_or_unchanged_timber_relief': exposed, 'passed': not originally_curtain or exposed})
        affected = [row for row in rays if row['baseline_curtain_occlusion']]
        visibility.append({'camera_role': 'full' if camera['name'] == 'Full_hall_three_quarter' else 'rear', 'camera_name': camera['name'], 'camera_source': 'Actual immutable v1 native-render-report orientation; orthographic rays through unchanged actual gable facet centers', 'passed': len(affected) >= 4 and all(row['passed'] for row in rays), 'tested_facet_centers': len(rays), 'formerly_curtain_occluded_centers': len(affected), 'rays': rays, 'photo_calibrated': False})
    need(len(visibility) == 2, 'Expected two actual native oblique cameras')
    groups = [fills, curtains, high_pitch, connections, visibility]
    passed = all(row['passed'] for group in groups for row in group)
    report = {
        'schema': 'zhenru-v2-actual-descending-ridge-gable-review-v1', 'passed': passed,
        'raw': new.raw['raw'], 'baseline_raw': old.raw['raw'],
        'source_geometry': filemeta(SOURCE / 'geometry-input.json'), 'calibration': filemeta(SOURCE / 'calibration.json'),
        'source_freeze': filemeta(lock), 'actual_structure_report': filemeta(args.structure_report), 'v1_native_report': filemeta(native_path),
        'raw_part_manifest_sha256': new.raw['side_sha256'], 'baseline_part_manifest_sha256': old.raw['side_sha256'],
        'four_ridge_labels': labels, 'required_neighbor_directed_geometry_preservation': preserved,
        'gable_fill_preservation_checks': fills, 'ridge_curtain_projection_checks': curtains,
        'high_pitch_contact_checks': high_pitch, 'ridge_connection_checks': connections,
        'actual_camera_gable_visibility_checks': visibility,
        'actual_contact_cell_diagnostics': new.cell_diagnostics,
        'rejected_candidate_interval_witnesses': new.rejected_interval_witnesses,
        'rejected_witnesses_never_counted_as_contact': True,
        'contact_method': 'Overlay actual exported upper/lower triangle projections. Intersect valid interior piecewise-planar cells and clip by both top-minus-other-bottom>=10micron inequalities; require positive projected area and independently verify every retained interior witness has exactly two actual surface crossings in each solid. Nearly vertical Float32 cap slivers that fail global interval ordering are excluded from existence-only contact witnesses and explicitly reported; no whole-solid vertical-monotonicity claim is made for those parts. No convex-hull envelope or boundary-only contact is accepted.',
        'scope': 'Only four corrected descending ridges, their unchanged roof/main/hip neighbors and the two unchanged gable fills. All other non-allowlisted geometry preservation and140bracket checks belong to the separate audit. Native camera directions are observed prior-render metadata, not photo calibration. Numeric visibility is not a new render or aesthetic acceptance.',
        'tolerances': {'positive_contact_embed_m': POSITIVE_EMBED, 'single_heightfield_area_tolerance_m2': 1e-7, 'curtain_overlap_area_tolerance_m2': 1e-8},
        'model_appearance_accepted': False, 'native_or_browser_accepted': False, 'whole_model_collision_free_claim': False,
        'geometry_generated_or_modified': False, 'elapsed_seconds': time.monotonic() - started,
    }
    need(sha(args.raw) == new.raw['raw']['sha256'] and sha(lock) == FREEZE_SHA, 'Inputs changed during audit')
    return report

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw', type=Path, required=True)
    parser.add_argument('--structure-report', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    need(out.is_relative_to(HERE) and not out.exists(), 'Use new report in this independent-review directory')
    try:
        report = run(args)
    except Exception as error:
        report = {'schema': 'zhenru-v2-actual-descending-ridge-gable-review-v1', 'passed': False, 'error': str(error), 'model_appearance_accepted': False}
    encoded = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
    need(len(encoded.encode()) < 2_000_000, 'Report exceeds bounded size')
    out.write_text(encoded)
    print(json.dumps({'report': str(out), 'passed': report['passed'], 'error': report.get('error'), 'elapsed_seconds': report.get('elapsed_seconds'), 'raw': report.get('raw')}, ensure_ascii=False))
    raise SystemExit(0 if report['passed'] else 1)

if __name__ == '__main__':
    main()
