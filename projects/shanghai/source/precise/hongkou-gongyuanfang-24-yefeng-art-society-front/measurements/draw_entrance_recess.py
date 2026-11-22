"""Render the registered 2022 view and its painted-reveal detail from the author mesh."""
import ctypes as ct
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from draw_upper_balcony import HERE, SHARED, digest, renderer


def main(mesh,destination):
    source=json.loads((HERE/'press-entrance-camera.json').read_bytes())
    renderer.CAMERA=np.asarray(source['press'])
    sheet=Image.new('RGB',(947,765),'#f5f3ed')
    draw=ImageDraw.Draw(sheet)
    def label(x,y,t,n):
        f=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',n,index=2)
        draw.text((x,y),t,font=f,fill='#302c28')
    label(24,15,'公园坊24号　砖券内的木框与灰墙',31)
    label(24,66,'同一扇木框在砖券深处，右侧灰色粉墙上方留有红色箱体。',18)
    captions=['原图视角下的砖券截段','靠墙的红箱、浅色标片与门框边线']
    views=[]
    with tempfile.TemporaryDirectory() as d:
        so=Path(d)/'local-triangles.so'
        subprocess.run(['cc','-O2','-shared','-fPIC',str(SHARED/'gable_raster.c'),'-o',str(so),'-lm'],check=True)
        fd=os.memfd_create('painted-reveal')
        try:
            os.write(fd,so.read_bytes())
            lib=ct.CDLL(f'/proc/self/fd/{fd}')
            lib.paint.restype=lib.shadow_depth.restype=None
            for crop,width,xy in [((20,144,310,603),372,(24,109)),((120,301,228,427),469,(454,109))]:
                renderer.CROP=crop
                im,meta=renderer.raster(mesh,lib,width)
                assert meta['zbuffer_foreground_pixels']>50000
                sheet.paste(im,xy)
                views.append({'original_crop':list(crop),'visible_raster_samples':meta['materials_visible_samples']})
        finally:
            os.close(fd)
    label(24,713,captions[0],16);label(454,678,captions[1],16)
    label(454,717,'根据2022年刊图，只表现可辨外形。',15)
    destination.parent.mkdir(parents=True,exist_ok=True)
    sheet.save(destination,quality=90,optimize=True)
    destination.with_suffix('.json').write_text(json.dumps(
        {'source_mesh_sha256':digest(mesh),'image_sha256':digest(destination),'photograph':source['image'],
         'views':views},ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':
    main(*map(Path,sys.argv[1:3]))
