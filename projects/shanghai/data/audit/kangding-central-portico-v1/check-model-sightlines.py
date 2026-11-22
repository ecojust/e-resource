"""Check which physical corner facade surfaces the two public cameras see in the actual optimized meshes."""
from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import math
import runpy
import subprocess

import numpy as np


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
IDENT = 'jingan-kangding-garden-central-portico'
CAMERA_TARGETS = {'西圆柱柱身': {'Ivory carved stone'}, '东圆柱柱身': {'Ivory carved stone'}, '西柱顶方帽': {'Ivory carved stone'}, '东柱顶方帽': {'Ivory carved stone'}, '西段露台石栏': {'Ivory carved stone'}, '中段露台石栏': {'Ivory carved stone'}, '东段露台石栏': {'Ivory carved stone'}, '中段石栏顶': {'Ivory carved stone'}, '顶层回纹栏墙': {'Warm white render'}, '正中老虎窗玻璃': {'Dark grey glazing'}, '老虎窗顶徽': {'Oxide red timber'}, '坡顶陶瓦': {'Terracotta roof tiles'}}


def check(manifest, sightlines, contract):
    geometry = json.loads(manifest.read_bytes())['assets']
    views = json.loads(sightlines.read_bytes())['cases']['delivered']
    placement = json.loads(contract.read_bytes())
    angle = math.radians(placement['heading'])
    helpers = runpy.run_path(str(PROJECT / 'data/audit/postal-office-v1/independent-glb-review-helpers.py'))

    def local(enu):
        east, north, height = enu
        return np.array([east * math.cos(angle) - north * math.sin(angle),
                         east * math.sin(angle) + north * math.cos(angle),
                         height - placement['altitude']])

    measurements = []
    with TemporaryDirectory() as scratch:
        for level in ('full', 'lod'):
            asset = geometry[level]
            delivery = manifest.parent / asset['file']
            assert sha256(delivery.read_bytes()).hexdigest() == asset['sha256']
            decoded = Path(scratch) / (level + '.glb')
            subprocess.run(['node', PROJECT / 'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs',
                            delivery, decoded, PROJECT / 'vendor/meshopt_decoder.module.js'],
                           check=True, stdout=subprocess.DEVNULL)
            scene = helpers['SerialScene'](decoded)
            assert len(scene.tri) == asset['triangles']
            for view in views:
                eye = local(view['camera_enu'])
                assert {p['feature'] for p in view['probes']} == set(CAMERA_TARGETS)
                samples = []
                for probe in view['probes']:
                    name = probe['feature']
                    assert probe['clear'] and probe['within_visible_map']
                    ray = local(probe['target_enu']) - eye
                    distance = float(np.linalg.norm(ray))
                    hit = scene.ray(eye, ray.copy(), length=distance + .40)
                    assert hit and hit['material'] in CAMERA_TARGETS[name], (level, view['view'], name, hit)
                    residual = hit['distance_m'] - distance
                    tolerance = .075
                    assert abs(residual) <= tolerance, (name, residual)
                    samples.append(dict(feature=name, depth_residual_m=round(residual, 4),
                                        tolerance_m=tolerance, first_intersection=hit))
                measurements.append(dict(level=level, asset_sha256=asset['sha256'], triangles=len(scene.tri),
                                         screen=view['view'], camera_local_m=eye.tolist(), samples=samples))
    return dict(passed=True, camera_file_sha256=sha256(sightlines.read_bytes()).hexdigest(),
                contract_sha256=sha256(contract.read_bytes()).hexdigest(), views=measurements)


if __name__ == '__main__':
    cli = ArgumentParser(description=__doc__)
    cli.add_argument('--manifest', type=Path, default=PROJECT / 'assets/models/candidates' / IDENT / 'manifest.json')
    cli.add_argument('--sightlines', type=Path, default=HERE / 'overview-sightlines.json')
    cli.add_argument('--contract', type=Path, default=HERE / 'final-placement-contract.json')
    cli.add_argument('--out', type=Path, default=HERE / 'model-sightlines.json')
    args = cli.parse_args()
    result = check(args.manifest, args.sightlines, args.contract)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
