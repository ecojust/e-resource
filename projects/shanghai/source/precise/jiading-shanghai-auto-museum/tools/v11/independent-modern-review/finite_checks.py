"""Finite geometry checks over ACTUAL triangles, shared by raw and decoded assets.

No author module imports. A request specifies a question/location, not its result.
Positive contact proves a local joint only; a missing witness is not a global
collision/clearance conclusion. Every ray uses actual closed-solid intervals.
"""
from itertools import product
from pathlib import Path
import json
import numpy as np
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
from shapely.strtree import STRtree
from modern_mesh import require, filemeta, oriented_position_hash


def frame_matrix(frame):
    origin = np.asarray(frame['origin_enu_m'], float)
    basis = np.asarray(frame['axes_enu'], float)
    require(origin.shape == (3,) and basis.shape == (3, 3) and
            np.isfinite(origin).all() and np.isfinite(basis).all(), 'Invalid probe frame')
    require(np.max(abs(basis @ basis.T - np.eye(3))) < 1e-8 and
            np.linalg.det(basis) > .999999, 'Probe frame must be right-handed orthonormal')
    return origin, basis


def transformed(part, frame):
    origin, basis = frame_matrix(frame)
    return (part.triangles_enu - origin) @ basis.T


def polygons(geometry):
    if geometry.is_empty:
        return []
    if geometry.geom_type == 'Polygon':
        return [geometry] if geometry.area > 0 else []
    return [p for g in getattr(geometry, 'geoms', []) for p in polygons(g)]


def plane_clip(vertices, plane):
    """Clip a convex 2D cell by affine a*u+b*v+c >=0, without snapping."""
    if not vertices:
        return []
    result = []
    for a, b in zip(vertices, vertices[1:] + vertices[:1]):
        da, db = np.dot(plane, [*a, 1]), np.dot(plane, [*b, 1])
        if da >= 0:
            result.append(a)
        if (da < 0) != (db < 0):
            r = da / (da - db)
            result.append((np.asarray(a) + r * (np.asarray(b)-a)).tolist())
    return result


def ray_intervals(triangles, uv, cluster_tolerance_m=1e-7):
    """Line parallel to local +d. Never replace separated intervals by min/max."""
    a = triangles[:, 0, :2]
    b, c = triangles[:, 1, :2]-a, triangles[:, 2, :2]-a
    det = b[:, 0]*c[:, 1] - b[:, 1]*c[:, 0]
    good = np.flatnonzero(abs(det) > 1e-12)
    if not len(good):
        return {'state': 'clear', 'intervals_m': [], 'crossing_clusters': []}
    a, b, c, det, t = a[good], b[good], c[good], det[good], triangles[good]
    delta = np.asarray(uv)-a
    u = (delta[:, 0]*c[:, 1]-delta[:, 1]*c[:, 0])/det
    v = (b[:, 0]*delta[:, 1]-b[:, 1]*delta[:, 0])/det
    inside = (u >= -1e-10) & (v >= -1e-10) & (u+v <= 1+1e-10)
    depths = t[:, 0, 2] + u*(t[:, 1, 2]-t[:, 0, 2]) + v*(t[:, 2, 2]-t[:, 0, 2])
    hits = sorted((float(depths[i]), 1 if det[i] > 0 else -1) for i in np.flatnonzero(inside))
    groups = []
    for d, sign in hits:
        if groups and abs(d-groups[-1]['depth_m']) <= cluster_tolerance_m:
            groups[-1]['signs'].add(sign)
            groups[-1]['hit_count'] += 1
            groups[-1]['max_cluster_spread_m'] = max(groups[-1]['max_cluster_spread_m'],
                                                     abs(d-groups[-1]['depth_m']))
        else:
            groups.append({'depth_m': d, 'signs': {sign}, 'hit_count': 1, 'max_cluster_spread_m': 0.})
    intervals, valid = [], len(groups) % 2 == 0
    for i in range(0, len(groups)-1, 2):
        low, high = groups[i:i+2]
        valid = valid and low['signs'] == {-1} and high['signs'] == {1} and high['depth_m'] > low['depth_m']
        intervals.append([low['depth_m'], high['depth_m']])
    for g in groups:
        g['signs'] = sorted(g['signs'])
    return {'state': 'valid' if valid and groups else ('clear' if not groups else 'ambiguous'),
            'intervals_m': intervals if valid else [], 'crossing_clusters': groups,
            'cluster_tolerance_m': cluster_tolerance_m}


