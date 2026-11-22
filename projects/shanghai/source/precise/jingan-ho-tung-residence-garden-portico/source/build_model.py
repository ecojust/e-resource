"""Rebuild the garden portico of Ho Tung's former Shanghai residence, 457 North Shaanxi Road."""

from pathlib import Path
import argparse, os, sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE))
sys.path.insert(0, str(SOURCE.parents[3] / "tools"))
from package_architectural_model import build
from ionic_garden import PALETTE, AXES, ionic_column, entablature, parapet
from garden_doors import platform, masonry, fenestration, balcony

ID = "jingan-ho-tung-residence-garden-portico"
META = dict(
    id=ID,
    name="何东上海公馆花园侧四柱门廊",
    viewer_page="ho-tung-garden-portico.html",
    status="photo-informed-garden-portico",
    reference_height_m=8.68,
    scope="南向花园中央门廊的四根爱奥尼柱、花园弧阶、两层门窗、内凹折面铁阳台、返折檐口与石栏。接至两侧短返面。",
    estimated="用三张花园立面照片拟合柱距、门距、门墙退进与券顶，以原城与OpenStreetMap建筑轮廓校定比例。细部断面、栏杆重复数和遮挡区按可辨轮廓估算。",
    coordinate_convention="Metres. Positive X follows a bearing of 64.30022 degrees. Positive Y points into the house at 334.30022 degrees. Z points up. The column centreline is at Y=0.30.",
    source_register="source/precise/" + ID + "/reference-review.json",
    photos_embedded=False,
    third_party_models_embedded=False,
)


def add_building(builder, lod):
    platform(builder, lod)
    masonry(builder, lod)
    fenestration(builder, lod)
    balcony(builder, lod)
    for i, x in enumerate(AXES):
        ionic_column(builder, i, x, lod)
    entablature(builder, lod)
    parapet(builder, lod)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--blender", default="blender")
    options, remaining = parser.parse_known_args()
    os.environ["HO_TUNG_PORTICO_BLENDER"] = options.blender
    sys.argv[1:] = [*remaining, "--blender", str(SOURCE / "blender_preview.py")]
    build(SOURCE, META, PALETTE, add_building)
