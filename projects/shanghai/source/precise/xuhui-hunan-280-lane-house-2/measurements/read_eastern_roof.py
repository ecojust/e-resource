"""Triangulate the solid south-east roof turn in four same-site winter surveys."""
import argparse
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
# The cropped close-station images were reopened using the original orientation, focal
# length and width and 1450 rows instead of 750. Native row = tall row - 350.
OBSERVATIONS = {
    '6-1512': {'uv':[768.,-49.], 'sigma':5., 'note':'Solid edge, approximate tangent junction behind fine lines and wire, hedge/tree to right.'},
    '6-2002': {'uv':[796.,-216.5], 'sigma':6., 'note':'Rounded dark cap. Projected tangent join and visible outer edge bound the read.'},
    'east-1512': {'uv':[532.,-62.], 'sigma':3., 'note':'Exterior solid corner in 800×1000: subtract 200 from native tall row.'},
    'east-2002': {'uv':[434.,87.], 'sigma':2.5, 'note':'Solid corner below the separate upright of the handrail.'}
}

def calculate(core, east):
    cameras = dict(core['cameras'])
    archive = east['eastern_roof_and_windows']['east_cameras']
    cameras.update({'east-'+k:v for k,v in archive.items()})
    def solve(keys):
        from scipy.optimize import least_squares
        def err(x):
            points=[]
            for key in keys:
                v=cameras[key]
                c,R,K=np.asarray(v['C']),np.asarray(v['R']),np.asarray(v['K'])
                q=K@R@(x-c)
                points.append(q[:2]/q[2]-OBSERVATIONS[key]['uv'])
            return np.asarray(points)
        result=least_squares(lambda q:(err(q)/np.array([OBSERVATIONS[k]['sigma']for k in keys])[:,None]).ravel(),[13.7,1,17.7],loss='soft_l1')
        return {'xyz':result.x.tolist(),'residual_pixels':dict(zip(keys,err(result.x).tolist()))}
    keys=list(OBSERVATIONS)
    return {'original_pixels':OBSERVATIONS,'all':solve(keys),'close_front_only':solve(['6-1512','6-2002']),'east_pair_only':solve(['east-1512','east-2002']),'leave_one_out':{k:solve([v for v in keys if v!=k])for k in keys},
            'scope':'The close stations see a radius of curvature, not a sharp arris; far positions discern its two tangents. The railing is hidden in the near-vertical front views and is read from the east stations.'}

if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('output',type=Path);args=cli.parse_args()
    args.output.write_text(json.dumps(calculate(json.loads((HERE/'house-cameras.json').read_bytes()),json.loads((HERE/'eastern-window-planes.json').read_bytes())),indent=2)+'\n')
