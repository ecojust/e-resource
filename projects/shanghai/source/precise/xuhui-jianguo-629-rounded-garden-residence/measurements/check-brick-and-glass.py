"""Check the actual cut surfaces against the measured decorative panel and glazing grid."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'source'))
sys.path.insert(0, str(ROOT.parent/'xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
from glb_triangles import SerialScene
from materials import BLOCK, BRICK, FRAME, GLASS, MID_GLASS, MORTAR, TRIM


def samples(layout, state):
    for row in layout['levels']:
        key = row['id']
        x0, x1, foot, shoulder, crown = row['pier']
        width = x1 - x0
        for name, x, z in [('centre', .50, .45), ('left brickwork', .08, .65),
                           ('right brickwork', .88, .83)]:
            yield f'{key} pier {name}', x0+x*width, foot+z*(shoulder-foot), [BRICK]
        if crown - shoulder > .005:
            yield f'{key} segmental head', (x0+x1)/2, (crown+shoulder)/2, [BRICK]
        x0, x1, z0, z1 = row['strip']
        red0, red1 = row['brick_bottom'], row['brick_top']
        yield f'{key} interposed brick', (x0+x1)/2, (red0+red1)/2, [BRICK]
        yield f'{key} left mineral edge', x0-.021, red0+.05, [TRIM]
        for light, bottom, top, count, panel in [('lower', z0, red0, row['courses'][1], MID_GLASS),
                                                  ('upper', red1, z1, row['courses'][0], GLASS)]:
            w = x1-x0
            if state == '2017':
                yield f'{key} {light} edge stile', x0+.014, (bottom+top)/2, [FRAME]
                yield f'{key} {light} first pane area', x0+w/3, (bottom+top)/2, [panel]
                yield f'{key} {light} second pane area', x0+w*2/3, (bottom+top)/2, [panel]
            else:
                for course in range(count):
                    z = bottom+(course+.5)*(top-bottom)/count
                    for col in range(3):
                        x = x0+(col+.5)*w/3
                        yield f'{key} {light} block {course+1}/{col+1}', x, z, [BLOCK]
                for col in (1, 2):
                    yield f'{key} {light} vertical joint {col}', x0+w*col/3, (bottom+top)/2, [MORTAR]
                yield f'{key} {light} first bed joint', x0+w/2, bottom+(top-bottom)/count, [MORTAR]


def verify(path, profiles, state):
    scene = SerialScene(path)
    probes = []
    for name, x, z, accepted in samples(profiles, state):
        hit = scene.ray((x, profiles['face_y']-.50, z), (0.,1.,0.), .85)
        probes.append({'detail': name, 'local_xz': [x,z], 'expected_materials': accepted,
                       'actual': hit, 'passed': bool(hit and hit['material'] in accepted)})
    return {'mesh': scene.asset, 'state': state, 'passed': sum(row['passed'] for row in probes),
            'total':len(probes), 'method':'Perpendicular half-metre cross sections of the six decorative shapes in model coordinates.',
            'probes': probes}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mesh', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--profiles', type=Path, default=ROOT/'measurements/brick-and-glass-profiles.json')
    parser.add_argument('--state', choices=['2019','2017'], default='2019')
    args = parser.parse_args()
    report = verify(args.mesh, json.loads(args.profiles.read_text()), args.state)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(f"{report['passed']}/{report['total']}", [q['detail'] for q in report['probes'] if not q['passed']])
