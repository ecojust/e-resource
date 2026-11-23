"""Trace the seven public cameras through a raw or independently decoded Yanqing Road mesh."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

SITE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SITE / 'source'))
from check_front_pixels import check as check_photograph
from glb_triangles import SerialScene
from brick_finishes import GREY_BRICK, HERRINGBONE, RED_BAND
from materials import GLASS, GREEN, PALE
import western_bay as bay

# Metres in the facade coordinate system. Points behind glazing cross the original
# opening before reaching the target. Only the first intersected triangle counts.
SAMPLES = {
    'overview': [
        ('upper parapet', [-5.15, -.01, 7.58], PALE),
        ('west green door leaf', [.46, 1.49, 1.72], bay.GREEN),
        ('upper grey brick', [-9.72, 0, 5.35], GREY_BRICK),
    ],
    'windows': [
        (label, [x, .098, 5.17], GLASS)
        for label, x in [('east pale sash', -14.83), ('second pale sash', -10.84),
                        ('middle timber sash', -8.22), ('fourth timber sash', -6.17),
                        ('west timber sash', -3.36)]
    ],
    'bond': [('grey Flemish field', [-7.06, 0, 4.78], GREY_BRICK),
             ('red horizontal course', [-6.94, -.01, 4.30], RED_BAND)],
    'herringbone': [('left of panel', [-8.40, -.015, 3.56], HERRINGBONE),
                    ('right of panel', [-7.88, -.015, 3.75], HERRINGBONE)],
    'entry': [('green door', [-5.21, .076, 1.29], GREEN),
              ('red course beside shopfront', [-6.02, -.008, .933], RED_BAND)],
    'oriel': [('single glazed casement', [-.61, .778, 5.11], bay.BLUE),
              ('opaque front panel', [.24, .734, 5.22], bay.CREAM),
              ('left timber post', [-.926, .671, 5.22], bay.TIMBER)],
    'arch': [('left painted leaf', [-.25, 1.485, 1.20], bay.GREEN),
             ('right painted leaf', [.46, 1.485, 1.72], bay.GREEN),
             ('keystone', [0, 1.053, 3.20], bay.DARK)]
}

def inspect(mesh: Path) -> dict:
    camera_file = SITE / 'source/cameras.json'
    cameras = json.loads(camera_file.read_bytes())
    assert set(SAMPLES) == {v['name'] for v in cameras}
    scene = SerialScene(mesh)
    rows = []
    for camera in cameras:
        eye = np.asarray(camera['eye'])
        for label, xyz, expected in SAMPLES[camera['name']]:
            hit = scene.ray(eye, np.asarray(xyz) - eye, 100)
            rows.append({'camera': camera['name'], 'feature': label, 'target_m': xyz,
                         'expected': expected, 'first_hit': hit,
                         'matched': bool(hit and hit['material'] == expected)})
    return {'mesh': mesh.name, 'mesh_sha256': hashlib.sha256(mesh.read_bytes()).hexdigest(),
            'cameras_sha256': hashlib.sha256(camera_file.read_bytes()).hexdigest(),
            'viewer_samples': rows, 'viewer_matches': sum(row['matched'] for row in rows),
            'viewer_total': len(rows), 'original_2018_registration': check_photograph(mesh)}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mesh', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = inspect(args.mesh)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(result['viewer_matches'], result['viewer_total'], result['original_2018_registration']['matched'],
          result['original_2018_registration']['count'])
