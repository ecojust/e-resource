"""Render the delivered triangles from Antigng's 2015 camera alongside the licensed original."""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image,ImageOps,ImageDraw,ImageFont

HERE=Path(__file__).resolve().parent
RASTER=HERE.parents[1]/'huangpu-yuanmingyuan-apartments-street-front/measurements'
sys.path[:0]=[str(HERE.parent/'source'),str(RASTER)]
from upper_casements import OBS
from huanlong_photo_plane import CALIBRATION
from photo_glb_raster import raster

def font(size,bold=False):
    face='NotoSansCJK-'+('Bold' if bold else 'Regular')+'.ttc'
    return ImageFont.truetype('/usr/share/fonts/opentype/noto/'+face,size,index=2)
def compare(model,photo,dest):
    original=OBS['principal']
    assert hashlib.sha256(photo.read_bytes()).hexdigest()==original['sha256']
    crop=(3650,750,4930,1550)
    photograph=ImageOps.exif_transpose(Image.open(photo)).convert('RGB').crop(crop)
    projection=np.asarray(CALIBRATION['camera_matrices']['commons_2015'])
    sun=np.array([.47,-.72,.71],np.float32);sun/=np.linalg.norm(sun)
    with tempfile.TemporaryDirectory() as td:
        so=Path(td)/'paint.so'
        subprocess.run(['cc','-O2','-shared','-fPIC','-o',so,RASTER/'photo_glb_raster.c','-lm'],check=True)
        lib=ctypes.CDLL(str(so));lib.shadow_depth.restype=lib.paint.restype=None
        render,info=raster(model,lib,1152,projection,crop,sun,[225,28])
    board=Image.new('RGB',(1510,650),'#f7f5ee');draw=ImageDraw.Draw(board)
    draw.text((30,13),'南昌路212弄1–10号　楼上两组外开木窗',font=font(32,True),fill='#352d27')
    for x,im,label in ((30,photograph,'2015年9月9日　Antigng 原照局部'),(765,render,'木窗模型　同一机位与取景')):
        draw.text((x,76),label,font=font(20),fill='#635646')
        board.paste(im.resize((715,447),Image.Resampling.LANCZOS),(x,114))
    draw.text((30,576),'每个窗洞可辨三处向街面开启的木扇。扇上细梃将玻璃分成两列四行。',font=font(20),fill='#433a31')
    draw.text((30,617),'照片摘自 Wikimedia Commons《南昌路212弄.jpg》，Antigng 摄；图版依 CC BY-SA 4.0 发布。',font=font(17),fill='#66584b')
    board.save(dest,quality=91)
    record=dict(photograph=original['url'],credit=original['author'],license='https://creativecommons.org/licenses/by-sa/4.0/',changes='EXIF orientation, crop, resizing, adjoining separate rendering',original_sha256=original['sha256'],camera='commons_2015',camera_calibration_sha256=hashlib.sha256((HERE/'212-window-cameras.json').read_bytes()).hexdigest(),crop_upright_px=crop,model_sha256=hashlib.sha256(model.read_bytes()).hexdigest(),render=info,board_sha256=hashlib.sha256(dest.read_bytes()).hexdigest())
    dest.with_suffix('.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser()
    for k in ('model','photo','output'):p.add_argument(k,type=Path)
    a=p.parse_args();compare(a.model,a.photo,a.output)
