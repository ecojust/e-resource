"""Rectify the published entrance image in the frontage plane, leaving absolute dimensions open."""

from pathlib import Path
import numpy as np, json, hashlib
from scipy.optimize import least_squares
from PIL import Image
import argparse

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("published_image", type=Path)
parser.add_argument("output", type=Path)
args = parser.parse_args()
photo = args.published_image
assert (
    hashlib.sha256(photo.read_bytes()).hexdigest()
    == "4a74113e48ad683f4ea154707a6b2283ee2087b08d95e862119b83e87fc49991"
)
im = Image.open(photo).convert("RGB")
# Upper/lower corners of the outer stone sign frame, inset sign, and two second-floor windows.
# These are independent hand-read screen pixels in the actual 465 by 314 news photograph.
sets = {
    "portal_top": [(122, 74), (347, 74)],
    "portal_bottom": [(111, 143), (360, 145)],
    "inset_top": [(143, 84), (331, 84)],
    "inset_bottom": [(132, 133), (342, 133)],
    "upper_left": [(186, 23), (224, 23), (221, 71), (181, 71)],
    "upper_right": [(255, 23), (291, 23), (295, 71), (254, 71)],
    "entry_head": [(153, 145), (333, 145)],
    "letter_band": [(184, 99), (301, 117)],
}
# Two vertical sides of the sign surround and the upper windows supply vanishing directions.
# Lines on slight bevels are deliberately independent of the main front-plane controls.
rays = [
    [(122, 74), (111, 143)],
    [(347, 74), (360, 145)],
    [(186, 23), (181, 71)],
    [(224, 23), (221, 71)],
    [(255, 23), (254, 71)],
    [(291, 23), (295, 71)],
    [(143, 84), (132, 133)],
    [(331, 84), (342, 133)],
]
lines = []
for a, b in rays:
    a = np.r_[a, 1.0]
    b = np.r_[b, 1.0]
    l = np.cross(a, b)
    l /= np.linalg.norm(l[:2])
    lines.append(l)
lines = np.array(lines)
fit = least_squares(lambda u: lines @ np.r_[u, 1.0], [240.0, -550.0], loss="soft_l1", f_scale=5.0)
vp = fit.x


# Horizontal courses in this near-frontal image are almost parallel to scanlines.
# A homography sending their direction and vertical VP to infinity gives affine ratios
# within each axis. The two axis scales stay independent pending the second street station.
def rectify(u, v):
    h = (v - vp[1]) / (143.0 - vp[1])
    return [(u - vp[0]) / h, (v - 143.0) / h]


flat = {name: [rectify(*p) for p in points] for name, points in sets.items()}
span = flat["portal_top"][1][0] - flat["portal_top"][0][0]
origin = (flat["portal_top"][0][0] + flat["portal_top"][1][0]) * 0.5
norm = {name: [[(x - origin) / span, z / span] for x, z in values] for name, values in flat.items()}
out = dict(
    source_url="https://sh.people.com.cn/NMediaFile/2022/0129/LOCAL202201291119000348441479699.jpg",
    source_file_sha256=hashlib.sha256(photo.read_bytes()).hexdigest(),
    image_size=list(im.size),
    pixel_features=sets,
    vertical_controls=rays,
    vertical_vanishing_px=vp.tolist(),
    vertical_line_residuals_px=(lines @ np.r_[vp, 1.0]).round(2).tolist(),
    affine_ratios=norm,
    method="Near-frontal street photo. The horizontal direction is approximated by parallel scanlines. Robust common vertical vanishing point from two window frames and the portal edges. Horizontal and vertical scales have not been assumed equal; normalized values are within-axis controls until a second view fixes the metric ratio.",
)
args.output.write_text(json.dumps(out, indent=2) + "\n")
print(
    "VP",
    vp,
    "outer width",
    (flat["portal_top"][1][0] - flat["portal_top"][0][0]),
    "clear/outer",
    round((flat["entry_head"][1][0] - flat["entry_head"][0][0]) / span, 3),
    "inset/outer",
    round((flat["inset_top"][1][0] - flat["inset_top"][0][0]) / span, 3),
)
