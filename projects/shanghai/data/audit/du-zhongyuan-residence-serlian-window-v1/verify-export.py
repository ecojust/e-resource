"""Probe the Serlian window, separate glazed lights, colonnade and keystone at real model surfaces."""
from pathlib import Path
from math import cos, pi, sin
import argparse
import json
import runpy

HERE=Path(__file__).resolve().parent
trace=runpy.run_path(HERE.parent/'central-reserve-bank-changshu-front-v1/verify-export.py')['inspect']


def cases():
    tests=[]
    def ray(name, x, z, lo=None, hi=None, material=None):
        tests.append(dict(name=name,origin=[x,-2,z],direction=[0,1,0],length=3.5,
                          allowed=[material] if material else None,range_m=[lo,hi] if material else None))
    for x in (-2.75,2.75):
        for z in (.42,1.40,2.88,3.50):
            ray(f'roughcast jamb {x} {z}',x,z,1.99,2.01,'Painted garden wall plaster')
    for x in (-.54,-.24,.24,.54):
        ray(f'lower paired sash glazing {x}',x,.92,2.24,2.28,'Shaded garden glazing')
        ray(f'upper paired sash glazing {x}',x,1.55,2.24,2.28,'Pale reflected garden glazing')
        ray(f'cross rail of double sash {x}',x,1.25,2.15,2.18,'Red brown timber joinery')
    for x in (-1.97,1.97,-2.20,2.20):
        for z in (.78,1.52):
            ray(f'outer sidelight glass {x} {z}',x,z,2.24,2.28,'Pale reflected garden glazing')
    for x in (-1.235,1.235):
        for z in (.63,1.33,1.77,1.90):
            ray(f'round column face {x} {z}',x,z,1.78,1.85,'Pale dressed arch stone')
        ray(f'column plinth {x}',x,.318,1.74,1.79,'West window sill and plinth')
        ray(f'column cap {x}',x,2.022,1.74,1.80,'Pale dressed arch stone')
    for x in (-2.0,2.0):
        ray(f'straight side lintel {x}',x,2.128,1.80,1.85,'Pale dressed arch stone')
    for index in range(1,8):
        angle=pi*index/8
        ray(f'fanlight spoke {index}',.72*cos(angle),2.08+.72*sin(angle),2.18,2.22,'Bronze fanlight bars')
        if index!=4:
            for r,mat,lo,hi in [(1.141,'Pale dressed arch stone',1.93,1.96),(1.221,'Pale dressed arch stone',1.90,1.93)]:
                ray(f'arch moulding {index} {r}',r*cos(angle),2.08+r*sin(angle),lo,hi,mat)
    for index in range(8):
        a=(index+.5)*pi/8
        ray(f'curved garden fanlight pane {index}',.78*cos(a),2.08+.78*sin(a),2.24,2.28,'Shaded garden glazing')
    for x in (-.062,0,.062):
        ray(f'exposed keystone below scroll {x}',x,3.207,1.80,1.83,'Pale dressed arch stone')
        ray(f'projecting horizontal scroll face {x}',x,3.37,1.724,1.738,'Pale dressed arch stone')
        ray(f'keystone cap projecting {x}',x,3.49,1.74,1.78,'Pale dressed arch stone')
    for x in (-1.94,0,1.94):
        ray(f'continuous projecting sill {x}',x,.247,1.83,1.86,'Pale dressed arch stone')
    for x in (-3.05,3.05):
        ray(f'beyond local window segment {x}',x,2.6)
    return tests


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('raw','full','lod','output'):
        parser.add_argument(key,type=Path)
    args=parser.parse_args()
    result={role:trace(getattr(args,role),cases())for role in ('raw','full','lod')}
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=1)+'\n')
    for role,row in result.items():
        print(role,len(row['cases']),[(v['name'],v['first_hit']) for v in row['cases']if not v['passed']],flush=True)
    raise SystemExit(not all(row['passed']for row in result.values()))
