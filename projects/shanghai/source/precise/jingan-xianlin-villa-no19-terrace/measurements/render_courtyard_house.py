"""Photographic and rendered views of the same courtyard façade in No.19."""
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
HELPER=HERE.parents[1]/'jingan-jiaozhou-450-garden-residence'/'measurements'
sys.path[:0]=[str(HERE.parent/'source'),str(HELPER)]
from courtyard_photo_plane import CAMERA,P
from photo_glb_raster import raster

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def draw(photo,glb,out):
    assert sha(photo)==CAMERA['image_sha256']
    sun=np.array([.4,-.84,.39],dtype='float32');sun/=np.linalg.norm(sun)
    with tempfile.TemporaryDirectory() as td:
        so=Path(td)/'raster.so'
        subprocess.run(['cc','-O2','-fPIC','-shared',str(HELPER/'photo_glb_raster.c'),'-o',str(so),'-lm'],check=True)
        lib=ctypes.CDLL(str(so));lib.paint.restype=lib.shadow_depth.restype=None
        crop=(231,64,1718,1312)
        rendered,detail=raster(glb,lib,760,P,crop,sun,(145,25))
    source=Image.open(photo).convert('RGB').crop(crop).resize(rendered.size,Image.Resampling.LANCZOS)
    w,h=rendered.size; sheet=Image.new('RGB',(w*2+54,h+164),'#faf7ef')
    d=ImageDraw.Draw(sheet);fonts=Path('/usr/share/fonts/opentype/noto')
    def label(x,y,s,size):
        d.text((x,y),s,font=ImageFont.truetype(str(fonts/'NotoSansCJK-Regular.ttc'),size,index=2),fill='#302c26')
    label(18,10,'愚园路470弄19号　庭院与转角露台',36)
    label(19,62,'Fayhoo 摄于2015年12月26日',21)
    label(w+36,62,'模型从同一照相机位置看去',21)
    sheet.paste(source,(18,101));sheet.paste(rendered,(w+36,101))
    label(18,h+113,'据30皮砖取得米制比例。树后屋面与近地面受遮挡；对照图裁自 Xianlin Bieshu.JPG，依 CC BY-SA 3.0 共享。',19)
    out.parent.mkdir(parents=True,exist_ok=True);sheet.save(out,quality=89,optimize=True)
    out.with_suffix('.json').write_text(json.dumps(dict(asset_sha256=sha(glb),source='https://commons.wikimedia.org/wiki/File:Xianlin_Bieshu.JPG',
        source_sha256=sha(photo),credit='Fayhoo, 26 December 2015',licence='https://creativecommons.org/licenses/by-sa/3.0/',changes='Cropped and resized photograph beside original model rendering.',**detail),indent=2,ensure_ascii=False)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('photo',type=Path);p.add_argument('decoded',type=Path);p.add_argument('out',type=Path);q=p.parse_args()
    draw(q.photo,q.decoded,q.out)
