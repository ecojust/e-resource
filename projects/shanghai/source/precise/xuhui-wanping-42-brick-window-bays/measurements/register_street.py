"""Register Livelikerw's 2019 Wanping Road photograph to the front brick plane."""
from pathlib import Path
import argparse
import json
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

SIZE = (1050, 788)
# Each line stays on a single wall plane. Paired sides of projecting bays are omitted.
HORIZONTALS = [
    (291, 360, 421, 289), (493, 247, 765, 86),
    (297, 609, 406, 600), (534, 585, 807, 556),
    (297, 630, 402, 622), (548, 608, 804, 580),
    (337, 734, 404, 740), (531, 751, 585, 756), (640, 760, 701, 765),
    (574, 483, 624, 472), (750, 453, 793, 444),
    (578, 476, 622, 465), (754, 444, 789, 435),
]
VERTICALS = [
    (293, 363, 280, 727), (422, 290, 412, 599),
    (488, 265, 479, 557), (771, 92, 812, 550),
    (812, 550, 831, 767), (628, 185, 637, 391),
    (576, 493, 578, 574), (646, 477, 651, 565),
    (751, 460, 758, 553), (361, 546, 359, 603),
    (392, 535, 390, 593), (411, 529, 409, 596),
]
# Front corners at sidewalk level and central entrance, same physical brick plane.
CORNERS = [(278, 735), (833, 778)]
DOOR_BASE = (451, 747)


def fit():
    width, height = SIZE
    centre = (np.array(SIZE) - 1) / 2
    focal = 27 * np.hypot(width, height) / np.hypot(36, 24)
    align = Rotation.from_matrix(np.array([[.66, .75, 0], [.15, -.14, -.98], [-.73, .65, -.20]]))
    def matrices(v):
        f = np.exp(v[3])
        return np.array([[f, 0, centre[0]], [0, f, centre[1]], [0, 0, 1]]), Rotation.from_rotvec(v[:3]).as_matrix()
    def residual(v):
        k, r = matrices(v)
        vp = k @ r
        distances = []
        for axis, edges in ((0, HORIZONTALS), (2, VERTICALS)):
            for x, y, a, b in edges:
                ray = vp[:2, axis] - vp[2, axis] * np.array([(x+a)/2, (y+b)/2])
                ray /= np.linalg.norm(ray)
                distances.append((a-x)*ray[1] - (b-y)*ray[0])
        return np.r_[distances, (np.exp(v[3])-focal)/8]
    result = least_squares(residual, [*align.as_rotvec(), np.log(focal)], loss="soft_l1", f_scale=1.35)
    k, r = matrices(result.x)
    return k, r, residual(result.x)


class Camera:
    """X goes north towards the right-hand edge, +Y enters the house, Z is up."""
    def __init__(self, width):
        self.K, self.R, self.errors = fit()
        self.inv = self.R.T @ np.linalg.inv(self.K)
        self.C = np.array([0., -1., 0.])
        left, right = [self.wall(p)[0] for p in CORNERS]
        self.C[1] *= width / (right-left)
        doorway = self.wall(DOOR_BASE)
        self.C[[0, 2]] -= doorway[[0, 2]]
    def wall(self, pixel, depth=0):
        ray = self.inv @ [*pixel, 1.]
        return self.C + ray*(depth-self.C[1])/ray[1]
    def pixel(self, xyz):
        p = self.K @ self.R @ (np.array(xyz) - self.C)
        return p[:2]/p[2]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--front-width', type=float, required=True)
    args = parser.parse_args()
    c = Camera(args.front_width)
    info = dict(image='Livelikerw, 42 Wanping Road.jpg, 2019-02-23', working_size=SIZE,
                source='https://commons.wikimedia.org/wiki/File:42_Wanping_Road.jpg',
                equivalent_focal_mm=27, front_width_input=args.front_width,
                corner_marks=CORNERS, entrance_datum=DOOR_BASE, horizontal_edges=HORIZONTALS,
                vertical_edges=VERTICALS, intrinsic=c.K.tolist(), world_to_camera=c.R.tolist(),
                camera_centre=c.C.tolist(), direction_errors_px=c.errors[:-1].tolist())
    args.output.write_text(json.dumps(info, indent=2)+'\n')
    print(c.C, c.K[0,0], np.median(np.abs(c.errors[:-1])))
    for p in [*CORNERS,(292,356),(777,82),(492,249),(421,285),(492,209),(766,16),(798,438),(809,551),(823,608)]:
        print(p, c.wall(p).round(3))
