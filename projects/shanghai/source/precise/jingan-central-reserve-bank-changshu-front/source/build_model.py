"""Rebuild the central entrance block of the former Central Reserve Bank house, 10 Lane 100 Changshu Road."""

from pathlib import Path
import argparse, hashlib, json, os, sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE))
sys.path.insert(0, str(SOURCE.parents[3] / "tools"))
from package_architectural_model import build
from stonework import (
    PALETTE,
    HALF,
    TERRACE,
    BAYS,
    storey_windows,
    return_windows,
    walls,
    crown,
    podium,
)
from balconies import portal, railing
from joinery import sash, door

ID = "jingan-central-reserve-bank-changshu-front"
META = dict(
    id=ID,
    name="中央储备银行常熟路旧址正门与三跨石阳台",
    viewer_page="central-reserve-bank-changshu-front.html",
    status="photo-informed-southeast-entrance-block",
    scope="花园朝向的东南正门中央三跨，含石门套、两层六组透空石窗栏、折面中央阳台、局部返面、上檐和短压顶、门前石阶。东西两翼、后楼、院门、室内与屋顶花园留待后续。",
    reference_height_m=20.45,
    estimated="三跨宽16.11米来自原城与OSM相合的凸部足印。檐口、门窗、栏杆与局部压顶按照片透视估算，地台高、阳台深度与背侧估计，未经现场测量。",
    coordinate_convention="Local metres. Positive X heads 71.53 degrees along the garden face, positive Y heads 341.53 degrees into the house, and Z is up.",
    source_register="source/precise/" + ID + "/reference-review.json",
    photos_embedded=True,
    photographic_material="Five small window textile and reflection crops from Antigng, 7 February 2018. Resized and assembled into one atlas, CC BY-SA 4.0.",
    photo_license="CC BY-SA 4.0",
    photo_license_url="https://creativecommons.org/licenses/by-sa/4.0/",
    photo_source="https://commons.wikimedia.org/wiki/File:常熟路中央储备银行旧址.jpg",
)


def add_building(builder, lod):
    walls(builder, lod)
    podium(builder, lod)
    for floor, i, x, width, sill, head in storey_windows():
        mapper = lambda u, z, d, x=x: (x + u, -d, z)
        sash(builder, mapper, floor, i, width, sill, head, False, lod)
    for floor, u, width, sill, head in return_windows():
        mapper = lambda v, z, d, u=u: (HALF + d, u + v, z)
        sash(builder, mapper, floor, 2, width, sill, head, True, lod)
    for level in (1, 2):
        for i, x in enumerate(BAYS):
            railing(builder, level, i, x, lod)
    door(builder, lod)
    portal(builder, lod)
    crown(builder, lod)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--blender", default="blender")
    parser.add_argument("--out", required=True, type=Path)
    opts, args = parser.parse_known_args()
    os.environ["CHANGSHU_RESIDENCE_BLENDER"] = opts.blender
    sys.argv[1:] = [*args, "--out", str(opts.out), "--blender", str(SOURCE / "blender_preview.py")]
    build(SOURCE, META, PALETTE, add_building)
    path = opts.out / "manifest.json"
    manifest = json.loads(path.read_bytes())
    manifest.update(
        photos_embedded=True,
        photographic_texture_sha256=hashlib.sha256(
            (SOURCE / "window-samples.png").read_bytes()
        ).hexdigest(),
        photographic_texture_license=META["photo_license"],
        photographic_attribution=META["photographic_material"],
    )
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