def clipped_intervals(intervals, bounds):
    return [[max(a, bounds[0]), min(b, bounds[1])] for a, b in intervals
            if min(b, bounds[1])-max(a, bounds[0]) > 1e-8]


def select_many(asset, selectors):
    require(selectors, 'No selected geometry')
    parts = [p for s in selectors for p in asset.select(s)]
    require(len({p.key for p in parts}) == len(parts), 'Overlapping selectors duplicate actual parts')
    return parts


def ray_check(asset, request):
    parts = select_many(asset, request['selectors'])
    ts = [(p, transformed(p, request['frame'])) for p in parts]
    bounds = np.asarray(request['depth_range_m'],float)
    require(bounds.shape==(2,) and np.isfinite(bounds).all() and bounds[1] > bounds[0], 'Ray depth range invalid')
    expect = request['expect']
    require(expect in ['clear', 'solid'], 'Unknown ray expectation')
    stations=np.asarray(request['points_uv_m'],float)
    require(stations.ndim==2 and stations.shape[1]==2 and len(stations)>0 and
            np.isfinite(stations).all(), 'Ray stations must be nonempty finite UV points')
    minimum=request.get('minimum_single_interval_m',1e-6)
    require(np.isfinite(minimum) and minimum>0, 'Solid ray thickness threshold must be positive and finite')
    rows = []
    for uv in request['points_uv_m']:
        intervals, ambiguous, hits = [], [], []
        for p, t in ts:
            result = ray_intervals(t, uv)
            if result['state'] == 'ambiguous':
                ambiguous.append({'key': p.key, 'ray': result})
            current = clipped_intervals(result['intervals_m'], bounds)
            if current:
                hits.append({'key': p.key, 'intervals_m': current, 'ray': result})
                intervals.extend(current)
        found = max((b-a for a, b in intervals), default=0.)
        passed = not ambiguous and (not intervals if expect == 'clear' else
                    bool(intervals) and found >= minimum)
        rows.append({'uv_m': uv, 'actual_hits': hits, 'ambiguous_parts': ambiguous,
                     'largest_individual_solid_interval_m': found, 'passed': bool(passed)})
    require(rows, 'No finite ray stations')
    return {'passed': all(r['passed'] for r in rows), 'rays': rows,
            'scope': 'Only the stated finite lines and depth intervals; no global collision or whole-opening claim.'}


