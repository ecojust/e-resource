"""Measure the profile, joints, lintels, and empty space in the exported historical ornament."""
import argparse
import json
import math
from pathlib import Path
import runpy

HERE = Path(__file__).resolve().parent
inspect = runpy.run_path(HERE.parent / 'central-reserve-bank-changshu-front-v1/verify-export.py')['inspect']
TILES = ['Ochre glazed ceramic', 'Honey glazed ceramic', 'Weathered buff glaze', 'Brown glazed ceramic']
TURN = math.pi * .55 / 2


def frame(station):
    if station < 0:
        return [station, 0], [0, -1]
    if station > TURN:
        return [.55, .55 + station - TURN], [1, 0]
    angle = station / .55
    normal = [math.sin(angle), -math.cos(angle)]
    return [.55 * normal[0], .55 + .55 * normal[1]], normal


def cases():
    out = []

    def radial(name, station, z, materials, expected=None):
        center, normal = frame(station)
        start = [a + .40 * n for a, n in zip(center, normal)]
        out.append(dict(name=name, origin=[*start, z], direction=[-normal[0], -normal[1], 0],
                        length=.58, allowed=materials, range_m=expected))

    def vertical(name, station, offset, z, direction, material, limits, extent=.40):
        center, normal = frame(station)
        start = [a + offset * n for a, n in zip(center, normal)]
        out.append(dict(name=name, origin=[*start, z], direction=[0, 0, direction], length=extent,
                        allowed=[material] if material else None, range_m=limits))

    for station in [-1.13, -.77, -.37, -.11, .105, .263, .446, .631, .799, 1.04, 1.36]:
        key = f'{station:+.3f}'
        radial('Main rolled face '+key, station, 1.206, ['Upper rolled edge'], [.098, .108])
        radial('Upper recessed line '+key, station, 1.171, ['Dark drip groove'], [.105, .116])
        radial('Lower main fascia '+key, station, 1.132, ['Muted tan upper fascia'], [.100,.111])
        vertical('Main cap '+key, station, .21, 1.50, -1, 'Muted tan upper fascia', [.25,.255])
        vertical('Deep main soffit '+key, station, .16, .994, 1, 'Shadowed eave soffit', [.070,.085])
        radial('Sky above cap '+key, station, 1.26, None)
        if station > 0:
            radial('Exposed aggregate lip '+key, station, .815,
                   ['Washed stone on window hood'], [.243,.251])
            radial('Lip recessed underside '+key, station, .796,
                   ['Dark drip groove'], [.254,.266])
            vertical('Closed soffit above curved glass '+key, station,.001,.62,1,
                     'Shadowed eave soffit',[.042,.053])
            # Probe inside each course, away from the vertical grout lines.
            tile_station = -.045 + (math.floor((station + .045) / .083) + .5) * .083
            for z in [.705, .762]:
                radial('Two glazed apron courses '+key+' '+str(z), tile_station, z,
                       TILES, [.28,.287])
            vertical('Casing behind projecting lip '+key, station,.095,.85,-1,
                     'Washed stone on window hood',[.012,.018])
        else:
            radial('Straight lower window lintel '+key, station,.647,
                   ['Muted tan upper fascia'],[.366,.372])
            radial('Straight window underside bead '+key, station,.590,
                   ['Upper rolled edge'],[.355,.363])

    for i in [1, 6, 10, 16, 19, 23, 27, 31, 36]:
        center = -1.28 + (i + .5) * .072
        for row in [3, 4, 5, 6]:
            height = .693 + (.374 / 7) * (row + .5)
            radial(f'Field tile {i} course {row+1}',center,height,TILES,[.383,.39])
            radial(f'Recessed upright joint {i} course {row+1}',center-.036,height,
                   ['Weathered lime joint'],[.390,.4])
        radial(f'Recessed bed joint {i}',center,.693+.374*5/7,
               ['Weathered lime joint'],[.390,.4])
    for station in [-1.09,-.64,-.25,.23,.39,.58,1.03,1.22]:
        radial(f'Window pane {station}',station,.304,['Muted blue glass'],[.459,.465])
        z=.392 if station<0 else .445
        radial(f'Steel transom {station}',station,z,['Dark steel window casing'],[.435,.442])
    for station in [-.745,-.295,.135,TURN-.125]:
        radial(f'Vertical steel bar {station}',station,.18,['Dark steel window casing'],[.432,.439])
    radial('Pale outer corner upright',-.026,.61,['Light ceramic window trim'],[.279,.306])
    return out


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['raw', 'full', 'lod', 'output']:
        parser.add_argument(name,type=Path)
    opt = parser.parse_args()
    result = {role: inspect(getattr(opt,role),cases()) for role in ('raw','full','lod')}
    opt.output.write_text(json.dumps(result,ensure_ascii=False,indent=1)+'\n')
    for role, record in result.items():
        failed = [(v['name'],v['first_hit']) for v in record['cases'] if not v['passed']]
        print(role,len(record['cases']),len(failed),failed)
    raise SystemExit(int(not all(r['passed'] for r in result.values())))
