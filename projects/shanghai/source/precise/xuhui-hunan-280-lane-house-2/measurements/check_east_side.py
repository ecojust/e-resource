"""Check independent wall, glazing and skyline pixels on the two east street photographs."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from check_east_station_views import HELPER
import runpy

HERE = Path(__file__).resolve().parent
# Native 800 x 600. Window picks fall inside the frames, away from the four fitted jambs.
POINTS = {
    '1512': {
        'opening': [(650,79), (655,86), (658,164), (668,172), (664,256), (673,263)],
        'wall': [(636,99), (675,118), (643,132), (674,209), (691,238), (698,302)],
        'sky': [(716,96), (726,143)],
    },
    '2002': {
        'opening': [(542,190), (552,194), (549,268), (547,337), (558,342)],
        'wall': [(500,174), (559,219), (518,227), (577,247), (572,304), (601,289)],
        'sky': [(464,80), (625,188)],
    },
}
EXPECTED = {
    'opening': ('reflection', 'joinery', 'replacement frame', 'grille'),
    'wall': ('roughcast','lower render'),
}

def inspect(asset):
    scene = runpy.run_path(str(HELPER))['SerialScene'](asset)
    cameras = json.loads((HERE/'eastern-window-planes.json').read_bytes())['eastern_roof_and_windows']['east_cameras']
    rows = []
    for key, groups in POINTS.items():
        camera = cameras[key]
        origin, rotation, intrinsics = (np.asarray(camera[k]) for k in ('C','R','K'))
        for surface, pixels in groups.items():
            for uv in pixels:
                direction = rotation.T @ np.linalg.solve(intrinsics, [*uv,1])
                hit = scene.ray(origin, direction / np.linalg.norm(direction), 100.)
                material = hit['material'] if hit else None
                match = hit is None if surface == 'sky' else bool(hit and any(s in material for s in EXPECTED[surface]))
                nearest = [0,0] if match else None
                if not match:
                    for radius in (1,2,3,4,5,6,8,10,12,16,20):
                        for dx,dy in ((radius,0),(-radius,0),(0,radius),(0,-radius),(radius,radius),(-radius,-radius)):
                            delta = rotation.T @ np.linalg.solve(intrinsics,[uv[0]+dx,uv[1]+dy,1])
                            probe = scene.ray(origin,delta/np.linalg.norm(delta),100.)
                            agrees = probe is None if surface=='sky' else bool(probe and any(s in probe['material'] for s in EXPECTED[surface]))
                            if agrees:
                                nearest = [dx,dy]
                                break
                        if nearest is not None:
                            break
                rows.append(dict(station=key, pixel=uv, observed=surface, hit_material=material, matched=match, sampled_offset_px=nearest))
    return {'mesh_sha256':hashlib.sha256(asset.read_bytes()).hexdigest(), 'total':len(rows),
            'exact':sum(r['matched'] for r in rows), 'rays':rows,
            'scope':'East return only. Branches, utility cables and the separate villa were omitted when selecting checks. The middle opening in 2020 is partially screened and only its position was read.'}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('asset', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.write_text(json.dumps(inspect(args.asset),indent=2)+'\n')
