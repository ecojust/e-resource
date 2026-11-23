"""Compare the first material reached by each native photo observation with a complete GLB."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

import numpy as np

measurements = Path(__file__).resolve().parent
project = measurements.parents[3]
sys.path.insert(0, str(project / 'source/precise/xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
from glb_triangles import SerialScene


def verify(asset, report, local=False):
    survey = json.loads((measurements/'house-eight-entrance-observations.json').read_bytes())
    layout = json.loads((measurements.parent/'source/garden-layout.json').read_bytes())
    scene = SerialScene(asset)
    transform = np.eye(4)
    if not local:
        frame = layout['8']['garden_transform']
        transform[:2,:2] = np.array([frame['local_X_unit_EN'], frame['local_Y_unit_EN']]).T
        transform[:2,3] = frame['left_wall_projection']['garden_ENU_m']
    records = {}
    stations = dict(survey['views'])
    court = json.loads((measurements/'courtyard-front-station.json').read_bytes())
    stations['winter2023-04-courtyard'] = {
        **stations['winter2023-04'],
        'P': court['house8_to_upright_pixel_camera'],
        'camera_kind': 'Separate exterior courtyard reconstruction of station 04, using identical photo pixels.',
    }
    for name, station in stations.items():
        P = np.array(station['P']) @ np.linalg.inv(transform)
        inverse = np.linalg.inv(P[:,:3])
        eye = -inverse @ P[:,3]
        rows = []
        for point in station['rays']:
            direction = inverse @ np.r_[point['uv'], 1.]
            hit = scene.ray(eye, direction, 120.)
            material = hit['material'] if hit else None
            outcome = 'matched' if material in point['first_materials'] else 'different material'
            if material is None:
                outcome = 'clear ray'
            elif 'garden |' in material and outcome != 'matched':
                outcome = 'garden occlusion'
            rows.append({**point, 'first_hit': hit, 'outcome': outcome})
        records[name] = {'camera': station['camera_kind'], 'counts': dict(Counter(row['outcome'] for row in rows)),
                         'records': rows}
    data = {'asset': scene.asset, 'author_local_to_scene_enu': transform.tolist(),
            'method': 'First intersection of the unfiltered decoded triangle mesh. Each point was recorded in the published image before testing the full building. A second count retains modern foliage across an older sightline. Camera 12 is a planar transfer of station 04.',
            'total': sum(len(record['records']) for record in records.values()), 'stations': records}
    report.write_text(json.dumps(data, ensure_ascii=False, indent=1)+'\n')
    print(asset.name, {key: row['counts'] for key, row in records.items()})
    return data


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('glb', type=Path)
    parser.add_argument('report', type=Path)
    parser.add_argument('--local', action='store_true', help='Input uses the No. 8 local frame, before placement in the garden')
    args = parser.parse_args()
    verify(args.glb, args.report, args.local)
