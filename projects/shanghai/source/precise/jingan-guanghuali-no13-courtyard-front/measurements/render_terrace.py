"""Draw the 13号 terrace from the two recorded camera positions, using only released mesh geometry."""
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
RASTER = HERE.parents[1] / 'jingan-jiaozhou-450-garden-residence/measurements'
CLIP = HERE.parents[1] / 'huangpu-zhengjia-lane-39-street-gate/measurements'
sys.path[:0] = [str(RASTER), str(CLIP)]
from photo_glb_raster import raster
from clip_courtyard_camera import clip_near_plane


def local_from_world(placement):
    matrix = np.eye(4)
    if placement:
        data = json.loads(placement.read_text())
        angle = np.radians(data['yaw_degrees'])
        matrix[:2, :2] = [[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]]
        matrix[:3, 3] = data['origin']
    return np.linalg.inv(matrix)


def digest(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def render(full, low, destination, placement=None):
    survey = json.loads((HERE / 'terrace-reconstruction.json').read_text())
    world = local_from_world(placement)
    canvas = Image.new('RGB', (1300, 1002), '#f6f3eb')
    draw = ImageDraw.Draw(canvas)
    def label(x, y, message, size, bold=False, color='#2c3635'):
        name = 'NotoSansCJK-' + ('Bold' if bold else 'Regular') + '.ttc'
        font = ImageFont.truetype(str(Path('/usr/share/fonts/opentype/noto') / name), size, index=2)
        draw.text((x,y), message, font=font, fill=color)

    label(36, 18, '光华里 13 号的屋顶露台', 40, True)
    label(38, 83, '巨鹿路 786 弄　｜　从弄堂两端看凸窗上的钢管栏杆和后方的小坡屋面', 22)
    views = [('yan07', full, [645, 550, 1680, 1120], (36, 145), 722, '东侧机位　可见小屋的前檐、坡顶和三扇玻璃窗'),
             ('yan05', low, [1260, 85, 2535, 845], (797, 145), 466, '西侧机位　远景保留四道连续横杆'),
             ('yan05', full, [1340, 108, 2392, 572], (36, 624), 722, '斜切转角处的立柱与多层灰色压檐')]
    rows = []
    sun = np.array([-.36,-.60,.71], dtype=np.float32)
    sun /= np.linalg.norm(sun)
    with tempfile.TemporaryDirectory() as tmp:
        library = Path(tmp) / 'roof_raster.so'
        subprocess.run(['cc','-O2','-shared','-fPIC',str(RASTER/'photo_glb_raster.c'),
                        '-o',str(library),'-lm'], check=True)
        lib = ctypes.CDLL(str(library))
        lib.paint.restype = lib.shadow_depth.restype = None
        for k, model, crop, (x,y), width, description in views:
            camera = np.array(survey['cameras'][k]) @ world
            clipped = Path(tmp) / 'visible.glb'
            near = clip_near_plane(model, clipped, camera)
            result, stats = raster(clipped, lib, width*2, camera, crop, sun, [205,38])
            height = round(width * (crop[3]-crop[1])/(crop[2]-crop[0]))
            canvas.paste(result.resize((width,height),Image.Resampling.LANCZOS), (x,y))
            label(x,y+height+7,description,17)
            rows.append(dict(camera=k, mesh_sha256=digest(model), near_clip=near, **stats))
    label(798,503,'栏杆平面',24,True)
    xy = np.array(survey['handrail_path_m'])
    path = [(int(901+91*x),int(793-91*y)) for x,y,_ in xy]
    draw.line(path,fill='#38504e',width=5,joint='curve')
    for x,y in path:
        draw.ellipse((x-5,y-5,x+5,y+5),fill='#38504e')
    draw.line((901,811,1068,811),fill='#6b7a76',width=2)
    for x in (901,1068):
        draw.line((x,805,x,818),fill='#6b7a76',width=2)
    label(923,816,'约 1.84 米',18)
    label(800,882,'以 33 皮砖估算整体尺度。',17)
    label(800,915,'坡屋面的后缘取可见范围。',17)
    destination.parent.mkdir(parents=True,exist_ok=True)
    canvas.save(destination,quality=92,optimize=True)
    destination.with_suffix('.json').write_text(json.dumps(dict(figure_license='MIT',
        photo_pixels_embedded=False, original_2018_station_times=['12:52:09','12:53:03'],
        placement_sha256=digest(placement) if placement else None, views=rows),
        ensure_ascii=False,indent=2)+'\n')


if __name__ == '__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    for key in ('full','lod','destination'):
        ap.add_argument(key,type=Path)
    ap.add_argument('--placement',type=Path)
    args=ap.parse_args()
    render(args.full,args.lod,args.destination,args.placement)
