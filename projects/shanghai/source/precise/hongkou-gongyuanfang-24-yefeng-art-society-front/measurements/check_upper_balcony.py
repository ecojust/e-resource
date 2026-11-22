"""Intersect the full model with horizontal, vertical, and registered photograph rays."""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'source'),
                str(HERE.parents[1] / 'xuhui-pathe-records-office/measurements/city-contact')]
from frontage_coordinates import FRONT_CAMERA, GABLE_CAMERA
from glb_triangles import SerialScene
from upper_balcony import COVER, CUT, EDGE, FASCIA, IRON, JOINT, LIP, LOW, PLASTER, SOFFIT, WHITE


def section_probes():
    for x in (.18, .42, .66, 1.05, 1.41, 1.76, 2.23, 2.66, 3.12, 3.50):
        for z, material in [(1.55, LOW), (1.83, EDGE), (1.995, LIP), (2.045, JOINT), (2.127, LIP),
                            (4.946, FASCIA), (5.053, COVER)]:
            yield 'curved edge or eave', [x, -1.4, z], [0, 1, 0], material
    for x in (.51, .64, .91, 1.5, 1.73, 2.33, 2.79, 3.21):
        for z in (2.738, 2.92):
            yield 'continuous horizontal railing', [x, -1.4, z], [0, 1, 0], IRON
        yield 'canopy underside', [x, .48, 4.50], [0, 0, 1], SOFFIT
        yield 'rear beam', [x, .48, 4.71], [0, 1, 0], FASCIA
    uprights = np.linspace(.388, 3.358, 24)
    for x0, x1 in zip(uprights, uprights[1:]):
        yield 'full-height upright', [x0, -1.4, 2.49], [0, 1, 0], IRON
        yield 'short upper upright', [(x0+x1)/2, -1.4, 2.84], [0, 1, 0], IRON
        yield 'opening under the short upright', [(x0+x1)/2, -1.4, 2.51], [0, 1, 0], CUT
    for x in (.11, .29):
        yield 'solid left screen', [x,-1.4,2.61], [0,1,0], WHITE
    for x in (3.47,3.82):
        yield 'pebble-dash end pier', [x,-1.4,3.35], [0,1,0], PLASTER


def pixel_ray(camera, px):
    matrix = camera[:, :3]
    eye = -np.linalg.solve(matrix, camera[:,3])
    direction = np.linalg.solve(matrix, [*px,1.])
    return eye, direction


# In both published photographs the upper eave is visible against the sky.
# Points lie inside the band, avoiding the silhouette's subpixel ambiguity.
PHOTO_PROBES = [
    ('figure 6', FRONT_CAMERA, (285,250), FASCIA),
    ('figure 6', FRONT_CAMERA, (341,270), FASCIA),
    ('figure 6', FRONT_CAMERA, (407,294), FASCIA),
    ('figure 4', GABLE_CAMERA, (568,161), FASCIA),
    ('figure 4', GABLE_CAMERA, (593,155), FASCIA),
    ('figure 4', GABLE_CAMERA, (617,148), FASCIA),
]


def examine(path):
    scene = SerialScene(path)
    records = []
    def test(label, origin, direction, material, length, pixel=None):
        hit = scene.ray(origin,direction,length)
        records.append(dict(test=label,origin=np.asarray(origin).tolist(),
                            direction=np.asarray(direction).tolist(),
                            expected=material,first_hit=hit,original_pixel=pixel,
                            passed=hit is not None and hit['material']==material))
    for label,origin,direction,material in section_probes():
        test(label,origin,direction,material,3.)
    for source,camera,px,material in PHOTO_PROBES:
        origin,direction=pixel_ray(camera,px)
        test(source,origin,direction,material,100.,px)
    return dict(asset=scene.asset,tests=len(records),passed=sum(row['passed'] for row in records),
                records=records)


if __name__=='__main__':
    destination=Path(sys.argv[1])
    entries=[examine(Path(mesh)) for mesh in sys.argv[2:]]
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text(json.dumps(dict(
        study='Gongyuanfang No. 24 | third-storey exterior balcony', roles=entries),
        ensure_ascii=False,separators=(',',':'))+'\n')
    for record in entries:
        print(record['asset']['file'],record['passed'],record['tests'])
        for row in record['records']:
            if not row['passed']: print(row['test'],row['original_pixel'],row['origin'],row['expected'],(row['first_hit'] or {}).get('material'))
    sys.exit(any(item['passed']!=item['tests'] for item in entries))
