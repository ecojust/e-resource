"""Trace native image rays and portal-camera sightlines to the actual first surface."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'xuhui-pathe-records-office/measurements/city-contact'))
from glb_triangles import SerialScene

OBS = HERE / 'entrance-soffit-photo-observations.json'


def inspect(mesh):
    data = json.loads(OBS.read_bytes())
    scene = SerialScene(mesh)
    checks = {}

    def trace(eye, direction):
        h = scene.ray(eye, direction, 65)
        if h is None:
            return None
        return {'material': h['material'], 'xyz_m': np.round(h['point_enu_m'], 4).tolist()}

    for group, witness, token in [('street_grey_underside', 'street', 'exposed grey plaster'),
                                  ('interior_downstand', 'inside', 'blue-grey inner face'),
                                  ('below_downstand', 'inside', None)]:
        camera = data[witness]['camera']
        P = np.asarray(camera['P'] if isinstance(camera, dict) else camera)
        inverse = np.linalg.inv(P[:, :3])
        eye = -inverse @ P[:, 3]
        readings = []
        for uv in data['probes'][group]:
            hit = trace(eye, inverse @ [*uv, 1])
            material = '' if hit is None else hit['material']
            passes = token in material if token else 'Entry beam /' not in material
            readings.append(dict(uv=uv, first=hit, matches=passes))
        checks[group] = readings

    portal = data['probes']['portal_view_screened_old_ceiling']
    eye = np.asarray(portal['eye'])
    checks['portal_view'] = []
    for point in portal['targets']:
        hit = trace(eye, np.asarray(point) - eye)
        screened = hit is not None and hit['material'] != 'Passage / warm ceiling'
        checks['portal_view'].append(dict(old_top_xyz=point, first=hit, matches=screened))
    return dict(asset=scene.asset, counts={k:[sum(p['matches'] for p in v),len(v)] for k,v in checks.items()},
                checks=checks)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('mesh', nargs='+',type=Path)
    ap.add_argument('--output', required=True, type=Path)
    args = ap.parse_args()
    results = {'photo_controls_sha256':hashlib.sha256(OBS.read_bytes()).hexdigest(),
               'meshes':[inspect(path) for path in args.mesh]}
    args.output.write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
