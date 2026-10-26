#!/usr/bin/env python3
"""Explicit v2-input runner; original area mathematics imported byte-exact.

Only binding/output reporting changes. No altered thresholds, cells, facets or
ray interval algorithms, and no rewriting the frozen historical request hash.
"""
import argparse,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
V11=HERE.parents[1]
OLD_CHECKER=V11/'independent-museum-review/checker-v2'
sys.path.insert(0,str(OLD_CHECKER))
from audit_pane_area_seating_v2 import (SmallFacetCache,pair_seat,MINIMUM_CELL_AREA_M2,
    MINIMUM_EMBED_M,MINIMUM_END_EXTENSION_M,MINIMUM_FACING_VERTICAL_COSINE,
    MAXIMUM_OPPOSITE_PLANE_SEPARATION_M,MAXIMUM_ENDPOINT_ARITHMETIC_ERROR_M,
    MAXIMUM_CELLS_PER_PAIR,EXPECTED_REQUEST_SHA256)
from modern_mesh import filemeta,load_raw,oriented_position_hash,require
from rebind_requests import (read,desc,identity,bound,validate_context,transform,OLD,GROUPS)

def validate_area_input(args):
    lock=read(HERE/'adaptation-input-lock.json')
    for row in lock['original_requests']+lock['mathematics_dependencies']:bound(row)
    manifest=read(args.rebinding_manifest)
    require(manifest['schema']=='museum-v2-request-rebinding-manifest-v1' and
        manifest['questions_prepared'] is True and manifest['actual_checks_executed'] is False,
        'Explicit question-only rebinding manifest required')
    require(identity(manifest['old_request_lock'])==identity(desc(HERE/'adaptation-input-lock.json')) and
        identity(manifest['generator'])==identity(desc(HERE/'rebind_requests.py')),'Rebinding code/input lock differs')
    for item in manifest['context'].values():bound(item)
    wanted=manifest['requests']['02-curtain-local-seating']
    require(identity(desc(args.requests))==identity(wanted),'Exact actual5114 request bytes required')
    bound(wanted)
    structure,binding,context=validate_context(args.raw,args.structure,bound(manifest['context']['preservation']))
    require(manifest['context']==context and manifest['source_binding']==binding,'Current rebinding context differs')
    original=[read(OLD/(name+'.requests.json'))for name in GROUPS]
    require(desc(OLD/'02-curtain-local-seating.requests.json')['sha256']==EXPECTED_REQUEST_SHA256,
        'Historical area question SHA changed')
    groups,mapping=transform(original,structure['part_results'])
    request=read(args.requests)
    require(request['checks']==groups[1] and request['source_binding']==binding,
        'Actual5114 suite does not equal exact allowed seven-support rebinding')
    mapped=read(bound(manifest['mapping']))
    require(mapped['old_question_mappings']==mapping and mapped['old_question_count']==6102 and
        mapped['new_question_count']==6114,'Complete old-to-new question accounting differs')
    return manifest

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--structure", type=Path, required=True)
    parser.add_argument("--requests", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--rebinding-manifest", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    require(output.is_relative_to(HERE) and not output.exists(), "Expected a new local immutable report")
    rebinding = validate_area_input(args)
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
    report = {"schema": "museum-actual-finite-area-pane-seating-v3", "finite_area_seating_passed": passed,
        "asset_identity": asset.identity, "source_binding": binding,
        "source_structure_report": filemeta(args.structure), "requests_file": filemeta(args.requests),
        "all_actual_parts_position_hash_verified": True, "verified_actual_part_count": len(asset.parts),
        "pane_count": 2557, "boundary_question_count": len(rows), "boundary_results": rows,
        "minimum_actual_cell_xy_area_m2": MINIMUM_CELL_AREA_M2, "minimum_volume_embed_m": MINIMUM_EMBED_M,
        "minimum_opposed_facing_vertical_cosine": MINIMUM_FACING_VERTICAL_COSINE,
        "minimum_actual_end_extension_m": MINIMUM_END_EXTENSION_M,
        "fixed_original_request_sha256": EXPECTED_REQUEST_SHA256,
        "actual_rebinding_manifest": filemeta(args.rebinding_manifest),
        "actual_preservation_prerequisite": rebinding["context"]["preservation"],
        "mathematics_unchanged_from": filemeta(OLD_CHECKER / "audit_pane_area_seating_v2.py"),
        "maximum_opposite_plane_separation_m": MAXIMUM_OPPOSITE_PLANE_SEPARATION_M,
        "maximum_endpoint_arithmetic_error_m": MAXIMUM_ENDPOINT_ARITHMETIC_ERROR_M,
        "maximum_cells_per_pair": MAXIMUM_CELLS_PER_PAIR,
        "checker_files": [filemeta(__file__), filemeta(HERE / "rebind_requests.py"),
            filemeta(OLD_CHECKER / "audit_pane_area_seating_v2.py"),
            filemeta(OLD_CHECKER / "modern_mesh.py"), filemeta(OLD_CHECKER / "finite_checks.py")],
        "scope": "Each pane bottom and top requires one true four-facet cell of projected area at least1e-5 square metres, opposed facing facets within60 degrees of vertical normals, and matching actual closed-solid intervals, with each outside solid end extending at least1e-6m beyond the opposite solid end in the stated support direction. No allowed air gap, whole-edge bearing, seal, structural-safety or appearance claim.",
        "model_appearance_accepted": False, "complete_collision_checked": False,
        "physical_structural_safety_verified": False}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"report": filemeta(output), "passed": passed, "failed": sum(not r["passed"] for r in rows)}))
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
