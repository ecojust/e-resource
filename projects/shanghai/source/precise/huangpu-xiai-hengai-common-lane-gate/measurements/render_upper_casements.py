"""Render the measured upper gatehouse windows from the GLB in their photographic perspectives."""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image,ImageDraw,ImageFont

HERE=Path(__file__).resolve().parent
RASTER=HERE.parents[1]/"huangpu-yuanmingyuan-apartments-street-front"/"measurements"
sys.path[:0]=[str(HERE.parent/"source"),str(RASTER)]
from yongjia_photo_plane import matrix
from photo_glb_raster import raster


def font(n,bold=False):
    name="NotoSansCJK-Bold.ttc" if bold else "NotoSansCJK-Regular.ttc"
    return ImageFont.truetype("/usr/share/fonts/opentype/noto/"+name,n,index=2)


def build(model,dest):
    board=Image.new("RGB",(1450,815),"#f3f0e8")
    draw=ImageDraw.Draw(board)
    draw.text((34,16),"永嘉路19弄、21弄　共用门屋二层高窗",font=font(37,True),fill="#34312c")
    draw.text((36,75),"按2015年12月的开窗状态复原。2020年同门屋的闭窗记录提供了每扇四格的分隔依据。",font=font(20),fill="#5d554d")
    details=[("center15-upper",(300,188,749,541),"正面两窗",(36,155,735,560)),
             ("west15-upper",(505,219,638,454),"从街道西侧看右窗的开启",(795,155,295,545)),
             ("center15-upper",(326,220,487,480),"左窗遮眉及直框",(1114,155,295,545))]
    logs=[]
    sun=np.array([-.71,-.35,.61],np.float32);sun/=np.linalg.norm(sun)
    with tempfile.TemporaryDirectory() as t:
        so=Path(t)/"raster.so";subprocess.run(["cc","-O2","-shared","-fPIC","-o",so,RASTER/"photo_glb_raster.c","-lm"],check=True)
        lib=ctypes.CDLL(str(so));lib.shadow_depth.restype=lib.paint.restype=None
        for camera,crop,title,(x,y,width,height) in details:
            im,meta=raster(model,lib,850,matrix(camera),crop,sun,[240,38])
            im.thumbnail((width,height),Image.Resampling.LANCZOS)
            board.paste(im,(x,y));draw.text((x,y-37),title,font=font(20,True),fill="#37322c")
            logs.append({"camera":camera,"title":title,**meta})
    draw.text((36,749),"右窗两叶的转角为影像估算。左侧白色拱窗、相邻商铺和临时装饰均在本组取景之外。",font=font(18),fill="#524a42")
    board.save(dest,quality=90)
    dest.with_suffix(".json").write_text(json.dumps({"model_sha256":hashlib.sha256(model.read_bytes()).hexdigest(),"board_sha256":hashlib.sha256(dest.read_bytes()).hexdigest(),"source":"Original GLB rasterization. The images contain no street panorama pixels. Fixed study illumination.","views":logs},ensure_ascii=False,indent=2)+"\n")


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("model",type=Path);p.add_argument("output",type=Path);a=p.parse_args();build(a.model,a.output)
