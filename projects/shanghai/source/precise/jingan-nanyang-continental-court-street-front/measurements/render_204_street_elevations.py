"""Render Continental Court at the measured street cameras using the published meshes."""
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

HERE=Path(__file__).resolve().parent
RASTER=HERE.parents[1]/'jingan-jiaozhou-450-garden-residence/measurements'
sys.path.insert(0,str(RASTER))
from photo_glb_raster import raster

def digest(f):
    with f.open('rb') as src: return hashlib.file_digest(src,'sha256').hexdigest()

def render(asset,out):
    cams=json.loads((HERE/'street-and-204-projections.json').read_text())
    canvas=Image.new('RGB',(1180,975),'#f4f0e7')
    draw=ImageDraw.Draw(canvas)
    def text(x,y,message,size,bold=False):
        font=Path('/usr/share/fonts/opentype/noto')/('NotoSansCJK-'+('Bold' if bold else 'Regular')+'.ttc')
        draw.text((x,y),message,font=ImageFont.truetype(str(font),size,index=2),fill='#263c39')
    text(25,10,'南洋大楼　从街角到204号门洞',34,True)
    text(27,62,'南京西路与陕西北路交会处。砖立面随街弯折，十二根尖墩分隔十一个开间。',19)
    sun=np.array([-.38,-.73,.565],dtype=np.float32)
    sun/=np.linalg.norm(sun)
    layout=[
        ('a',asset,[54,37,490,263],(26,99),1126,'从路口看向两翼　　底层商铺按各自可辨的开口、框格和石带展开。'),
        ('204-hi11',asset,[395,1810,1575,2670],(26,733),306,'204号四道尖龛及宽券'),
        ('204-gao10',asset,[820,2650,2390,3630],(361,733),350,'同一门洞的另一摄影方向'),
        ('c',asset,[123,91,472,273],(743,733),407,'沿陕西北路看墩座与店面')]
    rows=[]
    with tempfile.TemporaryDirectory() as temp:
        libpath=Path(temp)/'paint.so'
        subprocess.run(['cc','-O2','-shared','-fPIC',str(RASTER/'photo_glb_raster.c'),'-o',str(libpath),'-lm'],check=True)
        lib=ctypes.CDLL(str(libpath));lib.paint.restype=lib.shadow_depth.restype=None
        for tag,asset,crop,(x,y),width,label in layout:
            cam=np.array(cams[tag]['P'])
            picture,stats=raster(asset,lib,width*2,cam,crop,sun,[207,35])
            height=round(width*(crop[3]-crop[1])/(crop[2]-crop[0]))
            canvas.paste(picture.resize((width,height),Image.Resampling.LANCZOS),(x,y))
            text(x,y+height+8,label,15 if width<500 else 17)
            rows.append(dict(camera=tag,label=label,sha256=digest(asset),**stats))
    out.parent.mkdir(parents=True,exist_ok=True);canvas.save(out,quality=92,optimize=True)
    out.with_suffix('.json').write_text(json.dumps(dict(license='MIT',source_photo_pixels=0,
        model_sha256=digest(asset),board_sha256=digest(out),lighting='illustrative daylight',views=rows),ensure_ascii=False,indent=1)+'\n')
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('asset',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();render(args.asset,args.output)
