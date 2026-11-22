"""Produce two same-camera comparisons of the measured timber and glazing."""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageOps
HERE=Path(__file__).resolve().parent
RUNTIME=HERE.parents[1]/'huangpu-yuanmingyuan-apartments-street-front/measurements'
sys.path[:0]=[str(HERE.parent/'source'),str(RUNTIME)]
from marconi_photo_plane import CALIBRATION
from photo_glb_raster import raster
def font(n,bold=False):
 name='NotoSansCJK-'+('Bold' if bold else 'Regular')+'.ttc'
 return ImageFont.truetype('/usr/share/fonts/opentype/noto/'+name,n,index=2)
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def make(model,front,oblique,out):
 board=Image.new('RGB',(1450,1030),'#f8f5ee');draw=ImageDraw.Draw(board)
 draw.text((26,14),'马可尼公司旧址　北京东路131号门上窗',font=font(34,True),fill='#352c28')
 draw.text((28,68),'门楼的两间矮窗各有九格玻璃。上层四扇木窗的东侧两扇向外开启，窗后留有两道横栏。',font=font(20),fill='#4d4941')
 specs=[('2017_front',front,[(1920,1280,2690,1920),(1940,2150,2660,2605)],'2017年8月31日　正面'),('2015_oblique',oblique,[(1630,2280,2190,3050),(1680,3330,2050,3830)],'2015年7月20日　斜面')]
 output=[]
 with tempfile.TemporaryDirectory() as td:
  native=Path(td)/'render.so';subprocess.run(['cc','-O2','-shared','-fPIC','-o',native,RUNTIME/'photo_glb_raster.c','-lm'],check=True)
  lib=ctypes.CDLL(str(native));lib.shadow_depth.restype=lib.paint.restype=None
  sun=np.array([-.52,-.78,.51],np.float32);sun/=np.linalg.norm(sun)
  for i,(key,photo,crops,label) in enumerate(specs):
   data=CALIBRATION['cameras'][key];assert sha(photo)==data['sha256'];original=ImageOps.exif_transpose(Image.open(photo)).convert('RGB')
   x=28+i*718;draw.text((x,112),label,font=font(23,True),fill='#42352f')
   draw.text((x,156),'Antigng 摄影',font=font(18),fill='#554b43')
   draw.text((x+348,156),'同一视角的窗件模型',font=font(18),fill='#554b43')
   for j,crop in enumerate(crops):
    img,info=raster(model,lib,672,np.array(CALIBRATION['camera_matrices'][key]),crop,sun,[214,30])
    orig=original.crop(crop);scale=min(335/orig.width,345/orig.height);size=(round(orig.width*scale),round(orig.height*scale))
    top=198+j*386
    for dx,row in ((0,orig),(348,img)):board.paste(row.resize(size,Image.Resampling.LANCZOS),(x+dx,top))
    output.append(dict(camera=key,crop_upright_px=crop,photo_file=data['file'],render=info))
 draw.text((28,924),'模型还原2017年木扇开度。2015年斜照的窗扇角度有所变化，矮窗玻璃和屋身砖券可用于两期位置比对。',font=font(18),fill='#51473f')
 draw.text((28,975),'照片由 Antigng 拍摄，原件见 Wikimedia Commons《北京东路131号.jpg》和《北京东路131号-2017-08-31.jpg》。照片经裁切，图版依 CC BY-SA 4.0 共享。',font=font(16),fill='#61534b')
 board.save(out,quality=90)
 out.with_suffix('.json').write_text(json.dumps(dict(model_sha256=sha(model),license='https://creativecommons.org/licenses/by-sa/4.0/',images=output,camera_sha256=sha(HERE/'marconi-front-cameras.json'),board_sha256=sha(out)),ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser()
 for k in ('model','front','oblique','output'):p.add_argument(k,type=Path)
 a=p.parse_args();make(a.model,a.front,a.oblique,a.output)
