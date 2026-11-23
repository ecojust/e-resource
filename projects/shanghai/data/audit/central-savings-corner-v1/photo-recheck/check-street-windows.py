"""Register the three vertical stacks of steel windows against two street photographs."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

import numpy as np
from PIL import Image, ImageOps

# Centres of the glazed opening, left to right on the 600 × 900 reference image.
# Rows are ordered from the bank entrance up to the crown.
CENTRES = [
    [(250, 546), (288, 548), (328, 550)],
    [(255, 459), (290, 460), (326, 462)],
    [(257, 376), (291, 379), (325, 381)],
    [(260, 305), (292, 307), (324, 309)],
    [(263, 241), (294, 243), (323, 245)],
    [(265, 184), (294, 185), (323, 188)],
    [(268, 135), (295, 136), (322, 138)],
    [(269, 103), (295, 104), (322, 106)],
]
FIT = [0, 1, 2, 9, 11, 21, 22, 23]
DISTRICT_CENTRES = [
    [(275, 435), (302, 435), (327, 435)],
    [(275, 374), (300, 374), (325, 374)],
    [(275, 316), (298, 316), (322, 316)],
    [(274, 265), (297, 265), (320, 265)],
    [(274, 219), (295, 219), (318, 220)],
    [(274, 176), (294, 176), (316, 176)],
    [(273, 137), (293, 137), (314, 137)],
    [(273, 112), (292, 112), (312, 112)],
]
DISTRICT_PHOTO = 'e58a9e1135a3d2021d8a549ad2141988dcb77da004b14309833c631e0cefd296'
PHOTO = 'dcf753c8907c940afa39d6d370c360cdf7149c57a2bc9764f9d19fb6fff56c85'
MODEL = 'huangpu-central-savings-society-corner-tower'


def glazing_centres(triangles, materials):
    selected = ((materials == 'Smoked blue steel sash glazing')
                & np.isclose(triangles[:, :, 1], .36, atol=.001).all(axis=1)
                & (np.abs(triangles[:, :, 0]) < 2).all(axis=1)
                & (triangles[:, :, 2] > 8).all(axis=1))
    glass = triangles[selected][:, :, [0, 2]]
    bounds = np.unique(np.round((glass.min(axis=1) + glass.max(axis=1)) / 2, 4), axis=0)
    assert bounds.shape == (24, 2)
    return bounds[np.lexsort((bounds[:, 0], bounds[:, 1]))]


def fit(source, target):
    equations = []
    values = []
    for (x, z), (u, v) in zip(source[FIT], target[FIT], strict=True):
        equations.extend(([x, z, 1, 0, 0, 0, -u*x, -u*z], [0, 0, 0, x, z, 1, -v*x, -v*z]))
        values.extend((u, v))
    coefficients, _, rank, _ = np.linalg.lstsq(equations, values, rcond=None)
    assert rank == 8
    homography = np.r_[coefficients, 1.].reshape(3, 3)
    projected = np.c_[source, np.ones(len(source))] @ homography.T
    return homography, projected[:, :2] / projected[:, 2:]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project', type=Path)
    parser.add_argument('commons_photo', type=Path)
    parser.add_argument('district_photo', type=Path)
    parser.add_argument('result', type=Path)
    args = parser.parse_args()
    assert sha256(args.commons_photo.read_bytes()).hexdigest() == PHOTO
    with Image.open(args.commons_photo) as image:
        assert ImageOps.exif_transpose(image).size == (1357, 2034)
    assert sha256(args.district_photo.read_bytes()).hexdigest() == DISTRICT_PHOTO
    with Image.open(args.district_photo) as image:
        assert image.size == (1080, 810) and image.transpose(Image.Transpose.ROTATE_270).size == (810, 1080)
    folder = args.project / 'assets/models/candidates' / MODEL
    manifest = json.loads((folder / 'manifest.json').read_bytes())
    routine = args.project / 'data/audit/central-savings-corner-v1/check-delivered-surfaces.py'
    triangles = runpy.run_path(str(routine))['triangles']
    references = [
        dict(photo_url='https://commons.wikimedia.org/wiki/File:The_Bank_of_Canton.jpg', original_sha256=PHOTO, original_size=[1357, 2034], clockwise_degrees=0, reading_size=[600, 900], centres=CENTRES, variants=[]),
        dict(photo_url='https://www.sohu.com/a/1005319047_121123854', original_sha256=DISTRICT_PHOTO, original_size=[1080, 810], clockwise_degrees=90, reading_size=[600, 800], centres=DISTRICT_CENTRES, variants=[]),
    ]
    with tempfile.TemporaryDirectory() as tmp:
        for role in ('raw', 'full', 'lod'):
            item = manifest['assets'][role]
            file = folder / item['file']
            assert sha256(file.read_bytes()).hexdigest() == item['sha256']
            if role != 'raw':
                decoded = Path(tmp) / (role + '.glb')
                subprocess.run(['node', args.project / 'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs', file, decoded, args.project / 'vendor/meshopt_decoder.module.js'], check=True)
                file = decoded
            centres = glazing_centres(*triangles(file))
            for ref in references:
                target = np.asarray(ref['centres']).reshape(-1, 2)
                matrix, projected = fit(centres, target)
                residuals = np.linalg.norm(projected - target, axis=1)
                holdout = np.delete(residuals, FIT)
                ref['variants'].append(dict(role=role, sha256=item['sha256'], decoded_sha256=sha256(file.read_bytes()).hexdigest(), centres_xz_m=centres.tolist(), fitted_homography=matrix.tolist(), distance_px=residuals.round(3).tolist(), held_out_median_px=round(float(np.median(holdout)), 3), held_out_max_px=round(float(holdout.max()), 3)))
    result = dict(references=references, fit_point_indices=FIT, held_out_points_per_photo=16, limits='取点范围为塔楼街面24扇窗的玻璃开口。侧翼进深另见足迹。街线上跨低层窗扇，最底排的窗台局部被铭牌墙遮挡。')
    args.result.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
