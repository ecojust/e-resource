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
import re
from datetime import date
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
CURRENT_INVENTORY = PROJECT / "data/global-models/candidate-inventory.json"
CATALOG = PROJECT / "data/candidate-city-integrations.json"
DISTRICTS = {"chongming": ("310151", "崇明区"), "hongkou": ("310109", "虹口区"),
             "huangpu": ("310101", "黄浦区"), "xuhui": ("310104", "徐汇区"),
             "yangpu": ("310110", "杨浦区"), "jingan": ("310106", "静安区"),
             "changning": ("310105", "长宁区"), "putuo": ("310107", "普陀区")}


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def read_file(path, revision):
    path = Path(path)
    local = ROOT / path
    if local.is_file():
        return local.read_bytes()
    # Incremental deliveries are checked before commit. Once published, sparse
    # checkouts can recover their bytes from HEAD even though the immutable
    # historical inventory's revision predates the new building.
    for ref in dict.fromkeys((revision, "HEAD")):
        try:
            return git("show", f"{ref}:{path.as_posix()}")
        except subprocess.CalledProcessError:
            pass
    raise FileNotFoundError(path)


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


def verify_manifest(path, revision, existing_ids, viewers, jobs, manifest_blob=None):
    path = Path(path)
    manifest_blob = read_file(path, revision) if manifest_blob is None else manifest_blob
    manifest = json.loads(manifest_blob)
    ident = manifest["id"]
    assert ident == path.parent.name
    assets, geometry = {}, None
    overhead = manifest.get("ground_collision_mode") == "overhead-connector"
    verified_minima = {}
    verified_files, verified_bytes = 0, 0
    assert all(not Path(asset["file"]).is_absolute() and ".." not in Path(asset["file"]).parts
               for asset in manifest["assets"].values()), "Asset file must remain inside its delivery directory"
    with ThreadPoolExecutor(max_workers=4) as pool:
        blobs = {variant: pool.submit(checked_asset, path.parent / asset["file"], asset, revision)
                 for variant, asset in manifest["assets"].items()}
    for variant, asset in manifest["assets"].items():
        file = path.parent / asset["file"]
        blob = blobs[variant].result()
        verified_files += 1
        verified_bytes += len(blob)
        assets["web" if variant == "full" else variant] = {**asset, "file": file.relative_to("projects/shanghai").as_posix()}
        if variant == "raw" or (overhead and variant in ("full", "lod")):
            measurements = raw_geometry(blob)
            assert measurements["triangles"] == asset["triangles"]
            if variant == "raw":
                geometry = measurements
            if overhead:
                verified_minima["web" if variant == "full" else variant] = measurements["bounds_glb"]["min"][1]
    assert geometry and set(assets) == {"raw", "native", "web", "lod"}
    if overhead:
        assert set(verified_minima) == {"raw", "web", "lod"}
        geometry["overhead_min_y_m"] = verified_minima
    viewer, job = viewers.get(ident, {}), jobs.get(ident, {})
    page = viewer.get("page") or job.get("preview_source") or manifest.get("viewer_page") or job.get("url")
    assert page, f"No individual page metadata for {ident}"
    page = page.rsplit("/", 1)[-1].split("#")[0]
    assert page.endswith(".html") and page != "index.html", f"Independent page metadata must not alias the shared map: {ident}"
    district_id, district = DISTRICTS[ident.split("-", 1)[0]]
    record = {"id": ident, "name": job.get("name", manifest["name"]), "districtId": district_id,
              "district": district, "already_in_city": ident in existing_ids,
              "individual_page": page, "manifest": path.relative_to("projects/shanghai").as_posix(),
              "manifest_sha256": hashlib.sha256(manifest_blob).hexdigest(), "assets": assets,
              "geometry": geometry,
              "coordinate_convention": "GLB [east, up, -north] in metres; placement rotates this local basis",
              "original_delivery_status": manifest.get("status"),
              "description": viewer.get("description") or job.get("scope") or manifest.get("estimated", "")}
    return record, verified_files, verified_bytes


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
        record, files, size = verify_manifest(path, revision, existing_ids, viewers, jobs, git("show", f"{revision}:{path}"))
        records.append(record)
        verified_files += files
        verified_bytes += size
        print(f"Verified {len(records)}/{len(paths)}: {record['id']}", flush=True)
    new = [row for row in records if not row["already_in_city"]]
    assert len({row["id"] for row in records}) == len(records)
    return {"schema": "candidate-city-inventory-v1", "asset_baseline_commit": revision,
            "existing_city_count": 40, "existing_city_ids": sorted(existing_ids),
            "candidate_manifest_count": len(records), "already_integrated_candidate_ids": [row["id"] for row in records if row["already_in_city"]],
            "new_city_model_count": len(new), "resulting_city_count": 40 + len(new),
            "new_models_by_district": dict(sorted(Counter(row["district"] for row in new).items())),
            "verification": {"all_manifest_assets_read": True, "files": verified_files, "bytes": verified_bytes,
                             "byte_lengths_and_sha256_match": True, "single_file_limit_bytes_exclusive": 100_000_000,
                             "geometry_scope": "Raw model world bounds and triangle counts only; this is not a renewed shape or source-identity acceptance"},
            "records": records}


