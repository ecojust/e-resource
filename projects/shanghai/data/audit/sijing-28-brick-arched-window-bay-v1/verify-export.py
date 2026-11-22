"""Intersect the actual exported triangles of the two arched windows and the end pilaster."""
import json
from pathlib import Path
import runpy
import sys

import numpy as np
from shapely.geometry import Polygon

HERE = Path(__file__).absolute().parent
PROJECT = next(p for p in HERE.parents if (p / 'tools/package_architectural_model.py').is_file())
SOURCE = PROJECT / 'source/precise/huangpu-sijing-28-brick-arched-window-bay'
sys.path.insert(0, str(SOURCE / 'source'))
sys.path.insert(0, str(PROJECT / 'source/precise/hongkou-general-post-office/source/common'))
from photo_plane import position, original
from measured_arches import BRICK, RIM, STONE, SPRING_BLOCKS
from casements import DATA
from east_wall import MORTAR, BLUE, DARK
from material_names import MATERIAL
inspect = runpy.run_path(str(PROJECT / 'data/audit/central-reserve-bank-changshu-front-v1/verify-export.py'))['inspect']


def cases():
    tests = []

    def ray(name, origin, direction, allowed, near, far):
        tests.append(dict(name=name, origin=np.asarray(origin).tolist(), direction=np.asarray(direction).tolist(),
                          length=far + .025, allowed=allowed, range_m=[near, far]))

    def frontal(name, u, v, depth, materials, tolerance=.007):
        x, _, z = position(u, v, depth)
        ray(name, [x, -1.4, z], [0, 1, 0], materials, 1.4+depth-tolerance, 1.4+depth+tolerance)

    def cell(name, polygon, depth, mat):
        pt = Polygon(polygon).representative_point()
        frontal(name, pt.x, pt.y, depth, [mat])

    arches = json.loads((SOURCE / 'measurements/arch-outlines.json').read_text())
    for tier, row in arches['tiers'].items():
        for part in row['face_cells'][2::3]:
            cell(part['id'], part['polygon'], -.022, BRICK[part['color']])
        for part in row['rim_bricks'][2::6]:
            cell(part['id'], part['polygon'], -.036, RIM)
        cell(tier + ' keystone', row['key'], -.060, STONE)
        for i, polygon in enumerate(SPRING_BLOCKS[tier]):
            cell(tier + ' springing block ' + str(i+1), polygon, -.024, STONE)

    for leaf in DATA['opening_estimates']:
        # The free edge, bar and glass are sampled normal to their own measured
        # plane. A frontal cast could hit another overlapping leaf.
        ht, ft, fb, hb = np.array(leaf['face_points'])
        normal = np.cross(ft-ht, hb-ht)
        normal /= np.linalg.norm(normal)
        if normal[1] > 0:
            normal *= -1
        for fraction in (.26, .76):
            edge = ft + fraction * (fb-ft)
            ray(leaf['name'] + ' free edge ' + str(fraction), edge+.10*normal, -normal, [leaf['material']], .065, .09)
        pane = .38*(ht+.16*(hb-ht)) + .62*(ft+.16*(fb-ft))
        ray(leaf['name']+' glazing', pane+.10*normal, -normal, ['open sash glazing'], .099, .119)
        for fraction in leaf['horizontal_bars_fraction_down']:
            bar = .5*(ht+ft) + .5*fraction*((hb-ht)+(fb-ft))
            ray(leaf['name']+' rail '+str(fraction), bar+.10*normal, -normal, [leaf['material']], .075, .095)

    for i, uv in enumerate([(634,428),(645,471),(672,559),(694,653),(706,722),
                            (554,40),(566,80),(580,140),(590,184)]):
        frontal('blue brick in recessed field ' + str(i+1), *original(*uv), .016, [MATERIAL, BLUE, MORTAR], .013)
    uv = original(637,436)
    x, _, z = position(*uv,.014)
    ray('inside small vent along normal', [x,-1.4,z],[0,1,0],[DARK],1.50,1.51)
    origin = position(*uv,-1.4)
    direction = position(*uv,.014) - origin
    direction /= np.linalg.norm(direction)
    ray('small vent from the photograph', origin, direction, [DARK], 1.40, 2.5)
    views = {v['name']:v for v in json.loads((SOURCE/'source/cameras.json').read_text())}
    witness = json.loads((SOURCE/'measurements/view-window-rebates.json').read_text())
    for role, points in witness.items():
        v = views[role]
        eye = np.array(v['eye'])
        sight = np.array(v['target']) - eye
        focal = v['width'] * np.linalg.norm(sight) / v['width_m']
        forward = sight/np.linalg.norm(sight)
        right = np.cross(forward,[0.,0.,1.])
        right /= np.linalg.norm(right)
        up = np.cross(right,forward)
        for u,vv in points:
            direction = forward + right*((u+.5-v['width']/2)/focal) + up*((v['height']/2-vv-.5)/focal)
            name = f'{role} frame backing at {u},{vv}'
            ray(name, eye, direction / np.linalg.norm(direction), [
                'Dark recess behind upper casements','Recessed timber jamb lining','Painted opening sill',
                'Linen visible behind lower sashes','Muted curtain weave','dark wood rebate'
            ],3.0,9.0)
    for u,vv in [(150,100),(200,85),(240,77),(260,74),(355,67),(415,72),(480,83)]:
        v = views['upper']
        eye = np.array(v['eye'])
        forward = np.array(v['target']) - eye
        focal = v['width'] * np.linalg.norm(forward) / v['width_m']
        forward /= np.linalg.norm(forward)
        right = np.cross(forward,[0.,0.,1.])
        right /= np.linalg.norm(right)
        up = np.cross(right,forward)
        direction = forward + right*((u+.5-v['width']/2)/focal) + up*((v['height']/2-vv-.5)/focal)
        ray(f'outer arch bed at {u},{vv}',eye,direction/np.linalg.norm(direction),[MORTAR],3.0,9.0)
    return tests


if __name__ == '__main__':
    files = list(map(Path, sys.argv[1:]))
    roles = ['raw','full','lod'] if len(files)==4 else ['model']
    probes = cases()
    reports = {role:inspect(f, probes) for role,f in zip(roles,files[:-1])}
    files[-1].write_text(json.dumps(reports,ensure_ascii=False,indent=1)+'\n')
    failures = {k:[(v['name'],v['first_hit'] and (v['first_hit']['material'],v['first_hit']['distance_m'])) for v in r['cases'] if not v['passed']] for k,r in reports.items()}
    print(len(probes), failures)
    sys.exit(int(any(failures.values())))
