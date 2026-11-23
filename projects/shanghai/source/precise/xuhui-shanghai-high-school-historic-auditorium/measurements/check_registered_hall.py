"""Compare observed pixels with first-surface intersections in a delivered GLB."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import runpy

import numpy as np
from register_court import Camera


HERE = Path(__file__).absolute().parent
HELPER = 'data/audit/postal-office-v1/independent-glb-review-helpers.py'
PROJECT = next(p for p in HERE.parents if (p / HELPER).is_file())
MATERIALS = {
    'east_glazing': {'recessed east window glass', 'dark east window frames'},
    'trim': {'cool grey cast trim', 'recessed facade panels', 'shadow in cast ornament'},
    'masonry': {'ochre render'}, 'timber': {'reddish door timber'},
    'glazing': {'smoked reflecting entrance glass'}, 'stone': {'dressed stair stone'}
}


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def accepts(hit, expectation):
    if expectation == 'sky':
        return hit is None
    if hit is None:
        return False
    if expectation == 'solid':
        return True
    return hit['material'].split(' | ')[-1] in MATERIALS[expectation]


def check(mesh):
    controls = HERE / 'registered-outline-controls.json'
    entries = json.loads(controls.read_bytes())['checks']
    scene = runpy.run_path(str(PROJECT / HELPER))['SerialScene'](mesh)
    cameras = {name: Camera(name) for name in ('1934', '2020')}
    offsets = sorted((x * x + y * y, x, y) for x in range(-4, 5)
                     for y in range(-4, 5) if x * x + y * y <= 16)
    rows, tally = [], {}
    for entry in entries:
        view = entry['view']
        camera = cameras[view]
        scale = camera.size[0] / (1200 if view == '1934' else 675)
        peak = None
        pixel = np.asarray(entry['source_pixel'])
        for squared, dx, dy in offsets:
            hit = scene.ray(camera.c, camera.ray(pixel + scale * np.array([dx, dy])), 235.)
            if squared == 0:
                direct = hit
            if accepts(hit, entry['expected']):
                peak = {'working_offset': [dx, dy], 'working_radius': squared ** .5, 'hit': hit}
                break
        group = entry['scope']
        stat = tally.setdefault(group, Counter())
        stat.update(total=1, exact=int(accepts(direct, entry['expected'])),
                    within_tolerance=int(peak is not None))
        rows.append({**entry, 'direct_surface': direct, 'nearest_matching_first_surface': peak})
    return {'model_sha256': sha(mesh), 'model': mesh.name, 'cameras_sha256': sha(HERE / 'court-cameras.json'),
            'measurements_sha256': sha(controls), 'counts': tally, 'rays': rows}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mesh', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    data = check(args.mesh)
    args.output.parent.mkdir(exist_ok=True, parents=True)
    args.output.write_text(json.dumps(data, indent=2) + '\n')
    print(json.dumps(data['counts']))
