#!/usr/bin/env python3
"""Actual finite-area curtain pane seats, excluding vertical side slivers.

Revision2: strictly positive support/pane extension and exact request SHA.
Independent supplemental method; the six shared frozen checker files are not
modified. All four bounding facets and actual single-solid ray intervals must
agree. This establishes finite local seating only, not full-edge bearing.
"""
import argparse
from collections import OrderedDict
from itertools import product
import json
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon

from finite_checks import Facets, plane_clip, polygons, ray_intervals
from modern_mesh import filemeta, load_raw, oriented_position_hash, require

HERE = Path(__file__).resolve().parent
WORLD = {"origin_enu_m": [0., 0., 0.], "axes_enu": [[1., 0., 0.], [0., 1., 0.], [0., 0., 1.]]}
MINIMUM_CELL_AREA_M2 = 1e-5
MINIMUM_EMBED_M = 1e-6
MINIMUM_END_EXTENSION_M = 1e-6
MINIMUM_FACING_VERTICAL_COSINE = .5
MAXIMUM_OPPOSITE_PLANE_SEPARATION_M = 1e-9
MAXIMUM_ENDPOINT_ARITHMETIC_ERROR_M = 1e-7
MAXIMUM_CELLS_PER_PAIR = 20000
EXPECTED_REQUEST_SHA256 = '610a076ddd48afb77be52cdbeb0bb2074fcb74864718d4bedf5374ba95553803'


class SmallFacetCache:
    def __init__(self, limit=48):
        self.limit = limit
        self.rows = OrderedDict()

    def get(self, part):
        if part.key not in self.rows:
            self.rows[part.key] = Facets(part, WORLD)
        self.rows.move_to_end(part.key)
        while len(self.rows) > self.limit:
            self.rows.popitem(last=False)
        return self.rows[part.key]


def facing_cosine(plane):
    return float(1. / np.sqrt(1. + plane[0] ** 2 + plane[1] ** 2))


