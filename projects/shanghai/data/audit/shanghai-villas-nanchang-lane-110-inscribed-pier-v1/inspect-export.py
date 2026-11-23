"""Rasterize the actually decoded freestanding piers through its documented inspection cameras."""

from pathlib import Path
import argparse
import json
import runpy

HERE = Path(__file__).resolve().parent
CAMERAS = (
    HERE.parents[2] / "source/precise/huangpu-shanghai-villas-nanchang-lane-110-inscribed-pier/source/cameras.json"
)
renderer = runpy.run_path(HERE.parent / "nanshi-bank-southeast-corner-v1/inspect-export.py")[
    "render"
]
renderer.__globals__["VIEWS"] = json.loads(CAMERAS.read_bytes())
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("decoded_glb", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    renderer(args.decoded_glb, args.out)
