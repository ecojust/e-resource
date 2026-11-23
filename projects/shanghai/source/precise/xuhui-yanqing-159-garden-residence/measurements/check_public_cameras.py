"""Check first-hit materials and image bounds for each of the seven model-page cameras."""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'source'
sys.path[:0] = [str(SOURCE), str(HERE.parents[1] / 'xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact')]
from glb_triangles import SerialScene
from residence_materials import GLASS, IVORY_RENDER, PEBBLEDASH, SHADE, SILL
from upper_sash import GREEN_GLASS, LIGHT_GLASS


def leaf_point(name):
    control = json.loads((HERE/'return-casement-photo-control.json').read_bytes())
    leaf = control['leaves'][name]
    t = math.radians(leaf['swing_degrees'])
    width = .44 * leaf['leaf_width_m']
    return [.010 + width * math.sin(t), leaf['working_hinge_u'] + width * math.cos(t),
            leaf['sill'] + .26 * (leaf['head'] - leaf['sill'])]


def targets():
    return {
        'overview': [('garden aggregate', [-2.53, 0., 2.56], PEBBLEDASH),
                     ('corner render', [-.07, -.02, 2.63], IVORY_RENDER),
                     ('street aggregate', [0., 3.48, 2.21], PEBBLEDASH)],
        'entrance': [('pier beside the arch', [-5.27, -.018, 2.18], IVORY_RENDER),
                     ('high landing glass', [-7.87, .109, 5.28], GLASS)],
        'return': [('lower glazing', [-.110, 1.33, 1.47], GLASS),
                   ('upper render band', [.019, 4.07, 5.87], IVORY_RENDER)],
        'arch': [('recess', [-4.56, .528, 1.63], SHADE), ('medallion', [-4.54, -.039, 2.98], SILL),
                 ('left arched surround', [-5.055, -.062, 1.80], IVORY_RENDER)],
        'steel': [('near open glazed leaf', leaf_point('near-open'), GREEN_GLASS),
                  ('rendered lintel', [.079, 1.85, 4.34], IVORY_RENDER)],
        'attic': [('first green leaf', leaf_point('attic-green-first'), GREEN_GLASS),
                  ('second green leaf', leaf_point('attic-green-second'), GREEN_GLASS),
                  ('pale leaf', leaf_point('attic-pale'), LIGHT_GLASS)],
        'lintels': [('middle raised lintel face', [.079, 4.48, 3.93], IVORY_RENDER),
                    ('far raised lintel face', [.079, 7.22, 3.84], IVORY_RENDER),
                    ('aggregate between window heads', [0., 6.19, 4.03], PEBBLEDASH)],
    }


def projected(camera, xyz):
    eye = np.array(camera['eye'])
    axis = np.array(camera['target']) - eye
    distance = np.linalg.norm(axis)
    axis /= distance
    right = np.cross(axis, [0., 0., 1.])
    right /= np.linalg.norm(right)
    down = np.cross(axis, right)
    delta = xyz - eye
    depth = np.dot(axis, delta)
    fx = distance * camera['width'] / camera['width_m']
    return [(camera['width']/2 + fx*np.dot(right,delta)/depth) / camera['width'],
            (camera['height']/2 + fx*np.dot(down,delta)/depth) / camera['height']]


def inspect(mesh):
    from build_model import METRIC_SCALE
    camera_file = SOURCE / 'cameras.json'
    cameras = json.loads(camera_file.read_bytes())
    features = targets()
    assert {camera['name'] for camera in cameras} == set(features)
    scene = SerialScene(mesh)
    observations = []
    for camera in cameras:
        for name, target, expected in features[camera['name']]:
            xyz = np.array(target) * METRIC_SCALE
            eye = np.array(camera['eye'])
            hit = scene.ray(eye, xyz-eye, 120)
            uv = projected(camera, xyz)
            inside = all(0 < value < 1 for value in uv)
            observations.append({'camera': camera['name'], 'feature': name, 'surface': expected,
                'target_m': xyz.tolist(), 'relative_image_position': uv, 'within_frame': inside,
                'first_hit': hit, 'matches': bool(inside and hit and hit['material'] == expected)})
    return {'mesh': mesh.name, 'mesh_sha256': hashlib.sha256(mesh.read_bytes()).hexdigest(),
            'cameras_sha256': hashlib.sha256(camera_file.read_bytes()).hexdigest(),
            'count': len(observations), 'matched': sum(row['matches'] for row in observations),
            'observations': observations}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mesh', type=Path)
    p.add_argument('output', type=Path)
    args = p.parse_args()
    result = inspect(args.mesh)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(result['matched'], '/', result['count'])
