"""Render the measured street piers from two registered photographic viewpoints."""
import argparse
import ctypes
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
RASTER = HERE.parents[1] / 'jingan-jiaozhou-450-garden-residence/measurements'
CLIPPING = HERE.parents[1] / 'huangpu-zhengjia-lane-39-street-gate/measurements'
sys.path[:0] = [str(RASTER), str(CLIPPING), str(HERE.parent / 'source')]
from clip_courtyard_camera import clip_near_plane
from photo_glb_raster import raster
from pointed_piers import STONE, BOWL, LEAF, RECESS, EDGE


def digest(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def render(near, distant, output):
    observations = HERE / 'pointed-piers-photo-evidence.json'
    data = json.loads(observations.read_text())
    cameras = {}
    for key, source in [('a', 'gao00'), ('c', 'gao08')]:
        width = data['sources'][source]['size'][0]
        cameras[key] = np.diag([width / 512, width / 512, 1]) @ np.array(data['camera_512'][key])

    board = Image.new('RGB', (1240, 990), '#f4f1ea')
    draw = ImageDraw.Draw(board)
    def text(x, y, value, size, bold=False):
        weight = 'Bold' if bold else 'Regular'
        font = ImageFont.truetype(f'/usr/share/fonts/opentype/noto/NotoSansCJK-{weight}.ttc', size, index=2)
        draw.text((x, y), value, fill='#2c2927', font=font)

    text(30, 15, '南洋大楼临街水刷石立墩', 39, True)
    text(32, 73, '陕西北路与南京西路街角  ·  依高参88的2018、2019年街面照片机位渲染', 20)
    # The tallest view shows the depth of the ridge in relation to its neighbours.
    # Each detail retains the aspect ratio of its crop in the original camera.
    tiles = [
        (near, 'c', [145, 0, 2200, 3190], 28, 128, 500, '折脊从叶饰托向上延伸至尖顶', (STONE, BOWL, EDGE)),
        (near, 'c', [805, 0, 1185, 368], 553, 128, 312, '尖脊与台阶形斜肩', (STONE,)),
        (near, 'c', [842, 1243, 1137, 1528], 891, 128, 312, '凹凸叶纹与侧部圆饰', (BOWL, LEAF)),
        (distant, 'a', [2275, 1810, 2575, 2192], 567, 509, 279, '中段较短的凹龛与托座', (RECESS, EDGE)),
        (near, 'c', [680, 2308, 1250, 3100], 918, 509, 255, '转角以南较深的阶式托座', (RECESS, EDGE)),
    ]
    sun = np.array([-.64, .43, .64], dtype=np.float32)
    sun /= np.linalg.norm(sun)
    angles = [round(float(np.degrees(np.arctan2(sun[0], sun[1]))) % 360, 3),
              round(float(np.degrees(np.arcsin(sun[2]))), 3)]
    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        scratch = Path(tmp)
        library = scratch / 'raster.so'
        subprocess.run(['cc', '-O2', '-shared', '-fPIC', str(RASTER / 'photo_glb_raster.c'),
                        '-o', str(library), '-lm'], check=True)
        lib = ctypes.CDLL(str(library))
        lib.paint.restype = lib.shadow_depth.restype = None
        views = {}
        for mesh, key, crop, x, y, width, caption, expected_materials in tiles:
            camera = cameras[key]
            if (mesh, key) not in views:
                clipped = scratch / f'view-{len(views)}.glb'
                views[mesh, key] = clipped, clip_near_plane(mesh, clipped, camera)
            clipped, clipping = views[mesh, key]
            image, review = raster(clipped, lib, round(width * 1.25), camera, crop, sun, angles)
            visible = review['materials_visible_samples']
            missing = [mat for mat in expected_materials if not visible.get(mat, 0)]
            if missing:
                raise ValueError(f'{caption}: missing visible surface {missing}')
            height = round(width * (crop[3] - crop[1]) / (crop[2] - crop[0]))
            board.paste(image.resize((width, height), Image.Resampling.LANCZOS), (x, y))
            text(x, y + height + 8, caption, 18, True)
            rows.append(dict(source='gao00' if key == 'a' else 'gao08', camera_native=camera.tolist(),
                             native_crop=crop, mesh=mesh.name, sha256=digest(mesh),
                             measured_visible_materials=list(expected_materials), clipping=clipping, render=review))
    text(30, 956, '图像由模型的实体、原创水刷石纹理和光照生成。', 16)
    output.parent.mkdir(parents=True, exist_ok=True)
    board.save(output, quality=92, optimize=True)
    record = dict(views=rows, observations_sha256=digest(observations), output_sha256=digest(output),
                  embedded_source_photographs=False, image_size=list(board.size))
    output.with_suffix('.json').write_text(json.dumps(record, ensure_ascii=False, indent=1) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('near', type=Path)
    parser.add_argument('distant', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    render(args.near, args.distant, args.output)
