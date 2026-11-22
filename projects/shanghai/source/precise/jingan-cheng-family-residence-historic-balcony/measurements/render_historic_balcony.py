"""Draw only the historic exterior modelling fragment, using the two registered street cameras."""
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

def render(full,lod,out):
    cams={'period':json.loads((HERE/'historic-balcony-period-camera.json').read_text()),
          '2018':json.loads((HERE/'historic-balcony-cameras.json').read_text())['gao2018']}
    canvas=Image.new('RGB',(1240,900),'#f4f0e7')
    draw=ImageDraw.Draw(canvas)
    def text(x,y,message,size,bold=False):
        font=Path('/usr/share/fonts/opentype/noto')/('NotoSansCJK-'+('Bold' if bold else 'Regular')+'.ttc')
        draw.text((x,y),message,font=ImageFont.truetype(str(font),size,index=2),fill='#283a34')
    text(35,13,'程氏旧宅的临街花栏',35,True)
    text(36,63,'南京西路 1550 号　　中央二层阳台与两侧可辨的折面窗',19)
    sun=np.array([-.38,-.73,.565],dtype=np.float32)
    sun/=np.linalg.norm(sun)
    layout=[
        ('period',full,[24,12,588,270],(34,109),710,'历史近照的视角　　四段花栏随阳台转折'),
        ('2018',lod,[630,585,3200,1860],(784,109),421,'2018 年街面视角 · 远景模型'),
        ('2018',full,[1028,1482,2053,1814],(34,520),710,'两端各一块、中央两块。每块花板均有四个透孔。'),
        ('2018',full,[1216,1497,1770,1804],(784,472),421,'中央花板的切角、斜肋和石台'),
    ]
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
    text(34,800,'旧影的两种刊本来自同一次曝光。',22,True)
    text(34,849,'栏杆高度采用 0.96 ± 0.12 米估算。石材色泽和照明用于表现浮雕与镂空，各图均取自模型。',17)
    out.parent.mkdir(parents=True,exist_ok=True);canvas.save(out,quality=92,optimize=True)
    out.with_suffix('.json').write_text(json.dumps(dict(license='MIT',source_photo_pixels=0,
        lighting='illustrative warm daylight',views=rows),ensure_ascii=False,indent=1)+'\n')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['full','lod','output']:parser.add_argument(name,type=Path)
    args=parser.parse_args();render(args.full,args.lod,args.output)
