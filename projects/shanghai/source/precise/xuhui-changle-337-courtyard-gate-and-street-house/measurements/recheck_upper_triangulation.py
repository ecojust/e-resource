"""Recalculate the registered window corners and both independently identified gates.

Each observation is a native image pixel. Gate cameras that share a fitted
central station keep full weight. Other provider positions have weaker
orientation and are applied at 0.43 weight.
"""
import argparse
import json
from pathlib import Path
import numpy as np

D = Path(__file__).resolve().parent

def solve(cameras, points, gate):
    planes = []
    offsets = []
    for key, pixel in points.items():
        cam = cameras[key]
        direction = np.asarray(cam['R']).T @ np.linalg.solve(cam['K'], [*pixel, 1])
        direction /= np.linalg.norm(direction)
        weight = .43 if gate and not cam.get('parent') else 1.
        normal = weight * (np.eye(3) - np.outer(direction,direction))
        planes.append(normal)
        offsets.append(normal @ cam['eye'])
    return np.linalg.lstsq(np.concatenate(planes), np.concatenate(offsets), rcond=None)[0]

def audit():
    checks = []
    for path, field in [('upper-room-stations.json','controls'),('separate-335-and-337-plates.json','observations')]:
        data = json.loads((D/path).read_text())
        for name, observation in data[field].items():
            point = solve(data['cameras'], observation['native_pixels'], field=='observations')
            residual = np.max(np.abs(point - observation['xyz']))
            checks.append(dict(source=path, name=name, xyz=point.tolist(), roundtrip_metres=residual))
    return checks

if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--output',type=Path)
    args=cli.parse_args()
    checks=audit()
    result={'checked':len(checks),'maximum_coordinate_difference_m':max(r['roundtrip_metres'] for r in checks),'rows':checks}
    if args.output:args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(result['checked'],result['maximum_coordinate_difference_m'])
