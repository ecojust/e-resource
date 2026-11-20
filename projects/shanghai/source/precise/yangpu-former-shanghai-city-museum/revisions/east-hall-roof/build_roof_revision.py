"""Build the existing Jiangwan museum, adding only the observed eastern roof cover."""
import argparse
import json
from pathlib import Path
import sys
from shapely.geometry import Polygon
from shapely.ops import unary_union

REVISION = Path(__file__).resolve().parent
BASE = REVISION.parents[1] / "source"
sys.path.insert(0, str(BASE))
from build_model import ID, build as build_existing
from east_hall_roof import add_east_hall_cover


def build(lod=False):
    builder, metadata, features, probes = build_existing(lod)
    original = json.loads((BASE / "model-parameters.json").read_text())
    params = json.loads((REVISION / "roof-parameters.json").read_text())
    footprint = Polygon(original.get("modeled_footprint_enu", original["source_footprint_enu"])["coordinates"][0])
    retained = unary_union([Polygon(item["geometry_local_enu"]["coordinates"][0]) for item in original["retained_contact_sources"]])
    retained = retained.buffer(original["contact_trim_clearance_m"], join_style=2)
    builder.palette["cover panel"] = {"color": [.56, .63, .59], "roughness": .66}
    builder.palette["cover frame"] = {"color": [.68, .69, .65], "roughness": .72}
    features.append(add_east_hall_cover(builder, params, footprint.difference(retained), probes))
    metadata["east_hall_cover"] = params
    metadata["scope"] = (
        "Western historic museum range with present two-storey north/south wings and central yellow double-eaved tower, "
        "open red-column gallery, narrow high windows and octagonal entrance windows. The current eastern rear hall "
        "uses estimated plain walls and a contemporary shallow rectangular roof cover with observable cross divisions. "
        "Its date, materials, detailed elevations and interior are unverified. Courtyard links and other hospital sources "
        "remain separate. Not an exact 1930s reconstruction; interiors, exhibits, trees, banners and site surfaces excluded."
    )
    return builder, metadata, features, probes


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--lod", action="store_true")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    builder, metadata, features, probes = build(args.lod)
    suffix = "-lod" if args.lod else ""
    asset = args.out / (ID + ("-lod.glb" if args.lod else "-raw.glb"))
    builder.save(asset, metadata)
    for label, doc in [("features", features), ("surface-probes", probes)]:
        (args.out / (label + suffix + ".json")).write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n")
    print(asset)
