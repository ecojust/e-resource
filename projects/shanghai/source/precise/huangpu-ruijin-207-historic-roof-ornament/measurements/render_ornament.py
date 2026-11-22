"""Render only original geometry, with views referenced to the historic camera and its return side."""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import numpy as np
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).resolve().parent
SHARED=HERE.parents[1]/'huangpu-yuanmingyuan-apartments-street-front/measurements'
sys.path[:0]=[str(HERE.parent/'source'),str(SHARED)]
from rosholt_ornament_plane import PROJECTION,ORIGIN
import photo_glb_raster as renderer

def pinhole(axes,anchor):
    direction=np.cross(axes[0],axes[1]);direction/=np.linalg.norm(direction)
    perspective=direction/900
    return np.vstack((np.r_[axes[0]+anchor[0]*perspective,anchor[0]],
                         np.r_[axes[1]+anchor[1]*perspective,anchor[1]],np.r_[perspective,1.]))
def draw(model,out):
    with tempfile.TemporaryDirectory() as temp:
        so=Path(temp)/'paint.so'
        raster_source=Path(renderer.__file__).with_suffix('.c')
        subprocess.run(['cc','-O2','-shared','-fPIC','-o',so,raster_source,'-lm'],check=True)
        lib=ctypes.CDLL(str(so));lib.shadow_depth.restype=lib.paint.restype=None
        sun=np.array([.5,-.72,.68],np.float32);sun/=np.linalg.norm(sun)
        left,lmeta=renderer.raster(model,lib,640,pinhole(PROJECTION,ORIGIN),(557,101,632,219),sun,[145,43])
        yaw=np.radians(-55.);rot=np.array([[np.cos(yaw),-np.sin(yaw),0],[np.sin(yaw),np.cos(yaw),0],[0,0,1]])
        right,rmeta=renderer.raster(model,lib,640,pinhole(PROJECTION@rot,ORIGIN),(555,101,630,219),sun,[145,43])
    board=Image.new('RGB',(1030,750),'#f4f2eb');d=ImageDraw.Draw(board)
    def label(x,y,s,size,bold=False):
        face='NotoSansCJK-'+('Bold' if bold else 'Regular')+'.ttc'
        font=ImageFont.truetype('/usr/share/fonts/opentype/noto/'+face,size,index=2)
        d.text((x,y),s,font=font,fill='#393a36')
    label(25,14,'公董局医学化验所　1930年代屋顶饰件',30,True)
    for x,im,s in ((25,left,'历史摄影方向'),(535,right,'旋转55°观察横翅进深')):
        label(x,70,s,19);im.thumbnail((465,535),Image.Resampling.LANCZOS);board.paste(im,(x+44,111))
    label(25,656,'四层横翅按1938年前后原照的亮缘与暗影间距重建。绝对尺寸按估计层高折算。',17)
    label(25,704,'史料　Malcolm Rosholt，布里斯托大学 Historical Photographs of China，Ro-s018。两幅为模型渲染。',15)
    board.save(out,quality=91)
    out.with_suffix('.json').write_text(json.dumps(dict(left=lmeta,right=rmeta,image_content='Original rendered GLB geometry only',model_sha256=hashlib.sha256(model.read_bytes()).hexdigest(),sha256=hashlib.sha256(out.read_bytes()).hexdigest()),indent=1)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('model',type=Path);p.add_argument('output',type=Path);a=p.parse_args();draw(a.model,a.output)
