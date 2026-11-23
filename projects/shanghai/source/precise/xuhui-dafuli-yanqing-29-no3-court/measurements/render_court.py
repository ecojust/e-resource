"""Render the surveyed court from the recorded Livelikerw 2016 camera."""
import argparse
import ctypes
import json
from pathlib import Path
import runpy
import subprocess
import tempfile
from unittest.mock import patch

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from register_court import Camera

HERE = Path(__file__).resolve().parent
PRECISE = HERE.parents[1]
backend = runpy.run_path(str(PRECISE / 'changning-hongji-yuyuan-garden-houses-8-and-9/measurements/render-garden-stations.py'))
CROPS = {'2016-court': (3490, 290, 4912, 3264), '2016-gate': (3900, 1730, 4912, 2970),
         '2016-terrace': (3400, 550, 4780, 1740), '2016-window': (4020, 0, 4720, 1070)}

def render(mesh, photo, output):
    engine = backend['renderer']
    parts = engine.read_glb(mesh)
    p = Camera().projection()
    clipped = backend['projected_parts'](parts, p)
    light = np.array([.34, -.75, .57], dtype=np.float32)
    light /= np.linalg.norm(light)
    angles = [float(np.degrees(np.arctan2(light[0], light[1])) % 360), float(np.degrees(np.arcsin(light[2])))]
    with tempfile.TemporaryDirectory() as temp, Image.open(photo) as original:
        lib = Path(temp) / 'court.so'
        subprocess.run(['cc','-O2','-shared','-fPIC',str(PRECISE/'huangpu-old-jiefu-nanjing-road-shopfront/measurements/northwest_raster.c'),'-lm','-o',str(lib)],check=True)
        dll = ctypes.CDLL(str(lib))
        output.mkdir(parents=True, exist_ok=True)
        report = {}
        for key,crop in CROPS.items():
            with patch.object(engine, 'read_glb', return_value=clipped):
                raster, report[key] = engine.raster(mesh, dll, 880, p, crop, light, angles)
            raster.thumbnail((730, 850), Image.Resampling.LANCZOS)
            src = original.crop(crop).convert('RGB').resize(raster.size,Image.Resampling.LANCZOS)
            width, height = raster.size
            sheet = Image.new('RGB', (width*2+6,height+60),'#f1eee9')
            sheet.paste(src, (0,0)); sheet.paste(raster.convert('RGB'),(width+6,0))
            draw = ImageDraw.Draw(sheet)
            draw.text((8,height+4),'2016 | Livelikerw | CC BY-SA 4.0',fill='#242628')
            draw.text((width+14,height+4),'Model | Same camera and crop',fill='#242628')
            draw.text((8,height+29),'commons.wikimedia.org/wiki/File:Dafu_Li_Shanghai.JPG',fill='#3e4143')
            sheet.save(output/(key+'-comparison.jpg'),quality=94,optimize=True)
    (output/'model-projection-renders.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('mesh','photo','output'): parser.add_argument(key,type=Path)
    args=parser.parse_args()
    render(args.mesh,args.photo,args.output)
