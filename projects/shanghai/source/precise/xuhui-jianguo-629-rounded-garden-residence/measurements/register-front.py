"""Recompute the exterior photo registration, right-hand return and conditional dimensions.

Run with Python, NumPy and SciPy. Optionally pass both original JPEG filenames with
--photos to check the two SHA-256 values. Image coordinates below use upright rasters.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

HERE = Path(__file__).resolve().parent
CONTROLS = HERE / "front-registration-controls.json"
DATA = json.loads(CONTROLS.read_text())
# World u,d,z; camera x-right, y-down, z-forward.
CANONICAL = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], float)


def intrinsic(focal, cx, cy):
    return np.array([[focal, 0, cx], [0, focal, cy], [0, 0, 1.0]])


def rotation(angles):
    return Rotation.from_rotvec(angles).as_matrix() @ CANONICAL


def rays(points, camera):
    points = np.atleast_2d(points)
    return np.column_stack([points, np.ones(len(points))]) @ np.linalg.inv(camera).T


def line_errors(matrix, camera, lines):
    """Signed normal misclosure of the measured horizontal/vertical segments in pixels."""
    errors = []
    for _, first, last, axis in lines:
        vanishing = camera @ matrix[:, 0 if axis == "u" else 2]
        direction = vanishing[:2] - 0.5 * (np.array(first) + last) * vanishing[2]
        direction /= np.linalg.norm(direction)
        segment = np.array(last) - first
        errors.append(segment[0] * direction[1] - segment[1] * direction[0])
    return np.array(errors)


def fit_arc(bands):
    """Fit one tangent circular arc to all visible horizontal courses in plan."""
    samples = np.vstack([band["plan"] for band in bands.values()])
    def errors(parameters):
        tangent, radius = parameters
        offset = samples[:, 0] - tangent
        return np.where(offset < 0, samples[:, 1],
                        np.hypot(offset, samples[:, 1] - radius) - radius)
    fit = least_squares(errors, [3, 1.35], bounds=([1, 0.6], [3.9, 8]),
                        loss="soft_l1", f_scale=0.05)
    return {"tangent_u": float(fit.x[0]), "radius": float(fit.x[1]),
            "plan_rms_m": float(np.sqrt(np.mean(errors(fit.x)**2)))}


def registration(course=0.063, focal17=3946.0, focal19_prior=570.0, omit=(), rng=None):
    matched = DATA["matched_points"]
    known = np.array([r["p2017"] for r in matched], float)
    observed = np.array([r["p2019"] for r in matched], float)
    training = np.array([i not in omit for i in range(len(matched))])
    lines17 = DATA["orthogonal_directions"]["image_2017"]
    lines19 = DATA["orthogonal_directions"]["image_2019"]
    traces = DATA["horizontal_course_samples_2019"]
    centre = np.array([319.5,239.5])
    if rng is not None:
        known += rng.normal(0, 2, known.shape)
        observed += rng.normal(0, 0.9, observed.shape)
        centre += rng.uniform(-12, 12, 2)
        def vary_lines(rows, sigma):
            return [(label, np.array(a) + rng.normal(0,sigma,2),
                     np.array(b) + rng.normal(0,sigma,2), axis) for label,a,b,axis in rows]
        lines17 = vary_lines(lines17,1.25)
        lines19 = vary_lines(lines19,0.7)

    cam17 = intrinsic(focal17, 1493.5, 2655.5)
    attitude17 = least_squares(lambda v: line_errors(rotation(v), cam17, lines17),
                               [0.10,-0.30,0.02], loss="soft_l1")
    rot17 = rotation(attitude17.x)
    anchor = rays([[486,3284]], cam17)[0]

    def rectify(points):
        direction = rays(points, cam17)
        depth = (anchor @ rot17[:,1]) / (direction @ rot17[:,1])
        return (direction * depth[:,None] - anchor) @ rot17

    ties = DATA["scale_ties_2017"]
    pixels = np.array(ties["pairs"]).reshape(-1,2)
    heights = abs(np.diff(rectify(pixels)[:,2].reshape(-1,2), axis=1))
    scale = ties["course_intervals"] * course / heights.mean()
    plane_points = rectify(known) * scale

    def intrinsic19(parameters):
        return intrinsic(np.exp(parameters[6]), *centre)

    def project(parameters):
        points = plane_points @ rotation(parameters[:3]).T + parameters[3:6]
        pixels = points @ intrinsic19(parameters).T
        return pixels[:,:2] / pixels[:,2,None]

    def residual(parameters):
        pixels = (project(parameters) - observed)[training].ravel()
        directions = line_errors(rotation(parameters[:3]), intrinsic19(parameters), lines19)
        # Original focal length unavailable for this reproduction; use a weak log prior.
        return np.r_[pixels, 0.8 * directions, 1.8 * (parameters[6] - np.log(focal19_prior))]

    fit = least_squares(residual, [.24,.01,0,.95,.5,16,np.log(focal19_prior)],
                        bounds=([-1,-1,-.3,-12,-8,4,np.log(320)],
                                [1,1,.3,12,8,40,np.log(1000)]),loss="soft_l1")
    rot19 = rotation(fit.x[:3])
    cam19 = intrinsic19(fit.x)
    centre19 = -rot19.T @ fit.x[3:6]

    def intersect(points, axis, value):
        direction = rays(points, cam19) @ rot19
        return centre19 + direction * ((value-centre19[axis]) / direction[:,axis])[:,None]

    floor_z = intersect([DATA["base_reference_2019"]], 1, 0)[0,2]
    middle_sill = DATA["facade_measurements_2019"]["central_brick_middle"][2:]
    mid_u = intersect(middle_sill, 1, 0)[:,0].mean()
    origin = np.array([mid_u,0,floor_z])
    bands = {}
    for name, trace in traces.items():
        plane_z = intersect([trace["straight"]], 1, 0)[0,2]
        pixels = np.array(trace["trace"])
        if rng is not None:
            pixels = pixels + rng.normal(0,0.65,pixels.shape)
        plan = (intersect(pixels, 2, plane_z) - origin)[:,:2]
        bands[name] = {"z": float(plane_z - floor_z), "plan": plan.tolist()}
    features = {key:(intersect(points,1,0) - origin).tolist()
                for key,points in DATA["facade_measurements_2019"].items()}
    errors = np.linalg.norm(project(fit.x) - observed,axis=1)
    camera17 = -anchor @ rot17 * scale - origin
    camera19 = centre19 - origin
    return {
        "course_m_assumed":course, "storey_m":bands["middle"]["z"]-bands["lower"]["z"],
        "rms_px_2019":float(np.sqrt(np.mean(errors**2))), "point_errors_px":errors.tolist(),
        "camera_2017":{"K":cam17.tolist(),"R_world_to_camera":rot17.tolist(),"eye":camera17.tolist()},
        "camera_2019_publication":{"K":cam19.tolist(),"R_world_to_camera":rot19.tolist(),"eye":camera19.tolist()},
        "matched_world_points":(plane_points-origin).tolist(),
        "feature_points_u_d_z":features,"cornices":bands,"arc":fit_arc(bands)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--photos",nargs=2,metavar=("PHOTO_2017","PHOTO_PUBLISHED_2019"))
    parser.add_argument("--output",type=Path,default=HERE/"front-registration.json")
    args=parser.parse_args()
    if args.photos:
        for filename,role in zip(args.photos,("2017","2019_publication"),strict=True):
            with open(filename,"rb") as stream:
                assert hashlib.file_digest(stream,"sha256").hexdigest()==DATA["images"][role]["sha256"]
    result=registration()
    assert result["rms_px_2019"]<2.0
    error=result["point_errors_px"]
    result["matched_observations"]=[{"id":p["id"],"error_px":e}
                                    for p,e in zip(DATA["matched_points"],error,strict=True)]
    result["holdout"]=[]
    for group in ["upper.red","middle.red","lower.red","left.label","strip"]:
        omitted=[i for i,row in enumerate(DATA["matched_points"]) if row["id"].startswith(group)]
        refit=registration(omit=omitted)
        errors=np.array(refit["point_errors_px"])[omitted]
        result["holdout"].append({"group":group,"count":len(omitted),"rms_px":float(np.sqrt(np.mean(errors**2))),"max_px":float(errors.max())})
    result["arc_fit_without_one_course"]={
        name:fit_arc({k:v for k,v in result["cornices"].items() if k!=name}) for name in result["cornices"]}
    rng=np.random.default_rng(760)
    draws=[]
    for _ in range(60):
        sample=registration(course=rng.uniform(.060,.066),focal17=rng.uniform(3770,4140),
                            focal19_prior=rng.uniform(390,750),rng=rng)
        draws.append([sample["storey_m"],sample["arc"]["tangent_u"],sample["arc"]["radius"],
                      sample["cornices"]["middle"]["plan"][-1][1],
                      sample["cornices"]["top"]["z"],sample["camera_2019_publication"]["K"][0][0]])
    result["sensitivity"]={"draws":60,"seed":760,"columns":["storey_m","tangent_u_m","radius_m","middle_visible_end_depth_m","top_course_z_m","focal19_px"],
                           "p05_p50_p95":np.percentile(draws,[5,50,95],axis=0).tolist(),
                           "interpretation":"Perturbation envelope of the specified camera, picks and brick course hypotheses. It does not bound unknown site dimensions."}
    H=result["storey_m"]
    result["normalized_by_middle_storey"]={
        "feature_points":{k:(np.asarray(v)/H).tolist() for k,v in result["feature_points_u_d_z"].items()},
        "tangent_u":result["arc"]["tangent_u"]/H,"radius":result["arc"]["radius"]/H,
        "cornice_z":{k:v["z"]/H for k,v in result["cornices"].items()}}
    result["coordinate_system"]="u is positive to image right on the central wall, d is inward perpendicular to that wall, z is up. d=0 is the front brick reference plane. u=0 is the midpoint of the second-storey brick panel sill. z=0 is the apparent plane through the visible lower plaster/plinth junction; no surveyed ground datum."
    result["project"]="column convention: xyz_cam = R_world_to_camera @ (xyz_local - eye); pixel_h=K @ xyz_cam; divide by pixel_h.z"
    result["source_controls_sha256"]=hashlib.sha256(CONTROLS.read_bytes()).hexdigest()
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print("registration RMS",result["rms_px_2019"],"samples",len(error),"story",H,"arc",result["arc"])


if __name__=="__main__":
    main()
