"""Refit four moving leaves and their transoms to points on the registered garden photograph."""
from pathlib import Path
import argparse
import json
import numpy as np
from scipy.optimize import least_squares,minimize_scalar


def fit(control):
    projection=np.asarray(control['projection_xyz_to_pixels']);report={}
    def pixels(points):
        p=np.c_[points,np.ones(len(points))]@projection.T
        return p[:,:2]/p[:,2:]
    for name,leaf in control['leaves'].items():
        pts=np.asarray(leaf['pixel_hinge_top_bottom_free_bottom_top']);u=leaf['working_hinge_u']
        def corners(v):
            axis,low,top,normal,along=v
            return np.array([[.01,axis,top],[.01,axis,low],[.01+normal,axis+along,low],[.01+normal,axis+along,top]])
        result=least_squares(lambda v:(pixels(corners(v))-pts).ravel(),[u,leaf['sill'],leaf['head'],.2,.05])
        axis,low,top,normal,along=result.x;a,b,c,d=corners(result.x);rows=[]
        for observation in leaf['visible_transoms']:
            sample=np.asarray(observation['sample_pixels'])
            def residual(q):
                line=np.cross(projection@[*((1-q)*b+q*a),1.],projection@[*((1-q)*c+q*d),1.]);return np.c_[sample,np.ones(len(sample))]@line/np.linalg.norm(line[:2])
            fraction=minimize_scalar(lambda q:(residual(q)**2).sum(),bounds=(.15,.9),method='bounded').x
            rows.append({'fraction_above_sill':round(fraction,5),'observation_normal_error_px':residual(fraction).round(4).tolist()})
        report[name]={'hinge_station_m':axis,'bottom_m':low,'head_m':top,'projection_m':normal,
                      'width_m':np.hypot(normal,along),'swing_degrees':np.rad2deg(np.arctan2(normal,along)),
                      'corner_error_px':np.linalg.norm(pixels(corners(result.x))-pts,axis=1).round(4).tolist(),
                      'transoms':rows}
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('output',type=Path)
    parser.add_argument('--control',type=Path,default=Path(__file__).with_name('return-casement-photo-control.json'))
    args=parser.parse_args();args.output.write_text(json.dumps(fit(json.loads(args.control.read_text())),indent=2)+'\n')
