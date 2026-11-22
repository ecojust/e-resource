"""Fit each southwest photograph to the surveyed south apertures and west parapet.

Run beside riverfront-layout.json and west-return-windows.json. The report
contains native pixel observations so the photographed corner fits can be
repeated without redistributing the photographs.
"""
import json
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

HERE = Path(__file__).resolve().parent


def register_camera(source, layout):
    openings = {row['key']: row for row in layout['openings']}
    bays = {row['bay']: row for row in layout['bays']}
    xyz, pixels = [], []
    for name, corners in source['south_aperture_pixels'].items():
        opening = openings[name]
        bay = bays[opening['bay']]
        for index, pixel in enumerate(corners):
            x = opening['x1' if index % 2 else 'x0']
            z = opening['z1' if index < 2 else 'z0']
            y = np.interp(x, [bay['x0'], bay['x1']], [bay['y0'], bay['y1']])
            xyz.append([x,y,z])
            pixels.append(pixel)
    street, cut = np.array(layout['west_return'])
    direction = (cut-street) / np.linalg.norm(cut-street)
    xyz.append([*street, layout['bay_wall_top']])
    pixels.append(source['street_corner'])
    has_back = source['back_corner'] is not None
    if has_back:
        xyz.append([*(street + source['back_corner_plan_d_m']*direction), layout['bay_wall_top']])
        pixels.append(source['back_corner'])
    xyz, pixels = np.array(xyz), np.array(pixels)
    width, height = source['image_size']
    focal = source['start_focal_px']
    principal = np.array([width/2, height/2])
    first_eye = np.array([-80.,-85.,34.] if has_back else [-100.,-75.,3.])
    facing = np.array([0.,0.,15.]) - first_eye
    facing /= np.linalg.norm(facing)
    right = np.cross(facing,[0,0,1])
    right /= np.linalg.norm(right)
    rot = np.array([right, np.cross(facing,right), facing])
    initial = np.r_[Rotation.from_matrix(rot).as_rotvec(), -rot@first_eye, np.log(focal)]
    vertical_edge = np.column_stack((np.tile(street,(3,1)),[8.,12.,15.]))

    def project(parameters, points):
        rotation = Rotation.from_rotvec(parameters[:3]).as_matrix()
        camera = points@rotation.T + parameters[3:6]
        return principal + np.exp(parameters[6])*camera[:,:2]/camera[:,2:]

    def residual(parameters):
        error = project(parameters,xyz)-pixels
        error[-(2 if has_back else 1):] *= 4
        c = project(parameters,vertical_edge)
        # The studio view has corrected verticals. On the bridge panorama the
        # same vertical edge slopes visibly and is measured at five ordinates.
        jamb = c[:,0]-316.7 if has_back else c[:,0]-np.interp(
            c[:,1], [339,383,402,450,474], [363.,368.5,369.5,374.,376.])
        focal_prior = (parameters[6]-np.log(focal))/(.9 if has_back else .001)
        return np.r_[error.ravel(), jamb*(3. if has_back else 1.5), focal_prior]

    result = least_squares(residual,initial,loss='soft_l1',f_scale=1,max_nfev=500).x
    rotation = Rotation.from_rotvec(result[:3]).as_matrix()
    lens = np.array([[np.exp(result[6]),0,width/2],[0,np.exp(result[6]),height/2],[0,0,1]])
    camera = lens @ np.column_stack((rotation,result[3:6]))
    plane = camera @ np.array([[direction[0],0,street[0]],[direction[1],0,street[1]],
                               [0,1,0],[0,0,1]])
    return plane, np.linalg.norm(project(result,xyz)-pixels,axis=1)


def main():
    layout = json.loads((HERE/'riverfront-layout.json').read_text())
    survey = json.loads((HERE/'west-return-windows.json').read_text())
    for source in survey['sources']:
        plane, errors = register_camera(source,layout)
        distances = []
        for key, corners in source['west_aperture_pixels'].items():
            pixels = np.column_stack((corners,np.ones(4)))
            world = np.linalg.solve(plane,pixels.T).T
            world = world[:,:2] / world[:,2:]
            original = source['inverse_measured_edges_d_z'][key]
            distances.append(float(np.abs(world-original).max()))
        # A new truncation point can slightly round the unit return vector.
        assert max(distances) < .015, (source['id'],distances)
        print(source['id'], 'median/p90 residual in pixels', np.percentile(errors,[50,90]).round(3),
              'maximum change on repeated edge solution in metres',round(max(distances),5))


if __name__ == '__main__':
    main()
