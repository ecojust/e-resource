"""Fit the photographed pole silhouette and retain the conflict in field depth estimates."""
import json
import math
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from register_court import Camera

HERE = Path(__file__).resolve().parent

def fit():
    read = json.loads((HERE / 'courtyard-pole-observations.json').read_text())
    inner = Camera()
    court = read['fayhoo']
    line = np.array(court['shaft_axis'])
    slope, intercept = np.polyfit(line[:, 1], line[:, 0], 1)
    road = {key: Camera(key) for key in read['street']}

    def axis(depth, height):
        # Intersect the measured image line with a constant-depth vertical plane.
        p, q = (inner.wall((slope*v+intercept, v), depth) for v in [150,1092])
        return p + (q-p)*(height-p[2])/(q[2]-p[2])

    def at_row(station, depth, v):
        camera = road[station]
        a, b = [camera.P @ [*axis(depth,z),1] for z in [0,1]]
        d = b-a
        z = (v*a[2]-a[1])/(d[1]-v*d[2])
        return float(z), camera.pixel(axis(depth,z))

    def road_errors(params):
        depth = params[0]
        return [at_row(key,depth,v)[1][0]-u for key, data in read['street'].items()
                for u,v in data['line']]

    free_depth = float(least_squares(road_errors,[-.2],loss='soft_l1',f_scale=3).x[0])
    def radius(pairs, depth):
        widths=[]
        for left,right,v in pairs:
            centre=inner.wall(((left+right)/2,v),depth)
            r0,r1=[inner.ray((u,v)) for u in (left,right)]
            widths.append(np.linalg.norm(centre-inner.c)*math.sin(math.acos(np.clip(r0@r1,-1,1))/2))
        return float(np.median(widths))
    shaft_r=radius(court['shaft_edges'],-read['parapet_projection_m'])
    depth=min(free_depth,-read['parapet_projection_m']-shaft_r-.005)
    shaft_r=radius(court['shaft_edges'],depth)
    stone_r=radius(court['plinth_edges'],depth)
    front=axis(depth,0)[:2]
    to_eye=inner.c[:2]-front
    to_eye/=np.linalg.norm(to_eye)
    def front_z(pixel,rad):
        return float(inner.wall(pixel,depth+to_eye[1]*rad)[2])
    base=front_z(court['foot_front'],stone_r)
    shoulder=front_z(court['shoulder_seat'],shaft_r)
    chamfer=front_z(court['shoulder_break'],stone_r)
    tie=front_z((1297,1033),shaft_r)
    road_fit={}
    tops=[]
    for key, data in read['street'].items():
        residuals = [float(at_row(key, depth, v)[1][0]-u) for u,v in data['line']]
        road_fit[key] = {'signed_axis_residuals_px':residuals}
        if data['top'] is not None:
            top_z,uv = at_row(key, depth, data['top'][1])
            road_fit[key].update(upper_end_estimate_m=top_z, projected_tip_at_observed_row=uv.tolist())
            tops.append(top_z)
    tip=float(np.median(tops))
    return {'free_depth_m':free_depth,'selected_depth_m':depth,'shaft_radius_m':shaft_r,
            'faceted_base_radius_m':stone_r,'base_z_m':base,'shoulder_z_m':shoulder,
            'chamfer_z_m':chamfer,'binding_z_m':tie,'top_z_m':tip,
            'shaft_base':axis(depth,base).tolist(),'shaft_tip':axis(depth,tip).tolist(),
            'street_positions':road_fit}

if __name__=='__main__':
    print(json.dumps(fit(),indent=2))
