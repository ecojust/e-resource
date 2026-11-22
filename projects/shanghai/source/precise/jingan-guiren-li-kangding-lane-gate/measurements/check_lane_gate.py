"""Check sight lines through the actual exported gate and onto its steel bars."""

import argparse
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent/'source'),
                str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact')]
from glb_triangles import SerialScene
from lane_iron_gate import FRAME, BARS


def check(mesh):
    drawing = json.loads((HERE/'lane-gate-2016.json').read_text())
    source = drawing['drawing']
    x0, y0, _, _ = source['crop_source_rect']
    sx, sy = source['drawing_to_source_scale']
    h = np.asarray(source['drawing_to_metric_xz'])
    scene = SerialScene(mesh)
    samples = []

    def shoot(label, xz, uv, want_iron):
        start = [float(xz[0]), -.60, float(xz[1])]
        hit = scene.ray(start, [0, 1, 0], 1.0)
        iron = bool(hit and hit['material'] in [FRAME, BARS])
        passed = iron if want_iron else hit is None
        samples.append(dict(feature=label, source_pixels=np.round(uv, 2).tolist(),
                            xz_m=np.round(xz, 5).tolist(), want_steel=want_iron,
                            first_material=hit and hit['material'],
                            first_surface_y_m=round(start[1]+hit['distance_m'],5) if hit else None,
                            passed=passed))

    for member in drawing['members']:
        ends = np.asarray(member['xz']).copy()
        # The low rails sit on the estimated ground datum of their own plane.
        ends[:,1] = np.maximum(ends[:,1], .045 if member['plane']=='small' else .025)
        shoot(member['member'], ends.mean(axis=0),
              np.mean(member['source_uv'],axis=0), True)

    gaps = {
        'transom, between consecutive uprights': [(u,79) for u in [53,90,123,159,194,230,266,300,335,370,405,443,477]],
        'above small door head': [(u,189) for u in [59,88,115,139,164,189,215,238,260]],
        'right leaf, open cells': [(u,v) for v in [195,292,382] for u in [305,328,352,376,400,424,452,474,499]],
        'small door, open cells': [(u,v) for v in [299,391,475,577] for u in [143,165,192,220,245,266]],
        'slender standing strip': [(u,v) for v in [299,410,481] for u in [63,88]],
    }
    for feature, points in gaps.items():
        for u,v in points:
            x,z,q=h@[u,v,1]
            shoot(feature, [x/q,z/q],[x0+u*sx,y0+v*sy],False)
    return dict(asset=scene.asset, count=len(samples), bar_centres=len(drawing['members']),
                independent_open_cells=sum(map(len,gaps.values())), forward_interval_y_m=[-.60,.40],
                all_first_intersections_unfiltered=True, passed=all(s['passed'] for s in samples),
                samples=samples)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('mesh',type=Path); p.add_argument('output',type=Path)
    a=p.parse_args(); data=check(a.mesh)
    a.output.write_text(json.dumps(data,ensure_ascii=False,indent=1)+'\n')
    print(data['count'],[(s['feature'],s['source_pixels'],s['first_material']) for s in data['samples'] if not s['passed']])
    raise SystemExit(int(not data['passed']))