def aperture_check(asset, request):
    """Wall-only through-opening proof, with opaque-neighbor negative controls.

    Entire selected solids MUST fit declared depth slab. Without this gate a
    projection of only clipped boundary faces could falsely miss an enclosing
    solid. Additional all-opaque finite rays are required by the building plan.
    """
    parts = select_many(asset, request['wall_selectors'])
    target = Polygon(request['polygon_uv_m'])
    require(target.is_valid and target.area > 0, 'Invalid aperture probe polygon')
    maximum=request['maximum_blocked_area_m2']
    require(np.isfinite(maximum) and 0<=maximum<target.area, 'Aperture blocked area allowance invalid')
    bounds = np.asarray(request['depth_range_m'],float)
    require(bounds.shape==(2,) and np.isfinite(bounds).all() and bounds[1]>bounds[0], 'Aperture depth range invalid')
    projected, actual_keys = [], []
    for p in parts:
        t = transformed(p, request['frame'])
        require(t[:, :, 2].min() >= bounds[0]-1e-7 and t[:, :, 2].max() <= bounds[1]+1e-7,
                'Aperture wall solid extends outside depth slab: ' + p.key)
        actual_keys.append(p.key)
        projected.extend(Polygon(q[:, :2]) for q in t if Polygon(q[:, :2]).area > 1e-14)
    opaque = unary_union(projected)
    blocked = target.intersection(opaque)
    negative = request['negative_controls_uv_m']
    require(negative, 'Aperture must have solid-wall negative controls')
    neg = ray_check(asset, {'selectors': request['wall_selectors'], 'frame': request['frame'],
        'depth_range_m': bounds, 'expect': 'solid', 'points_uv_m': negative,
        'minimum_single_interval_m': request.get('negative_minimum_wall_thickness_m', .01)})
    return {'passed': bool(blocked.area <= request['maximum_blocked_area_m2'] and neg['passed']),
            'actual_wall_part_keys': actual_keys, 'aperture_probe_area_m2': target.area,
            'actual_opaque_projected_overlap_m2': blocked.area,
            'wall_negative_controls': neg,
            'scope': 'Actual selected full-depth wall projections exclude the entire test aperture; panes/frames and other solids require separate controls.'}


class Facets:
    def __init__(self, part, frame):
        self.part = part
        self.t = transformed(part, frame)
        self.sides = {'up': [], 'down': []}
        self.excluded_near_parallel_triangles = 0
        for q in self.t:
            cross = np.cross(q[1]-q[0], q[2]-q[0])
            if abs(cross[2]) <= 1e-12:
                self.excluded_near_parallel_triangles += 1
                continue
            poly = Polygon(q[:, :2])
            plane = np.linalg.solve(np.column_stack([q[:, :2], np.ones(3)]), q[:, 2])
            self.sides['up' if cross[2] > 0 else 'down'].append((poly, plane))
        self.trees = {side: STRtree([p for p, z in fs]) for side, fs in self.sides.items()}
        self.bbox = self.t.min(axis=(0, 1)), self.t.max(axis=(0, 1))


