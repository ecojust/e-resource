"""Render the three measured exterior shutters from the GLB in their photographic perspectives."""
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
from hefei_photo_plane import matrix
from photo_glb_raster import raster


def font(n,bold=False):
    name="NotoSansCJK-Bold.ttc" if bold else "NotoSansCJK-Regular.ttc"
    return ImageFont.truetype("/usr/share/fonts/opentype/noto/"+name,n,index=2)


def build(model,dest):
    board=Image.new("RGB",(1450,815),"#f3f0e8")
    draw=ImageDraw.Draw(board)
    draw.text((34,16),"合肥路592弄弄口　东侧山墙百叶窗",font=font(37,True),fill="#34312c")
    draw.text((36,75),"沿街向弄内看，白墙的三处开口可见。此图按2015年2月街道观测绘制。",font=font(20),fill="#5d554d")
    details=[("2015_west",(175,175,380,509),"三处开口",(36,155,350,570)),
             ("2015_oblique",(294,296,487,397),"从西侧看两副上层百叶",(417,155,485,386)),
             ("2015_west",(284,375,344,483),"下层合拢木扇",(960,155,450,580))]
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
    draw.text((36,749),"上层朝弄内的一扇向外翻开，显露浅色背面。下层木扇上实下透，斜叶片数与开启角度为摄影估算。",font=font(18),fill="#524a42")
    board.save(dest,quality=90)
    dest.with_suffix(".json").write_text(json.dumps({"model_sha256":hashlib.sha256(model.read_bytes()).hexdigest(),"board_sha256":hashlib.sha256(dest.read_bytes()).hexdigest(),"source":"Original GLB rasterization. The images contain no street panorama pixels. Fixed study illumination.","views":logs},ensure_ascii=False,indent=2)+"\n")


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("model",type=Path);p.add_argument("output",type=Path);a=p.parse_args();build(a.model,a.output)
