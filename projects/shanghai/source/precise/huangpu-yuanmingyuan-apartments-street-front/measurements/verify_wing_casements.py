"""Decode GLB triangles and check street-facing intersections at windows and sills."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "source"))
from wing_casements import BEAD, GLASS, PAINT, STONE, TRANSOM, openings, sash_face_depths


def decode(path):
    data = path.read_bytes()
    magic, version, size, length, kind = struct.unpack_from("<4sIIII", data)
    if (magic, version, size, kind) != (b"glTF", 2, len(data), 0x4E4F534A):
        raise ValueError("Invalid GLB container")
    doc = json.loads(data[20:20 + length])
    binary_start = 28 + length

    def acc(index):
        a = doc["accessors"][index]
        v = doc["bufferViews"][a["bufferView"]]
        dtype = np.dtype({5121: "u1", 5123: "<u2", 5125: "<u4", 5126: "<f4"}[a["componentType"]])
        columns = {"SCALAR": 1, "VEC3": 3}[a["type"]]
        return np.ndarray((a["count"], columns), dtype=dtype, buffer=data,
                          offset=binary_start + v.get("byteOffset", 0) + a.get("byteOffset", 0),
                          strides=(v.get("byteStride", columns * dtype.itemsize), dtype.itemsize))

    triangles, labels = [], []
    for node_id in doc["scenes"][doc.get("scene", 0)]["nodes"]:
        node = doc["nodes"][node_id]
        if any(k in node for k in ("children", "matrix", "rotation", "translation", "scale")):
            raise ValueError("Expected directly exported world coordinates")
        for q in doc["meshes"][node["mesh"]]["primitives"]:
            xyz = acc(q["attributes"]["POSITION"])
            points = xyz[acc(q["indices"]).reshape(-1, 3)].astype(float)
            points = points[:, :, [0, 2, 1]]
            points[:, :, 1] *= -1
            triangles.append(points)
            labels.append(np.full(len(points), q["material"]))
    return np.concatenate(triangles), np.concatenate(labels), doc


def street_intersection(triangles, labels, materials, x, z):
    # Barycentric interpolation on the XZ projection. The observer is at negative Y.
    a = triangles[:, 0, :]
    u = triangles[:, 1, :] - a
    v = triangles[:, 2, :] - a
    det = u[:, 0] * v[:, 2] - u[:, 2] * v[:, 0]
    candidate = np.abs(det) > 1.e-13
    det = np.where(candidate, det, 1.)
    dx, dz = x - a[:, 0], z - a[:, 2]
    s = (dx * v[:, 2] - dz * v[:, 0]) / det
    t = (u[:, 0] * dz - u[:, 2] * dx) / det
    candidate &= (s >= 0) & (t >= 0) & (s + t <= 1)
    if not candidate.any():
        return None
    y = np.where(candidate, a[:, 1] + s * u[:, 1] + t * v[:, 1], np.inf)
    first = int(np.argmin(y))
    return {"material": materials[int(labels[first])]["name"], "y_m": round(float(y[first]), 5)}


def samples(r):
    width = r["right"] - r["left"]
    height = r["top"] - r["bottom"]
    border = min(0.081, 0.048 * width, 0.085 * height)
    left, right = r["left"] + border, r["right"] - border
    bottom, top = r["bottom"] + border, r["top"] - border
    level = r["level"]
    yield "north jamb", r["right"] - border / 2, r["bottom"] + .45 * height, [PAINT]
    yield "meeting stile", (left + right) / 2, bottom + .45 * (top - bottom), [PAINT, BEAD]
    if level == "attic":
        yield "attic glass", left + .14 * (right - left), bottom + .45 * (top - bottom), [GLASS]
        yield "attic glazing bar", left + .14 * (right - left), bottom + .62 * (top - bottom), [PAINT]
    else:
        for label, xx, zz, mat in [
            ("lower glazing", .20, .45, GLASS), ("fine horizontal bar", .2, .675 * .48, PAINT),
            ("top-light pane", .15, .78, TRANSOM), ("top-light vertical", .25, .78, PAINT),
            ("top-light horizontal", .16, .675 + .325 * .51, PAINT),
            ("solid transom", .2, .675, PAINT),
        ]:
            yield label, left + xx * (right - left), bottom + zz * (top - bottom), [mat]
    # Corresponding sills touch the underside of both main windows. The attic
    # pair shares one level instead of two independent sills.
    if level != "attic":
        yield "stone sill", (left + right) / 2, r["bottom"] - .055, [STONE]


def check_model(path):
    triangles, labels, doc = decode(path)
    materials = doc["materials"]
    records = []
    rows = openings()
    for row in rows:
        face = sash_face_depths()[row["wing"], row["level"]]
        for name, x, z, expected in samples(row):
            hit = street_intersection(triangles, labels, materials, x, z)
            depth_ok = bool(hit and (-.36 < hit["y_m"] < -.07 if STONE in expected
                                       else face - .003 <= hit["y_m"] <= face + .105))
            records.append({"window": row["label"], "feature": name, "xz_m": [x, z],
                            "expected": expected, "first": hit,
                            "passed": bool(hit and hit["material"] in expected and depth_ok)})
    for wing in ("near", "far"):
        pair = sorted((r for r in rows if r["wing"] == wing and r["level"] == "attic"),
                      key=lambda r: r["left"])
        x = (pair[0]["right"] + pair[1]["left"]) / 2
        z = (pair[0]["bottom"] + pair[1]["bottom"]) / 2 - .055
        hit = street_intersection(triangles, labels, materials, x, z)
        records.append({"window": wing, "feature": "attic sill across central pier",
                        "xz_m": [x, z], "first": hit, "expected": [STONE],
                        "passed": bool(hit and hit["material"] == STONE and hit["y_m"] < 0)})
    return {"model": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "triangles": len(triangles), "samples": records, "passed": all(p["passed"] for p in records)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    result = check_model(args.model)
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(result['model'], result['triangles'], len(result['samples']), result['passed'])
    raise SystemExit(0 if result["passed"] else 1)
