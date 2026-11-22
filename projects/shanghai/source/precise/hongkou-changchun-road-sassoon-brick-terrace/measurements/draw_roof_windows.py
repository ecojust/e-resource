"""Draw the seven dormers directly from the finished mesh through three published exterior views."""
from pathlib import Path
import ctypes as ct
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import numpy as np
from PIL import Image,ImageDraw,ImageFont

M=Path(__file__).resolve().parent
SHARED=M.parents[1]/'hongkou-wujin-225-acanthus-gable/measurements'
spec=importlib.util.spec_from_file_location('triangle_raster',SHARED/'render_gable.py')
renderer=importlib.util.module_from_spec(spec);spec.loader.exec_module(renderer)
def font(size):return ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',size,index=2)
def digest(path):
    with path.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(mesh,dest):
    a=json.loads((M/'north-frontage-cameras.json').read_bytes());third=json.loads((M/'third-street-view.json').read_bytes())
    views=[('区文旅图中的北立面',a['front'],(50,-5,850,166),1090),
           ('从街道斜看东侧两座山花',a['gao'],(2380,360,3480,1070),565),
           ('从较远处斜看两对山花',third['camera'],(180,7,550,289),485)]
    results=[];images=[]
    with tempfile.TemporaryDirectory()as tmp:
        p=Path(tmp)/'roof-image.so'
        subprocess.run(['cc','-O2','-fPIC','-shared',str(SHARED/'gable_raster.c'),'-o',str(p),'-lm'],check=True)
        fd=os.memfd_create('gable-triangles');os.write(fd,p.read_bytes())
        lib=ct.CDLL(f'/proc/self/fd/{fd}');lib.paint.restype=lib.shadow_depth.restype=None
        for title,camera,crop,width in views:
            renderer.CROP=crop;renderer.CAMERA=np.array(camera)
            im,meta=renderer.raster(mesh,lib,width)
            assert meta['zbuffer_foreground_pixels']>5500
            results.append(dict(caption=title,original_pixel_crop=list(crop),
                visible_attic_materials={k:v for k,v in meta['materials_visible_samples'].items() if k.startswith('Attic |')}))
            images.append(im)
        os.close(fd)
    board=Image.new('RGB',(1150,795),'#f7f5ef');d=ImageDraw.Draw(board)
    def label(x,y,t,n):d.text((x,y),t,font=font(n),fill='#302b26')
    label(30,14,'长春路沙逊楼群　北立面的七座屋窗',33)
    label(30,69,'四座陡坡山花成对布置，中间三座低坡屋窗向内退进。',19)
    board.paste(images[0],(30,109)); label(30,350,views[0][0]+'的模型投影',17)
    board.paste(images[1],(30,399));board.paste(images[2],(630,399))
    label(30,770,'短回墙窗与深色木托头',16);label(630,770,'近处一对与街道远端一对',16)
    dest.parent.mkdir(parents=True,exist_ok=True)
    board.save(dest,quality=90,optimize=True)
    dest.with_suffix('.json').write_text(json.dumps(dict(mesh_sha256=digest(mesh),image_sha256=digest(dest),views=results),ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main(*map(Path,sys.argv[1:3]))
