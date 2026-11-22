"""Compare two crops of Fayhoo's No.19 courtyard photograph with the same camera in a decoded model."""
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
RASTER = HERE.parents[1]/'jingan-jiaozhou-450-garden-residence/measurements'
sys.path[:0] = [str(HERE.parent/'source'), str(RASTER)]
from courtyard_photo_plane import CAMERA, P
from photo_glb_raster import raster


def board(glb, photo_path, output):
    source_sha = hashlib.sha256(photo_path.read_bytes()).hexdigest()
    if source_sha != CAMERA['image_sha256']:
        raise ValueError('The original 2144 × 1424 Fayhoo photograph is required')
    photo = Image.open(photo_path).convert('RGB')
    sheet = Image.new('RGB', (1400, 1060), '#faf9f3')
    draw = ImageDraw.Draw(sheet)
    fonts = Path('/usr/share/fonts/opentype/noto')
    def label(x, y, value, size, bold=False, fill='#28332c'):
        weight = 'Bold' if bold else 'Regular'
        font = ImageFont.truetype(str(fonts/f'NotoSansCJK-{weight}.ttc'),size,index=2)
        draw.text((x,y),value,font=font,fill=fill)
    label(38,17,'贤邻别墅 19 号的转角露台',40,True)
    label(40,84,'2015 年庭院原照',23,True)
    label(710,84,'近景模型，同一机位',23,True)
    panels = [((850,270,1385,540),130), ((916,300,1210,448),540)]
    records = []
    sun = np.array([.42,-.50,.75],np.float32);sun /= np.linalg.norm(sun)
    with tempfile.TemporaryDirectory() as temp:
        so = Path(temp)/'terrace-render.so'
        subprocess.run(['cc','-O2','-fPIC','-shared',str(RASTER/'photo_glb_raster.c'),'-o',str(so),'-lm'],check=True)
        lib = ctypes.CDLL(str(so));lib.shadow_depth.restype=lib.paint.restype=None
        for box, top in panels:
            width = 654
            height = round((box[3]-box[1])*width/(box[2]-box[0]))
            original = photo.transform((width,height),Image.Transform.EXTENT,box,Image.Resampling.BICUBIC)
            rendered, stats = raster(glb,lib,2*width,P,box,sun,[130,48])
            if stats['zbuffer_foreground_pixels']<10000:
                raise ValueError('Projected model is missing from the crop')
            sheet.paste(original,(40,top));sheet.paste(rendered.resize((width,height),Image.Resampling.LANCZOS),(709,top))
            records.append({'original_crop_ltrb':box, **stats})
    label(40,469,'檐口沿转角连续折返。正面栏杆延伸到树干遮挡处。',23)
    label(40,886,'方柱表面有宽竖棱。两根端柱之间可以看到小栏柱，枝叶和织物遮住了部分柱身。',22)
    label(40,964,'摄影  Fayhoo，《Xianlin Bieshu.JPG》，2015-12-26，Wikimedia Commons。',17)
    label(40,998,'本图裁切了原照，并加入三维模型视图和文字。整张图版按 CC BY-SA 3.0 共享。',17)
    output.parent.mkdir(parents=True,exist_ok=True)
    sheet.save(output,quality=92,optimize=True)
    output.with_suffix('.json').write_text(json.dumps({'source_photo':'https://commons.wikimedia.org/wiki/File:Xianlin_Bieshu.JPG',
      'title':'Xianlin Bieshu.JPG','photographer':'Fayhoo','photo_sha256':source_sha,
      'source_license_and_adapted_board_license':'https://creativecommons.org/licenses/by-sa/3.0/',
      'changes':'Two resized crops of the original photo, paired with two calibrated mesh renders and original layout and text.',
      'decoded_mesh_sha256':hashlib.sha256(glb.read_bytes()).hexdigest(),'solar_direction_explanatory':sun.round(4).tolist(),
      'rendered_panels':records},ensure_ascii=False,indent=2)+'\n')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('decoded_mesh','original_photo','output_jpg'):
        parser.add_argument(name,type=Path)
    q=parser.parse_args();board(q.decoded_mesh,q.original_photo,q.output_jpg)
