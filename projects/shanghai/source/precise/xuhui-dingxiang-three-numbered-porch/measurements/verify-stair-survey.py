"""Project the six paired iron posts into both source photographs and check the measured stone noses.

The control points, cameras and dimensional assumptions are stored in two-view-stair-and-rail.json.
The calculation does not require copies of the privately held reference photographs.
"""
from argparse import ArgumentParser
import json
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation


def check(path):
    survey = json.loads(path.read_bytes())
    residuals = []
    for source in survey['sources']:
        camera = source['camera']
        flip = np.array([[1., 0., 0.], [0., 0., -1.], [0., 1., 0.]])
        rotation = Rotation.from_rotvec(camera['rotation_vector_after_x_up_conversion']).as_matrix() @ flip
        scale = np.array(source['size']) / [840, 559]
        for side, sign in [('left', -1), ('right', 1)]:
            points = []
            for post in survey['rail_posts_front_to_rear']:
                for height in ['wood_underside_z', 'foot_z']:
                    points.append([sign * post['x_right'], post['y'], post[height]])
            xyz = np.asarray(points) @ rotation.T + camera['translation']
            uv = camera['focal_at_840'] * xyz[:, :2] / xyz[:, 2, None] + camera['principal_at_840']
            original_pixels = (uv + .5) * scale - .5
            for measured, projected in zip(source['support_pixels'][side], original_pixels, strict=True):
                if measured is not None:
                    residuals.append(np.asarray(measured) - projected)
    errors = np.asarray(residuals)
    assert len(errors) == survey['points_taken'] == 22
    rms = np.sqrt(np.mean(errors**2))
    assert abs(rms - survey['accuracy']['post_coordinates_rms_original_px']) < .03
    for step in survey['tread']['five_noses_top_to_bottom']:
        # The bow is the setback at the end of a 0.9W chord from its centre.
        assert abs(.45**2 * step['k'] - step['bow_on_0_9W_chord_W']) < .00001
    return {'observations': len(errors), 'reprojection_rms_original_px': float(rms),
            'treads': len(survey['tread']['five_noses_top_to_bottom'])}


if __name__ == '__main__':
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('study', type=Path, nargs='?',
                        default=Path(__file__).with_name('two-view-stair-and-rail.json'))
    print(json.dumps(check(parser.parse_args().study), indent=2))
