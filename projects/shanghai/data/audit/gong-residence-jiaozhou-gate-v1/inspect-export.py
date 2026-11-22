"""Render the brick piers, attributed plaques and pierced ironwork from the decoded geometry."""

import argparse, json, runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("decoded", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    cams = json.loads((HERE / "inspection-cameras.json").read_bytes())
    render = runpy.run_path(
        HERE.parent / "fifth-textile-warehouse-river-front-v1/inspect-export.py"
    )["render"]
    render(
        args.decoded,
        args.out,
        [(c["name"], c["eye"], c["target"], c["width_m"]) for c in cams],
        600,
        675,
    )
