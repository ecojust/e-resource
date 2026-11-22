"""The black open-work gate recorded on the public street face in July 2016."""

import json
from pathlib import Path

import numpy as np

SURVEY = Path(__file__).resolve().parents[1] / 'measurements' / 'lane-gate-2016.json'
FRAME = 'Gate | dark charcoal painted frame'
BARS = 'Gate | charcoal painted slender bars'


def finish(rgb, roughness):
    srgb = np.asarray(rgb, dtype=float) / 255
    linear = np.where(srgb <= .04045, srgb / 12.92, ((srgb + .055) / 1.055) ** 2.4)
    return dict(color=linear.tolist(), roughness=roughness, metallic=.23)


PALETTE = {FRAME: finish([47, 48, 44], .67), BARS: finish([54, 54, 50], .62)}


def add_lane_gate(b, lod=False):
    """Add the two shut leaves, the visible nested door and their fixed transom."""
    survey = json.loads(SURVEY.read_text())
    simple = lod is True or lod == 'lod'
    for row in survey['members']:
        points = np.asarray(row['xz'], dtype=float)
        width = row['width_m']
        # The nested door's low rail projects below the fixed threshold in the
        # photograph. Its own plane and ground clearance are approximate.
        min_height = .045 if row['plane'] == 'small' else .025
        points[:, 1] = np.maximum(points[:, 1], min_height)
        delta = points[1] - points[0]
        span = float(np.linalg.norm(delta))
        along = np.array([delta[0], 0., delta[1]]) / span
        inward = np.array([0., 1., 0.])
        cross = np.cross(along, inward)
        mid = points.mean(axis=0)
        face = survey['depth'][f"{row['plane']}_center_m"]
        material = FRAME if row['finish'] == 'frame' else BARS
        depth = row['section_depth_m']
        # Thin highlights on the broad head are two independent raised strips.
        # Both tiers preserve the same grille openings and all visible bars.
        if not simple and row['member'] == 'Small door opening | head face':
            for side in [-1, 1]:
                ridge = np.array([mid[0], face-depth/2, mid[1]]) + cross * (side * width * .36)
                b.box(ridge, [span, .008, .010], BARS, [along, inward, cross],
                      f'Small door head | edge moulding {side:+d}')
        b.box([mid[0], face, mid[1]], [span, depth, width], material,
              [along, inward, cross], row['member'])
