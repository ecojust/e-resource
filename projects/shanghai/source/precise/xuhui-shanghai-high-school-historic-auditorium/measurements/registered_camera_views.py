"""Export two registered pinhole poses for a horizontal-fit Blender camera."""
import argparse
import json
from pathlib import Path
import numpy as np
from register_court import Camera


def photographic_view(station):
    camera = Camera(station)
    width, height = camera.size
    fx, fy = camera.k[0, 0], camera.k[1, 1]
    cx, cy = camera.k[:2, 2]
    depth = -camera.c[1] / camera.r[2, 1]
    target = camera.c + depth * camera.r[2]
    pixel_aspect = fx / fy
    return {
        'name': 'photo-' + station,
        'label': {'1934': '1934年礼堂与东墙', '2020': '2020年礼堂正门'}[station],
        'eye': camera.c.tolist(), 'target': target.tolist(),
        'width_m': float(width * depth / fx), 'width': width, 'height': height,
        'world_up': (-camera.r[1]).tolist(), 'reference': 'Hall photograph ' + station,
        'pixel_aspect_y': float(pixel_aspect),
        'sensor_fit': 'HORIZONTAL',
        'shift_x': float((width * .5 - cx) / width),
        'shift_y': float((cy - height * .5) * pixel_aspect / width),
        'principal_point_px': [float(cx), float(cy)]
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.write_text(json.dumps(
        [photographic_view(station) for station in ('1934', '2020')],
        ensure_ascii=False, indent=2
    ) + '\n')
