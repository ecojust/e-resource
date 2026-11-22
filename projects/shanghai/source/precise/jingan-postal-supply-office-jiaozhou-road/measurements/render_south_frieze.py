"""Render the lower spandrel and upper frieze from their measured survey poses."""

import argparse
import ctypes
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image,ImageDraw,ImageFont

HERE=Path(__file__).resolve().parent
RASTER=HERE.parents[1]/'jingan-jiaozhou-450-garden-residence/measurements'
CLIP=HERE.parents[1]/'huangpu-zhengjia-lane-39-street-gate/measurements'
sys.path[:0]=[str(RASTER),str(CLIP)]
from photo_glb_raster import raster
from clip_courtyard_camera import clip_near_plane


def draw(near,far,output,head):
    observations=HERE/'south-bay-frieze-observations.json'
    data=json.loads(observations.read_text())
    if head is None:head=data['layout']['window_head_z_m']
    board=Image.new('RGB',(1170,683),'#f0ede5')
    pen=ImageDraw.Draw(board)
    def text(x,y,copy,size,bold=False):
        family='Bold' if bold else 'Regular'
        font=ImageFont.truetype(f'/usr/share/fonts/opentype/noto/NotoSansCJK-{family}.ttc',size,index=2)
        pen.text((x,y),copy,font=font,fill='#302e28')
    text(30,20,'胶州路邮政旧址的窗间红饰带',36,True)
    text(31,75,'临街白楼南端双窗与端柱　｜　2015年两处冬季拍摄机位的模型视图',18)
    shots=[(near,'pair-2015-south',[309,1,546,307],30,129,360,'南斜视　窗间墙至挑檐'),
           (near,'pair-2015-north',[265,255,479,319],438,148,668,'一层双窗与楼上窗台之间的两段红色饰面'),
           (far,'pair-2015-north',[343,53,503,128],438,411,455,'二层窗边回折纹与浅色方框')]
    sun=np.asarray([-.35,-.72,.60],np.float32);sun/=np.linalg.norm(sun)
    angles=[float(np.degrees(np.arctan2(sun[0],sun[1]))%360),float(np.degrees(np.arcsin(sun[2])))]
    records=[]
    with tempfile.TemporaryDirectory() as td:
        directory=Path(td);so=directory/'render.so'
        subprocess.run(['cc','-O2','-shared','-fPIC',str(RASTER/'photo_glb_raster.c'),'-lm','-o',str(so)],check=True)
        lib=ctypes.CDLL(str(so));lib.paint.restype=lib.shadow_depth.restype=None
        for i,(mesh,key,crop,x,y,width,caption) in enumerate(shots):
            cam=np.array(data['cameras'][key]['matrix_reference_window_head'])
            cam[:,3]-=cam[:,2]*head
            clean=directory/(str(i)+'.glb');clip=clip_near_plane(mesh,clean,cam)
            # Keep the actual source picture crop, including the relative pitch.
            image,render=raster(clean,lib,round(width*1.45),cam,crop,sun,angles)
            ht=round(width*image.height/image.width)
            board.paste(image.resize((width,ht),Image.Resampling.LANCZOS),(x,y))
            text(x,y+ht+6,caption,17,True)
            records.append(dict(view=key,source_native_crop=crop,mesh_sha256=hashlib.sha256(mesh.read_bytes()).hexdigest(),render=render,clip=clip))
    text(31,640,'两窗中心相距约1.41米。饰面厚度和檐下凸出量为照片估计。',17)
    output.parent.mkdir(parents=True,exist_ok=True);board.save(output,quality=91,optimize=True)
    output.with_suffix('.json').write_text(json.dumps(dict(photo_pixels_embedded=False,head_z_m=head,views=records,calibration_sha256=hashlib.sha256(observations.read_bytes()).hexdigest(),board_sha256=hashlib.sha256(output.read_bytes()).hexdigest()),ensure_ascii=False,indent=1)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('near',type=Path);p.add_argument('far',type=Path);p.add_argument('output',type=Path);p.add_argument('--head',type=float)
    a=p.parse_args();draw(a.near,a.far,a.output,a.head)
