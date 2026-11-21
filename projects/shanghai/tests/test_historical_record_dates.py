"""Chronology and different source media for the city's historical site records."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import runpy
import unittest

BUILDER = Path(__file__).resolve().parents[1] / "tools/build_candidate_city_integrations.py"
CATALOG = runpy.run_path(str(BUILDER))
PERIOD = {"kind": "archival-facade", "listed_year": 1994, "approximate_loss_year": 1996,
          "evidence_kind": "published-drawing", "evidence_years": [2015, 2020]}


class HistoricalRecordDates(unittest.TestCase):
    def test_published_drawing_and_photographed_building(self):
        check = CATALOG["validate_historical_period"]
        check(PERIOD, "published")
        check({"kind": "archival-facade", "building_year": 1933, "evidence_years": [1934, 1937]}, "photographed")

    def test_ambiguous_or_invalid_evidence(self):
        check = CATALOG["validate_historical_period"]
        for changes in ({"listed_year": True}, {"listed_year": 1997}, {"building_year": 1994},
                        {"approximate_loss_year": None}, {"evidence_kind": "photographs"},
                        {"evidence_years": [2020, 2015]}, {"evidence_years": [2015, 3000]}):
            with self.subTest(changes=changes), self.assertRaises(AssertionError):
                check({**PERIOD, **changes}, "invalid")
        with self.assertRaises(AssertionError):
            check({k: v for k, v in PERIOD.items() if k != "listed_year"}, "undated")

    def test_original_delivery_status_must_match_drawing_evidence(self):
        ident = "archival-roof"
        folder = f"assets/models/candidates/{ident}"
        assets = {kind: {"file": f"{folder}/{ident}-{kind}.glb", "sha256": str(index) * 64}
                  for index, kind in enumerate(("raw", "web", "lod"), 1)}
        item = {"id": ident, "name": "Archival roof", "districtId": "310105", "district": "长宁区",
                "individual_page": "archival-roof-history.html", "manifest": f"{folder}/manifest.json", "assets": assets,
                "original_delivery_status": "historical-illustration-informed-facade-study"}
        placement = {"id": ident, "lng": 121.37, "lat": 31.19, "historical_view": PERIOD, "navigation": {"listed": False},
                     "collision_geometry": None, "replacement_geometry": None,
                     "source_feature_ids": {"building": [], "building_part": []},
                     "model_geometry_sha256": {kind: asset["sha256"] for kind, asset in assets.items()}}
        make_record = CATALOG["historical_site_record"]
        with TemporaryDirectory() as tmp, patch.dict(make_record.__globals__, {"PROJECT": Path(tmp)}):
            (Path(tmp) / item["individual_page"]).write_text(f"showCandidateAssetViewer('{ident}')")
            self.assertEqual(make_record(item, placement)["historical_view"], PERIOD)
            with self.assertRaises(AssertionError):
                make_record({**item, "original_delivery_status": "historical-photo-informed-facade-study"}, placement)
            with self.assertRaises(AssertionError):
                make_record(item, {**placement, "collision_geometry": {"type": "Polygon"}})


if __name__ == "__main__":
    unittest.main()
