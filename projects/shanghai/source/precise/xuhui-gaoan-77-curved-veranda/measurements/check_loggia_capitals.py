"""Reproject the measured capital under the south porch, keeping its axis and foot fixed."""
import argparse
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'source'))
from house_layout import D, U, Z
from photo_cameras import projection
from south_verandah import CAPITAL_BELOW_EAVE_M, EAVE, FACE, START

# Pixel centres in the original working rasters, read at the crown of the round
# moulding immediately below the square block. The eastern capital is obscured.
OBSERVATIONS = {'paper-25': (393.,139.), 'sina-35': (223.,204.)}


def compare():
    x = U(START) + .12
    y = D(FACE) + .11
    top = Z(EAVE)
    readings = []
    for name, xy in OBSERVATIONS.items():
        camera = projection(name)
        row = {'photo':name,'observed_px':xy}
        for stage, drop in [('before',.09),('after',CAPITAL_BELOW_EAVE_M)]:
            h = camera @ [x,y,top-drop,1.]
            pixel = h[:2] / h[2]
            row[stage] = {'projected_px':np.round(pixel,4).tolist(),
                          'residual_px':round(float(np.linalg.norm(pixel-xy)),4)}
        # The other photograph alone determines height when this observation is withheld.
        other = next(key for key in OBSERVATIONS if key != name)
        other_p = projection(other)
        other_y = OBSERVATIONS[other][1]
        constraint = other_p[1] - other_y * other_p[2]
        z_other = -(constraint @ [x,y,0.,1.]) / constraint[2]
        predicted = camera @ [x,y,z_other,1.]
        predicted = predicted[:2] / predicted[2]
        row['held_out'] = {'fit_vertical_coordinate_from':other,
                           'capital_separation_m':round(float(top-z_other),4),
                           'predicted_px':np.round(predicted,4).tolist(),
                           'residual_px':round(float(np.linalg.norm(predicted-xy)),4)}
        readings.append(row)
    return {'feature':'Centre of the western south-loggia circular capital just below its square bearing',
            'scope':'Only the height of the circular capital was adjusted. The foot and soffit remain at their established levels. The absolute scale is approximate. The hidden eastern support repeats the measured western arrangement.',
            'method':'One vertical parameter chosen to minimize the sum of squared image errors from the two fixed south-window-and-gallery-fit.json cameras. The held_out entries fit height using only the other photograph’s vertical observation.',
            'references':{'paper-25':'https://sh.people.com.cn/n2/2022/1227/c350122-40245366.html',
                          'sina-35':'https://blog.sina.com.cn/s/blog_5d1bdf480101ee2y.html'},
            'working_rasters':{'paper-25':[640,368],'sina-35':[690,390]},
            'previous_separation_m':.09,'fitted_separation_m':CAPITAL_BELOW_EAVE_M,
            'lowering_m':round(CAPITAL_BELOW_EAVE_M-.09,3),'observations':readings}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path)
    args = parser.parse_args()
    result = json.dumps(compare(),ensure_ascii=False,indent=2) + '\n'
    if args.output:
        args.output.write_text(result)
    else:
        print(result,end='')