def contact_witness(left, right, frame, minimum_embed_m=1e-6, maximum_cells=100000,
                    contact_mode='positive_volume'):
    """Actual four-facet affine cells + exact interval interior witness.

    No analytic author surfaces, center bbox proxies or min/max solid envelopes.
    The first strict positive-volume witness suffices only for local contact.
    """
    require(contact_mode in ['positive_volume', 'volume_or_exact_area'], 'Unknown contact mode')
    require(np.isfinite(minimum_embed_m) and minimum_embed_m >= 1e-7, 'Requested embed is below numerical interval resolution')
    require(isinstance(maximum_cells,int) and 0<maximum_cells<=1000000, 'Invalid finite facet cell budget')
    area_tolerance = 1e-9  # numerical facet-plane coincidence, NOT a general permitted model gap
    a, b = Facets(left, frame), Facets(right, frame)
    result = {'left_key': left.key, 'right_key': right.key,
              'positive_volume_contact_found': False, 'positive_area_coincidence_found': False,
              'contact_found': False, 'contact_mode': contact_mode, 'state': 'NO_WITNESS',
              'excluded_parallel_or_tiny_projection_triangles':
                  [a.excluded_near_parallel_triangles, b.excluded_near_parallel_triangles]}
    bbox_overlap = np.minimum(a.bbox[1], b.bbox[1])-np.maximum(a.bbox[0], b.bbox[0])
    if np.any(bbox_overlap[:2] <= 0) or bbox_overlap[2] < 0 or (contact_mode == 'positive_volume' and bbox_overlap[2] == 0):
        return {**result, 'state': 'DISJOINT_OR_TANGENT_AABB'}
    cells, rejected = 0, 0
    for ap, az in a.sides['up']:
        for bi in b.trees['up'].query(ap):
            bp, bz = b.sides['up'][int(bi)]
            common = ap.intersection(bp)
            if common.area <= 1e-12:
                continue
            for ai in a.trees['down'].query(common):
                adp, adz = a.sides['down'][int(ai)]
                common2 = common.intersection(adp)
                if common2.area <= 1e-12:
                    continue
                for bj in b.trees['down'].query(common2):
                    bdp, bdz = b.sides['down'][int(bj)]
                    for poly in polygons(common2.intersection(bdp)):
                        cells += 1
                        if cells > maximum_cells:
                            return {**result, 'state': 'INDETERMINATE_CELL_BUDGET', 'cells_examined': cells}
                        require(not poly.interiors, 'Unexpected holes in convex facet cell')
                        original = [list(v) for v in poly.exterior.coords[:-1]]
                        candidates = []
                        vertices = original
                        for plane in [az-bdz, bz-adz, az-adz, bz-bdz]:
                            plane = plane.copy(); plane[2] -= minimum_embed_m
                            vertices = plane_clip(vertices, plane)
                        if len(vertices) >= 3 and Polygon(vertices).area > 1e-10:
                            candidates.append(('volume', Polygon(vertices), None))
                        if contact_mode == 'volume_or_exact_area':
                            # Opposite actual surfaces must coincide over the
                            # WHOLE finite cell, not merely cross at a line.
                            vv=np.column_stack([np.asarray(original),np.ones(len(original))])
                            for separation in [az-bdz, bz-adz]:
                                values=vv@separation
                                if max(abs(values)) > area_tolerance:
                                    continue
                                vertices=original
                                for plane in [az-adz,bz-bdz]:
                                    plane=plane.copy();plane[2]-=minimum_embed_m
                                    vertices=plane_clip(vertices,plane)
                                if len(vertices)>=3 and Polygon(vertices).area>1e-10:
                                    candidates.append(('area',Polygon(vertices),values.tolist()))
                        for mode,joint,separations in candidates:
                            witness = joint.representative_point(); uv = [witness.x, witness.y]
                            ia, ib = ray_intervals(a.t, uv), ray_intervals(b.t, uv)
                            if ia['state'] == 'ambiguous' or ib['state'] == 'ambiguous':
                                rejected += 1; continue
                            witnesses = [(x, y, min(x[1], y[1])-max(x[0], y[0]))
                                         for x, y in product(ia['intervals_m'], ib['intervals_m'])]
                            witnesses = [x for x in witnesses if (x[2] >= minimum_embed_m-1e-8
                                         if mode=='volume' else abs(x[2])<=area_tolerance)]
                            # Actual intervals must belong to these four actual
                            # facets, not a disconnected component's envelope.
                            pa = [float(adz @ [*uv, 1]), float(az @ [*uv, 1])]
                            pb = [float(bdz @ [*uv, 1]), float(bz @ [*uv, 1])]
                            witnesses = [x for x in witnesses if max(abs(np.asarray(x[0])-pa)) < 1e-6
                                         and max(abs(np.asarray(x[1])-pb)) < 1e-6]
                            if not witnesses:
                                rejected += 1; continue
                            x, y, overlap = max(witnesses, key=lambda r: r[2])
                            return {**result, 'state': 'LOCAL_POSITIVE_VOLUME_WITNESS' if mode=='volume' else 'LOCAL_POSITIVE_AREA_COINCIDENCE',
                                'positive_volume_contact_found': mode=='volume',
                                'positive_area_coincidence_found': mode=='area','contact_found':True,
                                'cells_examined': cells,'rejected_ambiguous_interval_cells': rejected,
                                'witness_cell_area_m2': joint.area, 'witness_uv_m': uv,
                                'actual_left_interval_m': x, 'actual_right_interval_m': y,
                                'witness_overlap_m': overlap, 'minimum_clip_embed_m': minimum_embed_m,
                                'area_coincidence_tolerance_m':area_tolerance if mode=='area' else None,
                                'area_cell_vertex_separations_m':separations}
    return {**result, 'cells_examined': cells, 'rejected_ambiguous_interval_cells': rejected}


