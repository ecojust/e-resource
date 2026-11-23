"""Fit the corner entrance to eight independent jamb pixels in the two March 2016 photographs."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

HERE = Path(__file__).resolve().parent


def project(camera, points):
    frame = (np.asarray(points) - camera['centre']) @ np.asarray(camera['R']).T
    return camera['f_px'] * frame[:, :2] / frame[:, 2:] + [325., 433.]


def corners(parameters):
    x, y, angle, width, sill, height = parameters
    across = width * np.array([np.cos(angle), np.sin(angle), 0.])
    up = np.array([0., 0., height])
    base = np.array([x, y, sill])
    return np.array([base + up, base + across + up, base + across, base])


def main(out):
    obs_path = HERE / 'entrance-observations.json'
    camera_path = HERE / 'corner-two-view-bundle.json'
    observations = json.loads(obs_path.read_bytes())
    cameras = json.loads(camera_path.read_bytes())['cameras']
    pixels = np.array([observations['jamb_corners_px'][key] for key in ('84', '86')])

    def residual(parameters):
        return (np.array([project(cam, corners(parameters)) for cam in cameras]) - pixels).ravel()

    fit = least_squares(residual, [-.64, 1.16, .07, 1.47, -3.82, 2.33], loss='soft_l1', f_scale=2.)
    x, y, angle, width, sill, height = fit.x
    lamp = np.array(observations['measurements_84']['green_house_plaque_corners_px'])
    # Backproject the four board corners onto the same stucco plane as the jamb.
    ray = np.column_stack(((lamp - [325.,433.]) / cameras[0]['f_px'], np.ones(4))) @ np.array(cameras[0]['R'])
    eye = np.array(cameras[0]['centre'])
    tangent = np.array([np.cos(angle), np.sin(angle), 0.])
    normal = np.array([tangent[1], -tangent[0], 0.])
    origin = np.array([x,y,sill])
    xyz = eye + ray * (((origin-eye) @ normal) / (ray @ normal))[:,None]
    board = np.column_stack(((xyz-origin) @ tangent, xyz[:,2]-sill))
    # Independent physical aspect from the nearly face-on 83 close view.
    quad = np.array(observations['close_house_plaque_83']['outline_px'])
    aspect = (np.linalg.norm(quad[1]-quad[0])+np.linalg.norm(quad[2]-quad[3])) / (np.linalg.norm(quad[2]-quad[1])+np.linalg.norm(quad[3]-quad[0]))
    # Fix the aspect from 83; determine width, height and centre by reprojection into 84.
    def plate_shape(p):
        u,z,h=p
        normalized = np.array([[-.5,.5],[.5,.5],[.5,-.5],[-.5,-.5]])
        uv = normalized*[h*aspect,h]+[u,z]
        return origin + uv[:,0,None]*tangent + uv[:,1,None]*[0.,0.,1.]

    solution = least_squares(lambda p:(project(cameras[0],plate_shape(p))-lamp).ravel(),
                             [*board.mean(axis=0),np.ptp(board[:,1])], loss='soft_l1', f_scale=1.)
    pu,pz,ph = solution.x
    error = residual(fit.x).reshape(2,4,2); dist = np.linalg.norm(error,axis=2)
    assert fit.success and width>0 and height>width and abs(angle)<.3
    assert np.median(dist)<3 and dist.max()<12
    result = {
        'units':'Relative to the middle upper-window chord, length 1. The global building survey supplies the metric transform.',
        'model':'One vertical planar rectangle. Image rows run downward and both original frames are 650 × 866.',
        'source_sha256':{p.name:sha256(p.read_bytes()).hexdigest() for p in (obs_path,camera_path)},
        'left_sill_chord_xyz':origin.tolist(), 'across_unit_chord_xyz':tangent.tolist(),
        'opening_size_chords':[width,height], 'corners_chord_xyz':corners(fit.x).tolist(),
        'observed_and_reprojected':{k:{'observed_px':px.tolist(),'projected_px':(px+diff).tolist(),'radial_residual_px':ds.tolist()} for k,px,diff,ds in zip(('84','86'),pixels,error,dist)},
        'median_native_px':float(np.median(dist)), 'maximum_native_px':float(dist.max()),
        'plaque':{'centre_relative_to_left_sill_chords':[pu,pz],'size_chords':[ph*aspect,ph],
                  'angle_and_aspect_source':'Width/height ratio from 83, affixed to the visible plaster left of the jamb in 84.',
                  'ratio':aspect,'corners_84_projected':project(cameras[0],plate_shape(solution.x)).tolist(),
                  'residuals_native_84_px':np.linalg.norm(project(cameras[0],plate_shape(solution.x))-lamp,axis=1).tolist()}}
    out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__);cli.add_argument('output',type=Path)
    main(cli.parse_args().output)
