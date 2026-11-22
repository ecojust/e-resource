"""Compare the two stone tablets with the 2014 CC image in the registered facade plane."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from verify_wing_casements import decode
from gable_dedications import MATRIX, OBS

REGIONS = {
    'south': (350, 249, 606, 442),
    'north': (342, 258, 592, 448),
}


def plane(wing):
    x0, z1 = (-12., 26.) if wing == 'south' else (2.3, 26.3)
    grid = np.array([[100., 0., -100*x0], [0., -100., 100*z1], [0., 0., 1.]])
    return grid @ np.linalg.inv(MATRIX[:, [0, 2, 3]])


def source_crop(photo, wing, width, height):
    u0, v0, u1, v1 = REGIONS[wing]
    crop = np.array([[(u1-u0)/width, 0., u0], [0., (v1-v0)/height, v0], [0., 0., 1.]])
    transform = np.linalg.inv(plane(wing)) @ crop
    transform /= transform[2, 2]
    return photo.transform((width, height), Image.Transform.PERSPECTIVE, transform.flat[:8],
                           Image.Resampling.BICUBIC)


def model_crop(glb, wing, width, height):
    triangles, labels, doc = glb
    proj = plane(wing) @ MATRIX
    camera = triangles @ proj[:, :3].T + proj[:, 3]
    uv = camera[:, :, :2] / camera[:, :, 2:]
    u0, v0, u1, v1 = REGIONS[wing]
    uv = (uv - [u0, v0]) * [width/(u1-u0), height/(v1-v0)]
    zbuf = np.zeros((height, width), dtype='float32')
    colour = np.full((height, width, 3), [221, 218, 210], dtype='uint8')
    yy, xx = np.mgrid[:height, :width]
    base = [np.asarray(m['pbrMetallicRoughness']['baseColorFactor'][:3]) for m in doc['materials']]
    light = np.array([-.42, -.48, .77]);light /= np.linalg.norm(light)
    for q, spatial, xyz, slot in zip(uv, camera, triangles, labels):
        low = np.maximum([0, 0], np.floor(q.min(axis=0)).astype(int))
        high = np.minimum([width-1, height-1], np.ceil(q.max(axis=0)).astype(int))
        if np.any(high < low):
            continue
        a, b = q[1]-q[0], q[2]-q[0]
        det = a[0]*b[1] - a[1]*b[0]
        if abs(det) < 1.e-8:
            continue
        sy, sx = slice(low[1], high[1]+1), slice(low[0], high[0]+1)
        dx, dy = xx[sy,sx]+.5-q[0,0], yy[sy,sx]+.5-q[0,1]
        s, t = (dx*b[1]-dy*b[0])/det, (a[0]*dy-a[1]*dx)/det
        inverse = (1-s-t)/spatial[0,2] + s/spatial[1,2] + t/spatial[2,2]
        mask = (s>=0)&(t>=0)&(s+t<=1)&(inverse>zbuf[sy,sx])
        if not mask.any():
            continue
        normal = np.cross(xyz[1]-xyz[0], xyz[2]-xyz[0]);normal /= np.linalg.norm(normal)
        intensity = .65 + .59*max(0, normal@light) + .08*normal[2]
        linear = np.clip(base[slot]*intensity, 0., 1.)
        srgb = np.where(linear<.0031308, 12.92*linear, 1.055*linear**(1/2.4)-.055)
        colour[sy,sx][mask] = np.rint(srgb*255).astype('uint8')
        zbuf[sy,sx][mask] = inverse[mask]
    return Image.fromarray(colour)


def main():
    c = argparse.ArgumentParser(description=__doc__)
    c.add_argument('glb', type=Path)
    c.add_argument('original_photo', type=Path)
    c.add_argument('output', type=Path)
    a = c.parse_args()
    if hashlib.sha256(a.original_photo.read_bytes()).hexdigest()!=OBS['source_2014']['sha256']:
        raise ValueError('Wrong source photograph')
    photo = Image.open(a.original_photo)
    mesh = decode(a.glb)
    panel = Image.new('RGB', (1192, 1070), (249, 247, 241)); d = ImageDraw.Draw(panel)
    fonts = Path('/usr/share/fonts/opentype/noto')
    def font(size, bold=False):
        return ImageFont.truetype(str(fonts / ('NotoSansCJK-Bold.ttc' if bold else 'NotoSansCJK-Regular.ttc')), size, index=2)
    d.text((28, 18), '圆明园公寓 · 山墙石铭', font=font(36, True), fill='#34332e')
    d.text((28, 76), '圆明园路115号　｜　2014年街照校正与模型实物', font=font(19), fill='#57544e')
    for i, wing in enumerate(('south','north')):
        y = 131 + 425*i
        d.text((28, y), '南山墙 · A.D.' if i==0 else '北山墙 · 1904', font=font(20, True), fill='#38352f')
        box = REGIONS[wing];w = 520;h = round(w*(box[3]-box[1])/(box[2]-box[0]))
        real = source_crop(photo, wing, w, h)
        mod = model_crop(mesh, wing, w, h)
        panel.paste(real, (28, y+34)); panel.paste(mod,(601,y+34))
    d.text((28, 1001),'摄影 Livelikerw · 2014年1月27日 · Wikimedia Commons · CC BY-SA 3.0（校正与裁切）。图板 CC BY-SA 4.0。',font=font(17),fill='#55514b')
    d.text((28, 1033),'左为同幅街照，右为模型。另以2016年南侧近照与北侧斜照核对枝条遮住的笔画。',font=font(16),fill='#55514b')
    panel.save(a.output, quality=94, optimize=True, subsampling=0)


if __name__=='__main__':
    main()