def pair_seat(pane, frame, boundary, cache=None):
    require(boundary in ["bottom", "top"], "Unknown pane boundary")
    cache = cache or SmallFacetCache()
    a, b = cache.get(pane), cache.get(frame)
    result = {"pane_key": pane.key, "support_key": frame.key,
        "boundary": boundary, "passed": False, "state": "NO_QUALIFYING_AREA_WITNESS"}
    overlap = np.minimum(a.bbox[1], b.bbox[1]) - np.maximum(a.bbox[0], b.bbox[0])
    if np.any(overlap[:2] <= 0) or overlap[2] < 0:
        return {**result, "state": "DISJOINT_OR_XY_TANGENT_AABB"}
    cells = rejected = tiny = facing_rejected = 0
    for ap, az in a.sides["up"]:
        for bi in b.trees["up"].query(ap):
            bp, bz = b.sides["up"][int(bi)]
            if boundary == "top" and facing_cosine(az) < MINIMUM_FACING_VERTICAL_COSINE:
                facing_rejected += 1
                continue
            if boundary == "bottom" and facing_cosine(bz) < MINIMUM_FACING_VERTICAL_COSINE:
                facing_rejected += 1
                continue
            common = ap.intersection(bp)
            if common.area < MINIMUM_CELL_AREA_M2:
                tiny += 1
                continue
            for ai in a.trees["down"].query(common):
                adp, adz = a.sides["down"][int(ai)]
                if boundary == "bottom" and facing_cosine(adz) < MINIMUM_FACING_VERTICAL_COSINE:
                    facing_rejected += 1
                    continue
                common2 = common.intersection(adp)
                if common2.area < MINIMUM_CELL_AREA_M2:
                    tiny += 1
                    continue
                for bj in b.trees["down"].query(common2):
                    bdp, bdz = b.sides["down"][int(bj)]
                    if boundary == "top" and facing_cosine(bdz) < MINIMUM_FACING_VERTICAL_COSINE:
                        facing_rejected += 1
                        continue
                    for poly in polygons(common2.intersection(bdp)):
                        cells += 1
                        if cells > MAXIMUM_CELLS_PER_PAIR:
                            return {**result, "state": "INDETERMINATE_CELL_BUDGET", "cells_examined": cells}
                        require(not poly.interiors, "Unexpected holes in convex actual facet cell")
                        original = [list(v) for v in poly.exterior.coords[:-1]]
                        order = [adz - bdz, az - bz] if boundary == "bottom" else [bdz - adz, bz - az]
                        candidates = []
                        vertices = original
                        # True four-facet interval overlap, not only a surface projection.
                        for plane in [az - bdz, bz - adz, az - adz, bz - bdz]:
                            constraint = plane.copy()
                            constraint[2] -= MINIMUM_EMBED_M
                            vertices = plane_clip(vertices, constraint)
                        for plane in order:
                            constraint = plane.copy()
                            constraint[2] -= MINIMUM_END_EXTENSION_M
                            vertices = plane_clip(vertices, constraint)
                        if len(vertices) >= 3 and Polygon(vertices).area >= MINIMUM_CELL_AREA_M2:
                            candidates.append(("positive_volume", Polygon(vertices), None))
                        separation = bz - adz if boundary == "bottom" else az - bdz
                        vv = np.column_stack([np.asarray(original), np.ones(len(original))])
                        separations = vv @ separation
                        if max(abs(separations)) <= MAXIMUM_OPPOSITE_PLANE_SEPARATION_M:
                            vertices = original
                            for plane in [az - adz, bz - bdz]:
                                constraint = plane.copy()
                                constraint[2] -= MINIMUM_EMBED_M
                                vertices = plane_clip(vertices, constraint)
                            for plane in order:
                                constraint = plane.copy()
                                constraint[2] -= MINIMUM_END_EXTENSION_M
                                vertices = plane_clip(vertices, constraint)
                            if len(vertices) >= 3 and Polygon(vertices).area >= MINIMUM_CELL_AREA_M2:
                                candidates.append(("opposite_facet_area", Polygon(vertices), separations.tolist()))
                        for mode, joint, facet_separations in candidates:
                            point = joint.representative_point()
                            uv = [point.x, point.y]
                            ga, fb = ray_intervals(a.t, uv), ray_intervals(b.t, uv)
                            if ga["state"] != "valid" or fb["state"] != "valid":
                                rejected += 1
                                continue
                            xyz = np.array([*uv, 1.])
                            expected = [float(x @ xyz) for x in [adz, az, bdz, bz]]
                            intervals = []
                            for g, f in product(ga["intervals_m"], fb["intervals_m"]):
                                if max(abs(np.asarray([*g, *f]) - expected)) > MAXIMUM_ENDPOINT_ARITHMETIC_ERROR_M:
                                    continue
                                embed = min(g[1], f[1]) - max(g[0], f[0])
                                actual_separation = g[0] - f[1] if boundary == "bottom" else f[0] - g[1]
                                extensions = [g[0] - f[0], g[1] - f[1]] if boundary == "bottom" else [f[0] - g[0], f[1] - g[1]]
                                if min(extensions) < MINIMUM_END_EXTENSION_M:
                                    continue
                                if mode == "positive_volume" and embed < MINIMUM_EMBED_M - 1e-8:
                                    continue
                                if mode == "opposite_facet_area" and abs(actual_separation) > MAXIMUM_OPPOSITE_PLANE_SEPARATION_M:
                                    continue
                                intervals.append((g, f, embed, actual_separation, extensions))
                            if not intervals:
                                rejected += 1
                                continue
                            g, f, embed, actual_separation, extensions = intervals[0]
                            return {**result, "passed": True, "state": "ACTUAL_FINITE_AREA_SEAT",
                                "contact_mode": mode, "actual_joint_cell_xy_area_m2": float(joint.area),
                                "actual_joint_cell_xy_vertices_m": [list(p) for p in joint.exterior.coords[:-1]],
                                "witness_xy_m": uv, "pane_actual_interval_m": g, "support_actual_interval_m": f,
                                "actual_interval_overlap_m": embed, "actual_facing_endpoint_separation_m": actual_separation,
                                "actual_ordered_end_extensions_m": extensions,
                                "pane_facing_vertical_cosine": facing_cosine(adz if boundary == "bottom" else az),
                                "support_facing_vertical_cosine": facing_cosine(bz if boundary == "bottom" else bdz),
                                "actual_four_facet_planes": {"pane_down": adz.tolist(), "pane_up": az.tolist(),
                                    "support_down": bdz.tolist(), "support_up": bz.tolist()},
                                "opposite_facet_cell_vertex_separations_m": facet_separations,
                                "cells_examined": cells, "rejected_actual_interval_witnesses": rejected,
                                "rejected_small_xy_cells": tiny, "rejected_steep_facing_facets": facing_rejected}
    return {**result, "cells_examined": cells, "rejected_actual_interval_witnesses": rejected,
        "rejected_small_xy_cells": tiny, "rejected_steep_facing_facets": facing_rejected}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--structure", type=Path, required=True)
    parser.add_argument("--requests", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    require(output.is_relative_to(HERE) and not output.exists(), "Expected a new local immutable report")
    require(filemeta(args.requests)["sha256"] == EXPECTED_REQUEST_SHA256, "Original frozen5114-question content changed")
    requests = json.loads(args.requests.read_bytes())
    require(requests["schema"] == "modern-finite-requests-v1" and requests["state"] == "READY_FOR_ACTUAL_AUDIT", "Unbound requests")
    proof = json.loads(args.structure.read_bytes())
    binding = requests["source_binding"]
    require(filemeta(args.structure)["sha256"] == binding["structure_report_sha256"], "Structure report changed")
    require(proof["schema"] == "modern-actual-raw-structure-v1" and proof["structure_passed"] is True, "Closed actual structure required")
    require(proof["model_id"] == requests["model_id"] == "jiading-shanghai-auto-museum", "Wrong model")
    require(proof["asset_identity"]["raw"]["sha256"] == binding["raw_sha256"], "Raw binding changed")
    require(proof["source_geometry_sha256"] == binding["geometry_input_sha256"], "Geometry binding changed")
    require(proof["calibration_sha256"] == binding["calibration_sha256"], "Calibration binding changed")
    require(proof["frozen_source_manifest"]["sha256"] == binding["source_freeze_sha256"], "Frozen source binding changed")
    asset = load_raw(args.raw)
    require(asset.identity["raw"]["sha256"] == binding["raw_sha256"], "Current actual raw changed")
    require(asset.identity["raw"]["bytes"] < 100_000_000, "Raw must be below100MB")
    baseline = {r["key"]: r for r in proof["part_results"]}
    bykey = {p.key: p for p in asset.parts}
    require(len(bykey) == len(asset.parts) == len(baseline) == len(proof["part_results"]), "Part omission or duplicate")
    for part in asset.parts:
        old = baseline[part.key]
        require(old["label"] == part.label and old["material"] == part.material and old["triangles"] == len(part.triangles_enu), "Part identity changed")
        require(old["oriented_position_triangles_sha256"] == oriented_position_hash(part.triangles_enu), "Actual part geometry changed")
    rows = []
    cache = SmallFacetCache()
    require(len(requests["checks"]) == 5114 and len({r["id"] for r in requests["checks"]}) == 5114, "Full unchanged5114-question pane suite required")
    for question in requests["checks"]:
        require(question["kind"] == "support_each" and len(question["left_selectors"]) == 1, "One actual pane per question required")
        if question["id"].endswith("/bottom-frame-or-floor-local-joint"):
            boundary = "bottom"
        elif question["id"].endswith("/top-transom-local-joint"):
            boundary = "top"
        else:
            raise ValueError("Unexpected pane question: " + question["id"])
        left = question["left_selectors"][0]
        require(set(left) == {"key", "expected_count"} and left["expected_count"] == 1, "Exact single-part selector required")
        pane = bykey[left["key"]]
        candidates = []
        for selector in question["right_selectors"]:
            require(set(selector) == {"key", "expected_count"} and selector["expected_count"] == 1, "Exact support selector required")
            frame = bykey[selector["key"]]
            require(pane.key != frame.key, "Self seating forbidden")
            try:
                result = pair_seat(pane, frame, boundary, cache)
            except Exception as exc:
                result = {"pane_key": pane.key, "support_key": frame.key, "boundary": boundary,
                    "passed": False, "state": "ERROR_OR_UNRESOLVED_INPUT", "error": str(exc)}
            candidates.append(result)
            if result["passed"]:
                break
        require(candidates, "No required support parts")
        rows.append({"id": question["id"], "pane_key": pane.key, "boundary": boundary,
            "passed": any(r["passed"] for r in candidates), "actual_candidates": candidates})
    require(len({r["pane_key"] for r in rows}) == 2557, "Unexpected actual pane count")
    require(all({r["boundary"] for r in rows if r["pane_key"] == key} == {"bottom", "top"}
                for key in {r["pane_key"] for r in rows}), "Each pane needs bottom and top proof")
    passed = all(r["passed"] for r in rows)
    report = {"schema": "museum-actual-finite-area-pane-seating-v2", "finite_area_seating_passed": passed,
        "asset_identity": asset.identity, "source_binding": binding,
        "source_structure_report": filemeta(args.structure), "requests_file": filemeta(args.requests),
        "all_actual_parts_position_hash_verified": True, "verified_actual_part_count": len(asset.parts),
        "pane_count": 2557, "boundary_question_count": len(rows), "boundary_results": rows,
        "minimum_actual_cell_xy_area_m2": MINIMUM_CELL_AREA_M2, "minimum_volume_embed_m": MINIMUM_EMBED_M,
        "minimum_opposed_facing_vertical_cosine": MINIMUM_FACING_VERTICAL_COSINE,
        "minimum_actual_end_extension_m": MINIMUM_END_EXTENSION_M,
        "fixed_original_request_sha256": EXPECTED_REQUEST_SHA256,
        "maximum_opposite_plane_separation_m": MAXIMUM_OPPOSITE_PLANE_SEPARATION_M,
        "maximum_endpoint_arithmetic_error_m": MAXIMUM_ENDPOINT_ARITHMETIC_ERROR_M,
        "maximum_cells_per_pair": MAXIMUM_CELLS_PER_PAIR,
        "checker_files": [filemeta(__file__), filemeta(HERE / "modern_mesh.py"), filemeta(HERE / "finite_checks.py")],
        "scope": "Each pane bottom and top requires one true four-facet cell of projected area at least1e-5 square metres, opposed facing facets within60 degrees of vertical normals, and matching actual closed-solid intervals, with each outside solid end extending at least1e-6m beyond the opposite solid end in the stated support direction. No allowed air gap, whole-edge bearing, seal, structural-safety or appearance claim.",
        "model_appearance_accepted": False, "complete_collision_checked": False,
        "physical_structural_safety_verified": False}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"report": filemeta(output), "passed": passed, "failed": sum(not r["passed"] for r in rows)}))
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
