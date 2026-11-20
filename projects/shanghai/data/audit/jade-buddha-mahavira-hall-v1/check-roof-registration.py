"""Recompute three dated image measurements against the exact city feature table."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
from shapely.geometry import Point, Polygon, shape

AUDIT = Path(__file__).resolve().parent
SOURCE = AUDIT.parents[2] / "source/precise/putuo-jade-buddha-mahavira-hall"
cli = argparse.ArgumentParser(description=__doc__)
cli.add_argument("feature_table", type=Path)
cli.add_argument("output", type=Path)
args = cli.parse_args()

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

registration = SOURCE / "roof-registration.json"
source = json.loads((SOURCE / "footprint-review.json").read_bytes())
study = json.loads(registration.read_bytes())
table_sha = next(v["sha256"] for v in source["frozen_bindings"] if v["repository_path"].endswith("feature-table.json.gz"))
assert sha(args.feature_table) == table_sha
rows = json.loads(gzip.decompress(args.feature_table.read_bytes()))["features"]
frame = study["frame"]
origin_x, origin_y = frame["origin_pixel_xy"]
u, v = frame["step_x"], frame["step_y"]
col, row = frame["base_tile"]
world_size = 256 * 2 ** frame["zoom"]

def coordinate(xy):
    x, y = xy
    px = col * 256 + origin_x + x * u[0] + y * v[0]
    py = row * 256 + origin_y + x * u[1] + y * v[1]
    return (px / world_size * 360 - 180, math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * py / world_size)))))

center_lng,center_lat = coordinate([223,236.5])
def metres(point):
    lng,lat=point
    return ((lng-center_lng)*111195.08*math.cos(math.radians(center_lat)),(lat-center_lat)*111195.08)

target = next(r for r in rows if r["localId"] == source["owner"]["feature_local_id"])
assert target["geometry"] == source["source_outline"] and target["localId"] == 979
native = Polygon([metres(c) for c in target["geometry"]["coordinates"][0]])
results = {}
old_mid = None
for released, reading in study["periods"].items():
    center = coordinate(reading["roof_center"])
    assert math.dist(center, reading["roof_center_wgs84"]) < 1e-9
    owners = [r["localId"] for r in rows if shape(r["geometry"]).covers(Point(center))]
    expected = [979] if reading["capture"] else []
    assert owners == expected == reading["features_at_center"]
    ends = [metres(coordinate(pt)) for pt in reading["front"]]
    midpoint = tuple((a+b)/2 for a,b in zip(*ends))
    if old_mid is None: old_mid = midpoint
    delta = tuple(a-b for a,b in zip(midpoint,old_mid))
    shift = math.hypot(*delta)
    assert abs(shift-reading["movement_from_2016_front_midpoint"]["length_m"]) < .01
    projected = None
    if reading["capture"]:
        assert delta[0] < 0 < delta[1] and 28 < shift < 32
        providers = reading["imagery_metadata"]["features"]
        assert any(str(row["SRC_DATE"])==reading["capture"].replace("-","") and row["MaxMapLevel"]==19 for row in providers)
        bounds = Polygon([metres(coordinate(p)) for p in reading["approximate_eave_envelope"]])
        projected = bounds.intersection(native).area / bounds.union(native).area
        assert abs(projected-reading["iou_979"]) < .0001
    results[released] = {"acquired":reading["capture"],"owners_at_roof_center":owners,"front_eave_span_m":math.dist(*ends),
                         "east_north_from_old_m":delta,"distance_m":shift,"estimated_eave_iou":projected}
args.output.write_text(json.dumps({"records_sha256":table_sha,"study_sha256":sha(registration),
    "script_sha256":sha(Path(__file__)),"periods":results,"passed":True},indent=2)+"\n")
