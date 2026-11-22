"""Rebuild the detached gate at 522 Jiaozhou Road from its measured opening and photographic elevations."""

import hashlib
import json
import os
import sys
from pathlib import Path

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE))
sys.path.insert(0, str(SOURCE.parents[3] / "tools"))
from package_architectural_model import build
from gate_stone import PALETTE, add_stone, SPRING
from gate_iron import fan, leaf
from caution_sign import add_sign

ID = "jingan-gong-residence-jiaozhou-gate"
CLEAR_WIDTH = 3.62
SPRING_HEIGHT = 3.86
CROWN_RISE = 2.61


def height_m(z):
    if z <= SPRING:
        return SPRING_HEIGHT * z / SPRING
    return SPRING_HEIGHT + (z - SPRING) * CROWN_RISE / 0.735


META = dict(
    id=ID,
    name="龚氏花园住宅胶州路522号拱门",
    viewer_page="gong-residence-jiaozhou-gate.html",
    status="photo-informed-street-entrance",
    scope="胶州路522号临街独立院门的双砖墩、灰色勒脚、模制半圆拱、铁花扇面、两片铁门、三块铭牌与内侧圆形慢行牌。",
    reference_height_m=round(SPRING_HEIGHT + CROWN_RISE, 3),
    estimated="依2015年正面、2020年街景及2024年近照估算。门扇开启角为展示估计。",
    coordinate_convention="Local metres. X to the right looking in from the street, Y into the garden, Z up.",
    source_register="source/precise/" + ID + "/reference-review.json",
    photos_embedded=True,
    photographic_material="Three front lettering plaques from 522 Jiaozhou Rd. Shanghai, Livelikerw, 22 January 2015. Cropped, rectified and resized; CC BY-SA 4.0.",
    photo_source="https://commons.wikimedia.org/wiki/File:522_Jiaozhou_Rd._Shanghai.JPG",
    photo_license="CC BY-SA 4.0",
    photo_license_url="https://creativecommons.org/licenses/by-sa/4.0/",
)


def add_building(b, lod=False):
    add_stone(b, lod)
    add_sign(b, lod)
    fan(b, lod)
    leaf(b, -1, 82, lod)
    leaf(b, 1, 7, lod)
    for part in b.parts:
        part["vertices"] = [
            (x * CLEAR_WIDTH, y * CLEAR_WIDTH, height_m(z)) for x, y, z in part["vertices"]
        ]


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--blender", default="blender")
    parser.add_argument("--out", required=True, type=Path)
    opt, rest = parser.parse_known_args()
    os.environ["GONG_GATE_BLENDER"] = opt.blender
    sys.argv[1:] = [*rest, "--out", str(opt.out), "--blender", str(SOURCE / "blender_preview.py")]
    build(SOURCE, META, PALETTE, add_building)
    from plaque_samples import TILES
    import struct

    expected = hashlib.sha256((SOURCE / "entrance-plaques.png").read_bytes()).hexdigest()
    file = opt.out / "manifest.json"
    manifest = json.loads(file.read_bytes())
    for role in ("raw", "full", "lod"):
        data = (opt.out / manifest["assets"][role]["file"]).read_bytes()
        (length,) = struct.unpack_from("<I", data, 12)
        gltf = json.loads(data[20 : 20 + length])
        begin = 28 + length
        (image,) = gltf["images"]
        view = gltf["bufferViews"][image["bufferView"]]
        offset = begin + view.get("byteOffset", 0)
        assert hashlib.sha256(data[offset : offset + view["byteLength"]]).hexdigest() == expected
        assert sum(
            "baseColorTexture" in m["pbrMetallicRoughness"] for m in gltf["materials"]
        ) == len(TILES)
    manifest.update(
        geometry_license="MIT with photograph-derived lettering under CC BY-SA 4.0",
        photograph_derived_geometry="Black character on the yellow sign, traced from Livelikerw, 522 Jiaozhou Rd. Shanghai, CC BY-SA 4.0.",
        photos_embedded=True,
        photographic_texture_sha256=expected,
        photographic_texture_license="CC BY-SA 4.0",
        photographic_attribution=META["photographic_material"],
    )
    file.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
