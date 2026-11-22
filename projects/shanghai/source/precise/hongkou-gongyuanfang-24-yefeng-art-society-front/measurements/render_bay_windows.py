"""Render the full and reduced models from the two published photographic viewpoints."""
import argparse
import ctypes
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE=Path(__file__).resolve().parent
RASTER=HERE.parents[1]/'jingan-jiaozhou-450-garden-residence/measurements'
sys.path[:0]=[str(RASTER),str(HERE.parent/'source')]
from photo_glb_raster import raster
from frontage_coordinates import FRONT_CAMERA

def render(near, far, output, metadata):
    press=np.asarray(json.loads((HERE/'press-entrance-camera.json').read_bytes())['press'])
    board=Image.new('RGB',(1040,1000),'#f6f3ed')
    draw=ImageDraw.Draw(board)

    def label(x,y,value,size,bold=False):
        weight='Bold' if bold else 'Regular'
        font=ImageFont.truetype(f'/usr/share/fonts/opentype/noto/NotoSansCJK-{weight}.ttc',size,index=2)
        draw.text((x,y),value,fill='#272d2a',font=font)

    label(32,22,'公园坊24号弧形砖凸窗',35,True)
    label(32,83,'二层中扇外开。斜面露出的棕色扇背和白边，遮住右窗一小段。',21)
    # Top row shares both the camera and crop so detail levels can be compared directly.
    panels=[
        (near,FRONT_CAMERA,'2019 figure 06',(281,417,508,586),(32,136,472,320),'二层外开窗 · 近景'),
        (far,FRONT_CAMERA,'2019 figure 06',(281,417,508,586),(533,136,472,320),'同一视角 · 远景'),
        (near,press,'published 2022',(315,261,510,466),(32,518,472,350),'一层三扇白窗与连续石窗台'),
        (far,FRONT_CAMERA,'2019 figure 06',(328,748,521,817),(533,518,466,180),'三扇上亮的卷花铁格'),
        (near,FRONT_CAMERA,'2019 figure 06',(336,757,400,810),(533,740,180,126),'最左窗的局部'),
    ]
    sun=np.array([-.47,-.66,.71]);sun/=np.linalg.norm(sun)
    angles=[float(np.degrees(np.arctan2(sun[0],sun[1]))%360),float(np.degrees(np.arcsin(sun[2])))]
    views=[]
    with tempfile.TemporaryDirectory() as tmp:
        so=Path(tmp)/'raster.so'
        subprocess.run(['cc','-shared','-O2','-fPIC',RASTER/'photo_glb_raster.c','-lm','-o',so],check=True)
        lib=ctypes.CDLL(str(so));lib.paint.restype=lib.shadow_depth.restype=None
        for asset,camera,name,crop,(x,y,w,h),caption in panels:
            image,stats=raster(asset,lib,round(w*1.4),camera,crop,sun,angles)
            image.thumbnail((w,h),Image.Resampling.LANCZOS)
            board.paste(image,(x,y));label(x,y+h+3,caption,18,True)
            views.append(dict(crop=crop,caption=caption,camera=name,
                              mesh_sha256=hashlib.sha256(asset.read_bytes()).hexdigest(),**stats))
    label(32,929,'取景依据　虹口区2019年《公园坊24号现状》与文化虹口2022年所刊《野风画会旧址》。',17)
    label(32,963,'画面均由本项目三维模型生成。外开角与玻璃嵌深依据照片估计。',16)
    board.save(output,quality=91,optimize=True)
    metadata.write_text(json.dumps(dict(images=views,plate_sha256=hashlib.sha256(output.read_bytes()).hexdigest()),ensure_ascii=False,indent=1)+'\n')

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for key in ('near','far','image','metadata'):parser.add_argument(key,type=Path)
    args=parser.parse_args()
    render(args.near,args.far,args.image,args.metadata)
