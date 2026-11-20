"""Compare the four recorded camera poses against native and landmark surfaces."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import runpy
import subprocess
import sys

import numpy as np
import shapely
from embreex.mesh_construction import TriangleMesh
from embreex.rtcore_scene import EmbreeScene


def scene(triangles):
    target = EmbreeScene()
    mesh = TriangleMesh(target, triangles.astype(np.float32))
    return target, mesh


def cast(target, origins, directions):
    rays = np.ascontiguousarray(directions, dtype=np.float32)
    points = np.broadcast_to(origins, rays.shape).astype(np.float32).copy()
    return target.run(points, rays, output=1)


def grids():
    x, z = np.meshgrid(np.arange(-8.2, 20.55, .35), np.arange(.8, 10.9, .32))
    south = np.column_stack((x.ravel(), np.full(x.size, -11), z.ravel()))
    y, z = np.meshgrid(np.arange(1, 41.4, .35), np.arange(.8, 10.9, .32))
    east = np.column_stack((np.full(y.size, 35), y.ravel(), z.ravel()))
    return np.vstack((south, east)), np.vstack((np.tile([0, 1, 0], (len(south), 1)),
                                               np.tile([-1, 0, 0], (len(east), 1))))


def camera_eye(state, placement, checked):
    camera = state['camera']
    center = camera['center']
    xy = checked.to_xy(np.array([[center['lng'], center['lat']]]))[0]
    focal = state['viewport'][1] / (2 * math.tan(math.radians(36.87) / 2))
    meters = (focal * math.cos(math.radians(placement['lat'])) * 40075016.68
              / (512 * 2 ** camera['zoom']))
    pitch, bearing = np.deg2rad([camera['pitch'], camera['bearing'] - placement['heading']])
    look = np.array([np.sin(bearing) * np.sin(pitch), np.cos(bearing) * np.sin(pitch), -np.cos(pitch)])
    return np.array([*xy, camera['elevation']]) - meters * look


def run():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--work', type=Path, required=True,
                        help='Working directory containing the SHA-256-bound source GLBs and metadata')
    parser.add_argument('--views', type=Path, nargs='+', required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    project = args.project.resolve()
    sys.path.insert(0, str(project / 'tools'))
    from candidate_placement_meshes import PlacementMeshes, read, write

    audit = project / 'data/audit/former-british-consulate-v1'
    placement = read(audit / 'final-placement-contract.json')
    model_id = placement['id']
    review = read(project / 'source/precise' / model_id / 'footprint-review.json')
    checked = PlacementMeshes(project, args.work, review)
    group = next(g for g in review['near_tiles'] if 3111 in g['feature_local_ids'])
    ids = np.array(group['feature_local_ids'])
    checked.link('baseline-far.glb', checked.files['far.glb'])
    checked.link('baseline-near.glb.gz', checked.files[Path(group['file']).name])
    checked.link('macro-READY.json', checked.files['READY.json'])
    work = checked.work
    write(work / 'context-features.json', [{'localId': local_id} for local_id in checked.footprints])
    subprocess.run(['node', checked.decoders / 'map-decode-source.mjs'], env=checked.env,
                   check=True, stdout=subprocess.DEVNULL)
    near = np.fromfile(work / 'baseline-near-triangles.f64').reshape(-1, 3, 3)
    far = np.fromfile(work / 'baseline-far-triangles.f64').reshape(-1, 3, 3)
    for block in (near, far):
        block[:, :, :2] = block[:, :, :2] @ checked.axes.T
    points = shapely.points(near.mean(axis=1)[:, :2])
    distances = np.column_stack([shapely.distance(points, checked.footprints[i]) for i in ids])
    near_ids = ids[np.argmin(distances, axis=1)]
    far_ids = np.fromfile(work / 'baseline-far-owners.u32', dtype=np.uint32)
    keep_near = near_ids != 3111
    keep_far = ~np.isin(far_ids, ids)
    native, native_mesh = scene(np.concatenate((near[keep_near], far[keep_far])))
    owner_ids = np.concatenate((near_ids[keep_near], far_ids[keep_far]))

    asset_directory = project / 'assets/models/candidates' / model_id
    asset = read(asset_directory / 'manifest.json')['assets']['raw']
    raw = asset_directory / asset['file']
    assert hashlib.sha256(raw.read_bytes()).hexdigest() == asset['sha256']
    decode = runpy.run_path(str(checked.decoders / 'independent-glb-review-helpers.py'))['load_triangles']
    landmark, landmark_mesh = scene(decode(raw)[0])
    origins, directions = grids()
    hits = cast(landmark, origins, directions)
    valid = hits['primID'] >= 0
    surface = origins[valid] + directions[valid] * hits['tfar'][valid, None]
    arcade = ((surface[:, 1] < 4.5) & (surface[:, 0] > -.9) &
              (surface[:, 0] < 13.45) & (surface[:, 2] < 5))

    evidence = []
    for report in args.views:
        data = read(report)
        assert data['completed']
        for state in data['views']:
            eye = camera_eye(state, placement, checked)
            delta = surface - eye
            distance = np.linalg.norm(delta, axis=1)
            directions = delta / distance[:, None]
            self_visible = cast(landmark, eye, directions)['tfar'] + .06 >= distance
            foreground = cast(native, eye, directions)
            clear = self_visible & (foreground['tfar'] + .06 >= distance)
            blocked = foreground['primID'][self_visible & ~clear]
            owners, counts = np.unique(owner_ids[blocked], return_counts=True)
            evidence.append({
                'view': state['view'], 'viewport': state['viewport'], 'camera': state['camera'],
                'sampled_surfaces': len(surface), 'self_visible': int(self_visible.sum()),
                'visible_through_city': int(clear.sum()), 'central_ground_self_visible': int((self_visible & arcade).sum()),
                'central_ground_clear': int((clear & arcade).sum()),
                'other_source_first_hit': dict(zip(map(str, owners), map(int, counts))),
                'projected_labels_included': False,
                'camera_report_sha256': hashlib.sha256(report.read_bytes()).hexdigest()
            })
    write(args.out, {'model': model_id, 'raw_sha256': asset['sha256'],
                     'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                     'near_source': group['id'], 'views': evidence})


if __name__ == '__main__':
    run()
