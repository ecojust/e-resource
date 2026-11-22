"""Verify the three full-length lower sashes using the second, captioned photograph of No. 24."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'source'),
                str(HERE.parents[1] / 'xuhui-pathe-records-office/measurements/city-contact')]
from bay_windows import GLASS, WHITE, LATER, opening_profiles, visible_opening
from glb_triangles import SerialScene

# Native source pixels in clear panes, with the left pane's diagonal plant stem excluded.
GLASS_PATCHES = {
    'lower-left': [(380,369),(381,410)],
    'lower-center': [(435,380),(435,419)],
    'lower-right': [(465,376),(465,414)],
}

def inspect(path, camera_path):
    camera = np.asarray(json.loads(camera_path.read_bytes())['press'])
    center = -np.linalg.solve(camera[:, :3], camera[:, 3])
    scene = SerialScene(path)
    result = []

    def trace(key, name, uv, material, evidence):
        direction = np.linalg.solve(camera[:, :3], [*uv, 1.])
        hit = scene.ray(center, direction, 30.)
        result.append(dict(window=key, feature=name, pixel=np.round(uv, 4).tolist(),
                           source=evidence, expected=material, actual=hit['material'] if hit else None,
                           xyz=hit['point_enu_m'] if hit else None,
                           passed=bool(hit and hit['material']==material)))

    for key, coordinates in GLASS_PATCHES.items():
        for uv in coordinates:
            trace(key, 'clear area of closed lower sash', uv, GLASS, 'published 2022, original pixels')
    for key, row in opening_profiles().items():
        if row['storey'] != 'lower':
            continue
        origin, tangent, normal = visible_opening(row)
        for index, fraction in enumerate((.16,.35,.55,.76,.88)):
            xy = origin + fraction * row['width'] * tangent + .013 * normal
            xyz = [*xy,row['bottom_z']+.039]
            projected = camera @ [*xyz, 1.]
            trace(key, f'bottom timber rail {index+1}', projected[:2]/projected[2], WHITE,
                  'projected timber, above the independently observed 2022 sill')
    return dict(mesh_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                photograph_sha256=LATER['photo_published_2022']['sha256'],
                camera_sha256=hashlib.sha256(camera_path.read_bytes()).hexdigest(),
                rows=result, count=len(result), matched=sum(row['passed'] for row in result),
                passed=all(row['passed'] for row in result))

if __name__ == '__main__':
    cli=argparse.ArgumentParser()
    cli.add_argument('asset',type=Path)
    cli.add_argument('report',type=Path)
    cli.add_argument('--camera',type=Path,default=HERE/'press-entrance-camera.json')
    args=cli.parse_args()
    result=inspect(args.asset,args.camera)
    args.report.write_text(json.dumps(result,indent=1)+'\n')
    print(result['matched'],result['count'])
    for row in result['rows']:
        if not row['passed']:
            print(row['window'],row['feature'],row['pixel'],row['actual'])
