"""Compare the bracket seats, garden sill timber and chimney in their original exterior photographs."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent


def load(filename):
    return json.loads((HERE / filename).read_bytes())


def homography_hit(matrix, uv):
    point = np.linalg.solve(matrix, [*uv, 1.0])
    return point[:2] / point[2]


def southern_point_at_depth(camera, uv, depth):
    plane = camera[:, [0, 2, 3]].copy()
    plane[:, 2] += depth * camera[:, 1]
    x, z = homography_hit(plane, uv)
    return [round(x, 4), depth, round(z, 4)]


def measure():
    survey = load('west-eave-photo-control.json')
    metric = load('metric-exterior-photo-frames.json')
    west = metric['western_wall_homographies']
    scale = west['metres_per_conditional_west_study_metre']
    seat = west['world_xyz_metres']['seat-1'][2]
    origin_y = west['world_xyz_metres']['seat-1'][1]
    deck = metric['layout']['deck_z']
    views = {k: np.array(v['plane_to_pixel']) for k, v in survey['cameras'].items()}
    views['commons-1250'] = np.diag([1250 / 3648, 704 / 2056, 1]) @ views['commons2013']
    # The published plate 26 reproduces the August 2013 exposure with a small crop.
    article_to_31 = np.array([[1.05155255, 0, 9.15396453], [0, 1.05414994, 4.152454], [0, 0, 1]])
    views['sina31-690'] = article_to_31 @ views['paper2022']

    # Each interval brackets an obscured joint. Different depths along the horizontal rail
    # are apparent in these glancing views. Both boundaries are retained in the result.
    limits = {'sina26': [(545, 149), (552, 160)], 'sina39': [(591, 27), (596, 34)],
              'sina31-690': [(503, 132), (509, 147)]}
    bracket_rows = []
    for view, pixels in limits.items():
        row = []
        for pixel in pixels:
            s, h = homography_hit(views[view], pixel)
            row.append({'pixel': pixel, 'wall_y_m': round(origin_y - scale * s, 3),
                        'implied_seat_if_point_is_at_sill_timber_m': round(deck - scale * h, 3)})
        bracket_rows.append({'view': view, 'intersections': row})

    marks = {'commons-1250': {'near_face_cap_edge': [(551.1, 89), (601.6, 78.2)],
                              'cap_return_corner': [(612, 84.5)],
                              'pot_bases_north_to_south': [(567.8, 69.5), (581.4, 67), (596.5, 63.8)],
                              'pot_tops_north_to_south': [(568, 45.1), (581.1, 41.6), (595.7, 38.4)]},
             'sina31-690': {'near_face_cap_edge': [(346.2, 20.5), (393.5, 8)],
                             'cap_return_corner': [(399.2, 22.8)],
                             'lower_shaft_shoulder': [(343, 59.5), (394, 48.5)]}}
    chimney = {}
    for view, names in marks.items():
        chimney[view] = {}
        for name, pixels in names.items():
            row = []
            for pixel in pixels:
                s, h = homography_hit(views[view], pixel)
                row.append({'pixel': pixel, 'conditional_s': round(s, 4),
                            'y_on_x0_m': round(origin_y - scale * s, 4),
                            'z_on_x0_m': round(seat + scale * h, 4)})
            chimney[view][name] = row

    south = metric['southern_photo_cameras']['arched timber and folded roof']['cameras']
    intersections = {}
    for view, controls in {'sina-37': [(192.7, 34, 2.41), (199.5, 40, 2.74), (205.5, 45.5, 3.03)],
                           'paper-25': [(265.2, 2.5, 2.41), (264.5, 23, 2.32)]}.items():
        camera = np.array(south[view]['world_xyz_metres_to_reference_pixels'])
        intersections[view] = [{'pixel': [u, v], 'xyz_at_west_side_y_m': southern_point_at_depth(camera, [u, v], y)}
                               for u, v, y in controls]
    return {
        'scale': {'post_span_m': metric['layout']['post_span'], 'garden_sill_timber_z_m': deck,
                  'seat_z_used_m': seat, 'outer_soffit_z_m': round(seat + scale * 1.31, 4)},
        'original_photos': survey['references'],
        'coordinate_systems': {'commons-1250': '3648 x 2056 original sampled at 1250 x 704',
                               'sina31-690': '4912 x 3264 source at 690 x 459',
                               'sina26': '690 x 528', 'sina39': '690 x 459',
                               'sina-37': '690 x 459', 'paper-25': '640 x 368'},
        'visible_south_timber': {'paper-25': [276.2, 110.4], 'sina-37': [136.6, 200.7]},
        'west_sill_to_saddle_brackets': bracket_rows, 'west_stack': chimney,
        'southern_checks': intersections,
        'interpretation': [
            'The exposed side of the south sill timber falls near the last western saddle in both the November 2012 and April 2018 photographs. The contact is partly hidden by the stone corbel. The seat is set 0.22 m above the sill timber, with approximate local uncertainty of 0.25 m.',
            'The three pot rims in March 2013 are visible again above the southern roof in February 2018. Their north-to-south stack axis, cap and tapered shoulders are independently visible in August 2013. The 2022 published front plate does not separate the three pots.',
            'Local estimates with the adopted 3.13 m scale are cap eave Z13.28, tapered cap top Z13.60, pot tops Z14.10 and common pot X about +0.055 m. The shaft and cap depth out of the western wall is weakly resolved. The roof hides the south-view cap corners.',
            'Native file references and the timber controls are documented in west-eave-photo-control.json and curved-veranda-folded-roof.json. The road elevation datum and the 3.13 m span carry additional common scale and height uncertainty.'
        ],
        'inputs': {n: sha256((HERE / n).read_bytes()).hexdigest() for n in
                   ['west-eave-photo-control.json', 'metric-exterior-photo-frames.json', 'curved-veranda-folded-roof.json']}
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    output = parser.parse_args().output
    output.write_text(json.dumps(measure(), ensure_ascii=False, indent=2) + '\n')
