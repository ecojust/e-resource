"""Verify completed candidate assets and build their global-scene catalogue.

Asset manifests remain the original individual-model delivery records. This
separate catalogue records the later city placement without rewriting the
historical model's reference and accuracy claims. Missing sparse-checkout assets
are read from their immutable Git objects; source files are never removed.
"""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import math
from pathlib import Path
import struct
import subprocess

import numpy as np
from shapely.geometry import Point, shape
from shapely.ops import transform

ROOT = Path(__file__).resolve().parents[3]
PROJECT = ROOT / "projects/shanghai"
AUDIT = PROJECT / "data/audit/global-model-integration-v1"
INVENTORY = AUDIT / "inventory.json"
CATALOG = PROJECT / "data/candidate-city-integrations.json"
DISTRICTS = {"chongming": ("310151", "崇明区"), "hongkou": ("310109", "虹口区"),
             "huangpu": ("310101", "黄浦区"), "xuhui": ("310104", "徐汇区")}


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def read_file(path, revision):
    path = Path(path)
    local = ROOT / path
    return local.read_bytes() if local.is_file() else git("show", f"{revision}:{path.as_posix()}")


def checked_asset(path, expected, revision):
    blob = read_file(path, revision)
    assert len(blob) == expected["bytes"], f"Asset size differs: {path}"
    assert 0 < len(blob) < 100_000_000, f"Asset exceeds single-file bound: {path}"
    digest = hashlib.sha256(blob).hexdigest()
    assert digest == expected["sha256"], f"Asset digest differs: {path}"
    return blob


def raw_geometry(blob):
    """Read actual FLOAT32 position arrays, not accessor-declared bounds."""
    magic, version, length = struct.unpack_from("<III", blob)
    assert magic == 0x46546C67 and version == 2 and length == len(blob)
    json_length, json_type = struct.unpack_from("<II", blob, 12)
    assert json_type == 0x4E4F534A
    doc = json.loads(blob[20:20 + json_length])
    bin_offset = 20 + json_length
    bin_length, bin_type = struct.unpack_from("<II", blob, bin_offset)
    assert bin_type == 0x004E4942 and bin_offset + 8 + bin_length == len(blob)
    data = memoryview(blob)[bin_offset + 8:]
    assert all("uri" not in item for item in doc.get("buffers", []))
    active = []
    def visit(index, parent):
        node = doc["nodes"][index]
        if "matrix" in node:
            local = np.asarray(node["matrix"], dtype=float).reshape((4, 4), order="F")
        else:
            local = np.eye(4)
            x, y, z, w = node.get("rotation", [0, 0, 0, 1])
            assert abs(x*x+y*y+z*z+w*w-1) < 1e-5
            rotation = np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
                                 [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
                                 [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])
            local[:3, :3] = rotation @ np.diag(node.get("scale", [1, 1, 1]))
            local[:3, 3] = node.get("translation", [0, 0, 0])
        world = parent @ local
        if "mesh" in node:
            active.append((node["mesh"], world))
        for child in node.get("children", []):
            visit(child, world)
    for node in doc["scenes"][doc.get("scene", 0)]["nodes"]:
        visit(node, np.eye(4))
    minimum, maximum = np.full(3, np.inf), np.full(3, -np.inf)
    triangles = 0
    for index, matrix in active:
        for primitive in doc["meshes"][index]["primitives"]:
            assert primitive.get("mode", 4) == 4
            accessor = doc["accessors"][primitive["attributes"]["POSITION"]]
            assert accessor["type"] == "VEC3" and accessor["componentType"] == 5126 and "sparse" not in accessor
            view = doc["bufferViews"][accessor["bufferView"]]
            offset = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
            positions = np.ndarray((accessor["count"], 3), dtype="<f4", buffer=data,
                                   offset=offset, strides=(view.get("byteStride", 12), 4))
            assert np.isfinite(positions).all()
            positions = positions @ matrix[:3, :3].T + matrix[:3, 3]
            minimum = np.minimum(minimum, positions.min(axis=0))
            maximum = np.maximum(maximum, positions.max(axis=0))
            indices = doc["accessors"][primitive["indices"]]
            assert indices["count"] % 3 == 0
            triangles += indices["count"] // 3
    assert np.isfinite(minimum).all() and (maximum > minimum).all()
    bounds = {"min": minimum.tolist(), "max": maximum.tolist()}
    enu = {"min": [float(minimum[0]), float(-maximum[2]), float(minimum[1])],
           "max": [float(maximum[0]), float(-minimum[2]), float(maximum[1])]}
    return {"bounds_glb": bounds, "bounds_enu_m": enu, "triangles": triangles,
            "scene_meshes": len(active), "method": "actual raw GLB FLOAT32 position arrays with complete scene-node world transforms"}


