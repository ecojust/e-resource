"""Render three window crops with the real 2014 camera and photographed aperture masks."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from verify_wing_casements import decode, openings
from east_photo_plane import CAMERAS, pixel

RANGES = [
    ("阁楼四列小窗与通长窗台", (1800, 495, 2550, 940)),
    ("中层窗及三段挑出的窗台", (1690, 985, 2590, 1528)),
    ("下层双扇与分格上亮子", (1692, 1638, 2123, 2185)),
]


def crop_model(model, rectangle, width):
    faces, labels, gltf = model
    u0, v0, u1, v1 = rectangle
    scale = width / (u1 - u0)
    height = round((v1 - v0) * scale)
    m = CAMERAS['2014_oblique']
    camera = faces @ m[:, :3].T + m[:, 3]
    if camera[:, :, 2].min() <= 0:
        raise ValueError("A window crosses the camera plane")
    projected = (camera[:, :, :2] / camera[:, :, 2:] - [u0, v0]) * scale
    backdrop = np.full((height, width, 3), [220, 218, 212], 'uint8')
    depth = np.zeros((height, width))
    # The neutral mount masks the exterior edges of a recessed frame at the
    # registered masonry openings. Only the actual GLB supplies visible detail.
    yy, xx = np.mgrid[0:height, 0:width]
    H = np.column_stack([m[:, 0], m[:, 2], m[:, 3]])
    rays = np.stack([u0 + (xx + .5) / scale, v0 + (yy + .5) / scale,
                     np.ones_like(xx)], axis=-1) @ np.linalg.inv(H).T
    xw, zw = rays[:, :, 0] / rays[:, :, 2], rays[:, :, 1] / rays[:, :, 2]
    open_mask = np.zeros((height, width), dtype=bool)
    for row in openings():
        open_mask |= (xw > row['left']) & (xw < row['right']) & (zw > row['bottom']) & (zw < row['top'])
    wall_depth = m[2, 0] * xw + m[2, 2] * zw + m[2, 3]
    depth[~open_mask] = 1 / wall_depth[~open_mask]
    backdrop[open_mask] = [150, 148, 144]
    colours = np.asarray([q['pbrMetallicRoughness']['baseColorFactor'][:3] for q in gltf['materials']])
    direction = np.asarray([-.24, -.83, .51])
    direction /= np.linalg.norm(direction)
    for q, plane, xyz, mat in zip(projected, camera, faces, labels):
        lo = np.maximum([0, 0], np.floor(q.min(axis=0)).astype(int))
        hi = np.minimum([width - 1, height - 1], np.ceil(q.max(axis=0)).astype(int))
        if np.any(hi < lo):
            continue
        ab, ac = q[1] - q[0], q[2] - q[0]
        det = ab[0] * ac[1] - ac[0] * ab[1]
        if abs(det) < 1e-10:
            continue
        sy = slice(lo[1], hi[1] + 1)
        sx = slice(lo[0], hi[0] + 1)
        dx, dy = xx[sy, sx] + .5 - q[0, 0], yy[sy, sx] + .5 - q[0, 1]
        s, t = (dx * ac[1] - dy * ac[0]) / det, (ab[0] * dy - ab[1] * dx) / det
        inv = (1 - s - t) / plane[0, 2] + s / plane[1, 2] + t / plane[2, 2]
        mask = (s >= 0) & (t >= 0) & (s + t <= 1) & (inv > depth[sy, sx])
        if not mask.any():
            continue
        normal = np.cross(xyz[1] - xyz[0], xyz[2] - xyz[0])
        normal /= np.linalg.norm(normal)
        diffuse = .74 + .30 * max(0, normal @ direction) + .07 * normal[2]
        linear = np.clip(colours[mat] * diffuse, 0, 1)
        srgb = np.where(linear <= .0031308, 12.92 * linear, 1.055 * linear ** (1 / 2.4) - .055)
        backdrop[sy, sx][mask] = np.rint(255 * srgb).astype('uint8')
        depth[sy, sx][mask] = inv[mask]
    return Image.fromarray(backdrop)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('model', type=Path)
    p.add_argument('photo', type=Path)
    p.add_argument('output', type=Path)
    args = p.parse_args()
    if hashlib.sha256(args.photo.read_bytes()).hexdigest() != 'efc50b1013bf893fce9273984440ad952763564eb387088dc40c5835848f65f3':
        raise ValueError("Expected the original Livelikerw 2014 photograph")
    model = decode(args.model)
    real = Image.open(args.photo)
    panel = Image.new('RGB', (1272, 840), (248, 246, 241))
    draw = ImageDraw.Draw(panel)
    fonts = Path('/usr/share/fonts/opentype/noto')
    def font(n, bold=False):
        return ImageFont.truetype(str(fonts / ('NotoSansCJK-Bold.ttc' if bold else 'NotoSansCJK-Regular.ttc')), n, index=2)
    draw.text((27, 16), '圆明园公寓 · 东立面窗扇与石窗台', font=font(34, True), fill='#302e2b')
    draw.text((29, 73), '上海市黄浦区圆明园路115号　｜　2014年1月27日街景与同机位构件', font=font(18), fill='#54504c')
    for i, (name, box) in enumerate(RANGES):
        x = 27 + i * 410
        w = 392
        h = 260
        pic = real.crop(box)
        model_image = crop_model(model, box, w * 2)
        draw.text((x, 120), name, font=font(19, True), fill='#34302d')
        for j, im in enumerate((pic, model_image)):
            # The original rectangle and its aspect ratio are shared by each pair.
            im.thumbnail((w, h), Image.Resampling.LANCZOS)
            y = 177 + 296 * j
            panel.paste(im, (x + (w - im.width) // 2, y + (h - im.height) // 2))
    draw.text((30, 149), '现场照片', font=font(15), fill='#54504c')
    draw.text((30, 445), '三维构件', font=font(15), fill='#54504c')
    draw.line((28, 745, 1243, 745), fill='#c6c4bd')
    draw.text((28, 762), '摄影 Livelikerw · Wikimedia Commons · CC BY-SA 3.0（同幅裁切）。图板 CC BY-SA 4.0。', font=font(17), fill='#54504c')
    draw.text((28, 798), '灰底按前墙洞口遮挡后退的框边。窗扇与石窗台取自实际模型。', font=font(17), fill='#54504c')
    panel.save(args.output, quality=92, optimize=True, subsampling=0)


if __name__ == '__main__':
    main()
