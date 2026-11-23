"""Build the two inscribed stone piers at Shanghai Villas from the February 2020 frontage."""

import argparse
import json
import os
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE))
sys.path.insert(0, str(SOURCE.parents[3] / "tools"))
from package_architectural_model import build
from stone_piers import FRAME, FIELD, INK, GRANITE, CROWN, add_pier
from lane_ironwork import IRON, METAL, SHEET, NOTICE, PAPER, add_leaf
from numbered_wall import WALL, COPING, NUMERAL, TIMBER, SUPPORT, GREEN, WHITE, make_wall, lane_plate

ID = "huangpu-shanghai-villas-nanchang-lane-110-inscribed-pier"
D = json.loads((SOURCE / "pier_dimensions.json").read_bytes())
META = dict(
    id=ID, name="上海别墅南昌路110弄双题名石柱与112号院墙",
    viewer_page="shanghai-villas-inscribed-pier.html", status="measured-from-nanchang-road-panoramas",
    reference_height_m=D["height"],
    scope="南昌路110弄街面的双题名石柱、敞口铁门、西接112号的短院墙和水平木条。依据2020年2月的现场外观。",
    estimated="双柱位置与尺度分取同日三处街景。柱身进深、短墙厚度、铁件截面及门扇开启角为近似值。题字采用可编辑的开放字体近似原笔画。",
    coordinate_convention=f"Metres. The origin is the midpoint between the street faces of the two piers. X follows the frontage at {D['axis_bearing']:.4f} degrees clockwise from north, Y is towards the lane and Z is up.",
    source_register="source/precise/" + ID + "/reference-review.json",
    photos_embedded=False, third_party_models_embedded=False
)


def surface(rgb, roughness, metallic=0.0):
    def linear(v):
        u = v / 255
        return u / 12.92 if u <= 0.04045 else ((u + 0.055) / 1.055) ** 2.4
    return {"color": [linear(c) for c in rgb], "roughness": roughness, "metallic": metallic}


PALETTE = {
    FRAME: surface((161, 158, 148), 0.82), FIELD: surface((126, 128, 124), 0.87),
    INK: surface((45, 48, 46), 0.92), GRANITE: surface((141, 142, 135), 0.84),
    CROWN: surface((166, 161, 150), 0.83), IRON: surface((49, 54, 48), 0.61, 0.47),
    SHEET: surface((62, 65, 57), 0.66, 0.28), METAL: surface((64, 69, 60), 0.57, 0.49),
    NOTICE: surface((193, 186, 169), 0.67, 0.17), PAPER: surface((165, 165, 171), 0.90),
    WALL: surface((146, 146, 137), 0.90), COPING: surface((170, 166, 153), 0.82),
    NUMERAL: surface((56, 56, 52), 0.89), TIMBER[0]: surface((105, 76, 59), 0.87),
    TIMBER[1]: surface((117, 85, 65), 0.87), SUPPORT: surface((64, 62, 53), 0.82),
    GREEN: surface((42, 93, 79), 0.53, 0.17), WHITE: surface((213, 213, 191), 0.67),
    "Pale lane information plate": surface((183, 184, 171), 0.71, 0.1),
}


def add_building(builder, lod):
    separation = D["centre_distance"]
    clear = separation - D["width"]
    for side, direction in (("West", -1), ("East", 1)):
        add_pier(builder, direction * separation / 2, D, side, lod)
        hinge = (direction * (clear / 2 - 0.025), D["gate_hinge_recess"])
        angle = D["west_open_deg" if direction < 0 else "east_open_deg"]
        add_leaf(builder, hinge, -direction, clear / 2 - 0.04, angle, D, lod, side + " iron leaf")
    make_wall(builder, D, lod)
    lane_plate(builder, D, lod)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--blender", default="blender")
    opts, rest = parser.parse_known_args()
    os.environ["SHANGHAI_VILLAS_BLENDER"] = opts.blender
    sys.argv[1:] = [*rest, "--blender", str(SOURCE / "blender_preview.py")]
    build(SOURCE, META, PALETTE, add_building)
