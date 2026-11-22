"""Repeat the two-photo triangulation at the open casements' visible lower ends."""
import argparse
import json
from pathlib import Path

import numpy as np


def compare(source):
    measurements=json.loads(source.read_bytes())
    cameras=[np.array(measurements[key]) for key in ('camera_P','camera_close_P')]
    groups={}
    for name, group in measurements['cross_read'].items():
        points=[]
        for pair in group['points']:
            uv=[np.asarray(pair[key]) for key in ('uv04','uv08')]
            equations=[]
            for p,s in zip(cameras,uv):
                equations.extend((s[0]*p[2]-p[0],s[1]*p[2]-p[1]))
            xyz=np.linalg.svd(equations)[2][-1]
            xyz/=xyz[-1]
            error=[]
            for camera, observed in zip(cameras,uv):
                projected=camera@xyz
                error.append(float(np.linalg.norm(projected[:2]/projected[2]-observed)))
            points.append(dict(xyz=xyz[:3].round(4).tolist(),residual_px=np.round(error,3).tolist()))
        depths=np.asarray([p['xyz'][1] for p in points])
        q20,q50,q80=np.quantile(depths,[.2,.5,.8])
        assert abs(q50-group['depth_median'])<.001
        groups[name]=dict(matches=len(points),depth_q20_q50_q80_m=np.round([q20,q50,q80],4).tolist(),
                          max_image_residual_px=max(max(p['residual_px'])for p in points),points=points)
    return dict(images=measurements['images'],units='m',world_y='positive into house; street wall reference 0',
                reconstruction='DLT with both full-resolution projection matrices and one record per unique image location.',
                groups=groups)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('output',type=Path)
    p.add_argument('--source',type=Path,default=Path(__file__).with_name('upper-window-observations.json'))
    args=p.parse_args()
    args.output.write_text(json.dumps(compare(args.source),ensure_ascii=False,indent=1)+'\n')
