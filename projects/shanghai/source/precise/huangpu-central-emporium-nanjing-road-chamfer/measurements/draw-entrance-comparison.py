"""Compare the 2022 corner-entrance photograph with the actual delivered GLB."""
import argparse
import hashlib
import io
import json
import runpy
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

PHOTO = "e3c32ee79cb3203236105cf72483c2e9df6d0013f52eba0b35a4ecedb52d9faf"


def projected_mesh(mesh, source, project):
    sys.path.insert(0, str(source))
    from photo_plane import H, D
    helper = project / "data/audit/postal-office-v1/independent-glb-review-helpers.py"
    faces, material_ids, _, info = runpy.run_path(helper)["load_triangles"](mesh)
    with mesh.open("rb") as stream:
        stream.seek(12)
        length, _ = struct.unpack("<II", stream.read(8))
        doc = json.loads(stream.read(length))
        _, _ = struct.unpack("<II", stream.read(8))
        start = stream.tell()
        palette = []
        for material in doc["materials"]:
            surface = material["pbrMetallicRoughness"]
            colour = np.array(surface.get("baseColorFactor", [1.] * 4)[:3])
            if "baseColorTexture" in surface:
                texture = doc["textures"][surface["baseColorTexture"]["index"]]
                im = doc["images"][texture["source"]]
                if "bufferView" in im:
                    view = doc["bufferViews"][im["bufferView"]]
                    stream.seek(start + view.get("byteOffset", 0))
                    with Image.open(io.BytesIO(stream.read(view["byteLength"]))) as tex:
                        tex.thumbnail((96, 96))
                        srgb = np.asarray(tex.convert("RGB"), dtype=float) / 255.
                        colour *= np.mean(np.where(srgb <= .04045, srgb / 12.92,
                                                   ((srgb + .055) / 1.055) ** 2.4), axis=(0,1))
            palette.append(colour)
    camera = np.linalg.solve(np.column_stack((H[:,0], D, H[:,1])), -H[:,2])
    n = np.cross(faces[:,1] - faces[:,0], faces[:,2] - faces[:,0])
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1.e-12)
    front = np.einsum("ij,ij->i", n, camera - faces[:,0]) > 0
    double = np.array([m.get("doubleSided", False) for m in doc["materials"]])[material_ids]
    visible = front | double
    light = np.array([-.57,-.7,.75])
    light /= np.linalg.norm(light)
    # Two-sided materials receive light on their visible side.
    lit = .49 + .69 * np.maximum(0., (n @ light) * np.where(front, 1., -1.))
    colour = np.array(palette)[material_ids] * lit[:,None]
    colour = np.where(colour <= .0031308, 12.92 * colour, 1.055 * colour ** (1/2.4) - .055)
    xyz = faces.reshape(-1, 3)
    q = np.column_stack((xyz[:,0], xyz[:,2], np.ones(len(xyz)))) @ H.T + xyz[:,1,None] * D
    if q[:,2].min() * q[:,2].max() <= 0:
        raise ValueError("Geometry crosses the camera plane")
    return ((q[:,:2] / q[:,2,None]).reshape(-1,3,2)[visible],
            1. / np.abs(q[:,2].reshape(-1,3)[visible]),
            np.rint(np.clip(colour[visible], 0, 1) * 255).astype("uint8"), info)


def draw_mesh(scene, box, size):
    xy, depth, colour, _ = scene
    width, height = size
    low = np.array(box[:2])
    p = (xy - low) * (np.array(size) / (np.array(box[2:]) - low))
    lower = np.floor(p.min(axis=1)).astype(int)
    upper = np.ceil(p.max(axis=1)).astype(int)
    keep = np.flatnonzero((upper[:,0] >= 0) & (upper[:,1] >= 0) &
                          (lower[:,0] < width) & (lower[:,1] < height))
    canvas = np.full((height,width,3), (225,224,216), dtype="uint8")
    zbuf = np.full((height,width), -np.inf)
    for k in keep:
        x0,y0 = np.maximum(lower[k], (0,0))
        x1,y1 = np.minimum(upper[k], (width-1,height-1))
        if x0 > x1 or y0 > y1:
            continue
        (ax,ay),(bx,by),(cx,cy) = p[k]
        denom = (by-cy)*(ax-cx) + (cx-bx)*(ay-cy)
        if abs(denom) < 1e-9:
            continue
        y,x = np.ogrid[y0+.5:y1+1.5, x0+.5:x1+1.5]
        a = ((by-cy)*(x-cx) + (cx-bx)*(y-cy)) / denom
        b = ((cy-ay)*(x-cx) + (ax-cx)*(y-cy)) / denom
        c = 1-a-b
        inv = a*depth[k,0] + b*depth[k,1] + c*depth[k,2]
        old = zbuf[y0:y1+1,x0:x1+1]
        hit = (np.minimum(np.minimum(a,b),c) >= -1e-8) & (inv > old)
        old[hit] = inv[hit]
        canvas[y0:y1+1,x0:x1+1][hit] = colour[k]
    return Image.fromarray(canvas)


def comparison(photo, scene, output):
    board = Image.new("RGB",(1100,823),"#f5f1e8")
    pen = ImageDraw.Draw(board)
    def text(x,y,line,pt,bold=False):
        weight = "Bold" if bold else "Regular"
        name = f"/usr/share/fonts/opentype/noto/NotoSansCJK-{weight}.ttc"
        pen.text((x,y),line,font=ImageFont.truetype(name,pt,index=2),fill="#302f2c")
    text(35,15,"中央商场的转角入口",34,True)
    text(36,69,"四川中路 355 号　｜　南京东路转角",19)
    pen.line((35,110,1064,110),fill="#aaa18e")
    for x,label in [(36,"2022 年街面照片"),(565,"按原照机位绘制的模型")]:
        text(x,122,label,20,True)
    with Image.open(photo) as im:
        if im.getexif().get(274,1) not in (0, 1):
            raise ValueError("Expected upright source")
        scale = im.width / 690.
        original = np.array(im.size,dtype=float)
        im.draft("RGB",(3200,2200))
        small = np.array(im.size,dtype=float) / original
        for region, y, h in [((173,86,383,252),166,399),((206,208,345,243),624,128)]:
            box = np.array(region,dtype=float) * scale
            native = np.rint(box * np.tile(small,2)).astype(int)
            size = (503,h)
            board.paste(im.crop(tuple(native)).resize(size,Image.Resampling.LANCZOS),(36,y))
            board.paste(draw_mesh(scene,box,size),(565,y))
    text(35,575,"门额四字「中央商場」",21,True)
    pen.line((35,773,1064,773),fill="#aaa18e")
    text(36,784,"摄影 Shwangtianyuan，2022 年 8 月 28 日。原照裁自 Wikimedia Commons。本图板采用 CC BY-SA 4.0。",15)
    board.save(output,quality=91,subsampling=0,optimize=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("photo","mesh","source","project","output"):
        parser.add_argument("--"+name,type=Path,required=True)
    args = parser.parse_args()
    with args.photo.open("rb") as stream:
        if hashlib.file_digest(stream,"sha256").hexdigest() != PHOTO:
            raise ValueError("Unexpected original photograph")
    scene = projected_mesh(args.mesh,args.source,args.project)
    comparison(args.photo,scene,args.output)
    print(scene[-1]["sha256"],hashlib.sha256(args.output.read_bytes()).hexdigest())

