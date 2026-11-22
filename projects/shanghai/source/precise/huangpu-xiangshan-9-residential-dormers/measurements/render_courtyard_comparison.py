"""Compare courtyard geometry in the supplied GLB with the licensed July 2018 photograph."""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1]
BACKEND = BASE / "huangpu-yuanmingyuan-apartments-street-front/measurements"
sys.path[:0] = [str(BACKEND), str(BASE / "huangpu-world-book-company-fuzhou-front/measurements")]
from photo_glb_raster import raster
from fuzhou_skylight import SurfaceCapture, horizon_shading


def geometry_view(model, path):
    """Keep only existing courtyard primitives; retain the original binary buffer verbatim."""
    data = model.read_bytes()
    length, tag = struct.unpack_from("<II", data, 12)
    assert tag == 0x4e4f534a
    document = json.loads(data[20:20+length])
    keep = {i for i, mat in enumerate(document["materials"]) if mat["name"].startswith("9 courtyard | ")}
    assert len(keep) == 8
    scene = document["scenes"][document.get("scene", 0)]
    nodes = []
    for node in scene["nodes"]:
        mesh = document["meshes"][document["nodes"][node]["mesh"]]
        mesh["primitives"] = [p for p in mesh["primitives"] if p["material"] in keep]
        if mesh["primitives"]:
            nodes.append(node)
    scene["nodes"] = nodes
    doc = json.dumps(document, ensure_ascii=False, separators=(",", ":")).encode()
    doc += b" " * (-len(doc) % 4)
    tail = data[20+length:]
    path.write_bytes(struct.pack("<4sIIII", b"glTF", 2, 20+len(doc)+len(tail), len(doc), tag) + doc + tail)


def detail_cameras():
    placement = json.loads((HERE / "courtyard-boundary-placement.json").read_text())
    profile = json.loads((HERE / "courtyard-pier-and-ironwork.json").read_text())
    start, end = placement["local_pier_centres_m"][1:]
    rods = start + (end-start) * np.array(profile["iron"]["measured_abscissae_m_on_winter_plane"]) / 4.83744
    scale = placement["horizontal_section_scale"]
    vertical = placement["vertical_section_scale"]
    unit = np.r_[placement["unit_x_in_building_xy"], 0.]
    inward = np.array([-unit[1], unit[0], 0.])
    up = np.array([0., 0., 1.])
    origin = np.array(placement["origin_in_building_xyz_m"])
    radius = min(.071, (rods[11]-rods[10]) / scale * .44)
    # A frontal detail of the same repeated casting from the complete second bay.
    result = {}
    for key, x, y, z, span, angle in [
        ("spear", rods[10], .018, 2.591, .224, .39),
        ("roundel", (rods[10]+rods[11])/2., .005, 2.382-.016-radius, .145, .21)
    ]:
        target = origin + x*unit + scale*y*inward + vertical*z*up
        forward = inward - angle*unit
        forward /= np.linalg.norm(forward)
        right = np.cross(forward, up)
        rot = np.stack((right, np.cross(forward, right), forward))
        distance = 10.
        eye = target - distance*forward
        focal = 700*distance/span
        k = np.array([[focal, 0., 350.], [0., focal, 350.], [0., 0., 1.]])
        result[key] = k @ np.column_stack((rot, -rot@eye))
    return result


def font(size, bold=False):
    weight = "Bold" if bold else "Regular"
    return ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-"+weight+".ttc", size, index=2)


def board(model, photograph, output):
    record = json.loads((HERE / "courtyard-pier-photo-controls.json").read_text())
    assert hashlib.sha256(photograph.read_bytes()).hexdigest() == record["photo_sha256"]
    source = Image.open(photograph).convert("RGB")
    canvas = Image.new("RGB", (1440, 1530), "#f5f2ec")
    draw = ImageDraw.Draw(canvas)
    ink, muted = "#32342e", "#595e53"
    def label(x, y, message, size=23, bold=False):
        draw.text((x, y), message, fill=ink if bold else muted, font=font(size, bold))
    def paste(img, x, y, size):
        canvas.paste(img.resize(size, Image.Resampling.LANCZOS), (x, y))
    label(35, 18, "香山路 9 号　院墙与铸铁栏杆", 44, True)
    label(37, 86, "黄浦区住宅　｜　2018 年 7 月街景与模型细部", 23)
    label(37, 136, "Antigng 摄影 · 原图局部", 24, True)
    label(740, 136, "同机位 · 模型院墙构件", 24, True)
    matrix = np.array(record["camera_matrix"])
    close = detail_cameras()
    meta = {"model_sha256": hashlib.sha256(model.read_bytes()).hexdigest(),
            "source": record["source"], "photo_sha256": record["photo_sha256"],
            "credit": record["credit"], "license_url": record["license_url"],
            "foreground_camera_controls": {"fit": record["fit"], "held_out": record["held_out"]},
            "views": {}}
    with tempfile.TemporaryDirectory() as temp:
        temp = Path(temp)
        filtered = temp / "courtyard.glb"
        geometry_view(model, filtered)
        so = temp / "raster.so"
        subprocess.run(["cc", "-O2", "-shared", "-fPIC", "-o", str(so), str(BACKEND/"photo_glb_raster.c"), "-lm"], check=True)
        lib = ctypes.CDLL(str(so))
        lib.shadow_depth.restype = lib.paint.restype = None
        light = np.array([-.40, -.67, .76], dtype="float32")
        light /= np.linalg.norm(light)
        def render(key, view, crop, width):
            capture = SurfaceCapture(lib, filtered)
            img, details = raster(filtered, capture, width, view, crop, light, None)
            img, amount = horizon_shading(img, capture.depth, view, crop)
            details["camera_matrix"] = view.tolist()
            details["mean_local_sky_occlusion"] = amount
            meta["views"][key] = details
            return img
        for key, crop, y in [("street", (0, 1940, 2900, 2988), 184), ("pier", (1720, 1995, 2855, 2988), 502)]:
            size = (663, round(663*(crop[3]-crop[1])/(crop[2]-crop[0])))
            paste(source.crop(crop), 37, y, size)
            paste(render(key, matrix, crop, 960), 740, y, size)
        label(37, 445, "近柱的灰色压顶、退台与方形凹板", 25, True)
        label(37, 1111, "栏尖卷叶", 24, True)
        label(737, 1111, "圆环中的四瓣花饰", 24, True)
        for key, source_crop, model_crop, x in [
            ("spear", (3149, 2427, 3291, 2661), (138, 0, 563, 700), 37),
            ("roundel", (3233, 2788, 3376, 2931), (0, 0, 700, 700), 737)
        ]:
            width=round(263*(source_crop[2]-source_crop[0])/(source_crop[3]-source_crop[1]))
            paste(source.crop(source_crop), x, 1155, (width, 263))
            paste(render(key, close[key], model_crop, 530), x+width+18, 1155, (width, 263))
            meta["views"][key]["reference_photo_crop_px"] = source_crop
        draw.line((37, 1445, 1401, 1445), fill="#c3c5b8", width=2)
        label(37, 1458, "下排各组左为原照，右为同式铸件的模型正面。　照片及裁图：Antigng，CC BY-SA 4.0。", 21)
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, quality=91, optimize=True, subsampling=0)
    output.with_suffix(".json").write_text(json.dumps(meta, ensure_ascii=False, indent=1)+"\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("model", "photograph", "output"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    board(args.model, args.photograph, args.output)
