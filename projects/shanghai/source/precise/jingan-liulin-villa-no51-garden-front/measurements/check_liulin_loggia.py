"""Ray-test the two-storey loggia in a standalone or a whole-house decoded GLB.

The physical rays include open air. Photographic rays follow recorded native
pixels through a short depth interval around the loggia so that a gate or a
recessed window behind an opening is not mistaken for the balustrade itself.
"""
import argparse
import json
from pathlib import Path
import sys
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent/'source'), str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact')]
import liulin_loggia as loggia
from glb_triangles import SerialScene

def tally(rows):
    return {'passed':sum(bool(row['passed']) for row in rows), 'total':len(rows), 'rays':rows}


def inspect(asset):
    scene = SerialScene(asset)
    survey = json.loads((HERE/'no51-loggia-survey.json').read_text())
    cameras = json.loads((HERE/'no51-house-cameras.json').read_text())['source_poses']
    physical, surveyed, sightlines = [], [], []

    def check(rows, name, start, direction, distance, expected, **extra):
        hit = scene.ray(start, direction, distance)
        value = hit['material'] if hit else None
        rows.append(dict(feature=name, passed=value in expected, material=value, expected=expected, **extra))

    for i, (x, y) in enumerate(loggia.COLUMNS):
        for z in (.62, .88, 1.3, 1.52, 1.77, 2.10, 2.65, 3.32, 3.82, 4.00, 4.224,
                  4.81, 5.11, 5.49, 5.82, 6.03, 6.39, 7.10, 7.41, 7.76, 8.05, 8.14):
            check(physical, 'column', [x,y-.32,z], [0,1,0], .38,
                  [loggia.EDGE,loggia.PLINTH,loggia.PLASTER], group=i+1, z=z)
    for i,x in enumerate(loggia.RAIL_X):
        for z in (5.07,5.173,5.23,5.35,5.52,5.65):
            check(physical, 'square baluster', [x,loggia.rail_y(x)-.15,z], [0,1,0], .4,
                  [loggia.PLASTER], group=i+1, z=z)
    for i,(x0,x1) in enumerate(zip(loggia.RAIL_X, loggia.RAIL_X[1:])):
        if x1-x0 > .33: continue
        x=(x0+x1)/2
        for z in (5.09,5.18,5.30,5.42,5.51,5.65):
            normal=np.array([-(.01207329+2*.03755177*x),1.,0.])
            normal/=np.linalg.norm(normal)
            centre=np.array([x,loggia.rail_y(x)+.085,z])
            check(physical,'opening between balusters',centre-normal*.19,normal,.36,
                  [None],group=i+1,z=z)
    for x in (-3.7,-1.75,0.,1.72,3.7):
        for z in (4.37,4.53,4.71,4.94,5.81):
            check(physical,'balcony front',[x,loggia.rail_y(x)-.19,z],[0,1,0],.47,
                  [loggia.PLASTER,loggia.EDGE],x=x,z=z)
        for z in (8.201,8.32,8.44,8.51,8.65,8.725):
            check(physical,'terrace cornice',[x,loggia.terrace_y(x)-.19,z],[0,1,0],.48,
                  [loggia.PLASTER,loggia.EDGE],x=x,z=z)
    for x in (-3.55,-1.72,0.,1.72,3.55):
        for y in (.32,1.15):
            check(physical,'entrance landing',[x,y,.56],[0,0,-1],.059,[loggia.FLOOR],x=x,y=y)

    for row in survey['native_pixel_controls']:
        doc = cameras['gao'+row['tag']]
        p=np.array(doc['P'])
        eye=np.array(doc['eye_m'])
        direction=np.linalg.solve(p[:,:3],[*row['pixel'],1.])
        direction=direction/np.linalg.norm(direction)
        feature=row['feature']
        if feature=='shaft':
            xy=loggia.COLUMNS[row['group']-1]
            centre=(xy[1]-eye[1])/direction[1]
            radius=.32
        else:
            first=loggia.RAIL_X[row['group']-1]
            x=(first+loggia.RAIL_X[row['group']])/2 if feature=='opening' else first
            centre=(loggia.rail_y(x)+.085-eye[1])/direction[1]
            radius=.175
        expected = [None] if feature=='opening' else [loggia.PLASTER]
        check(surveyed,feature,eye+direction*(centre-radius),direction,radius*2,expected,
              station=row['tag'],group=row['group'],native_pixel=row['pixel'])
        direct = scene.ray(eye, direction, centre+radius)
        visible = direct is None if feature=='opening' else (
            direct is not None and direct['material'] in expected and direct['distance_m']>=centre-radius)
        sightlines.append(dict(feature=feature, passed=bool(visible), station=row['tag'],group=row['group'],
                               native_pixel=row['pixel'], first_material=direct['material'] if direct else None,
                               first_distance_m=direct['distance_m'] if direct else None))
    return dict(asset=scene.asset,physical=tally(physical),photo_pixels=tally(surveyed),
                unfiltered_original_camera=tally(sightlines))


if __name__ == '__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('asset',type=Path)
    ap.add_argument('output',type=Path)
    args=ap.parse_args()
    result=inspect(args.asset)
    args.output.write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n')
    for label in ('physical','photo_pixels','unfiltered_original_camera'):
        row=result[label]
        print(label,row['passed'],row['total'],[x for x in row['rays'] if not x['passed']][:4])
    raise SystemExit(int(result['physical']['passed']!=result['physical']['total']))
