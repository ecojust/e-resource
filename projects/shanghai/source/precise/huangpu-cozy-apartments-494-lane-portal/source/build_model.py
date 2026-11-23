"""Rebuild the stone portal and paired upper windows at Lane 494, Middle Huaihai Road."""

from pathlib import Path
import argparse
import json
import os
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE))
sys.path.insert(0, str(SOURCE.parents[3] / "tools"))
from package_architectural_model import build
from portal_stone import STONE, JOINT, EDGE, FACE, LETTER, add_portal
from lane_gate import IRON, PAINT, PLASTER, DADO, PAVING, CEILING, GLASS, opening
from upper_front import BRICK, MORTAR, SILL, PIPE, PANE, upper_front, street_plates

ID = "huangpu-cozy-apartments-494-lane-portal"
DIMENSIONS = json.loads((SOURCE / "portal_dimensions.json").read_text())
META = dict(
    id=ID,
    name="康绥公寓淮海中路494弄入口与二层窗",
    viewer_page="cozy-apartments-lane-portal.html",
    status="photo-informed-lane-portal",
    reference_height_m=DIMENSIONS["wall_top"],
    scope="康绥公寓淮海中路494弄入口的石框、门额四字、通道前段的两扇铁门，以及上方红砖墙和一对长方窗。",
    estimated="依据2022年人民网刊发的入口照片和街对面三个拍摄位置拟合外宽、洞宽、门楣及窗台标高。门扇转角、石材分缝、铁件断面和背后的前段通道进深为近似值。门额采用开放字体表现原照片可读的四字。",
    coordinate_convention="Metres. X runs along the street at 64.653624 degrees, Y into the passage at 334.653624 degrees, Z up. The street opening centre is X=0, stone face Y=0.",
    source_register="source/precise/" + ID + "/reference-review.json",
    photos_embedded=False,
    third_party_models_embedded=False,
)


def surface(rgb, roughness, metallic=0):
    def linear(x):
        s = x / 255
        return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4

    return dict(color=[linear(v) for v in rgb], roughness=roughness, metallic=metallic)


PALETTE = {
    STONE[0]: surface((171, 162, 143), 0.82),
    STONE[1]: surface((163, 157, 144), 0.84),
    STONE[2]: surface((176, 166, 148), 0.84),
    JOINT: surface((119, 118, 107), 0.93),
    EDGE: surface((182, 173, 152), 0.79),
    FACE: surface((136, 149, 145), 0.85),
    LETTER: surface((130, 56, 43), 0.66, 0.08),
    IRON: surface((49, 52, 48), 0.54, 0.37),
    PAINT: surface((57, 60, 55), 0.62, 0.10),
    PLASTER: surface((194, 191, 171), 0.90),
    DADO: surface((78, 82, 68), 0.86),
    CEILING: surface((173, 176, 164), 0.91),
    PAVING: surface((132, 132, 121), 0.92),
    GLASS: surface((78, 103, 98), 0.24, 0.21),
    PANE: surface((62, 77, 75), 0.29, 0.15),
    BRICK[0]: surface((141, 86, 73), 0.92),
    BRICK[1]: surface((127, 77, 65), 0.92),
    BRICK[2]: surface((154, 98, 84), 0.90),
    MORTAR: surface((124, 112, 99), 0.95),
    SILL: surface((94, 90, 79), 0.83),
    PIPE: surface((170, 170, 153), 0.62, 0.30),
    "Ochre street plate": surface((187, 148, 70), 0.72),
    "Pale enamel plate": surface((187, 181, 159), 0.64),
}


def add_building(b, lod):
    add_portal(b, DIMENSIONS, lod)
    opening(b, DIMENSIONS, lod)
    upper_front(b, DIMENSIONS, lod)
    street_plates(b, DIMENSIONS)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--blender", default="blender")
    opts, rest = parser.parse_known_args()
    os.environ["COZY_LANE_BLENDER"] = opts.blender
    sys.argv[1:] = [*rest, "--blender", str(SOURCE / "blender_preview.py")]
    build(SOURCE, META, PALETTE, add_building)
