#!/usr/bin/env python3
"""Finite independent measurements of actual Fangta GLB parts; no builder import."""
from pathlib import Path
import argparse, json, math, time
import numpy as np
from actual_glb import loadraw, enu_tri, z, need, sha, filemeta

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FREEZE_SHA = '8b5d640bdf4b83ddeda6463574a2e9a2d4ecf00fe61c8202e32064f6249a9e59'

def topology(triangles):
    vertices, inverse = np.unique(triangles.reshape(-1, 3), axis=0, return_inverse=True)
    t = inverse.reshape(-1, 3)
    directed = np.concatenate((t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]))
    edges, ix, counts = np.unique(np.sort(directed, axis=1), axis=0, return_inverse=True, return_counts=True)
    balance = np.bincount(ix, weights=np.where(directed[:, 0] < directed[:, 1], 1, -1))
    parent = list(range(len(vertices)))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for a, b in edges:
        parent[find(int(a))] = find(int(b))
    connected = len({find(i) for i in range(len(vertices))})
    chi = len(vertices) - len(edges) + len(t)
    return {'vertices': len(vertices), 'edges': len(edges), 'triangles': len(t), 'connected_components': connected, 'euler_characteristic': chi, 'genus_if_connected_closed_orientable': (2 - chi) // 2 if connected == 1 else None, 'non_two_edges': int((counts != 2).sum()), 'unpaired_edges': int((balance != 0).sum())}

def segment_hits(triangles, origin, end):
    """Moller-Trumbore intersections on the finite segment, without backface culling."""
    direction = np.asarray(end) - origin
    edge1 = triangles[:, 1] - triangles[:, 0]
    edge2 = triangles[:, 2] - triangles[:, 0]
    h = np.cross(np.broadcast_to(direction, edge2.shape), edge2)
    a = np.einsum('ij,ij->i', edge1, h)
    ok = np.abs(a) > 1e-11
    inv = np.divide(1., a, out=np.zeros_like(a), where=ok)
    s = np.asarray(origin) - triangles[:, 0]
    u = inv * np.einsum('ij,ij->i', s, h)
    q = np.cross(s, edge1)
    v = inv * (q @ direction)
    t = inv * np.einsum('ij,ij->i', edge2, q)
    hit = ok & (u >= -1e-8) & (v >= -1e-8) & (u + v <= 1 + 1e-8) & (t >= -1e-8) & (t <= 1 + 1e-8)
    return sorted(float(x) for x in t[hit])

def run(path):
    started = time.monotonic()
    raw = loadraw(path)
    lock_path = ROOT / 'raw-source-freeze.json'
    need(sha(lock_path.read_bytes()) == FREEZE_SHA, 'Wrong frozen author manifest')
    lock = json.loads(lock_path.read_bytes())
    for item in lock['files']:
        meta = filemeta(ROOT / item['file'])
        need(all(meta[k] == item[k] for k in ('bytes', 'sha256')), 'Frozen source changed: ' + item['file'])
    structure = json.loads((HERE / 'actual-raw-structure.json').read_text())
    need(structure['structure_passed'] and structure['raw']['sha256'] == raw['raw']['sha256'], 'Actual structure proof missing')
    g = json.loads((ROOT / 'geometry-input.json').read_text())
    cal = json.loads((ROOT / 'calibration.json').read_text())
    report_path = path.parent / 'geometry-report.json'
    design = json.loads(report_path.read_text())
    need(raw['doc']['extras']['id'] == g['id'] == 'songjiang-fangta-pagoda', 'Wrong model identity')
    for field, name in [('source_geometry_sha256', 'geometry-input.json'), ('calibration_sha256', 'calibration.json')]:
        need(raw['doc']['extras'][field] == design[field] == sha((ROOT / name).read_bytes()), 'Raw provenance mismatch')
    ring = np.asarray(raw['doc']['extras']['model_square_ring_enu'], float)
    need(ring.shape == (4, 2) and np.array_equal(ring, np.asarray(design['model_square_ring_enu'])), 'Actual architectural ring mismatch')
    need(design['source_owner_ring_enu_unchanged'] == g['polygon_local_east_north'], 'Owner boundary altered')
    cache = {}
    def part(label):
        if label not in cache:
            matches = [p for k, p in raw['parts'].items() if k[0] == label]
            need(len(matches) == 1, 'Missing or ambiguous actual part: ' + label)
            cache[label] = enu_tri(matches[0])
        return cache[label]
    def labels(prefix, suffix=''):
        return sorted(k[0] for k in raw['parts'] if k[0].startswith(prefix) and k[0].endswith(suffix))

    # The square wall has one central shaft plus four actual lateral tunnels:
    # a single closed orientable component of genus five, corroborated by rays.
    openings = []
    walls = []
    for v in cal['levels']:
        level = v['level']
        wall = part(f'L{level}/continuous-ring-with-reveals')
        q = topology(wall)
        need(q['connected_components'] == 1 and q['genus_if_connected_closed_orientable'] == 5, 'Wall does not contain four through tunnels')
        walls.append({'level': level, **q})
        for edge in range(4):
            record = next(x for x in design['openings'] if (x['level'], x['model_edge_id']) == (level, edge))
            a = ring[(edge + 1) % 4] * v['wall_scale']
            b = ring[edge] * v['wall_scale']
            tangent = (b - a) / np.linalg.norm(b - a)
            outward = np.array([tangent[1], -tangent[0]])
            center = (a + b) / 2
            empty = []
            solid = []
            for uf, hf in [(0, .20), (0, .40), (0, .60), (0, .80), (-.15, .35), (.15, .35), (-.15, .60), (.15, .60)]:
                xy = center + tangent * (uf * record['width_m'])
                height = record['bottom_m'] + hf * record['height_m']
                start = np.r_[xy + outward * .06, height]
                end = np.r_[xy - outward * (v['wall_thickness'] + .06), height]
                hits = segment_hits(wall, start, end)
                need(not hits, f'Blocked actual doorway L{level} edge{edge}')
                empty.append({'width_fraction': uf, 'height_fraction': hf, 'triangle_hits': len(hits)})
            for uf in [-.80, .80]:
                xy = center + tangent * (uf * record['width_m'])
                height = record['bottom_m'] + .45 * record['height_m']
                hits = segment_hits(wall, np.r_[xy + outward * .06, height], np.r_[xy - outward * (v['wall_thickness'] + .06), height])
                need(len(hits) >= 2, 'Adjacent solid wall control failed')
                solid.append({'width_fraction': uf, 'triangle_hits': len(hits)})
            openings.append({'level': level, 'model_edge_id': edge, 'clear_segment_rays': empty, 'solid_flank_controls': solid, 'geographic_phase_verified': False})
    need(len(openings) == 36, 'Expected 36 actual doorway checks')

    # Every actual hip seat is checked at seven positions and three offsets.
    seats = []
    contact_samples = []
    negative = {}
    for v in cal['levels']:
        level = v['level']
        roof = part(f'L{level}/continuous-curved-roof')
        inner = v['wall_scale'] * .945 if level < 9 else .075
        for corner in range(4):
            label = f'L{level}/continuous-grey-ridge-seat{corner}'
            seat = part(label)
            ridge = part(f'L{level}/continuous-upturned-corner-ridge{corner}')
            q = topology(seat)
            need(q['connected_components'] == 1 and q['genus_if_connected_closed_orientable'] == 0, 'Hip seat is not one closed solid')
            seats.append({'label': label, **q})
            axis = ring[corner] / np.linalg.norm(ring[corner])
            side = np.array([-axis[1], axis[0]])
            for radial in [.05, .20, .40, .60, .80, .95, .995]:
                center = ring[corner] * (inner * (1 - radial) + v['roof_scale'] * radial)
                for lateral in [-.025, 0, .025]:
                    xy = center + side * lateral
                    sb, st, rb, rt = z(seat, xy, False), z(seat, xy, True), z(ridge, xy, False), z(roof, xy, True)
                    missing = [name for name, value in [('seat_bottom', sb), ('seat_top', st), ('ridge_bottom', rb), ('roof_top', rt)] if value is None]
                    row = {'level': level, 'corner': corner, 'radial_fraction': radial, 'lateral_m': lateral, 'ray_surfaces_missing': missing, 'substrate_top_minus_seat_bottom_m': rt - sb if None not in (rt, sb) else None, 'seat_top_minus_ridge_bottom_m': st - rb if None not in (st, rb) else None}
                    # Preserve every failed full-width contact sample; centerline support is reported separately.
                    contact_samples.append(row)
                    if missing:
                        continue
                    for kind, overlap, sign in [('substrate', rt - sb, 1), ('ridge', st - rb, -1)]:
                        if kind not in negative and overlap > 0:
                            shifted = seat.copy()
                            shifted[:, :, 2] += sign * (overlap + .005)
                            measured = rt - z(shifted, xy, False) if kind == 'substrate' else z(shifted, xy, True) - rb
                            need(measured < -.0049, 'Negative contact control did not reject')
                            negative[kind] = {'shifted_in_memory_only': True, 'induced_gap_m': measured, 'rejected': True}
    need(len(seats) == 36 and len(contact_samples) == 756, 'Hip coverage differs')

    # Trace actual stone foot -> round column -> capital -> curved header -> roof.
    porch = []
    column_labels = labels('ground-porch/', '/round-column')
    need(len(column_labels) == 12, 'Expected 12 actual porch columns')
    headers = [part(f'ground-porch/continuous-roof-bearing-header{i}') for i in range(4)]
    low_roof = part('L1/continuous-curved-roof')
    for label in column_labels:
        column = part(label)
        base_label = label.removesuffix('/round-column')
        foot = part(base_label + '/stone-foot')
        capital = part(base_label + '/capital')
        center = (column[:, :, :2].min(axis=(0, 1)) + column[:, :, :2].max(axis=(0, 1))) / 2
        inward = -center / np.linalg.norm(center)
        samples = []
        for offset in [0., .025, .05]:
            xy = center + inward * offset
            fb, ft, cb, ct, ab, at, roof_bottom = z(foot, xy, False), z(foot, xy, True), z(column, xy, False), z(column, xy, True), z(capital, xy, False), z(capital, xy, True), z(low_roof, xy, False)
            need(None not in (fb, ft, cb, ct, ab, at, roof_bottom), 'Porch support ray missed')
            intervals = [(z(h, xy, False), z(h, xy, True)) for h in headers]
            intervals = [x for x in intervals if None not in x]
            need(intervals, 'No actual header over porch column')
            connected = [(min(at, ht) - max(ab, hb), min(ht, z(low_roof, xy, True)) - max(hb, roof_bottom)) for hb, ht in intervals]
            chain = max(connected, key=lambda x: min(x))
            row = {'radial_inward_offset_m': offset, 'foot_column_overlap_m': min(ft, ct) - max(fb, cb), 'column_capital_overlap_m': min(ct, at) - max(cb, ab), 'capital_header_overlap_m': chain[0], 'header_roof_overlap_m': chain[1]}
            need(all(value > 0 for key, value in row.items() if key.endswith('_overlap_m')), 'Actual porch support gap: ' + str(row))
            samples.append(row)
        porch.append({'label': label, 'actual_center_enu_m': center.tolist(), 'topology': topology(column), 'finite_support_chain_samples': samples})

    # A hoop must be one closed genus-one shell with an actual axial void.
    # Off-axis quadrant rays avoid the central spindle and its four spokes.
    hoops = []
    spindle = part('finial/central-spindle')
    hoop_labels = labels('finial/open-annular-ring-')
    need(len(hoop_labels) == 9, 'Expected nine actual finial hoops')
    for i in range(1, 10):
        label = f'finial/open-annular-ring-{i}'
        hoop = part(label)
        q = topology(hoop)
        need(q['connected_components'] == 1 and q['genus_if_connected_closed_orientable'] == 1, 'Hoop is not a closed annular shell')
        vertices = np.unique(hoop.reshape(-1, 3), axis=0)
        radii = np.linalg.norm(vertices[:, :2], axis=1)
        inner, outer = float(radii.min()), float(radii.max())
        need(inner > .20 and outer > inner, 'Actual hoop void collapsed')
        center_z = float((vertices[:, 2].min() + vertices[:, 2].max()) / 2)
        spokes = [part(f'finial/ring{i}-radial-spoke{j}') for j in range(4)]
        clear = []
        for j in range(4):
            angle = math.pi / 4 + j * math.pi / 2
            xy = np.array([math.cos(angle), math.sin(angle)]) * (inner * .60)
            start, end = np.r_[xy, center_z - .12], np.r_[xy, center_z + .12]
            intersections = sum(len(segment_hits(t, start, end)) for t in [hoop, spindle, *spokes])
            need(intersections == 0, 'Finial open quadrant is filled')
            clear.append({'azimuth_degrees': math.degrees(angle), 'radial_distance_m': inner * .60, 'triangle_hits': intersections})
        solid_xy = np.array([(inner + outer) / 2, 0.])
        need(len(segment_hits(hoop, np.r_[solid_xy, center_z - .12], np.r_[solid_xy, center_z + .12])) >= 2, 'Hoop solid annulus control failed')
        spoke_support = []
        for j, spoke in enumerate(spokes):
            angle = j * math.pi / 2
            axis = np.array([math.cos(angle), math.sin(angle)])
            xy = axis * (inner + .012)
            st, sb, ht, hb = z(spoke, xy, True), z(spoke, xy, False), z(hoop, xy, True), z(hoop, xy, False)
            need(None not in (st, sb, ht, hb), 'Spoke/hoop contact ray missed')
            overlap = min(st, ht) - max(sb, hb)
            need(overlap > 0, 'Spoke is disconnected from hoop')
            xy2 = axis * .082
            st2, sb2, mt, mb = z(spoke, xy2, True), z(spoke, xy2, False), z(spindle, xy2, True), z(spindle, xy2, False)
            need(None not in (st2, sb2, mt, mb), 'Spoke/spindle contact ray missed')
            inner_overlap = min(st2, mt) - max(sb2, mb)
            need(inner_overlap > 0, 'Spoke is disconnected from spindle')
            spoke_support.append({'spoke': j, 'hoop_overlap_m': overlap, 'spindle_overlap_m': inner_overlap})
        hoops.append({'label': label, 'topology': q, 'actual_inner_radius_m': inner, 'actual_outer_radius_m': outer, 'actual_center_z_m': center_z, 'clear_quadrant_rays': clear, 'finite_spoke_contacts': spoke_support})

    result = {
        'schema': 'fangta-actual-roles-finite-contacts-v1',
        'passed': all(not x['ray_surfaces_missing'] and x['substrate_top_minus_seat_bottom_m'] > 0 and x['seat_top_minus_ridge_bottom_m'] > 0 for x in contact_samples),
        'hip_full_width_finite_contact_passed': all(not x['ray_surfaces_missing'] and x['substrate_top_minus_seat_bottom_m'] > 0 and x['seat_top_minus_ridge_bottom_m'] > 0 for x in contact_samples),
        'hip_centerline_contact_passed': all(not x['ray_surfaces_missing'] and x['substrate_top_minus_seat_bottom_m'] > 0 and x['seat_top_minus_ridge_bottom_m'] > 0 for x in contact_samples if x['lateral_m'] == 0),
        'hip_nonpositive_contact_samples': [x for x in contact_samples if x['ray_surfaces_missing'] or x['substrate_top_minus_seat_bottom_m'] <= 0 or x['seat_top_minus_ridge_bottom_m'] <= 0],
        'raw': raw['raw'], 'raw_part_manifest_sha256': raw['side_sha256'],
        'structure_report': filemeta(HERE / 'actual-raw-structure.json'), 'source_lock': filemeta(lock_path),
        'geometry_input': filemeta(ROOT / 'geometry-input.json'), 'calibration': filemeta(ROOT / 'calibration.json'),
        'builder_numeric_report_for_sampling_only': filemeta(report_path),
        'actual_wall_shell_topology': walls, 'central_openings_passed': True, 'porch_support_chains_passed': True, 'open_finial_hoops_passed': True, 'central_opening_count': len(openings), 'central_opening_checks': openings,
        'continuous_hip_seat_count': len(seats), 'hip_seat_topology': seats, 'hip_contact_count': len(contact_samples),
        'hip_contact_samples': contact_samples, 'hip_negative_controls': negative,
        'minimum_substrate_seat_overlap_m': min(x['substrate_top_minus_seat_bottom_m'] for x in contact_samples if x['substrate_top_minus_seat_bottom_m'] is not None),
        'minimum_seat_ridge_overlap_m': min(x['seat_top_minus_ridge_bottom_m'] for x in contact_samples if x['seat_top_minus_ridge_bottom_m'] is not None),
        'porch_column_count': len(porch), 'porch_support_checks': porch,
        'open_finial_hoop_count': len(hoops), 'open_finial_hoop_checks': hoops,
        'elapsed_seconds': time.monotonic() - started, 'selected_actual_part_count': len(cache),
        'model_appearance_accepted': False, 'native_or_browser_accepted': False, 'whole_model_collision_free_claim': False,
        'geometry_regenerated': False, 'author_inputs_or_actual_glb_modified': False,
        'scope': 'Independent actual FLOAT32 GLB triangles selected through the SHA-bound part manifest. Actual wall genus and finite face-normal segments establish 36 central apertures. All 36 connected solid hip seats have 756 finite support samples. Twelve porch support chains and nine genus-one finial hoops have finite actual contact/void tests. Closedness and normals for every part are bound separately. No builder geometry function is imported. These are finite samples, not continuous contact, all-intersection, physical structural safety, historical measurement, native visual or browser acceptance.',
    }
    need(raw['raw']['sha256'] == sha(path.read_bytes()), 'Raw changed during audit')
    need(sha(lock_path.read_bytes()) == FREEZE_SHA, 'Source freeze changed during audit')
    return result

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--raw', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    out = args.output.resolve()
    need(out.is_relative_to(HERE) and not out.exists(), 'Use a new report in independent-review')
    result = run(args.raw.resolve())
    text = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    need(len(text.encode()) < 1_500_000, 'Report exceeded bounded size')
    out.write_text(text)
    print(json.dumps({k: result[k] for k in ['passed', 'hip_full_width_finite_contact_passed', 'hip_centerline_contact_passed', 'raw', 'central_opening_count', 'continuous_hip_seat_count', 'hip_contact_count', 'minimum_substrate_seat_overlap_m', 'minimum_seat_ridge_overlap_m', 'porch_column_count', 'open_finial_hoop_count', 'elapsed_seconds']}, indent=2))
    raise SystemExit(0 if result['passed'] else 1)

if __name__ == '__main__':
    main()
