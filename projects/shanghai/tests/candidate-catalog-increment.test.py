"""Focused incremental catalogue checks; historical GLBs are not revalidated."""
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("candidate_builder", PROJECT / "tools/build_candidate_city_integrations.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
BASELINE_BYTES = (PROJECT / "data/audit/global-model-integration-v1/inventory.json").read_bytes()
BASELINE = json.loads(BASELINE_BYTES)
PLACEMENTS = {name: json.loads((PROJECT / "data/global-models" / name).read_text())
              for name in ("urban-placement.json", "chongming-placement.json")}
NEW_ID = "huangpu-new-wing-on-company"


def raw_glb():
    binary = struct.pack("<9f3H", 0, 0, 0, 1, 1, 0, 0, 0, 1, 0, 1, 2)
    binary += b"\0" * ((-len(binary)) % 4)
    doc = {"asset": {"version": "2.0"}, "buffers": [{"byteLength": len(binary)}],
           "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": 36},
                           {"buffer": 0, "byteOffset": 36, "byteLength": 6}],
           "accessors": [{"bufferView": 0, "componentType": 5126, "type": "VEC3", "count": 3},
                         {"bufferView": 1, "componentType": 5123, "type": "SCALAR", "count": 3}],
           "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1}]}],
           "nodes": [{"mesh": 0}], "scenes": [{"nodes": [0]}], "scene": 0}
    payload = json.dumps(doc).encode()
    payload += b" " * ((-len(payload)) % 4)
    return (struct.pack("<III", 0x46546C67, 2, 28 + len(payload) + len(binary))
            + struct.pack("<II", len(payload), 0x4E4F534A) + payload
            + struct.pack("<II", len(binary), 0x004E4942) + binary)


class IncrementalCatalogTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.project = self.root / "projects/shanghai"
        self.baseline = self.project / "data/audit/global-model-integration-v1/inventory.json"
        self.baseline.parent.mkdir(parents=True)
        self.baseline.write_bytes(BASELINE_BYTES)
        (self.project / "data/model-todo").mkdir()
        (self.project / "data/model-todo/queue.json").write_text('{"production_queue":[],"existing_models":[]}')
        (self.project / "data/model-viewers.json").write_text('[]')
        directory = self.project / "assets/models/candidates" / NEW_ID
        directory.mkdir(parents=True)
        assets = {}
        for variant, blob in {"raw": raw_glb(), "full": b"full-contract-fixture", "lod": b"lod-contract-fixture", "native": b"native-contract-fixture"}.items():
            filename = variant + (".blend" if variant == "native" else ".glb")
            (directory / filename).write_bytes(blob)
            assets[variant] = {"file": filename, "bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest(), "triangles": 1}
        self.manifest = directory / "manifest.json"
        self.manifest.write_text(json.dumps({"id": NEW_ID, "name": "新永安公司", "viewer_page": "new-wing-on-company.html", "assets": assets}))
        self.globals = patch.multiple(builder, ROOT=self.root, PROJECT=self.project, INVENTORY=self.baseline)
        self.globals.start()
        # Any attempt to fetch a historical asset fails this test immediately.
        self.git = patch.object(builder, "git", side_effect=AssertionError("unexpected historical asset read"))
        self.git.start()

    def tearDown(self):
        self.git.stop()
        self.globals.stop()
        self.temporary.cleanup()

    def increment(self):
        return builder.build_incremental_inventory([str(self.manifest)], "fixture-revision", "data/audit/new-wing-on-company-v1")

    def test_only_new_assets_are_verified_and_old_evidence_is_preserved(self):
        result = self.increment()
        self.assertEqual(result["records"][:len(BASELINE["records"])], BASELINE["records"])
        self.assertEqual(self.baseline.read_bytes(), BASELINE_BYTES)
        self.assertEqual(result["verification"]["current_run_added_files"], 4)
        self.assertEqual(result["candidate_manifest_count"], 33)
        self.assertEqual(result["new_city_model_count"], 31)
        self.assertEqual(result["resulting_city_count"], 71)
        self.assertEqual(result["records"][-1]["geometry"]["bounds_glb"], {"min": [0, 0, 0], "max": [1, 1, 1]})
        self.assertEqual(builder.normalized_manifest_path(self.manifest),
                         builder.normalized_manifest_path("assets/models/candidates/" + NEW_ID + "/manifest.json"))
        self.assertEqual(self.increment(), result, "a later --check can reproduce the same current inventory")

    def test_changed_asset_bytes_are_rejected(self):
        (self.manifest.parent / "full.glb").write_bytes(b"changed")
        with self.assertRaisesRegex(AssertionError, "Asset size differs"):
            self.increment()

    def test_existing_delivery_cannot_be_overwritten_by_an_increment(self):
        existing = BASELINE["records"][0]["id"]
        with self.assertRaisesRegex(AssertionError, "historical inventory"):
            builder.build_incremental_inventory([f"assets/models/candidates/{existing}/manifest.json"], "fixture", "data/audit/new")

    def test_polygon_rejected_before_it_can_make_the_runtime_drop_all_candidates(self):
        ring = [[121.47 + .0001 * math.cos(i * math.tau / 65), 31.23 + .0001 * math.sin(i * math.tau / 65)] for i in range(65)]
        ring.append(ring[0])
        with self.assertRaisesRegex(AssertionError, "Runtime ring contract"):
            builder.checked_geometry({"type": "Polygon", "coordinates": [ring]}, "new model hull")

    def test_catalogue_accepts_31_records_and_requires_the_new_placement(self):
        inventory = self.increment()
        current = self.project / "data/global-models/candidate-inventory.json"
        current.parent.mkdir(parents=True)
        current.write_text(json.dumps(inventory))
        for name, data in PLACEMENTS.items():
            (current.parent / name).write_text(json.dumps(data))
        with self.assertRaisesRegex(AssertionError, "Placement IDs"):
            builder.build_catalog(inventory, current)
        geometry = {"type": "Polygon", "coordinates": [[[121.4744,31.2368],[121.4745,31.2368],[121.4745,31.2369],[121.4744,31.2369],[121.4744,31.2368]]]}
        record = {"id": NEW_ID, "lng": 121.47445, "lat": 31.23685, "heading": 0, "scale": 1,
                  "overviewBearing": 180, "overviewPitch": 50,
                  "model_geometry_sha256": {"raw": inventory["records"][-1]["assets"]["raw"]["sha256"]},
                  "navigation": {"listed": False}, "collision_geometry": geometry,
                  "replacement_geometry": None, "source_feature_ids": {"building": [], "building_part": []},
                  "placement": {"status": "estimated", "note": "Test placement only"}}
        (current.parent / "additional-placement.json").write_text(json.dumps({"records": [record]}))
        # The two original derived corridor assets already have frozen SHA evidence.
        with patch.object(builder, "checked_asset", return_value=b"") as derived:
            catalog, checks = builder.build_catalog(inventory, current)
        self.assertEqual(derived.call_count, 2)
        self.assertEqual(len(catalog["models"]), 31)
        self.assertEqual(catalog["resulting_city_count"], 71)
        self.assertEqual(checks["unique_city_destinations"], 71)
        self.assertEqual(checks["listed_spawn_count"], 0)
        self.assertEqual(catalog["models"][-1]["id"], NEW_ID)
        self.assertEqual(catalog["models"][-1]["navigation"], {"listed": False})
        self.assertEqual(catalog["models"][-1]["overviewBearing"], 180)
        self.assertEqual(catalog["models"][-1]["overviewPitch"], 50)
        self.assertEqual(self.baseline.read_bytes(), BASELINE_BYTES)
        record["model_geometry_sha256"]["raw"] = "0" * 64
        (current.parent / "additional-placement.json").write_text(json.dumps({"records": [record]}))
        with patch.object(builder, "checked_asset", return_value=b""), self.assertRaisesRegex(AssertionError, "Stale placement geometry"):
            builder.build_catalog(inventory, current)


if __name__ == "__main__":
    unittest.main()