def normalized_manifest_path(value):
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path if path.parts[0] == "projects" else PROJECT / path
    path = path.resolve().relative_to(ROOT)
    assert len(path.parts) == 7 and path.parts[:5] == ("projects", "shanghai", "assets", "models", "candidates") and path.name == "manifest.json"
    return path


def incremental_delivery_context(previous, manifests, requested_directory):
    """Freeze the preceding delivery before appending to the current inventory."""
    old_paths = set((previous or {}).get("incremental_manifests", []))
    appended = set(manifests) - old_paths
    directory = requested_directory or (previous or {}).get("incremental_audit_directory")
    assert directory, "An incremental delivery needs --audit-directory for its separate evidence"
    audit = (PROJECT / directory).resolve()
    directory = audit.relative_to(PROJECT).as_posix()
    assert audit != AUDIT and AUDIT not in audit.parents, "Do not rewrite the original integration audit"
    prior = (previous or {}).get("prior_incremental_inventory")
    if previous and appended:
        assert requested_directory, "A new delivery requires an explicit fresh --audit-directory"
        old_audit = (PROJECT / previous["incremental_audit_directory"]).resolve()
        assert audit != old_audit and old_audit not in audit.parents, "Do not rewrite the preceding delivery's audit"
        history, seen = prior, set()
        while history:
            history_path = (PROJECT / history["file"]).resolve()
            assert history_path not in seen, "Cyclic incremental audit history"
            seen.add(history_path)
            assert audit != history_path.parent and history_path.parent not in audit.parents, "Do not rewrite an earlier delivery's audit"
            history_blob = read_file(history_path.relative_to(ROOT), "HEAD")
            assert len(history_blob) == history["bytes"] and hashlib.sha256(history_blob).hexdigest() == history["sha256"], "Frozen previous inventory audit changed"
            history = json.loads(history_blob).get("prior_incremental_inventory")
        assert not (audit / "inventory-increment.json").exists(), "A new delivery must not reuse an earlier inventory audit"
        path = old_audit / "inventory-increment.json"
        blob = read_file(path.relative_to(ROOT), "HEAD")
        frozen = json.loads(blob)
        baseline_ids = set(previous["existing_city_ids"])
        baseline_ids.update(row["id"] for row in json.loads(INVENTORY.read_text())["records"])
        assert frozen["incremental_manifests"] == previous["incremental_manifests"], "Previous manifest history differs from its frozen audit"
        assert frozen["records"] == [row for row in previous["records"] if row["id"] not in baseline_ids], "Previous records differ from their frozen audit"
        assert frozen["verification"] == previous["verification"], "Previous verification differs from its frozen audit"
        prior = {"file": path.relative_to(PROJECT).as_posix(), "bytes": len(blob),
                 "sha256": hashlib.sha256(blob).hexdigest()}
    elif previous and requested_directory:
        assert directory == previous["incremental_audit_directory"], "An existing delivery must retain its audit directory"
    return directory, prior


def current_ordinary_ids(baseline_ids):
    """Include newly registered ordinary buildings alongside the frozen original inventory."""
    ordinary = json.loads((PROJECT / "data/landmarks.json").read_bytes())
    listed = {row["id"] for row in ordinary}
    assert len(listed) == len(ordinary) and baseline_ids.issubset(listed)
    for row in ordinary:
        if row["id"] in baseline_ids:
            continue
        assert row.get("accepted") is True and row.get("navigation", {}).get("listed") is True
        pointer_file = Path("projects/shanghai/data/precise-buildings/by-id") / (row["id"] + ".json")
        pointer = json.loads(read_file(pointer_file, "HEAD"))
        assert pointer["id"] == row["id"] and pointer["feature_local_id"] == row["owner"]["feature_local_id"]
        index = json.loads(read_file(Path("projects/shanghai") / pointer["macro_index"], "HEAD"))
        assert [entry for entry in index["models"] if entry["id"] == row["id"]] == [row]
    return listed


