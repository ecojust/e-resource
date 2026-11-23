"""Probe each brace, its horizontal head and the opening between them in an exported model."""
from pathlib import Path
import argparse
import json
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
from glb_triangles import SerialScene

FRACTIONS = (0, .14880, .65010, .76717, .88276, 1)
TIMBER = 'Gaoan 77 | exposed dark timber'


def check(mesh, layout):
    scene = SerialScene(mesh)
    frame, cfg = layout['side_frame'], layout['side_eave']
    along = np.asarray(frame['along'], dtype=float)
    along /= np.linalg.norm(along)
    outward = np.array([along[1], -along[0]])
    transform = np.asarray(layout.get('component_to_model', np.eye(4)), dtype=float)
    assert transform.shape == (4,4) and np.allclose(transform[3], [0,0,0,1])
    direction = transform[:3,:3] @ np.r_[along, 0.]
    segment = .40 * np.linalg.norm(direction)
    direction /= np.linalg.norm(direction)
    low, high = cfg['seat_z'] + .195, cfg['eave_z'] - .17
    projection = cfg.get('eave_projection', .70)
    height = low + .67 * (high - low)
    stations = [
        ('raking timber', .33 * .097 + .67 * (projection - .095), height, TIMBER),
        ('horizontal head', projection * .48, cfg['eave_z'] - .085, TIMBER),
        ('triangular opening', projection * .24, height, None),
    ]
    hits = []
    for number, fraction in enumerate(FRACTIONS, 1):
        centre = cfg['first_s'] + fraction * (cfg['last_s'] - cfg['first_s'])
        for name, depth, z, expected in stations:
            xy = np.asarray(frame['origin']) + (centre - .20) * along + depth * outward
            start = (transform @ np.r_[xy, z, 1.])[:3]
            hit = scene.ray(start, direction, segment)
            material = hit['material'] if hit else None
            hits.append(dict(support=number, section=name, origin=start.tolist(), direction=direction.tolist(),
                             segment_m=segment, first_hit=hit, expected_material=expected, match=material == expected))
    return dict(asset=scene.asset, matching=sum(r['match'] for r in hits), probes=hits)


if __name__ == '__main__':
    args = argparse.ArgumentParser(description=__doc__)
    for key in ('mesh', 'layout', 'output'):
        args.add_argument(key, type=Path)
    opt = args.parse_args()
    result = check(opt.mesh, json.loads(opt.layout.read_bytes()))
    opt.output.write_text(json.dumps(result, indent=2) + '\n')
    print(result['matching'], '/', len(result['probes']))
