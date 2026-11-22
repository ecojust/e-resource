"""Export the photographically measured casement and sill components."""
import argparse
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
PROJECT = next(root for root in SOURCE.parents if (root / 'tools/package_architectural_model.py').is_file())
sys.path.insert(0, str(PROJECT / 'source/precise/hongkou-general-post-office/source/common'))
from photo_architecture import Builder
from wing_casements import PALETTE, add_windows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--lod", action="store_true")
    args = parser.parse_args()
    building = Builder(PALETTE)
    add_windows(building, args.lod)
    building.save(args.output, {
        "name": "圆明园公寓东立面两翼矩窗与石窗台",
        "source": "Livelikerw, Yuanmingyuan Apartments Rockbund Shanghai.JPG (27 January 2014).",
        "photo_source": "https://commons.wikimedia.org/wiki/File:Yuanmingyuan_Apartments_Rockbund_Shanghai.JPG",
        "geometry_license": "CC BY-SA 4.0", "photo_license": "CC BY-SA 3.0",
        "photographs_embedded": False,
    })
    print(len(building.parts), sum(len(p['triangles']) for p in building.parts), args.output)