def build_inventory(revision):
    baseline = json.loads(git("show", f"{revision}:projects/shanghai/data/landmarks.json"))
    existing_ids = {row["id"] for row in baseline}
    assert len(existing_ids) == len(baseline) == 40
    viewers = {row["id"]: row for row in json.loads(git("show", f"{revision}:projects/shanghai/data/model-viewers.json"))}
    queue = json.loads(git("show", f"{revision}:projects/shanghai/data/model-todo/queue.json"))
    jobs = {row["id"]: row for row in queue["existing_models"] + queue["production_queue"]}
    paths = [path for path in git("ls-tree", "-r", "--name-only", revision,
              "projects/shanghai/assets/models/candidates").decode().splitlines() if path.endswith("/manifest.json")]
    records = []
    verified_files, verified_bytes = 0, 0
    for path in sorted(paths):
        manifest_blob = git("show", f"{revision}:{path}")
        manifest = json.loads(manifest_blob)
        ident = manifest["id"]
        assert ident == Path(path).parent.name
        assets = {}
        geometry = None
        with ThreadPoolExecutor(max_workers=4) as pool:
            blobs = {variant: pool.submit(checked_asset, Path(path).parent / asset["file"], asset, revision)
                     for variant, asset in manifest["assets"].items()}
        for variant, asset in manifest["assets"].items():
            file = Path(path).parent / asset["file"]
            blob = blobs[variant].result()
            verified_files += 1
            verified_bytes += len(blob)
            assets["web" if variant == "full" else variant] = {**asset, "file": file.relative_to("projects/shanghai").as_posix()}
            if variant == "raw":
                geometry = raw_geometry(blob)
                assert geometry["triangles"] == asset["triangles"]
        assert geometry and set(assets) == {"raw", "native", "web", "lod"}
        viewer, job = viewers.get(ident, {}), jobs.get(ident, {})
        page = viewer.get("page") or job.get("preview_source") or job.get("url")
        assert page, f"No individual page for {ident}"
        page = page.rsplit("/", 1)[-1].split("#")[0]
        district_id, district = DISTRICTS[ident.split("-", 1)[0]]
        records.append({"id": ident, "name": job.get("name", manifest["name"]), "districtId": district_id,
                        "district": district, "already_in_city": ident in existing_ids,
                        "individual_page": page, "manifest": Path(path).relative_to("projects/shanghai").as_posix(),
                        "manifest_sha256": hashlib.sha256(manifest_blob).hexdigest(), "assets": assets,
                        "geometry": geometry,
                        "coordinate_convention": "GLB [east, up, -north] in metres; placement rotates this local basis",
                        "original_delivery_status": manifest.get("status"),
                        "description": viewer.get("description") or job.get("scope") or manifest.get("estimated", "")})
        print(f"Verified {len(records)}/{len(paths)}: {ident}", flush=True)
    new = [row for row in records if not row["already_in_city"]]
    assert len(records) == 32 and len(new) == 30
    return {"schema": "candidate-city-inventory-v1", "asset_baseline_commit": revision,
            "existing_city_count": 40, "existing_city_ids": sorted(existing_ids),
            "candidate_manifest_count": len(records), "already_integrated_candidate_ids": [row["id"] for row in records if row["already_in_city"]],
            "new_city_model_count": len(new), "resulting_city_count": 40 + len(new),
            "new_models_by_district": dict(sorted(Counter(row["district"] for row in new).items())),
            "verification": {"all_manifest_assets_read": True, "files": verified_files, "bytes": verified_bytes,
                             "byte_lengths_and_sha256_match": True, "single_file_limit_bytes_exclusive": 100_000_000,
                             "geometry_scope": "Raw model world bounds and triangle counts only; this is not a renewed shape or source-identity acceptance"},
            "records": records}


def write_json(path, data, check=False):
    value = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    if check:
        assert path.read_text() == value, f"Generated file stale: {path.relative_to(ROOT)}"
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value)