def support_check(asset, request):
    left = select_many(asset, request['left_selectors'])
    right = select_many(asset, request['right_selectors'])
    require(not {p.key for p in left} & {p.key for p in right}, 'Self-contact query forbidden')
    rows = []
    for p in left:
        attempted = []
        for q in right:
            result = contact_witness(p, q, request['frame'],
                    request.get('minimum_embed_m', 1e-6), request.get('maximum_cells_per_pair', 100000),
                    request.get('contact_mode','positive_volume'))
            attempted.append(result)
            if result['contact_found']:
                break
        rows.append({'left_key': p.key,
                     'passed': any(x['contact_found'] for x in attempted),
                     'actual_pair_results': attempted})
    return {'passed': all(r['passed'] for r in rows), 'left_part_results': rows,
            'scope': 'Each specified left part has one actual local positive-volume joint, or explicitly requested finite-area opposite-surface coincidence, to a specified right part. Not complete bearing coverage or structural engineering verification.'}


def measure_check(asset, request):
    ranges=request['extent_ranges_m']
    require(isinstance(ranges,dict) and bool(ranges) and not set(ranges)-{'0','1','2'},'Extent axes must be nonempty subset of 0,1,2')
    for limits in ranges.values():
        q=np.asarray(limits,float)
        require(q.shape==(2,) and np.isfinite(q).all() and 0<=q[0]<=q[1], 'Extent limits must be finite ordered nonnegative ranges')
    rows = []
    for p in select_many(asset, request['selectors']):
        t = transformed(p, request['frame'])
        low, high = t.min(axis=(0, 1)), t.max(axis=(0, 1))
        extents = high-low
        passed = all(lo <= extents[int(axis)] <= hi
                     for axis, (lo, hi) in ranges.items())
        rows.append({'key': p.key, 'actual_bounds_probe_frame_m': [low.tolist(), high.tolist()],
                     'actual_extents_m': extents.tolist(), 'passed': bool(passed)})
    return {'passed': all(r['passed'] for r in rows), 'actual_parts': rows,
            'scope': 'Actual serialized extents in an explicit frame, compared with declared reconstruction bounds; not real-world measured dimensions.'}