def build_incremental_inventory(manifests, revision, audit_directory, prior_increment=None):
    """Retain the original 32-record evidence and verify only explicit additions.

    The current inventory records its baseline digest and the complete appended
    manifest list, so the ordinary --check command can reproduce this result.
    It does not reinterpret the original integration audit as a fresh acceptance.
    """
    baseline_blob = INVENTORY.read_bytes()
    baseline = json.loads(baseline_blob)
    records = list(baseline["records"])
    baseline_ids = {row["id"] for row in records}
    baseline_binding = {"file": INVENTORY.relative_to(PROJECT).as_posix(), "bytes": len(baseline_blob), "sha256": hashlib.sha256(baseline_blob).hexdigest()}
    frozen_paths = set()
    frozen_files, frozen_bytes = 0, 0
    if prior_increment:
        path = Path(prior_increment["file"])
        assert not path.is_absolute() and ".." not in path.parts and path.name == "inventory-increment.json"
        blob = read_file(Path("projects/shanghai") / path, revision)
        assert len(blob) == prior_increment["bytes"] and hashlib.sha256(blob).hexdigest() == prior_increment["sha256"], "Frozen previous inventory audit changed"
        frozen = json.loads(blob)
        assert frozen["schema"] == "candidate-city-inventory-increment-v1" and frozen["baseline_inventory"] == baseline_binding
        frozen_paths = set(frozen["incremental_manifests"])
        assert len(frozen_paths) == len(frozen["records"])
        assert {"projects/shanghai/" + row["manifest"] for row in frozen["records"]} == frozen_paths
        assert frozen_paths.issubset(normalized_manifest_path(value).as_posix() for value in manifests), "Cannot remove a previously delivered manifest"
        assert not baseline_ids.intersection(row["id"] for row in frozen["records"])
        records.extend(frozen["records"])
        frozen_files = sum(len(row["assets"]) for row in frozen["records"])
        frozen_bytes = sum(asset["bytes"] for row in frozen["records"] for asset in row["assets"].values())
    existing_ids = current_ordinary_ids(set(baseline["existing_city_ids"]))
    viewers = {row["id"]: row for row in json.loads((PROJECT / "data/model-viewers.json").read_text())}
    queue = json.loads((PROJECT / "data/model-todo/queue.json").read_text())
    jobs = {row["id"]: row for row in queue["existing_models"] + queue["production_queue"]}
    paths = []
    for value in manifests:
        path = normalized_manifest_path(value)
        assert path.parent.name not in baseline_ids, "Incremental delivery must not replace historical inventory records"
        paths.append(path.as_posix())
    assert len(paths) == len(set(paths)), "Duplicate incremental manifest"
    added_files, added_bytes = 0, 0
    for path in sorted(set(paths) - frozen_paths):
        record, files, size = verify_manifest(path, revision, existing_ids, viewers, jobs)
        records.append(record)
        added_files += files
        added_bytes += size
        print(f"Verified incremental asset: {record['id']}", flush=True)
    assert len({row["id"] for row in records}) == len(records)
    new = [row for row in records if not row["already_in_city"]]
    result = {**baseline,
              "existing_city_ids": sorted(existing_ids), "existing_city_count": len(existing_ids),
              "baseline_inventory": baseline_binding,
              "incremental_manifests": sorted(paths), "incremental_asset_revision": revision,
              "incremental_audit_directory": audit_directory,
              "candidate_manifest_count": len(records), "new_city_model_count": len(new),
              "resulting_city_count": len(existing_ids) + len(new),
              "new_models_by_district": dict(sorted(Counter(row["district"] for row in new).items())),
              "verification": {**baseline["verification"],
                               "files": baseline["verification"]["files"] + frozen_files + added_files,
                               "bytes": baseline["verification"]["bytes"] + frozen_bytes + added_bytes,
                               "current_run_added_files": added_files, "current_run_added_bytes": added_bytes,
                               "scope": "Original records retain their immutable baseline verification; only the explicitly listed incremental manifests/assets are read in this run."},
              "records": records}
    if prior_increment:
        result["prior_incremental_inventory"] = prior_increment
        result["current_delivery_manifests"] = sorted(set(paths) - frozen_paths)
        result["verification"].update(
            all_manifest_assets_read=False, all_current_delivery_assets_read=True,
            inherited_incremental_files=frozen_files,
            scope="Original and previous incremental records retain their frozen verification; only this delivery's manifests/assets are read. Prior increment bytes and SHA are checked before reuse.")
    return result


def write_json(path, data, check=False):
    value = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    if check:
        assert path.read_text() == value, f"Generated file stale: {path.relative_to(ROOT)}"
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value)


