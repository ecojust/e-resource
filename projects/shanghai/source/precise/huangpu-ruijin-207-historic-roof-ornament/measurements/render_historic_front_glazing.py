"""Illustrate the historical exterior and central glazing with pixels from the exported GLB."""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1]
BACKEND = BASE / 'huangpu-yuanmingyuan-apartments-street-front/measurements'
SKY = BASE / 'huangpu-world-book-company-fuzhou-front/measurements'
sys.path[:0] = [str(BACKEND), str(SKY), str(HERE.parent / 'source')]
from fuzhou_skylight import SurfaceCapture, horizon_shading
from photo_glb_raster import raster
from rosholt_front_plane import PROJECTION

FRONT = (8, -7, 998, 539)
CENTRE = (570, 412, 665, 503)
ROOF = (546, 63, 645, 219)

def face(size, bold=False):
    suffix = 'Bold' if bold else 'Regular'
    return ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-' + suffix + '.ttc', size, index=2)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def make(model, out):
    sun = np.array([-.48, -.73, .81], dtype='float32')
    sun /= np.linalg.norm(sun)
    board = Image.new('RGB', (1460, 1209), '#f6f4ee')
    pen = ImageDraw.Draw(board)
    ink, muted = '#2e332f', '#596059'
    pen.text((38, 17), '公董局医学化验所历史立面', font=face(43, True), fill=ink)
    pen.text((40, 82), '瑞金二路 207 号　｜　根据约 1938 年的街景复原', font=face(22), fill=muted)
    views = {}
    with tempfile.TemporaryDirectory() as temp:
        library = Path(temp) / 'raster.so'
        subprocess.run(['cc', '-O2', '-shared', '-fPIC', '-o', str(library),
                        str(BACKEND / 'photo_glb_raster.c'), '-lm'], check=True)
        lib = ctypes.CDLL(str(library))
        lib.shadow_depth.restype = lib.paint.restype = None
        for name, crop, width in [('front', FRONT, 1432), ('window', CENTRE, 554), ('roof', ROOF, 402)]:
            capture = SurfaceCapture(lib, model)
            img, meta = raster(model, capture, width, PROJECTION, crop, sun, None)
            img, occlusion = horizon_shading(img, capture.depth, PROJECTION, crop)
            meta['mean_sky_occlusion'] = occlusion
            views[name] = meta
            if name == 'front':
                img.thumbnail((1384, 755), Image.Resampling.LANCZOS)
                board.paste(img, (38, 130))
            elif name == 'window':
                img.thumbnail((298, 244), Image.Resampling.LANCZOS)
                board.paste(img, (40, 910))
            else:
                img.thumbnail((187, 244), Image.Resampling.LANCZOS)
                board.paste(img, (789, 910))
    pen.text((315, 917), '中央窗格', font=face(30, True), fill=ink)
    pen.text((317, 976), '四列三排玻璃', font=face(23), fill=ink)
    pen.text((317, 1018), '横梃、竖框与下部深色板', font=face(19), fill=muted)
    pen.text((974, 917), '屋顶饰件', font=face(30, True), fill=ink)
    pen.text((976, 976), '四层水平短翅', font=face(23), fill=ink)
    pen.text((976, 1018), '中央竖脊向上收束', font=face(19), fill=muted)
    pen.line((39, 1164, 1420, 1164), fill='#c9c9c0')
    pen.text((39, 1174), '三幅均为模型渲染。摄影参照为 Malcolm Rosholt 的 Ro-s018，藏于布里斯托大学。模型层高按 3.5 米估算。', font=face(16), fill=muted)
    out.parent.mkdir(parents=True, exist_ok=True)
    board.save(out, quality=92, optimize=True, subsampling=0)
    record = dict(input_glb_sha256=sha(model), board_sha256=sha(out), views=views,
                  image_content='Original GLB renders only. No photographic pixels.',
                  primary_reference='https://www.hpcbristol.net/visual/Ro-s018',
                  primary_reference_license='CC BY-NC-ND 4.0',
                  scale_basis='Reconstructed with 3.5 m estimated storeys.',
                  lighting_unit_xyz=sun.tolist(),
                  lighting='Illustrative directional light and local sky occlusion.')
    out.with_suffix('.json').write_text(json.dumps(record, ensure_ascii=False, indent=1) + '\n')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('model', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    make(args.model, args.output)