def section_check(asset, request):
    """Interior plane/actual triangles -> closed section loops per actual part.

    Endpoint merging is an explicit numerical operation on the computed
    section only, never a weld or repair of the actual model. Coplanar/on-vertex
    stations are retained as unresolved instead of silently moving the plane.
    """
    rows = []
    tolerance = request.get('endpoint_merge_tolerance_m', 1e-7)
    require(np.isfinite(tolerance) and 0 < tolerance <= 1e-6, 'Section endpoint tolerance too large')
    loop_range=request['loop_count_range']
    require(len(loop_range)==2 and all(isinstance(x,int) for x in loop_range) and 0<loop_range[0]<=loop_range[1], 'Invalid section loop range')
    if 'maximum_section_segment_length_m' in request:
        require(np.isfinite(request['maximum_section_segment_length_m']) and request['maximum_section_segment_length_m']>0,'Invalid section segment limit')
    for part in select_many(asset, request['selectors']):
        t = transformed(part, request['frame'])
        segments, ambiguous = [], 0
        for q in t:
            d = q[:, 2]
            if d.min() > 0 or d.max() < 0:
                continue
            if np.any(abs(d) <= 1e-10):
                ambiguous += 1
                continue
            points = []
            for i, j in [(0, 1), (1, 2), (2, 0)]:
                if (d[i] < 0) != (d[j] < 0):
                    points.append(q[i, :2]+d[i]/(d[i]-d[j])*(q[j, :2]-q[i, :2]))
            if len(points) == 2:
                segments.append(points)
        points, adjacency, buckets, maxmerge = [], {}, {}, 0.

        def node(p):
            nonlocal maxmerge
            bucket = tuple(np.floor(p/tolerance).astype(int))
            for dx, dy in product([-1, 0, 1], repeat=2):
                for k in buckets.get((bucket[0]+dx, bucket[1]+dy), []):
                    dist = float(np.linalg.norm(points[k]-p))
                    if dist <= tolerance:
                        maxmerge = max(maxmerge, dist)
                        return k
            k = len(points); points.append(p)
            buckets.setdefault(bucket, []).append(k); adjacency[k] = []
            return k

        for a, b in segments:
            i, j = node(a), node(b)
            adjacency[i].append(j); adjacency[j].append(i)
        components, seen = [], set()
        for i in adjacency:
            if i in seen:
                continue
            pending, component = [i], []
            while pending:
                j = pending.pop()
                if j in seen:
                    continue
                seen.add(j); component.append(j); pending.extend(adjacency[j])
            components.append(component)
        lengths = [float(np.linalg.norm(b-a)) for a, b in segments]
        bad = {str(i): len(js) for i, js in adjacency.items() if len(js) != 2}
        loop_shapes=[]
        if not bad:
            for component in components:
                start=component[0];order=[start];previous=None;current=start
                while True:
                    choices=[i for i in adjacency[current] if i!=previous]
                    nxt=choices[0]
                    if nxt==start:break
                    if nxt in order:break
                    order.append(nxt);previous,current=current,nxt
                shape=Polygon([points[i] for i in order]) if len(order)>=3 else Polygon()
                loop_shapes.append({'vertices':len(order),'area_m2':shape.area,
                                    'simple_closed':bool(nxt==start and len(order)==len(component) and shape.is_valid and shape.area>0)})
        minimum, maximum = request['loop_count_range']
        passed = bool(segments) and not ambiguous and not bad and minimum <= len(components) <= maximum and all(x['simple_closed'] for x in loop_shapes)
        if 'maximum_section_segment_length_m' in request:
            passed = passed and max(lengths, default=float('inf')) <= request['maximum_section_segment_length_m']
        rows.append({'key': part.key, 'passed': bool(passed),
            'state': 'UNRESOLVED_ON_VERTEX_OR_COPLANAR_STATION' if ambiguous else 'ACTUAL_SECTION',
            'segment_count': len(segments), 'closed_loop_candidate_count': len(components),
            'non_two_valence_section_nodes': bad, 'on_plane_triangle_count': ambiguous,
            'loop_shapes':loop_shapes,
            'minimum_segment_m': min(lengths) if lengths else None,
            'maximum_segment_m': max(lengths) if lengths else None,
            'maximum_actual_endpoint_merge_distance_m': maxmerge,
            'actual_section_bounds_uv_m': [np.min(points, axis=0).tolist(), np.max(points, axis=0).tolist()] if points else None})
    return {'passed': all(r['passed'] for r in rows), 'actual_sections': rows,
            'scope': 'Closed finite cross-section loops at the exact stated plane; no proof of smoothness everywhere or photo accuracy. Actual model coordinates remain unchanged.'}


