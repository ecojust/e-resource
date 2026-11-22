"""Inspect the main shutter wall and adjacent bay at their recorded camera positions."""
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
    cams=json.loads((HERE/'2016-two-window-cameras.json').read_bytes())
    canvas=Image.new('RGB',(1180,930),'#f4f0e7')
    draw=ImageDraw.Draw(canvas)
    def text(x,y,message,size,bold=False):
        font=Path('/usr/share/fonts/opentype/noto')/('NotoSansCJK-'+('Bold' if bold else 'Regular')+'.ttc')
        draw.text((x,y),message,font=ImageFont.truetype(str(font),size,index=2),fill='#263c39')
    text(25,10,'花雅堂　从三联窗看到两层折角',34,True)
    text(27,62,'2016年11月2日的两个取景方向。上层为弧形窗冠，下层为卷草三角山花。',19)
    sun=np.array([-.38,-.73,.565],dtype=np.float32)
    sun/=np.linalg.norm(sun)
    layout=[
        ('oblique',asset,[100,15,2810,3680],(25,102),548,'从直墙看向凸部，出挑的两层檐口随墙面折转。'),
        ('front',asset,[20,0,4060,2350],(600,102),552,'三联窗　　中窗右半部留素面'),
        ('oblique',asset,[1420,120,2390,1590],(601,492),265,'上层弧形窗冠与开扇'),
        ('oblique',asset,[1400,1700,2500,3170],(889,492),266,'下层转角窗与腰部挑檐')]
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