def checked_geometry(geometry, label, nullable=False, *, collision=False):
    if nullable and geometry is None:
        return None
    assert isinstance(geometry, dict) and geometry.get("type") in ("Polygon", "MultiPolygon"), label
    polygons = [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
    max_rings, max_points = (32, 256) if collision else (8, 65)
    assert 0 < len(polygons) <= 32 and all(0 < len(polygon) <= max_rings for polygon in polygons), f"Runtime polygon budget exceeded: {label}"
    assert not collision or sum(len(ring) for polygon in polygons for ring in polygon) <= 4096, f"Runtime collision point budget exceeded: {label}"
    assert all(4 <= len(ring) <= max_points and ring[0] == ring[-1]
               and all(len(point) == 2 and all(isinstance(v, (int, float)) and math.isfinite(v) for v in point) for point in ring)
               for polygon in polygons for ring in polygon), f"Runtime ring contract violated: {label}"
    result = shape(geometry)
    assert not result.is_empty and result.is_valid and result.area > 0, f"Invalid {label}"
    west, south, east, north = result.bounds
    assert 120.65 <= west <= east <= 122.3 and 30.55 <= south <= north <= 32, f"Out-of-Shanghai {label}"
    return result


def validate_historical_period(view, ident):
    def year(value):
        return type(value) is int and 1500 <= value <= date.today().year
    assert isinstance(view, dict) and view.get("kind") == "archival-facade", ident
    years = view.get("evidence_years")
    assert isinstance(years, list) and len(years) == 2 and all(year(value) for value in years), ident
    assert years[0] <= years[1], ident
    if view.get("evidence_kind") == "dated-photograph":
        assert set(view) == {"kind", "evidence_kind", "evidence_years", "site_status", "location_precision"}, ident
        assert years[0] == years[1] and view["site_status"] == "protected-building-unlocated", ident
        assert view["location_precision"] == "complex", ident
        return
    if "building_year" in view:
        assert set(view) == {"kind", "building_year", "evidence_years"}, ident
        assert year(view["building_year"]) and view["building_year"] <= years[0], ident
        return
    assert set(view) == {"kind", "listed_year", "approximate_loss_year", "evidence_kind", "evidence_years"}, ident
    assert view["evidence_kind"] in {"published-drawing", "reprinted-photograph"}, ident
    if view["evidence_kind"] == "reprinted-photograph":
        assert years[0] == years[1] and year(view["approximate_loss_year"]), ident
        assert view["approximate_loss_year"] <= years[0], ident
    assert year(view["listed_year"]) and year(view["approximate_loss_year"]), ident
    assert view["listed_year"] <= view["approximate_loss_year"], ident


def historical_site_record(item, placement):
    """An archive viewer supplies a destination only; it cannot edit the current city."""
    ident = item["id"]
    expected_status = ("historical-illustration-informed-facade-study" if placement.get("historical_view", {}).get("evidence_kind") == "published-drawing" else "historical-photo-informed-facade-study")
    assert item["original_delivery_status"] == expected_status, ident
    assert set(placement) == {"id", "lng", "lat", "historical_view", "navigation", "collision_geometry",
                              "replacement_geometry", "source_feature_ids", "model_geometry_sha256"}, ident
    assert placement["navigation"] == {"listed": False}, ident
    assert placement["collision_geometry"] is None and placement["replacement_geometry"] is None, ident
    assert placement["source_feature_ids"] == {"building": [], "building_part": []}, ident
    assert placement["model_geometry_sha256"] == {key: item["assets"][key]["sha256"] for key in ("raw", "web", "lod")}, ident
    view = placement["historical_view"]
    validate_historical_period(view, ident)
    archive_page = re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*-history\.html", item["individual_page"])
    custom_pages = {"jingan-chen-bingqian-historic-residence": "chen-bingqian-historic-residence.html",
                    "yangpu-yangshupu-power-turbine-hall": "yangshupu-turbine-hall.html"}
    assert archive_page or (ident in custom_pages and item["individual_page"] == custom_pages[ident]), ident
    assert re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", ident), ident
    page = (PROJECT / item["individual_page"]).read_text()
    assert "showCandidateAssetViewer('" + ident + "')" in page, f"Archive viewer identity differs: {ident}"
    assert item["manifest"] == f"assets/models/candidates/{ident}/manifest.json", ident
    for key in ("web", "lod"):
        expected = f"assets/models/candidates/{ident}/{ident}-{key}.glb"
        assert item["assets"][key]["file"] == expected, ident
    return {"id": ident, "name": item["name"], "kind": "historical-site", "districtId": item["districtId"],
            "district_name": item["district"], "lng": placement["lng"], "lat": placement["lat"],
            "individual_page": item["individual_page"], "candidate_manifest": item["manifest"], "historical_view": view,
            "assets": {key: item["assets"][key] for key in ("web", "lod")}, "navigation": {"listed": False},
            "collision_geometry": None, "replacement_geometry": None, "source_feature_ids": placement["source_feature_ids"]}


def checked_bridge_walk(item, placement):
    label = item["id"] + " bridge walk"
    b = placement["bridge_walk"]
    def number(x, low, high):
        return type(x) in (float, int) and math.isfinite(x) and low <= x <= high
    assert b["version"] == 1 and b["longitudinal_axis"] in ("x", "-z"), label
    assert set(placement.get("model_geometry_sha256", {})) == {"raw", "web", "lod"}, label
    assert placement["collision_geometry"] is None and not any(placement.get(k) for k in
        ("owner", "owners", "source_owner", "source_owners", "replacement_geometry", "site_replacement",
         "display_height_clips", "source_section_caps", "ground_collision_mode")), label
    assert not any(placement.get("source_feature_ids", {}).values()), label
    assert number(placement["altitude"], -1000, 1000) and number(b["shear"], -1, 1), label
    width, road = b["half_deck_m"], b["half_road_m"]
    assert number(road, .25, 50) and number(width, road + .5, 60) and number(b["sidewalk_rise_m"], 0, .2), label
    ids = b["transportation_feature_ids"]
    assert isinstance(ids, list) and 1 <= len(ids) <= 16 and len(ids) == len(set(ids)), label
    assert all(type(i) is int and 0 < i <= 2**53 - 1 for i in ids), label
    stations = b["stations_m"]
    assert 2 <= len(stations) <= 256 and all(len(s) == 2 and number(s[0], -1000, 1000)
        and number(s[1], -50, 100) for s in stations), label
    assert all(next_s[0] > s[0] for s, next_s in zip(stations, stations[1:])), label
    assert 2 <= len(b["rails"]) <= 16 and all(number(r["offset_m"], -width, width)
        and number(r["radius_m"], .01, 1) and number(r["base_above_road_m"], -.3, 2)
        and number(r["top_above_road_m"], r["base_above_road_m"], 4) for r in b["rails"]), label
    assert all(any(sign * r["offset_m"] > road for r in b["rails"]) for sign in (-1, 1)), label
    posts = b.get("posts", [])
    assert len(posts) <= 64 and all(number(p["station_m"], stations[0][0], stations[-1][0])
        and number(p["offset_m"], -width, width) and number(p["half_length_m"], .01, 3)
        and number(p["half_width_m"], .01, 3) and number(p["top_above_road_m"], .2, 8) for p in posts), label
    bounds = item["geometry"]["bounds_glb"]
    for s, height in stations:
        for offset in (-width, width):
            along = s + b["shear"] * offset
            x, z = (along, -offset) if b["longitudinal_axis"] == "x" else (offset, -along)
            for axis, value in enumerate((x, height + b["sidewalk_rise_m"], z)):
                assert bounds["min"][axis] - .02 <= value <= bounds["max"][axis] + .02, label
    return b


def checked_ground_clearance(item, placement):
    """A suspended connector may omit its 2D obstacle only with verified clearance in every GLB."""
    label = item["id"] + " overhead connector"
    assert placement["ground_collision_mode"] == "overhead-connector", label
    assert placement["collision_geometry"] is None and not placement["navigation"]["listed"], label
    assert not any(placement.get(key) for key in (
        "owner", "owners", "source_owner", "source_owners", "site_replacement", "replacement_geometry",
        "display_height_clips", "source_section_caps", "assets",
    )), label
    assert not any(placement.get("source_feature_ids", {}).values()), label
    assert set(placement.get("model_geometry_sha256", {})) == {"raw", "web", "lod"}, label
    geometry = item["geometry"]
    assert placement.get("bounds_glb", geometry["bounds_glb"]) == geometry["bounds_glb"], label
    minima = geometry.get("overhead_min_y_m", {})
    assert set(minima) == {"raw", "web", "lod"} and all(math.isfinite(v) for v in minima.values()), label
    altitude, scale = placement.get("altitude", 0), placement.get("scale", 1)
    assert math.isfinite(altitude) and math.isfinite(scale) and scale > 0, label
    clearance = altitude + min(minima.values()) * scale
    assert clearance > 2.0, f"{label} has insufficient ground clearance: {clearance} m"
    return clearance


def checked_height_clips(clips, label):
    assert isinstance(clips, list) and len(clips) <= 8, f"Invalid {label} display_height_clips"
    ids = set()
    for clip in clips:
        assert isinstance(clip, dict), f"Invalid {label} height clip"
        ident = clip.get("id")
        assert isinstance(ident, str) and ident and ident not in ids, f"Invalid {label} height clip id"
        ids.add(ident)
        checked_geometry(clip.get("geometry"), f"{label} display_height_clips geometry")
        owner = clip.get("owner")
        assert isinstance(owner, dict) and isinstance(owner.get("macro_id"), str) and owner["macro_id"], f"Invalid {label} height clip owner"
        assert type(owner.get("feature_local_id")) is int and owner["feature_local_id"] > 0, f"Invalid {label} height clip owner"
        assert "owners" not in clip and "source_feature_ids" not in clip, f"GPU-only {label} height clip cannot affect vector source IDs"
        low, high = clip.get("min_height"), clip.get("max_height")
        assert all(type(v) in (int, float) and math.isfinite(v) and abs(v) <= float(np.finfo(np.float32).max) for v in (low, high)) and low < high, f"Invalid {label} height range"
        reference = clip.get("height_reference")
        assert isinstance(reference, list) and len(reference) == 2 and all(type(v) in (int, float) and math.isfinite(v) for v in reference), f"Invalid {label} height reference"
        assert abs(reference[0]) <= 180 and abs(reference[1]) <= 85, f"Invalid {label} height reference"
    return clips


def check_source_section_caps(model, replacement):
    """Verify the source mesh and seam lines used to close a partial cut."""
    label = model["id"] + " source_section_caps"
    caps = model["source_section_caps"]
    owner = model.get("owner", {})
    assert replacement is not None and any(model["source_feature_ids"].values()), label
    macro = owner.get("macro_id", "").split("-")
    assert len(macro) == 3 and all(part.isascii() and part.isdigit() for part in macro), label
    assert type(owner.get("feature_local_id")) is int and owner["feature_local_id"] > 0, label
    far_path = Path("projects/shanghai/assets/city-detail/macros") / owner["macro_id"] / "far.glb"
    assert hashlib.sha256(read_file(far_path, "HEAD")).hexdigest() == caps["far_sha256"], label

    low, high = caps["base_m"], caps["roof_m"]
    assert all(type(v) in (int, float) and math.isfinite(v) for v in (low, high)) and low < high, label
    reference = caps["height_reference"]
    assert len(reference) == 2 and 120.65 <= reference[0] <= 122.3 and 30.55 <= reference[1] <= 32, label
    geometry = caps["geometry"]
    assert geometry["type"] == "MultiLineString" and geometry["coordinates"], label
    for line in geometry["coordinates"]:
        assert len(line) >= 2 and all(len(p) == 2 and 120.65 <= p[0] <= 122.3 and 30.55 <= p[1] <= 32 for p in line), label
        assert all(a != b for a, b in zip(line, line[1:])), label
    seams = shape(geometry)
    assert seams.is_valid and not seams.is_empty, label
    # Allow rounding at the source polygon's eight-decimal coordinate precision.
    assert replacement.boundary.buffer(1e-8).covers(seams), f"Section cap outside {label} cut boundary"


def revised_delivery(item, binding, revision):
    """Use the current four-file delivery while keeping its original inventory record reproducible."""
    original = Path(item["manifest"])
    path = Path(binding["file"])
    assert path.parent == original.parent and re.fullmatch(r"manifest-[a-z0-9-]+\.json", path.name), path
    assert binding["original_manifest_sha256"] == item["manifest_sha256"], "Revision refers to a different original delivery"
    path = Path("projects/shanghai") / path
    manifest_blob = checked_asset(path, binding, revision)
    updated, _, _ = verify_manifest(path, revision, set(), {}, {}, manifest_blob=manifest_blob)
    assert updated["id"] == item["id"] and updated["individual_page"] == item["individual_page"]
    assert updated["districtId"] == item["districtId"]
    for role, asset in updated["assets"].items():
        assert asset["file"] != item["assets"][role]["file"], f"Revision must preserve the original {role} file"
    return {**item, **{key: updated[key] for key in ("manifest", "manifest_sha256", "assets", "geometry", "original_delivery_status")}}


def build_catalog(inventory, inventory_path=INVENTORY):
    inputs, placements = [], {}
    filenames = ["urban-placement.json", "chongming-placement.json"]
    if (PROJECT / "data/global-models/additional-placement.json").exists():
        filenames.append("additional-placement.json")
    for filename in filenames:
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
    assert set(placements) == {row["id"] for row in new}, "Placement IDs must cover exactly the candidate inventory additions"
    models = []
    for item in new:
        ident = item["id"]
        placement = placements[ident]
        assert placement["id"] == ident
        if "revised_delivery" in placement:
            item = revised_delivery(item, placement["revised_delivery"], inventory["asset_baseline_commit"])
        geometry_sources = placement.get("model_geometry_sha256", {})
        assert set(geometry_sources).issubset({"raw", "web", "lod"}), f"Unknown {ident} placement geometry variant"
        for variant, digest in geometry_sources.items():
            assert digest == item["assets"][variant]["sha256"], f"Stale placement geometry: {ident}/{variant}"
        lng, lat = placement["lng"], placement["lat"]
        assert 120.65 < lng < 122.3 and 30.55 < lat < 32
        if "historical_view" in placement or item.get("original_delivery_status") in ("historical-photo-informed-facade-study", "historical-illustration-informed-facade-study"):
            models.append(historical_site_record(item, placement))
            continue
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
        clearance = None
        if "bridge_walk" in placement:
            checked_bridge_walk(item, placement)
        elif "ground_collision_mode" in placement:
            clearance = checked_ground_clearance(item, placement)
        else:
            checked_geometry(placement["collision_geometry"], f"{ident} collision_geometry", collision=True)
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
        if "osm_replacement_geometry" in placement:
            osm_geometry = placement["osm_replacement_geometry"]
            osm_cut = checked_geometry(osm_geometry, f"{ident} osm_replacement_geometry")
            assert replacement is not None and replacement.buffer(1e-12).covers(osm_cut), f"OSM-specific cut exceeds primary cut: {ident}"
            model["osm_replacement_geometry"] = osm_geometry
        if clearance is not None:
            model["ground_collision_mode"] = placement["ground_collision_mode"]
            model["ground_clearance_m"] = clearance
        for field in ("overview_focus_bounds_glb", "label_focus_bounds_glb"):
            if field not in placement:
                continue
            focus = placement[field]
            label = f"Invalid {ident} {field}"
            assert isinstance(focus, dict) and set(focus) == {"min", "max"}, label
            assert all(isinstance(axis, list) and len(axis) == 3 and
                       all(type(value) in (int, float) and math.isfinite(value) for value in axis)
                       for axis in focus.values()), label
            assert all(outer_low <= low < high <= outer_high for outer_low, low, high, outer_high in
                       zip(bounds["min"], focus["min"], focus["max"], bounds["max"])), label
            model[field] = focus
        for key in ("overviewBearing", "overviewPitch"):
            if key in placement:
                assert isinstance(placement[key], (float, int)) and math.isfinite(placement[key]), f"Invalid {ident} {key}"
                if key == "overviewPitch":
                    assert 0 <= placement[key] <= 85
                model[key] = placement[key]
        for key in ("owner", "owners", "source_owner", "source_owners", "site_replacement", "display_height_clips", "source_section_caps", "derived_asset_note", "partial_model", "model_scope", "altitude", "model_geometry_sha256", "bridge_walk"):
            if key in placement:
                model[key] = json.loads(json.dumps(placement[key]))
        site = model.get("site_replacement")
        if site and "owner" not in site and site.get("source_macro") and site.get("source_local_id"):
            site["owner"] = {"macro_id": site["source_macro"], "feature_local_id": site["source_local_id"]}
        if site:
            site_cut = checked_geometry(site["geometry"], f"{ident} site_replacement.geometry")
            if "source_section_caps" in site:
                check_source_section_caps(site, site_cut)
        if "display_height_clips" in model:
            checked_height_clips(model["display_height_clips"], ident)
        if "source_section_caps" in model:
            check_source_section_caps(model, replacement)
        models.append(model)
    base_clip_ids = {model["id"] for model in models if model.get("replacement_geometry")}
    base_clip_ids.update(model["site_replacement"]["id"] for model in models if model.get("site_replacement"))
    height_clip_ids = [clip["id"] for model in models for clip in model.get("display_height_clips", [])]
    assert len(set(height_clip_ids)) == len(height_clip_ids) and not base_clip_ids.intersection(height_clip_ids), "Height clip IDs must be unique and separate from 2D clips"
    assert len({model["id"] for model in models}) == len(models) == len(new)
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
        distances = [(other["id"], transform(project, shape(other["collision_geometry"])).distance(Point(0, 0))) for other in models
                     if other["collision_geometry"] is not None]
        nearest, distance = min(distances, key=lambda item: item[1])
        assert distance >= .38, f"Spawn intersects candidate body: {model['id']} -> {nearest}, {distance:.3f} m"
        spawn_checks.append({"id": model["id"], "nearest_candidate": nearest, "clearance_m": round(distance, 6)})
    inventory_blob = inventory_path.read_bytes()
    existing_count = len(inventory["existing_city_ids"])
    total = existing_count + len(models)
    catalog = {"schema": "candidate-city-integrations-v1", "asset_baseline_commit": inventory["asset_baseline_commit"],
               "scope": f"{len(models)} completed exterior candidates placed in the shared Shanghai scene; placement and model precision remain explicitly bounded",
               "existing_city_count": existing_count, "new_city_model_count": len(models), "resulting_city_count": total,
               "new_walk_entry_count": len(spawn_checks),
               "input_files": inputs, "inventory_sha256": hashlib.sha256(inventory_blob).hexdigest(),
               "models": models}
    history_count = sum(model.get("kind") == "historical-site" for model in models)
    if history_count:
        catalog["historical_site_count"] = history_count
        catalog["scope"] = f"{len(models) - history_count} current-scene models; {history_count} historical sites with separate archive viewers"
    checks = {"schema": "candidate-city-catalog-checks-v1", "existing_city_count": existing_count, "new_city_models": len(models),
              "unique_city_destinations": total, "inputs": inputs, "all_asset_contracts_match_inventory_or_checked_derivation": True,
              "all_placement_polygons_valid": True, "identified_source_required_for_replacement": True,
              "listed_spawn_count": len(spawn_checks), "spawn_clearance_radius_m": .38, "spawn_checks": spawn_checks,
              "limitation": "Static candidate geometry checks; source-map roads, vector clipping and loading/fallback behavior require separate runtime/browser checks."}
    return catalog, checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset-revision")
    parser.add_argument("--append-manifest", action="append", default=[],
                        help="Explicit local candidate manifest to add to the immutable original inventory; repeat for additional deliveries")
    parser.add_argument("--audit-directory", help="Project-relative directory for the new delivery's checks; never overwrites the original integration audit")
    parser.add_argument("--inventory-only", action="store_true")
    parser.add_argument("--catalog-only", action="store_true", help="Reuse previously verified inventory; still validate placements and derived assets")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    assert not (args.inventory_only and args.catalog_only)
    previous = json.loads(CURRENT_INVENTORY.read_text()) if CURRENT_INVENTORY.exists() else None
    manifests = sorted({normalized_manifest_path(path).as_posix()
                        for path in (previous or {}).get("incremental_manifests", []) + args.append_manifest})
    assert not (args.catalog_only and args.append_manifest), "Verify a new manifest before --catalog-only reuse"
    inventory_path, audit = INVENTORY, AUDIT
    if manifests:
        inventory_path = CURRENT_INVENTORY
        appended = set(manifests) - set((previous or {}).get("incremental_manifests", []))
        revision = args.asset_revision or (None if appended else (previous or {}).get("incremental_asset_revision")) or git("rev-parse", "HEAD").decode().strip()
        directory, prior = incremental_delivery_context(previous, manifests, args.audit_directory)
        audit = PROJECT / directory
        inventory = previous if args.catalog_only else build_incremental_inventory(manifests, revision, directory, prior)
        assert inventory is not None
    else:
        revision = args.asset_revision or (json.loads(INVENTORY.read_text())["asset_baseline_commit"] if INVENTORY.exists() else git("rev-parse", "HEAD").decode().strip())
        inventory = json.loads(INVENTORY.read_text()) if args.catalog_only else build_inventory(revision)
    if not args.catalog_only:
        write_json(inventory_path, inventory, args.check)
        if manifests:
            baseline_ids = {row["id"] for row in json.loads(INVENTORY.read_text())["records"]}
            delta = {"schema": "candidate-city-inventory-increment-v1", "baseline_inventory": inventory["baseline_inventory"],
                     "incremental_manifests": inventory["incremental_manifests"], "asset_revision_fallback": revision,
                     "current_inventory": inventory_path.relative_to(PROJECT).as_posix(),
                     "verification": inventory["verification"],
                     "records": [row for row in inventory["records"] if row["id"] not in baseline_ids]}
            for key in ("prior_incremental_inventory", "current_delivery_manifests"):
                if key in inventory:
                    delta[key] = inventory[key]
            write_json(audit / "inventory-increment.json", delta, args.check)
    if not args.inventory_only:
        catalog, checks = build_catalog(inventory, inventory_path)
        if manifests:
            checks["inventory_file"] = inventory_path.relative_to(PROJECT).as_posix()
            checks["inventory_sha256"] = hashlib.sha256(inventory_path.read_bytes()).hexdigest()
            checks["asset_verification_scope"] = inventory["verification"]["scope"]
        write_json(CATALOG, catalog, args.check)
        write_json(audit / "catalog-checks.json", checks, args.check)
    print(json.dumps({"candidates": inventory["candidate_manifest_count"], "new_city_models": inventory["new_city_model_count"],
                      "cumulative_verified_files": inventory["verification"]["files"],
                      "current_run_inventory_files": 0 if args.catalog_only else inventory["verification"].get("current_run_added_files", inventory["verification"]["files"]),
                      "cumulative_verified_bytes": inventory["verification"]["bytes"]}))


if __name__ == "__main__":
    main()
