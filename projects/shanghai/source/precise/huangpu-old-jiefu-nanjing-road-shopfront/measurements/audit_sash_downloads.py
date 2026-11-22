"""Check the visible north sash in the decoded downloadable meshes."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from inspect_north_sash import checks
from render_northwest_comparison import read_glb


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    meshes, materials, _ = read_glb(args.model)
    triangles = []
    labels = []
    for position, normal, uv, indices, material, texture in meshes:
        faces = position[indices.reshape(-1, 3)]
        triangles.append(faces)
        labels.append(np.full(len(faces), material))
    faces = np.concatenate(triangles)
    results = checks(faces, np.concatenate(labels), {"materials": materials})
    record = {
        "file": args.model.name,
        "sha256": hashlib.sha256(args.model.read_bytes()).hexdigest(),
        "bytes": args.model.stat().st_size,
        "triangles": len(faces),
        "checks": results,
        "passed": all(r["passed"] for r in results),
    }
    args.output.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    print(args.model.name, len(faces), len(results), record["passed"])
    if not record["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
