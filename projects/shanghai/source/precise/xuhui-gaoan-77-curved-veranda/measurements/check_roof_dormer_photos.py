"""Trace fixed roof and dormer samples through the exported building from the original camera."""
import argparse
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent / 'source'))
sys.path.insert(0,str(HERE.parents[1] / 'xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
from glb_triangles import SerialScene
from fit_west_dormer import P as WEST_CAMERA
from materials import DARK, FRAME, GLASS, PLASTER, RIDGE, ROOF, STONE
from photo_cameras import projection


def check(file, controls, east_light=False):
    group_material = {'clay':[ROOF,RIDGE],'fascia':[DARK],'bargeboard':[DARK],
                      'south dormer glass':[GLASS],'west dormer glass':[GLASS],
                      'south dormer cheek':[PLASTER],'west dormer cheek':[PLASTER],
                      'east dormer cheek':[PLASTER],'west dormer coping':[DARK,STONE],
                      'east dormer coping':[DARK,STONE], 'cheek':[PLASTER],
                      'coping':[DARK,STONE], 'glazing_or_frame':[GLASS,FRAME]}
    scene = SerialScene(file)
    rows = []
    observations = controls['surface_check_points'] if east_light else controls['observations']
    for image, groups in observations.items():
        if image == 'sina-38':
            east_registration = json.loads((HERE / 'east-return-photo-control.json').read_text())
            transfer = np.array(east_registration['registration']['homography_35_to_38'])
            p = transfer @ projection('sina-35')
        elif image == 'sina-26':
            p = WEST_CAMERA
        else:
            p = projection(image)
        inverse = np.linalg.inv(p[:, :3]); eye = -inverse @ p[:, 3]
        for name, pixels in groups.items():
            expected = group_material[name]
            for x,y in pixels:
                hit = scene.ray(eye,inverse@[x,y,1],130)
                actual = hit['material'] if hit else None
                rows.append(dict(photo=image,feature=name,pixel=[x,y],expected=expected,
                                 first_hit=actual,matched=actual in expected))
    groups = {}
    for row in rows:
        key = row['photo'] + ' | ' + row['feature']; counts = groups.setdefault(key,[0,0]);
        counts[0] += row['matched']; counts[1] += 1
    return dict(asset=scene.asset,matched=sum(r['matched'] for r in rows),total=len(rows),groups=groups,readings=rows)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mesh',type=Path);parser.add_argument('output',type=Path)
    parser.add_argument('--east-light',action='store_true',help='Check the east facing roof light in plates 35 and 38')
    args=parser.parse_args()
    control = 'east-roof-light-photo-control.json' if args.east_light else 'roof-dormer-photo-pixels.json'
    result=check(args.mesh,json.loads((HERE/control).read_text()),args.east_light)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(result['matched'],'/',result['total'],result['groups'])