def run_checks(asset, requests, *, source_structure_report_path):
    require(requests.get('schema') == 'modern-finite-requests-v1' and
            requests.get('state') == 'READY_FOR_ACTUAL_AUDIT', 'Requests are not frozen executable input')
    require(requests.get('checks'), 'No finite checks; empty suite cannot pass')
    proof = json.loads(Path(source_structure_report_path).read_bytes())
    proof_descriptor = filemeta(source_structure_report_path)
    binding = requests['source_binding']
    require(proof_descriptor['sha256'] == binding['structure_report_sha256'],
            'Independent source structure report hash differs')
    require(proof.get('schema') == 'modern-actual-raw-structure-v1' and
            proof.get('structure_passed') is True, 'No passing actual source structure prerequisite')
    require(proof['asset_identity']['raw']['sha256'] == binding['raw_sha256'] and
            proof['frozen_source_manifest']['sha256'] == binding['source_freeze_sha256'] and
            proof['model_id'] == requests['model_id'] and
            proof['source_geometry_sha256'] == binding['geometry_input_sha256'] and
            proof['calibration_sha256'] == binding['calibration_sha256'],
            'Actual source identity/calibration/freeze differs from finite requests')
    require('asset' in asset.identity or 'raw' in asset.identity, 'Current actual asset descriptor missing')
    current = asset.identity.get('asset', asset.identity.get('raw'))
    require(current.get('sha256') and current.get('bytes'), 'Current asset hash/size missing')
    require(current['bytes'] < 100_000_000, 'Current asset is not below100MB')
    baseline = {r['key']: r for r in proof['part_results']}
    require(len(baseline) == len(proof['part_results']), 'Duplicate baseline part keys')
    require(len({p.key for p in asset.parts}) == len(asset.parts), 'Duplicate current actual part keys')
    missing = sorted(set(baseline)-{p.key for p in asset.parts})
    require(set(missing) <= set(requests.get('allowed_omitted_part_keys', [])),
            'Current asset omits unapproved source parts')
    preservation = []
    for part in asset.parts:
        require(part.key in baseline, 'Unknown extra current actual part: ' + part.key)
        old = baseline[part.key]
        actual_hash = oriented_position_hash(part.triangles_enu)
        require(old['label'] == part.label and old['material'] == part.material and
                old['triangles'] == len(part.triangles_enu) and
                actual_hash == old['oriented_position_triangles_sha256'],
                'Actual current part geometry changed; new independent structure proof required: ' + part.key)
        preservation.append({'key': part.key, 'triangles': len(part.triangles_enu),
                             'actual_oriented_position_sha256': actual_hash})
    dispatch = {'wall_aperture_projection': aperture_check, 'ray_intervals': ray_check,
                'support_each': support_check, 'measure_part_extents': measure_check,
                'closed_plane_sections': section_check}
    rows = []
    require(len({r['id'] for r in requests['checks']}) == len(requests['checks']), 'Duplicate check IDs')
    for r in requests['checks']:
        if r['kind'] not in dispatch:
            rows.append({'id': r['id'], 'kind': r['kind'], 'passed': False,
                         'state': 'UNIMPLEMENTED_REQUIRED_CHECK'})
            continue
        try:
            result = dispatch[r['kind']](asset, r)
            rows.append({'id': r['id'], 'kind': r['kind'], 'state': 'ACTUAL_FINITE_CHECK', **result})
        except Exception as exc:
            rows.append({'id': r['id'], 'kind': r['kind'], 'passed': False,
                         'state': 'ERROR_OR_UNRESOLVED_INPUT', 'error': str(exc)})
    return {'schema': 'modern-actual-finite-checks-v1', 'asset_identity': asset.identity,
            'model_id': requests['model_id'], 'source_binding': binding,
            'source_structure_report': proof_descriptor,
            'actual_structure_carryforward': {'all_present_parts_position_identical': True,
                'actual_current_asset': current, 'source_raw_sha256': binding['raw_sha256'],
                'omitted_source_part_keys': missing, 'actual_part_comparisons': preservation,
                'normal_scope': 'Position/orientation/closed-component proof transfers only because actual oriented triangle positions are identical per part. Current delivery normals must satisfy separate decoder equivalence policy; raw0.001degree policy is not silently changed.'},
            'finite_checks_passed': all(r['passed'] for r in rows), 'check_results': rows,
            'model_appearance_accepted': False, 'complete_collision_checked': False,
            'physical_structural_safety_verified': False,
            'scope': 'Only listed finite, source-bound geometry questions over actual triangles. Unimplemented/missing/ambiguous checks cannot pass. Native/decoded/browser review remain separate.'}
