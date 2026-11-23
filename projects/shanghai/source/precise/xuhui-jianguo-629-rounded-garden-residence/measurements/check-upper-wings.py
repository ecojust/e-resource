"""Triangulate the visible upper exterior. Work from the upright image coordinates.

Requires Python 3, NumPy and SciPy. The four points in the right-hand extension
are observations from the published front view alone. Their reprojection is
included to show where the proposed other sightline meets foreground surfaces.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("front_registration", HERE / "register-front.py")
front = importlib.util.module_from_spec(spec)
spec.loader.exec_module(front)

# (feature, detail, pixel in 640 x 480 published image, pixel in upright 2017 image)
MATCHES = [
    ("high_eave", "left top fascia, below the rail", [264, 15.3], [95, 2093]),
    ("high_eave", "right top fascia, below the rail", [362.1, 19.7], [577, 2134]),
    ("high_eave", "left bottom corner of fascia", [264, 24.25], [94, 2138]),
    ("high_window", "left end of the visible horizontal head", [302.2, 35.7], [283, 2187]),
    ("high_window", "right end of the visible horizontal head", [325.3, 36.4], [400, 2198]),
    ("large_left_window", "bottom of right jamb", [271.7, 93.7], [119, 2441]),
    ("large_left_window", "top of right jamb", [271.6, 55.8], [128, 2246]),
]
# The published view is nearly frontal. These features are on a distinctly
# recessed face. No common right-extension fenestration is visible in the 2017 view.
RIGHT_EXTENSION = {
    "top floor sill, far end": [516, 178],
    "middle floor far border": [539, 292],
    "middle floor cornice, near end": [499, 298],
    "middle floor window, left top": [501, 224],
    "ground floor exterior arch, crown": [527, 323]
}


def ray(camera, pixel):
    return np.asarray(camera["R_world_to_camera"]).T @ np.linalg.solve(
        camera["K"], np.array([*pixel, 1.0]))


def at_depth(camera, pixel, depth):
    origin = np.asarray(camera["eye"])
    direction = ray(camera, pixel)
    return origin + direction * ((depth - origin[1]) / direction[1])


def pixel_of(camera, point):
    local = np.asarray(camera["R_world_to_camera"]) @ (point - camera["eye"])
    v = camera["K"] @ local
    return v[:2] / v[2]


def triangulate(scene, p19, p17):
    first, second = scene["camera_2019_publication"], scene["camera_2017"]
    def difference(depth):
        return pixel_of(second, at_depth(first, p19, depth[0])) - p17
    fit = least_squares(difference, [1.5])
    point = at_depth(first, p19, fit.x[0])
    return point, np.linalg.norm(fit.fun)


def artifact():
    scene = front.registration()
    observations = []
    for group, name, p19, p17 in MATCHES:
        xyz, error = triangulate(scene, p19, p17)
        observations.append({"feature":group, "name":name, "p2019":p19, "p2017":p17,
                             "u_d_z_conditional_m":xyz.tolist(), "miss_2017_original_px":float(error)})
    by_group = list(dict.fromkeys(p[0] for p in MATCHES))
    rng = np.random.default_rng(7602)
    trials = {g:[] for g in by_group}
    for _ in range(60):
        trial = front.registration(course=rng.uniform(.060, .066), focal17=rng.uniform(3770,4140),
                                    focal19_prior=rng.uniform(390,750), rng=rng)
        by_feature = {g:[] for g in by_group}
        for group, name, p19, p17 in MATCHES:
            xyz, _ = triangulate(trial, rng.normal(p19,1.3), rng.normal(p17,3))
            by_feature[group].append(xyz[1])
        for group, values in by_feature.items():
            trials[group].append(np.median(values))
    conditional = {}
    for feature, p19 in RIGHT_EXTENSION.items():
        projected = []
        for depth in [0,1,2,3,4,5]:
            xyz = at_depth(scene["camera_2019_publication"], p19, depth)
            projected.append({"assumed_d_m":depth, "u_d_z_m":xyz.tolist(),
                              "corresponding_2017_ray_pixel":pixel_of(scene["camera_2017"], xyz).tolist()})
        conditional[feature] = {"p2019":p19, "projective_family":projected}
    return {
        "coordinates": "World frame, cameras, image hashes and original-source attribution follow front-registration-controls.json and front-registration.json. Right is relative to the published garden elevation.",
        "front_controls_sha256":hashlib.sha256(front.CONTROLS.read_bytes()).hexdigest(),
        "front_script_sha256":hashlib.sha256((HERE/"register-front.py").read_bytes()).hexdigest(),
        "matched_upper_features":observations,
        "sensitivity": {
            "method":"60 deterministic independent camera recalibrations with perturbed brick-course scale, principal point, focal priors, reference controls and course traces as in front-registration.json. Upper picks are varied at 1.3px in 2019 and 3px in 2017 per coordinate. Percentiles describe those hypotheses, not a site-survey confidence interval.",
            "seed":7602, "stat":"median depth per feature, percentiles 5, 50, 95 in conditional metres",
            "depth":{g:np.percentile(v,[5,50,95]).tolist() for g,v in trials.items()}},
        "right_extension":conditional,
        "visibility":"The 2019 image shows two upper flat windows and the rounded ground-storey arcade opening behind the main body's rounded edge. In the 2017 source the corresponding projective loci of these features lie on, or behind, a nearer opaque ochre building and foreground ironwork. The left edge of the large upper flat window is outside the 2017 raster, but part of that window and its right jamb are visible. The upper white fascia and the centered small window can be recognized independently. Roof rail, tiles and foliage are excluded.",
        "scope":"Only exterior fragments selected from the two historical photographs. The right-hand d grid is a set of hypotheses for drawing the visible silhouette, with no measured right-extension depth."}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=HERE/"upper-wing-registration.json")
    args=parser.parse_args()
    data=artifact()
    args.output.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n")
    print(data["sensitivity"]["depth"])
