"""Render the study mesh through the two registered 2019 photographs of No. 24."""
import ctypes as ct
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE=Path(__file__).resolve().parent
SHARED=HERE.parents[1]/'hongkou-wujin-225-acanthus-gable/measurements'
spec=importlib.util.spec_from_file_location('triangle_raster',SHARED/'render_gable.py')
renderer=importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def main(mesh, destination):
    cameras=json.loads((HERE/'two-cameras-and-curved-sill.json').read_bytes())
    views=[
        ('图6视角　完整露台',cameras['front'],(236,220,508,492),522,(28,116)),
        ('图4视角　左端檐口',cameras['oblique_wall'],(468,100,640,323),388,(585,116)),
    ]
    board=Image.new('RGB',(1000,718),'#f5f3ed')
    draw=ImageDraw.Draw(board)
    def caption(x,y,label,size):
        font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',size,index=2)
        draw.text((x,y),label,font=font,fill='#302c28')
    caption(28,15,'公园坊24号野风画会旧址　弧形露台',32)
    caption(29,69,'三层露台铁栏沿楼板弯出，上方红褐色檐梁沿直线延伸。',19)
    reports=[]
    with tempfile.TemporaryDirectory() as directory:
        library=Path(directory)/'raster.so'
        subprocess.run(['cc','-O2','-shared','-fPIC',str(SHARED/'gable_raster.c'),'-o',str(library),'-lm'],check=True)
        fd=os.memfd_create('upper-balcony-renderer')
        try:
            os.write(fd,library.read_bytes())
            lib=ct.CDLL(f'/proc/self/fd/{fd}')
            lib.paint.restype=lib.shadow_depth.restype=None
            for name,camera,crop,width,xy in views:
                renderer.CROP=crop
                renderer.CAMERA=np.asarray(camera)
                image,meta=renderer.raster(mesh,lib,width)
                assert meta['zbuffer_foreground_pixels']>1500
                board.paste(image,xy)
                caption(xy[0],650,name,19)
                reports.append({'photograph':name,'source_pixel_crop':list(crop),
                                'raster_dimensions':list(image.size),'material_pixels':meta['materials_visible_samples']})
        finally:
            os.close(fd)
    caption(28,686,'按两张公开照片的视角投影同一模型。图4原幅只覆盖露台左端。',15)
    destination.parent.mkdir(parents=True,exist_ok=True)
    board.save(destination,quality=91,optimize=True)
    destination.with_suffix('.json').write_text(json.dumps(
        {'source_mesh_sha256':digest(mesh),'image_sha256':digest(destination),'views':reports},
        ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':
    main(*map(Path,sys.argv[1:3]))
