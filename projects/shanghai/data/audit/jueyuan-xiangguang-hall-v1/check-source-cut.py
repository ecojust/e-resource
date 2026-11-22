"""Determine ownership where the east-gallery mask meets the actual near and far meshes."""
from pathlib import Path
import sys
import subprocess
import json

import numpy as np
import shapely as geo
from shapely.geometry import Polygon

PROJECT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT / 'tools'))
from candidate_placement_meshes import PlacementMeshes, read, sha, write

ID = 'jingan-jueyuan-xiangguang-hall'
OWNER = 354


def local_mask(registration):
    return Polygon(registration['preliminary_mask_xy'])



def check(work):
    root = PROJECT / 'source/precise' / ID
    footprint = root / 'footprint-review.json'
    site = PlacementMeshes(PROJECT, work, read(footprint))
    cut = local_mask(read(root / 'source/frontage-registration.json'))
    group, = site.review['near_tiles']
    ids = np.array(group['feature_local_ids'])
    assert set(ids) == {800, 2273, 354, 499, 693, 2583, 184, 509}
    site.link('baseline-far.glb', site.files['far.glb'])
    site.link('baseline-near.glb.gz', site.files[Path(group['file']).name])
    site.link('macro-READY.json', site.files['READY.json'])
    write(work / 'context-features.json', [{'localId': int(k)}for k in ids])
    subprocess.run(['node', site.decoders / 'map-decode-source.mjs'],
                   env=site.env, check=True, stdout=subprocess.DEVNULL)
    results = {}
    for level in ('far', 'near'):
        triangles = np.fromfile(work / f'baseline-{level}-triangles.f64', np.float64).reshape(-1, 3, 3)
        triangles[:, :, :2] = triangles[:, :, :2] @ site.axes.T
        faces = geo.polygons(triangles[:, :, :2])
        hits = geo.intersects(faces, cut)
        if level == 'far':
            labels = np.fromfile(work / 'baseline-far-owners.u32', np.uint32)
            attribution = {'method': 'Per-vertex feature IDs in the archived far mesh'}
        else:
            points = geo.points(triangles[:, :, :2].mean(1))
            distances = np.stack([geo.distance(points, site.footprints[int(k)])for k in ids], axis=1)
            labels = ids[distances.argmin(1)]
            own_index = int(np.where(ids == OWNER)[0][0])
            own_distance = distances[:, own_index]
            margin = np.delete(distances, own_index, axis=1).min(1) - own_distance
            # Distinguish the facade from the other buildings in this shared draw group.
            uncertain = np.abs(margin) < .95
            buffer_hits = geo.distance(faces, cut) < .50
            uncertainty_distance = float(geo.distance(
                faces[uncertain], cut).min()) if uncertain.any() else None
            minimum = float(margin[buffer_hits].min())
            maximum = float(own_distance[hits].max())
            assert not (uncertain & buffer_hits).any() and minimum > 1.15 and maximum < .10
            attribution = {'method': 'Nearest source rings in a 0.50 m halo, compared with typed far mesh',
                           'halo_triangles': int(buffer_hits.sum()), 'halo_minimum_margin_m': minimum,
                           'max_hit_centroid_distance_to_owner_m': maximum,
                           'ambiguous_triangles_outside_scope': int(uncertain.sum()),
                           'closest_ambiguous_triangle_to_cut_m': uncertainty_distance}
        assert len(labels) == len(triangles) and set(labels) == set(ids) and hits.any()
        assert np.all(labels[hits] == OWNER)
        source = site.project_faces(triangles[labels == OWNER])
        peer_distance = float(geo.distance(faces[labels != OWNER], cut).min())
        assert peer_distance > .40 and source.difference(cut).area / source.area > .72
        heights = triangles[hits, :, 2]
        results[level] = {'group_triangles': len(triangles), 'triangles_intersecting_cut': int(hits.sum()),
                          'foreign_intersections': 0, 'other_face_distance_m': peer_distance,
                          'source_projected_m2': source.area, 'retained_m2': source.difference(cut).area,
                          'projected_area_basis': 'typed far' if level == 'far' else 'nearest-ring estimate outside cut',
                          'roof_m': float(heights.max()), 'attribution': attribution}
    assert abs(results['far']['roof_m'] - results['near']['roof_m']) < .10
    neighbors = {str(r['local_id']): site.footprints[r['local_id']].distance(cut)
                 for r in site.review['owners']if r['local_id'] != OWNER}
    assert min(neighbors.values()) > .40
    return {'id': ID, 'passed': True, 'source_review_sha256': sha(footprint),
            'mask_local_m': list(cut.exterior.coords), 'mask_area_m2': cut.area,
            'source_levels': results, 'neighbor_distance_m': neighbors}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    write(args.out, check(args.work))
