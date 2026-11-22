"""Probe the window leaves and projecting sill in three dimensions and check the brick bond."""
import argparse
import json
import math
from pathlib import Path
import runpy
import numpy as np

HERE = Path(__file__).absolute().parent
SOURCE = HERE.parents[2] / 'source/precise/changning-zhongyi-village-blue-steel-casements'
D = json.loads((SOURCE / 'source/dimensions.json').read_bytes())
BRICKS = json.loads((SOURCE / 'measurements/brick-course-measurement.json').read_bytes())
LINTELS = json.loads((SOURCE / 'measurements/soldier-joints.json').read_bytes())
INSPECT = runpy.run_path(HERE.parent / 'central-reserve-bank-changshu-front-v1/verify-export.py')['inspect']


def cases():
    probes = []
    def ray(name, origin, direction, length, materials, span):
        probes.append(dict(name=name, origin=list(map(float, origin)), direction=list(map(float, direction)),
                           length=length, allowed=materials, range_m=span))
    def front(name, x, z, materials, span):
        ray(name, [x, -.15, z], [0, 1, 0], .65, materials, span)
    brick = ['Zhongyi rose facing brick', 'Muted plum facing brick', 'Sunlit rose facing brick']
    mortar = ['Light grey bedding mortar']
    steel = ['Weathered green steel']
    blue = ['Blue inside glazing', 'Denim blue glazing', 'Shaded blue glazing']
    gx, gy = D['hinge_origin_x'], D['hinge_y_m']
    width = D['swinging_leaf_width']
    for i, (bounds, head) in enumerate(zip([D['open_bay'], D['closed']], LINTELS['bays'])):
        left, bottom, right, top = bounds
        joints = head['x_joints_m']
        for j, (a, b) in enumerate(zip(joints, joints[1:])):
            front(f'lintel {i+1} soldier {j+1}', (a+b)/2, top+.117, brick, [.141,.147])
        for j, x in enumerate(joints[1:-1]):
            front(f'lintel {i+1} pointed joint {j+1}', x, top+.117, mortar, [.165,.171])
        for j, fraction in enumerate([.14,.34,.61,.84]):
            x = left + (right-left)*fraction
            for k,y in enumerate([-.123,-.047]):
                height = bottom-.021+.026*(y+.16)/.29
                ray(f'sill {i+1} slope {j+1}/{k+1}', [x,y,bottom+.012], [0,0,-1], .10,
                    ['Grey projecting sill'], [bottom+.009-height,bottom+.015-height])
        middle = gx+width+.026 if i==0 else (left+right)/2
        closed_spans = [(middle+.012,right-.035)] if i==0 else [(left+.035,middle-.008),(middle+.008,right-.035)]
        low, high = bottom+.035, top-.034
        for j,(a,b) in enumerate(closed_spans):
            for k in range(4):
                for t in [.30,.65]:
                    front(f'closed light {i+1}/{j+1} pane {k+1} at {t}',a+(b-a)*t,low+(high-low)*(k+.5)/4,blue,[.291,.297])
            for k in range(1,4):
                front(f'closed light {i+1}/{j+1} transom {k}',a+(b-a)*.37,low+(high-low)*k/4,steel,[.242,.248])
    pitch = BRICKS['course_height_m']
    phase = BRICKS['resolved_mortar_beds_m'][0]
    short, long = BRICKS['header_module_m'], BRICKS['stretcher_module_m']
    for row in range(13):
        start = -1.76356 if row%2 == 0 else -1.51467
        z = phase + (row+.5)*pitch
        for name,x in [('header',start+short/2),('stretcher',start+short+long/2)]:
            front(f'pier course {row+1} {name}',x,z,brick,[.145,.152])
        for name,x in [('begin',start),('end',start+short)]:
            front(f'pier course {row+1} vertical joint {name}',x,z,mortar,[.165,.171])
        front(f'pier course {row+1} bedding',start+short/2,phase+row*pitch,mortar,[.165,.171])
    radians = math.radians(D['open_angle_degrees'])
    along = np.array([math.cos(radians), -math.sin(radians)])
    normal = np.array([along[1],-along[0]])
    low,high = D['swing_bottom_m'],D['swing_top_m']
    def door(name, fraction,z, materials,span):
        xy = np.array([gx,gy])+fraction*width*along+.15*normal
        ray(name, [*xy,z], [*-normal,0], .42, materials,span)
    for k in range(4):
        z = low+(k+.5)*(high-low)/4
        for t in [.3,.68]:
            door(f'open leaf reflecting pane {k+1}/{t}',t,z,['Street reflection','Grey green reflection'],[.167,.173])
        door(f'open leaf free stile {k+1}',.985,z,steel,[.122,.128])
    for k in range(1,4):
        door(f'open leaf transom {k}',.4,low+k*(high-low)/4,steel,[.122,.128])
    for j,t in enumerate([.17,.82]):
        door(f'external hinge pin {j+1}',.009/width,low+t*(high-low),['Oiled latch metal'],[.090,.101])
    for i,t in enumerate([.18,.38,.59,.84]):
        front(f'recess behind swinging leaf {i+1}',gx+width-.035,low+t*(high-low),['Shaded blue glazing'],[.437,.443])
    return probes


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ['raw','full','lod','output']:
        parser.add_argument(key, type=Path)
    args = parser.parse_args()
    result = {k: INSPECT(getattr(args,k), cases()) for k in ['raw','full','lod']}
    args.output.write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n')
    assert all(r['passed'] for r in result.values()), {k:[c['name'] for c in r['cases'] if not c['passed']] for k,r in result.items()}
    print(len(cases()),'probes per serialized file')
