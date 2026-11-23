"""Rectify the two upper floors in the municipal tourism photograph, in its original 640 × 426 frame."""
import argparse
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).absolute().parent
# Endpoints of two parallel courses across the three-window short front. The
# shadow cast by the projecting street porch belongs to a different plane.
COURSES = [[351, 27], [552, 99], [568.18, 264.98], [362.42, 246.92]]
WIDTH = 11.40
UPPER, LOWER = 12.12, 4.31

def solve(source, target):
    matrix = []
    for (u, v), (x, z) in zip(source, target):
        matrix.extend([[u, v, 1, 0, 0, 0, -u*x, -v*x, -x],
                       [0, 0, 0, u, v, 1, -u*z, -v*z, -z]])
    *_, vectors = np.linalg.svd(matrix)
    h = vectors[-1].reshape(3, 3)
    return h / h[2, 2]

def transform(h, p):
    q = h @ np.r_[p, 1.]
    return (q[:2] / q[2]).tolist()

def read_front():
    targets = [[0, UPPER], [WIDTH, UPPER], [WIDTH, LOWER], [0, LOWER]]
    h = solve(COURSES, targets)
    return dict(frame=[640,426], frame_index=1, source_pixels=COURSES,
                control_xz_m=targets, image_to_front_xz=h.tolist(),
                basis="Two visible courses on the short street front. The width is bounded by two 2020 street rays giving an 11.74 m projecting cornice. The lower band is 4.31 m in the December 2015 station pair. The first control is below the cornice, whose top is independently about 12.8 m. Front is Y=0, interior Y>0.")
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.write_text(json.dumps(read_front(), ensure_ascii=False, indent=2)+'\n')
