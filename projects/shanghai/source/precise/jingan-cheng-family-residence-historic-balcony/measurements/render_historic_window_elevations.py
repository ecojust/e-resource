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

def render(asset,out):
    cams={'period':json.loads((HERE/'historic-balcony-period-camera.json').read_text()),
          '2018':json.loads((HERE/'historic-balcony-cameras.json').read_text())['gao2018']}
    canvas=Image.new('RGB',(1180,917),'#f4f0e7')
    draw=ImageDraw.Draw(canvas)
    def text(x,y,message,size,bold=False):
        font=Path('/usr/share/fonts/opentype/noto')/('NotoSansCJK-'+('Bold' if bold else 'Regular')+'.ttc')
        draw.text((x,y),message,font=ImageFont.truetype(str(font),size,index=2),fill='#263c39')
    text(25,10,'南京西路1550号　旧门楼的五樘窗',34,True)
    text(27,62,'沿历史街照的视线，对照西折面、中央两扇长窗与东端转角。',19)
    sun=np.array([-.38,-.73,.565],dtype=np.float32)
    sun/=np.linalg.norm(sun)
    layout=[
        ('period',asset,[11,4,546,238],(26,108),1126,'旧刊照片的取景　　左端暗窗在原版边缘，中央长窗下部被阳台花栏遮住。'),
        ('period',asset,[289,112,496,225],(26,667),376,'东折面长窗与正面方窗'),
        ('2018',asset,[2450,642,3030,965],(425,667),350,'东端石冠的四个透孔与卷肩'),
        ('period',asset,[85,112,259,209],(801,667),346,'中央长窗的上亮和两扇窗框')]
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