def checked_geometry(geometry, label, nullable=False):
    if nullable and geometry is None:
        return None
    assert isinstance(geometry, dict) and geometry.get("type") in ("Polygon", "MultiPolygon"), label
    result = shape(geometry)
    assert not result.is_empty and result.is_valid and result.area > 0, f"Invalid {label}"
    west, south, east, north = result.bounds
    assert 120.65 <= west <= east <= 122.3 and 30.55 <= south <= north <= 32, f"Out-of-Shanghai {label}"
    return result


def build_catalog(inventory):
    inputs, placements = [], {}
    for filename in ("urban-placement.json", "chongming-placement.json"):
        path = PROJECT / "data/global-models" / filename
        blob = path.read_bytes()
        document = json.loads(blob)
        rows = document if isinstance(document, list) else document["records"]
        for row in rows:
            assert row["id"] not in placements, f"Duplicate placement {row['id']}"
            placements[row["id"]] = row
        inputs.append({"file": path.relative_to(PROJECT).as_posix(), "bytes": len(blob),
                       "sha256": hashlib.sha256(blob).hexdigest()})
    new = [row for row in inventory["records"] if not row["already_in_city"]]
    assert set(placements) == {row["id"] for row in new}, "Placement IDs must cover exactly the 30 previously unintegrated candidates"
    models = []
    for item in new:
        ident = item["id"]
        placement = placements[ident]
        assert placement["id"] == ident
        lng, lat = placement["lng"], placement["lat"]
        assert 120.65 < lng < 122.3 and 30.55 < lat < 32
        heading, scale = placement["heading"], placement.get("scale", 1)
        assert math.isfinite(heading) and isinstance(scale, (float, int)) and .1 <= scale <= 4
        bounds = placement.get("bounds_glb", item["geometry"]["bounds_glb"])
        if isinstance(bounds, list):
            assert len(bounds) == 2
            bounds = {"min": bounds[0], "max": bounds[1]}
        assert len(bounds["min"]) == len(bounds["max"]) == 3
        assert all(math.isfinite(v) for values in bounds.values() for v in values)
        assert all(b > a for a, b in zip(bounds["min"], bounds["max"]))
        assets = {variant: dict(item["assets"][variant]) for variant in ("web", "lod")}
        if "assets" in placement:
            assert set(placement["assets"]) == {"web", "lod"}
            for variant, asset in placement["assets"].items():
                assert ".." not in Path(asset["file"]).parts and not Path(asset["file"]).is_absolute()
                checked_asset(Path("projects/shanghai") / asset["file"], asset, inventory["asset_baseline_commit"])
                assets[variant] = dict(asset)
            assert "bounds_glb" in placement and "derived_asset_note" in placement
        navigation = placement["navigation"]
        assert isinstance(navigation["listed"], bool)
        if navigation["listed"]:
            assert len(navigation["walkStart"]) == 2 and all(math.isfinite(x) for x in navigation["walkStart"])
            assert math.isfinite(navigation["bearing"])
        collision = checked_geometry(placement["collision_geometry"], f"{ident} collision_geometry")
        replacement = checked_geometry(placement.get("replacement_geometry"), f"{ident} replacement_geometry", nullable=True)
        source_ids = placement.get("source_feature_ids", {"building": [], "building_part": []})
        assert set(source_ids) == {"building", "building_part"}
        assert all(isinstance(values, list) and len(values) == len(set(values)) for values in source_ids.values())
        assert replacement is None or any(source_ids.values()), f"Unidentified source clipping: {ident}"
        note = placement["placement"]
        assert note["status"] in ("estimated", "map-aligned") and note["note"]
        model = {"id": ident, "name": item["name"], "kind": "building", "candidate_id": ident,
                 "detail_level": "architectural", "districtId": item["districtId"], "district_name": item["district"],
                 "architecture_style": "外观候选 · 近似定位" if note["status"] == "estimated" else "外观候选 · 地图对齐",
                 "lng": lng, "lat": lat, "heading": heading, "scale": scale,
                 "height_m": bounds["max"][1] * scale, "height_estimated": True, "bounds_glb": bounds,
                 "assets": assets, "model": assets["web"]["file"], "lod_model": assets["lod"]["file"],
                 "web_bytes": assets["web"]["bytes"], "web_sha256": assets["web"]["sha256"],
                 "lod_bytes": assets["lod"]["bytes"], "lod_sha256": assets["lod"]["sha256"],
                 "triangles": assets["web"]["triangles"], "lod_triangles": assets["lod"]["triangles"],
                 "individual_page": item["individual_page"], "candidate_manifest": item["manifest"],
                 "navigation": navigation, "overviewZoom": placement.get("overviewZoom", 19),
                 "maxDistance": placement.get("maxDistance", 420 if item["districtId"] == "310151" else 650),
                 "lod_switch_in_m": placement.get("lod_switch_in_m", 70), "lod_switch_out_m": placement.get("lod_switch_out_m", 110),
                 "collision_geometry": placement["collision_geometry"], "replacement_geometry": placement.get("replacement_geometry"),
                 "source_feature_ids": source_ids, "placement": note,
                 "detail_note": note["note"] + "；" + item["description"],
                 "complete_photo_reconstruction_accepted": False}
        for key in ("owner", "owners", "source_owner", "source_owners", "site_replacement", "derived_asset_note", "partial_model", "model_scope", "altitude"):
            if key in placement:
                model[key] = json.loads(json.dumps(placement[key]))
        site = model.get("site_replacement")
        if site and "owner" not in site and site.get("source_macro") and site.get("source_local_id"):
            site["owner"] = {"macro_id": site["source_macro"], "feature_local_id": site["source_local_id"]}
        models.append(model)
    assert len({model["id"] for model in models}) == len(models) == 30
    assert not set(inventory["existing_city_ids"]).intersection(model["id"] for model in models)
    # Test every reviewed spawn against all new candidate obstacles in metres,
    # including neighboring buildings. This does not certify source-map streets.
    spawn_checks = []
    for model in models:
        if not model["navigation"]["listed"]:
            continue
        lng, lat = model["navigation"]["walkStart"]
        sx, sy = 6378137 * math.pi / 180 * math.cos(math.radians(lat)), 6378137 * math.pi / 180
        project = lambda x, y, z=None: ((np.asarray(x) - lng) * sx, (np.asarray(y) - lat) * sy)
        distances = [(other["id"], transform(project, shape(other["collision_geometry"])).distance(Point(0, 0))) for other in models]
        nearest, distance = min(distances, key=lambda item: item[1])
        assert distance >= .38, f"Spawn intersects candidate body: {model['id']} -> {nearest}, {distance:.3f} m"
        spawn_checks.append({"id": model["id"], "nearest_candidate": nearest, "clearance_m": round(distance, 6)})
    inventory_blob = INVENTORY.read_bytes()
    catalog = {"schema": "candidate-city-integrations-v1", "asset_baseline_commit": inventory["asset_baseline_commit"],
               "scope": "30 completed exterior candidates placed in the shared Shanghai scene; placement and model precision remain explicitly bounded",
               "existing_city_count": 40, "new_city_model_count": 30, "resulting_city_count": 70,
               "new_walk_entry_count": len(spawn_checks),
               "input_files": inputs, "inventory_sha256": hashlib.sha256(inventory_blob).hexdigest(),
               "models": models}
    checks = {"schema": "candidate-city-catalog-checks-v1", "existing_city_count": 40, "new_city_models": 30,
              "unique_city_destinations": 70, "inputs": inputs, "all_asset_contracts_match_inventory_or_checked_derivation": True,
              "all_placement_polygons_valid": True, "identified_source_required_for_replacement": True,
              "listed_spawn_count": len(spawn_checks), "spawn_clearance_radius_m": .38, "spawn_checks": spawn_checks,
              "limitation": "Static candidate geometry checks; source-map roads, vector clipping and loading/fallback behavior require separate runtime/browser checks."}
    return catalog, checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset-revision")
    parser.add_argument("--inventory-only", action="store_true")
    parser.add_argument("--catalog-only", action="store_true", help="Reuse previously verified inventory; still validate placements and derived assets")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    revision = args.asset_revision or (json.loads(INVENTORY.read_text())["asset_baseline_commit"] if INVENTORY.exists() else git("rev-parse", "HEAD").decode().strip())
    assert not (args.inventory_only and args.catalog_only)
    inventory = json.loads(INVENTORY.read_text()) if args.catalog_only else build_inventory(revision)
    if not args.catalog_only:
        write_json(INVENTORY, inventory, args.check)
    if not args.inventory_only:
        catalog, checks = build_catalog(inventory)
        write_json(CATALOG, catalog, args.check)
        write_json(AUDIT / "catalog-checks.json", checks, args.check)
    print(json.dumps({"candidates": inventory["candidate_manifest_count"], "new_city_models": inventory["new_city_model_count"],
                      "files_verified": inventory["verification"]["files"], "bytes_verified": inventory["verification"]["bytes"]}))


if __name__ == "__main__":
    main()
