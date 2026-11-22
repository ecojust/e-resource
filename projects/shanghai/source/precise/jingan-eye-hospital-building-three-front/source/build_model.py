"""Build the three-storey southwest bay of the former garden house at 805 North Shaanxi Road."""

from pathlib import Path
import argparse
import hashlib
import json
import os
import struct
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE))
sys.path.insert(0, str(SOURCE.parents[3] / "tools"))
from package_architectural_model import build
from bay import PALETTE
from crown import add_building

ID = "jingan-eye-hospital-building-three-front"
META = dict(
    id=ID,
    name="市眼科医院3号楼西南弧窗与山墙",
    viewer_page="eye-hospital-building-three-front.html",
    status="photo-informed-southwest-bay",
    scope="康定路院区3号楼院面西南端。重建底部两层弧形凸窗、三层曲栏阳台、凹入木门窗、双壁柱、弧肩山墙、球饰、墙上3号字与小型保护牌。中央雨棚、另一端和附楼保留。",
    reference_height_m=17.84,
    estimated="按两套2014年照片、建筑底图和航片估算；局部宽约6.48米，三层山墙顶17.84米。未作现场测量。",
    coordinate_convention="Local metres. X follows the courtyard face northeast, Y points into the house and Z is up.",
    source_register="source/precise/" + ID + "/reference-review.json",
    photos_embedded=True,
    photographic_material="Curtain RGB samples only. Legolas1024, 27 July 2014, CC BY-SA 4.0. Cropped, resized and arranged into an atlas.",
    photo_license="CC BY-SA 4.0",
    photo_license_url="https://creativecommons.org/licenses/by-sa/4.0/",
    photo_source="https://commons.wikimedia.org/wiki/File:Residence,_North_Shaanxi_Road,_Shanghai.jpg",
)


def verify_embedded_image(path, expected):
    data = path.read_bytes()
    json_size, tag = struct.unpack_from("<II", data, 12)
    assert tag == 0x4E4F534A
    gltf = json.loads(data[20 : 20 + json_size])
    bin_start = 28 + json_size
    assert len(gltf["images"]) == 1
    view = gltf["bufferViews"][gltf["images"][0]["bufferView"]]
    start = bin_start + view.get("byteOffset", 0)
    assert hashlib.sha256(data[start : start + view["byteLength"]]).hexdigest() == expected
    assert sum("baseColorTexture" in m["pbrMetallicRoughness"] for m in gltf["materials"]) == 5


if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--blender", default="blender")
    parser.add_argument("--out", type=Path, required=True)
    options, rest = parser.parse_known_args()
    os.environ["EYE_RESIDENCE_BLENDER"] = options.blender
    sys.argv[1:] = [
        *rest,
        "--out",
        str(options.out),
        "--blender",
        str(SOURCE / "blender_preview.py"),
    ]
    build(SOURCE, META, PALETTE, add_building)
    manifest_path = options.out / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    expected = hashlib.sha256((SOURCE / "curtain-samples.png").read_bytes()).hexdigest()
    for role in ("raw", "full", "lod"):
        verify_embedded_image(options.out / manifest["assets"][role]["file"], expected)
    manifest.update(
        photos_embedded=True,
        photographic_texture_sha256=expected,
        photographic_texture_license="CC BY-SA 4.0",
        photographic_attribution=META["photographic_material"],
    )
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
