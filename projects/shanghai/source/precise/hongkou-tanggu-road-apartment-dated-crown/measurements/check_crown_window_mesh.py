"""Check the constructed crown display, in the local units of its layout."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'xuhui-pathe-records-office/measurements/city-contact'))
from glb_triangles import SerialScene

FRAME = 'Tanggu windows | weathered frame'
BAR = 'Tanggu windows | painted glazing bars'
CLEAR = 'Tanggu windows | pale glass'
SHADED = 'Tanggu windows | shaded glass'
CANVAS = 'Tanggu shades | faded canvas'
HEM = 'Tanggu shades | pale stitched hem'
LIP = 'Tanggu panels | warm brick return'
FACE = 'Tanggu panels | inset brickwork'


def probes(layout):
    for index, row in enumerate(layout['openings'], 1):
        x0, x1, z0, z1 = (row[k] for k in ('x0', 'x1', 'z0', 'z1'))
        w, h = x1-x0, z1-z0
        frame = min(w*.038, h*.024)
        u, v = x0+frame, z0+frame
        clear_w, clear_h = w-2*frame, h-2*frame
        y = row['face_y']
        lower_start = y-.7*w
        # Start at the face beneath the two fabric hoods to inspect covered glazing.
        start = lower_start if index > 2 else y+.003*w
        def probe(name, x, z, target, origin_y=start, expected_y=None):
            return dict(group=f'window {index}', feature=name, x=x, z=z, y=origin_y,
                        material=target, expected_y=expected_y, width=w)

        yield probe('left jamb', x0+frame*.45, z0+.37*h, FRAME, lower_start)
        yield probe('right jamb', x1-frame*.45, z0+.37*h, FRAME, lower_start)
        if index > 2:
            rows = [0, .15, .31, .475, .645, .825, 1]
            columns = [[0, .25, .535, .745, 1]]*6
        else:
            rows = [0, .24, .54, 1]
            columns = [[0, .5, 1], [0, .5, 1], [0, 1]]
        for z in rows[1:-1]:
            yield probe('cross rail', u+.39*clear_w, v+z*clear_h, BAR)
        for low, high, division in zip(rows, rows[1:], columns):
            z = v+clear_h*(low+high)/2
            for x in division[1:-1]:
                yield probe('glazing bar', u+x*clear_w, z, BAR)
            for left, right in zip(division, division[1:]):
                yield probe('pane', u+(left+right)*clear_w/2, z, CLEAR if index>2 else SHADED)
        if index<=2:
            high = z1+.045*h
            drop = (.267 if index==1 else .284)*h
            forward_y = y-.028*w-row.get('shade_projection', .52*w)
            yield probe('curved canvas', x0+.44*w, high-.5*drop, CANVAS, lower_start)
            yield probe('pale scalloped edge', x0+.44*w, high-drop-.014*w-.019*h,
                        HEM, lower_start, forward_y)

    for index, row in enumerate(layout['panels'], 1):
        l, r, b, t = (row[k] for k in ('x0','x1','z0','z1'))
        w, h, y, d = r-l, t-b, row['face_y'], row['depth']
        edge = min(w*.030, h*.037)
        locs = [('left edge', l+edge*.50, b+.42*h, LIP, .02*d),
                ('right edge', r-edge*.50, b+.42*h, LIP, .02*d),
                ('top edge', l+.41*w, t-edge*.50, LIP, .02*d),
                ('bottom edge', l+.41*w, b+edge*.50, LIP, .02*d),
                ('stepped return', l+edge*1.20, b+.54*h, LIP, .24*d)]
        for fx, fz in [(.25,.25),(.5,.5),(.75,.75),(.25,.75),(.75,.25)]:
            locs.append(('recessed brick face', l+w*fx, b+h*fz, FACE, d))
        for name, x, z, mat, distance in locs:
            yield dict(group=f'brick panel {index}',feature=name,x=x,z=z,y=y-w*.40,
                       material=mat,expected_y=y+distance,width=w)


def test(model, layout):
    scene = SerialScene(model)
    records = []
    for p in probes(layout):
        hit = scene.ray([p['x'],p['y'],p['z']], [0,1,0], p['width']*1.75)
        actual = hit['material'] if hit else None
        depth = hit['point_enu_m'][1] if hit else None
        expected = p['expected_y']
        passed = actual==p['material'] and (expected is None or abs(depth-expected)<p['width']*.001)
        records.append(dict(group=p['group'],feature=p['feature'],expected=p['material'],
                            actual=actual,display_y=round(depth,6) if depth is not None else None,
                            passed=bool(passed)))
    return dict(model_sha256=scene.asset['sha256'],model_bytes=scene.asset['bytes'],
                tested=len(records),matched=sum(a['passed'] for a in records),
                count_by_feature=dict(Counter(a['feature'] for a in records)),probes=records)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('layout', type=Path)
    parser.add_argument('report', type=Path)
    parser.add_argument('models', nargs='+', type=Path)
    args=parser.parse_args()
    layout=json.loads(args.layout.read_bytes())
    rows=[test(path,layout) for path in args.models]
    args.report.write_text(json.dumps(dict(units='Decoration display scale',layout_sha256=hashlib.sha256(args.layout.read_bytes()).hexdigest(),assets=rows),ensure_ascii=False,indent=1)+'\n')
    for row in rows:
        print(row['matched'],row['tested'],[p for p in row['probes'] if not p['passed']][:3])
    raise SystemExit(any(row['matched']!=row['tested'] for row in rows))
