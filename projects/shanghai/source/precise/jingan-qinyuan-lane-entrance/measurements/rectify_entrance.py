"""Rectify the street photograph to the front rail and test the fit against the plaque photograph."""
import json
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
# Full photographs, pixels from top left. The two post centrelines at grade and
# the separating horizontal cap define the reference plane. The assumed cap
# height supplies scale. Width/depth will remain estimates pending a site survey.
WIDE = (1080, 719)
POST_SPACING = 3.94
CAP_HEIGHT = 2.70
WIDE_CONTROL = [[369, 624], [603, 633], [602, 478], [383, 470]]
DEST = [[-POST_SPACING / 2, 0], [POST_SPACING / 2, 0],
        [POST_SPACING / 2, CAP_HEIGHT], [-POST_SPACING / 2, CAP_HEIGHT]]

WIDE_POINTS = {
    'outer_crest': [497, 397], 'outer_west_shoulder': [424, 417], 'outer_east_shoulder': [563, 422],
    'inner_crest': [496, 418], 'inner_west_shoulder': [425, 435], 'inner_east_shoulder': [558, 438],
    'red_left': [444, 415], 'red_centre': [500, 406], 'red_right': [550, 420],
    'oval_left': [455, 443], 'oval_right': [536, 444], 'oval_top': [498, 433], 'oval_bottom': [498, 452],
    'wall_west_crop': [245, 487], 'wall_right_end': [360, 491],
    'cap_top': [292, 487], 'cap_lower': [292, 492], 'band_top': [291, 526],
    'band_bottom': [291, 530], 'plinth_top': [290, 612],
    'heritage_left': [254, 496], 'heritage_right': [285, 497], 'heritage_bottom': [270, 520],
    'address_left': [288, 499], 'address_right': [322, 500], 'address_bottom': [306, 510],
    'memorial_left': [332, 501], 'memorial_right': [356, 502], 'memorial_crown': [345, 486],
    'memorial_bottom': [344, 528],
}
# A closer photograph of the same wall independently resolves its plate widths.
CLOSE_POINTS = {
    'heritage_left_top': [463, 439], 'heritage_right_top': [618, 437],
    'heritage_right_bottom': [619, 572], 'heritage_left_bottom': [456, 570],
    'number_left_top': [629, 457], 'number_right_top': [810, 450],
    'number_right_bottom': [813, 509], 'number_left_bottom': [628, 515],
    'old_home_medallion': [960, 423], 'old_home_crown': [961, 369],
    'old_home_base': [962, 595], 'wall_belt': [627, 592],
}


def homography(points, target):
    system, values = [], []
    for (u, v), (x, z) in zip(points, target):
        system += [[u, v, 1, 0, 0, 0, -u*x, -v*x], [0, 0, 0, u, v, 1, -u*z, -v*z]]
        values.extend([x, z])
    coeff, *_ = np.linalg.lstsq(system, values, rcond=None)
    return np.append(coeff, 1.).reshape(3, 3)


def transformed(H, pair):
    x, z, scale = H @ [*pair, 1]
    return [round(x/scale, 5), round(z/scale, 5)]


def measure():
    H = homography(WIDE_CONTROL, DEST)
    measured = {key: transformed(H, pixel) for key, pixel in WIDE_POINTS.items()}
    left, right = measured['heritage_left'][0], measured['heritage_right'][0]
    top = (measured['heritage_left'][1] + measured['heritage_right'][1]) / 2
    bottom = measured['heritage_bottom'][1]
    image_points = list(CLOSE_POINTS.values())[:4]
    close = homography(image_points, [[left,top], [right,top], [right,bottom], [left,bottom]])
    other = {key: transformed(close, pixel) for key, pixel in CLOSE_POINTS.items()}
    return {'units':'metres','assumed_cap_height_m':CAP_HEIGHT,'estimated_post_axis_spacing_m':POST_SPACING,
            'wide_image_pixels':WIDE,'wide_controls_px':WIDE_CONTROL,'wide_control_metric':DEST,
            'wide_homography':H.tolist(),'wide_landmarks_px':WIDE_POINTS,'wide_landmarks_xz':measured,
            'close_landmarks_px':CLOSE_POINTS,'close_homography':close.tolist(),'close_landmarks_xz':other,
            'address_width_wide_m':round(measured['address_right'][0]-measured['address_left'][0],4),
            'address_width_close_m':round(other['number_right_top'][0]-other['number_left_top'][0],4),
            'scope':'Vertical street-facing planes. Post depth, gate-leaf angle and physical dimensions are estimates.'}


if __name__ == '__main__':
    (HERE/'photo-rectification.json').write_text(json.dumps(measure(),ensure_ascii=False,indent=2)+'\n')
