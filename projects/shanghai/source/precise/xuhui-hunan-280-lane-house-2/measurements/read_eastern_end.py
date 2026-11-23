"""Use two additional eastward road stations to bound the south elevation and its east return."""
import json
from pathlib import Path
from math import atan, cos, radians, sin, tan

import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

HERE = Path(__file__).resolve().parent


def front_corner(point, solved):
    if point in solved["points"]:
        return np.asarray(solved["points"][point])
    floor = int(point[1])
    upper = int(point[-2] == "T")
    right = int(point[-1] == "R")
    prm = solved["parameters"]
    return np.array([prm["span"][5+right], prm["depth"][3],
                     prm[f"z{floor}"][upper] + prm["ez"][2*(floor-1)+upper]])


def frame(angles):
    yaw, pitch, roll = np.radians(angles)
    front = np.array([sin(yaw)*cos(pitch), cos(yaw)*cos(pitch), sin(pitch)])
    right = np.array([cos(yaw), -sin(yaw), 0])
    down = np.cross(front, right)
    return np.array([right*cos(roll)+down*sin(roll), down*cos(roll)-right*sin(roll), front])


def compute(main, observations):
    azimuth = radians(90-main["x_azimuth_deg"])
    enu = Rotation.from_rotvec([0, 0, azimuth]).as_matrix()
    origin = main["origin_wgs"]
    metres = np.array([111320*cos(radians(origin[1])), 110860])
    results = {}
    for key, record in observations["stations"].items():
        station = record["station"]
        c0 = enu.T @ np.r_[(np.array(station["wgs"])-origin)*metres, station["z"]]
        pose0 = np.r_[c0, station["yaw"], station["pitch"], 0]
        w, h = record["size"]
        f = .5*w/tan(radians(station["hfov"]/2))
        K = np.array([[f,0,w/2],[0,f,h/2],[0,0,1]])
        xyz = np.array([front_corner(a, main) for a in record["window_points"]])
        obs = np.array(list(record["window_points"].values()))
        def errs(pose):
            R = frame(pose[3:]) @ enu
            projected = (xyz-pose[:3]) @ R.T @ K.T
            return projected[:,:2]/projected[:,2,None]-obs
        def loss(pose):
            return np.r_[(errs(pose)/3.4).ravel(), (pose-pose0)/[.45,.45,.23,4.,2.,1.]]
        model = least_squares(loss,pose0,loss="soft_l1",f_scale=1.3)
        pose = model.x
        R = frame(pose[3:]) @ enu
        def ray(pixel):
            d = R.T @ np.linalg.solve(K,[*pixel,1])
            return d/np.linalg.norm(d)
        def plane(pixel,y):
            d = ray(pixel)
            return pose[:3]+d*(y-pose[1])/d[1]
        points={}
        for name, uv in record["holdout"].items():
            points[name]={"pixel":uv,"ray":ray(uv).tolist(),"at_y_minus_0_33":plane(uv,-.33).tolist(),
                          "at_y_0":plane(uv,0).tolist()}
        results[key]={"camera":pose.tolist(),"R":R.tolist(),"K":K.tolist(),"points":points,
                      "window_residual_px":{k:v.tolist() for k,v in zip(record["window_points"],errs(pose))},
                      "window_median_px":float(np.median(np.linalg.norm(errs(pose),axis=1)))}
    for dest in ["roof_solid_corner","roof_rail_corner"]:
        rays=[(np.array(r["camera"][:3]),np.array(r["points"][dest]["ray"])) for r in (results[key] for key in observations["stations"])]
        (a,u),(b,v)=rays
        t = np.linalg.lstsq(np.column_stack((u,-v)), b-a,rcond=None)[0]
        p,q = a+t[0]*u,b+t[1]*v
        results.setdefault("two_station",{})[dest]={"xyz":((p+q)/2).tolist(),"line_separation_m":float(np.linalg.norm(p-q)),
                                                    "intersection_angle_degrees":float(np.degrees(np.arccos(np.clip(np.dot(u,v),-1,1))))}
    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output",type=Path)
    parser.add_argument("--survey",type=Path,default=HERE/"house-cameras.json")
    parser.add_argument("--readings",type=Path,default=HERE/"eastern-end-readings.json")
    args = parser.parse_args()
    result = compute(json.loads(args.survey.read_bytes()),json.loads(args.readings.read_bytes()))
    args.output.write_text(json.dumps(result,indent=2)+"\n")
