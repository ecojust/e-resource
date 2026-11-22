"""Triangulate the photographed roof features from the two street frames in the building-local frame."""
import argparse
import json
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
def triangulate(views,observed):
    constraints=[]
    for p,(u,v) in zip(views,observed):
        constraints.extend([u*p[2]-p[0],v*p[2]-p[1]])
    _,_,vh=np.linalg.svd(constraints)
    return vh[-1,:3]/vh[-1,3]
def measure():
    camera=json.loads((HERE/'xiangshan-exterior-cameras.json').read_text())
    obs=json.loads((HERE/'xiangshan-visible-landmarks.json').read_text())
    views=[np.asarray(camera['camera_matrices'][key]) for key in ('roof-15-west','alignment-roof-0')]
    results=[]
    for row in obs['street_dormer_triangulation']:
        measured=np.array([row['street_west'],row['street_east']])
        xyz=triangulate(views,measured)
        predictions=np.array([p@np.r_[xyz,1.]for p in views]);predictions=predictions[:,:2]/predictions[:,2,None]
        disparities=np.linalg.norm(predictions-measured,axis=1)
        results.append(dict(feature=row['feature'],observed_separate_frames_px=measured.tolist(),estimated_local_xyz_m=xyz.tolist(),reprojection_error_px=disparities.tolist(),metre_difference_from_original_triangulation=float(np.linalg.norm(xyz-row['xyz']))))
    return dict(frame='Building-local coordinates. The western and eastern street views date to December 2015.',units='metres and native image pixels',results=results,verified=all(r['metre_difference_from_original_triangulation']<.001 for r in results),max_two_view_reprojection_error_px=max(max(v['reprojection_error_px'])for v in results))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);args=p.parse_args();report=measure()
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    if not report['verified']:raise SystemExit(1)
