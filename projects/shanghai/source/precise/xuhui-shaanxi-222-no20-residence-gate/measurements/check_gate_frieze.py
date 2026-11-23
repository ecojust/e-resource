"""Compare each marked egg centre with the corresponding physical GLB relief in both photographs."""
from pathlib import Path
import argparse
import json
import sys

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

from register_gate import Camera

HERE = Path(__file__).resolve().parent
PRECISE = HERE.parent.parent
sys.path.append(str(PRECISE / 'xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
from glb_triangles import SerialScene


def egg_centres(scene):
    # Serialized GLB vertices can split along the UV or normal seam. Weld by
    # position before measuring each connected carved object independently.
    material = next(i for i, name in enumerate(scene.materials) if 'egg and tongue' in name)
    triangles = scene.tri[scene.mi == material]
    vertices, indices = np.unique(triangles.reshape(-1, 3).round(6), axis=0, return_inverse=True)
    corners = indices.reshape(-1, 3)
    graph = coo_matrix((np.ones(corners.size), (corners.ravel(), np.roll(corners, 1, axis=1).ravel())),
                       shape=(len(vertices), len(vertices)))
    n, labels = connected_components(graph, directed=False)
    groups = {'left_head': [], 'centre': [], 'right_head': []}
    for component in range(n):
        v = vertices[labels == component]
        lo, hi = v.min(axis=0), v.max(axis=0)
        span = hi - lo
        # The front eggs are the closed, upright forms with a single toe and
        # a single crown vertex. Cups have multiple end-ring vertices, and the
        # tongues are narrower. The two oblique returns have their width in Y.
        if not (span[0] > .046 and span[1] < .054 and span[2] > .09
                and np.count_nonzero(v[:, 2] == lo[2]) == 1 and np.count_nonzero(v[:, 2] == hi[2]) == 1):
            continue
        x, _, z = (lo + hi) / 2
        group = 'centre' if lo[1] > -.20 else ('left_head' if x < 0 else 'right_head')
        groups[group].append([float(x), float(lo[1]), float(z)])
    for points in groups.values():
        points.sort()
    return groups


def period_check(photo_path, survey):
    from hashlib import sha256
    from PIL import Image
    from scipy.ndimage import gaussian_filter, map_coordinates
    from scipy.signal import find_peaks
    if sha256(photo_path.read_bytes()).hexdigest() != survey['photo']['sha256']:
        raise ValueError('The source photo differs from the measured original')
    source = np.asarray(Image.open(photo_path).convert('RGB'), float).mean(axis=2)
    y0, slope = survey['straightened_row_native_y']
    period = {}
    for band, (x0, x1, ylo, yhi, reference, _) in survey['periods'].items():
        x, h = np.meshgrid(np.arange(x0, x1), np.arange(ylo, yhi))
        strip = map_coordinates(source, [y0+slope*x+h, x], order=1)
        strip -= gaussian_filter(strip, 3)
        last = 39 if source.shape[0] > 500 else 28
        spectrum = [np.corrcoef(strip[:, k:].ravel(), strip[:, :-k].ravel())[0, 1] for k in range(1, last)]
        peaks = find_peaks(spectrum)[0]
        peak = max(peaks, key=lambda i: spectrum[i])
        period[band] = {'lag_px': int(peak + 1), 'correlation': round(float(spectrum[peak]), 4),
                        'agrees_with_recorded_lag': bool(peak + 1 == reference)}
    return period


def check(asset, photo_folder):
    survey = json.loads((HERE/'frieze-photo-controls.json').read_text())
    scene = SerialScene(asset)
    centres = egg_centres(scene)
    result = {'asset': scene.asset, 'serialized_front_egg_counts': {k: len(v) for k, v in centres.items()},
              'head_return_eggs_excluded_from_count': True, 'source_pixels': 'frieze-photo-controls.json', 'views': {}}
    for view, photo in survey['photos'].items():
        camera = Camera(view)
        checks = []
        for item in photo['egg_controls']:
            x, y = item['pixel']
            centre = centres[item['band']][item['index_from_left'] - 1]
            projected = camera.pixel(centre)
            hit = scene.ray(camera.c, camera.ray([x, y]), 15)
            distance = np.linalg.norm(projected-[x, y])
            checks.append({**item, 'projected_egg_centre_px': projected.round(3).tolist(),
                           'centre_residual_px': round(float(distance), 3),
                           'first_hit': hit['material'] if hit else None,
                           'first_hit_relief': bool(hit and 'egg and tongue' in hit['material'])})
        result['views'][view] = record = {'count': len(checks), 'first_hit_relief': sum(q['first_hit_relief'] for q in checks),
            'median_centre_residual_px': round(float(np.median([q['centre_residual_px'] for q in checks])), 3),
            'max_centre_residual_px': max(q['centre_residual_px'] for q in checks), 'checks': checks}
        surfaces = []
        for item in photo['cornice_controls']:
            hit = scene.ray(camera.c, camera.ray(item['pixel']), 15)
            name = hit['material'] if hit else ''
            cornice = 'cornice stone' in name or 'cornice edge' in name
            expected = 'cornice edge' if item['region'] == 'rim' else 'cornice stone'
            dx, dy = item['pixel']
            nearby = 0 if expected in name else None
            if nearby is None:
                for offset in range(1, 9):
                    neighbours = [scene.ray(camera.c, camera.ray([dx, dy+sign*offset]), 15) for sign in (-1, 1)]
                    if any(h and expected in h['material'] for h in neighbours):
                        nearby = offset
                        break
            surfaces.append({**item, 'first_hit': name or None, 'hits_cornice': cornice,
                             'specific_finish_matches': expected in name, 'nearest_vertical_correct_finish_within_8_px': nearby})
        record['cornice_surface_controls'] = surfaces
        record['first_hit_cornice'] = sum(item['hits_cornice'] for item in surfaces)
        if photo_folder:
            record['recomputed_periods'] = period_check(photo_folder/f'gao-{view}.jpg', photo)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('asset', type=Path)
    parser.add_argument('out', type=Path)
    parser.add_argument('--original-photos', type=Path)
    args = parser.parse_args()
    report = check(args.asset, args.original_photos)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n')
    print(report['serialized_front_egg_counts'],
          [(k, v['first_hit_relief'], v['count'], v['median_centre_residual_px']) for k, v in report['views'].items()])
