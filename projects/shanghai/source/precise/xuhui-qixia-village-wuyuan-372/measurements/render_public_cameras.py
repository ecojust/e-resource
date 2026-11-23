"""Render all nine views, including the measured camera roll at the four 2016 stations."""
import argparse
import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np

HERE = Path(__file__).resolve().parent
SHARED = HERE.parents[1] / 'xuhui-huashan-823-827-stair-loggia/measurements/render_public_cameras.py'


def projection(view):
    eye = np.asarray(view['eye'], dtype=float)
    delta = np.asarray(view['target'], dtype=float) - eye
    distance = np.linalg.norm(delta)
    forward = delta / distance
    right = np.cross(forward, view.get('world_up', [0., 0., 1.]))
    right /= np.linalg.norm(right)
    down = np.cross(forward, right)
    rotation = np.stack((right, down, forward))
    width, height = view['width'], view['height']
    focal = distance * width / view['width_m']
    intrinsic = np.array([[focal, 0, width / 2], [0, focal, height / 2], [0, 0, 1]])
    return intrinsic @ np.column_stack((rotation, -rotation @ eye))


def render(mesh, output, cameras):
    spec = importlib.util.spec_from_file_location('ordinary_camera_renderer', SHARED)
    renderer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(renderer)
    with patch.object(renderer, 'camera', projection):
        renderer.main(mesh, output, cameras)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mesh', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--cameras', type=Path, default=HERE.parent / 'source/cameras.json')
    args = parser.parse_args()
    render(args.mesh, args.output, args.cameras)
