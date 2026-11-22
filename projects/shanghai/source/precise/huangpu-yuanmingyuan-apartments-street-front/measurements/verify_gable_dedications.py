"""Test photographed strokes, counters, tablet fields and both stone mouldings on an exported GLB."""
import argparse
import hashlib
import json
from pathlib import Path

from verify_wing_casements import decode, street_intersection
from gable_dedications import (COPING, FIELD, NORTH_SCRIPT, SHELL, SOUTH_SCRIPT, WORN_SCRIPT,
                              inscription_transform, point_on_stone)

# Independent interior points read on the enlarged registered frames, 405 x 246.
# The 0 is an open calligraphic form that joins the diagonal of the 4.
WITNESSES = {
    "south": [
        ("A south stroke", 44, 166, SOUTH_SCRIPT), ("A crossbar", 110, 138, SOUTH_SCRIPT),
        ("A north leg", 155, 164, SOUTH_SCRIPT), ("A counter", 120, 110, FIELD),
        ("dot between initials", 191, 199, SOUTH_SCRIPT),
        ("D stem", 235, 146, SOUTH_SCRIPT), ("D bowl", 318, 157, SOUTH_SCRIPT),
        ("D foot", 260, 198, SOUTH_SCRIPT), ("D counter", 279, 150, FIELD),
        ("space between D and bezel", 367, 143, FIELD),
    ],
    "north": [
        ("1 lower stroke", 36, 172, NORTH_SCRIPT), ("9 upper ring", 120, 77, NORTH_SCRIPT),
        ("9 counter", 125, 105, FIELD), ("9 descending tail", 139, 152, NORTH_SCRIPT),
        ("small upper nib", 210, 89, NORTH_SCRIPT), ("curled 0", 196, 166, NORTH_SCRIPT),
        ("0 interior", 222, 164, FIELD), ("worn right return of 0", 251, 164, WORN_SCRIPT), ("4 upright", 305, 153, NORTH_SCRIPT),
        ("4 crossbar", 332, 118, NORTH_SCRIPT), ("4 cut-out", 270, 104, FIELD),
        ("clear field above", 355, 47, FIELD),
    ],
}
ARCHITECTURAL = {
    "south": [(470, 280, COPING), (475, 306, SHELL), (423, 372, SHELL), (478, 409, COPING)],
    "north": [(457, 288, COPING), (467, 311, SHELL), (415, 381, SHELL), (475, 422, COPING)],
}


def verify(path):
    triangles, labels, gltf = decode(path)
    probes = []
    for wing in ('south', 'north'):
        signs = SOUTH_SCRIPT if wing == 'south' else NORTH_SCRIPT
        for name, x, v, mat in WITNESSES[wing]:
            uv = inscription_transform(wing) @ [x, v, 1.]
            u, v = uv[:2] / uv[2]
            xyz = point_on_stone(wing, u, v, -.089)
            hit = street_intersection(triangles, labels, gltf['materials'], xyz[0], xyz[2])
            expected_y = -.089 - (.012 if wing == 'south' else .010) if mat in (signs, WORN_SCRIPT) else -.089
            probes.append({"wing": wing, "feature": name, "xz_m": xyz[[0, 2]].tolist(),
                           "first": hit, "expected": mat,
                           "passed": bool(hit and hit['material'] == mat and abs(hit['y_m'] - expected_y) < .0035)})
        for u, v, mat in ARCHITECTURAL[wing]:
            xyz = point_on_stone(wing, u, v, -.13 if mat == COPING else -.085)
            hit = street_intersection(triangles, labels, gltf['materials'], xyz[0], xyz[2])
            probes.append({"wing": wing, "feature": "stone moulding" if mat == COPING else "surround",
                           "xz_m": xyz[[0, 2]].tolist(), "first": hit, "expected": mat,
                           "passed": bool(hit and hit['material'] == mat and hit['y_m'] < -.06)})
    return {"file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "triangles": len(triangles), "checks": probes, "passed": all(p['passed'] for p in probes)}


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('model', type=Path)
    cli.add_argument('record', type=Path)
    args = cli.parse_args()
    result = verify(args.model)
    args.record.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(result['file'], len(result['checks']), result['passed'],
          [(r['feature'], r['first']) for r in result['checks'] if not r['passed']])
    raise SystemExit(0 if result['passed'] else 1)
