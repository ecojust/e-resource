#!/usr/bin/env python3
"""Actual raw Float32 closure/orientation/normals. Never import author code."""
from pathlib import Path
from collections import Counter
import argparse, json
import numpy as np
from modern_mesh import load_raw, filemeta, verify_source_freeze, require, oriented_position_hash

HERE = Path(__file__).resolve().parent


def structure(asset, normal_tolerance_deg=.001):
    records, failures = [], []
    all_min, all_max = [], []
    for part in asset.parts:
        t, normals = part.triangles_enu, part.normals_enu
        require(np.isfinite(t).all() and np.isfinite(normals).all(), 'Nonfinite part')
        cross = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
        area2 = np.linalg.norm(cross, axis=1)
        nl = np.linalg.norm(normals, axis=2)
        valid = (area2 > 1e-12) & (nl.min(axis=1) > 0)
        angles = np.full((len(t), 3), np.inf)
        if valid.any():
            dots = np.einsum('ij,ikj->ik', cross[valid] / area2[valid, None],
                             normals[valid] / nl[valid, :, None])
            angles[valid] = np.degrees(np.arccos(np.clip(dots, -1, 1)))
        # Exact serialized positions, no tolerance snap/weld.
        unique, inverse = np.unique(t.reshape(-1, 3), axis=0, return_inverse=True)
        faces = inverse.reshape(-1, 3)
        directed = np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]])
        _, edge_ids, edge_counts = np.unique(np.sort(directed, axis=1), axis=0,
                                             return_inverse=True, return_counts=True)
        sign = np.where(directed[:, 0] < directed[:, 1], 1, -1)
        balance = np.bincount(edge_ids, weights=sign, minlength=len(edge_counts))
        face_ids = np.tile(np.arange(len(t)), 3)
        parent = np.arange(len(t))

        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i

        first = {}
        for edge, face in zip(edge_ids, face_ids):
            if int(edge) not in first:
                first[int(edge)] = int(face)
            else:
                a, b = find(first[int(edge)]), find(int(face))
                parent[b] = a
        groups = {}
        for i in range(len(t)):
            groups.setdefault(find(i), []).append(i)
        volumes = []
        for ids in groups.values():
            q = t[ids]
            q = q - q.reshape(-1, 3).mean(axis=0)
            volumes.append(float(np.einsum('ij,ij->i', q[:, 0],
                           np.cross(q[:, 1], q[:, 2])).sum() / 6))
        lower, upper = t.min(axis=(0, 1)), t.max(axis=(0, 1))
        all_min.append(lower); all_max.append(upper)
        row = {'key': part.key, 'label': part.label, 'material': part.material,
               'triangles': len(t), 'bounds_enu_m': [lower.tolist(), upper.tolist()],
               'oriented_position_triangles_sha256': oriented_position_hash(t),
               'exact_position_vertex_count': len(unique),
               'edge_component_count': len(groups), 'component_signed_volumes_m3': volumes,
               'non_two_edges': int((edge_counts != 2).sum()),
               'unpaired_oriented_edges': int((balance != 0).sum()),
               'degenerate_triangles': int((area2 <= 1e-12).sum()),
               'minimum_double_triangle_area_m2': float(area2.min()),
               'maximum_flat_normal_angle_degrees': float(angles.max()) if valid.all() else None,
               'normal_length_min': float(nl.min()), 'normal_length_max': float(nl.max())}
        row['closed_oriented_positive_components'] = (not row['non_two_edges'] and
            not row['unpaired_oriented_edges'] and not row['degenerate_triangles'] and
            all(v > 0 for v in volumes))
        row['flat_normals_match_actual_triangles'] = bool(valid.all() and
            angles.max() < normal_tolerance_deg and np.max(abs(nl - 1)) < 1e-5)
        if not row['closed_oriented_positive_components'] or not row['flat_normals_match_actual_triangles']:
            failures.append(part.key)
        records.append(row)
    require(records, 'No actual parts')
    return {'schema': 'modern-actual-raw-structure-v1', 'structure_passed': not failures,
            'asset_identity': asset.identity,
            'model_id': asset.extras.get('id'),
            'source_geometry_sha256': asset.extras.get('source_geometry_sha256'),
            'calibration_sha256': asset.extras.get('calibration_sha256'),
            'parts': len(records), 'triangles': sum(r['triangles'] for r in records),
            'bounds_enu_m': [np.min(all_min, axis=0).tolist(), np.max(all_max, axis=0).tolist()],
            'normal_tolerance_degrees': normal_tolerance_deg,
            'label_occurrence_counts': dict(Counter(p.label for p in asset.parts)),
            'failed_part_keys': failures, 'part_results': records,
            'model_appearance_accepted': False, 'browser_or_native_reviewed': False,
            'scope': 'Every actual serialized triangle/corner normal and exact-position oriented edge pair; every edge-connected shell has positive signed volume. This does not prove no self-intersections, all vertex links manifold, no overlaps between separate parts, actual openings, physical structural adequacy or photographic likeness.'}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--raw', type=Path, required=True)
    ap.add_argument('--geometry', type=Path)
    ap.add_argument('--id', required=True)
    ap.add_argument('--source-freeze', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args()
    output = a.output.resolve()
    require(output.is_relative_to(HERE) and not output.exists(),
            'Result must be a new immutable path within independent-modern-review')
    frozen = verify_source_freeze(a.source_freeze)
    asset = load_raw(a.raw, a.geometry)
    require(asset.extras.get('id') == a.id, 'Actual asset identity differs')
    for key, filename in [('source_geometry_sha256', 'geometry-input.json'),
                          ('calibration_sha256', 'calibration.json')]:
        require(asset.extras.get(key) == filemeta(a.source_freeze.parent/filename)['sha256'],
                'Actual raw does not bind frozen ' + filename)
    report = structure(asset)
    report['frozen_source_manifest'] = frozen
    report['checker_files'] = [filemeta(HERE/n) for n in ['modern_mesh.py', 'audit_raw_structure.py']]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'report': str(output), 'structure_passed': report['structure_passed']}))
    raise SystemExit(0 if report['structure_passed'] else 1)


if __name__ == '__main__':
    main()
