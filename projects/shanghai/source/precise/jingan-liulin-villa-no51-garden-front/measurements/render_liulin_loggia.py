"""Render the published garden front in the second historical camera, using only the GLBs."""
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

HERE = Path(__file__).resolve().parent
RASTER = HERE.parents[1]/'jingan-jiaozhou-450-garden-residence/measurements'
CLIP = HERE.parents[1]/'huangpu-zhengjia-lane-39-street-gate/measurements'
sys.path[:0] = [str(RASTER),str(CLIP)]
from photo_glb_raster import raster
from clip_courtyard_camera import clip_near_plane


def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()


def render(full, low, output):
    camera=np.array(json.loads((HERE/'no51-house-cameras.json').read_text())['source_poses']['gao06']['P'])
    canvas=Image.new('RGB',(1240,850),'#f5f2e9')
    draw=ImageDraw.Draw(canvas)
    def text(x,y,message,size,bold=False,color='#243832'):
        label='NotoSansCJK-'+('Bold' if bold else 'Regular')+'.ttc'
        font=ImageFont.truetype(str(Path('/usr/share/fonts/opentype/noto')/label),size,index=2)
        draw.text((x,y),message,fill=color,font=font)

    text(32,16,'柳林别业 51 号的花园柱廊',35,True)
    text(34,68,'愚园路 532 弄　　2014 年 6 月 2 日院内机位',18)
    sun=np.array([-.47,-.62,.63],dtype=np.float32)
    sun/=np.linalg.norm(sun)
    views=[
        (full,[838,0,4200,2880],(32,114),660,'园内所见的两层柱廊与两侧凸窗'),
        (low,[1265,1335,3025,1825],(728,114),478,'二楼弧栏和两端成对的方墩 · 远景模型'),
        (full,[2440,1730,2910,2540],(730,330),220,'底层柱头、收分柱身与双层柱础'),
        (full,[1420,1920,1800,2530],(985,330),217,'台座浅凹面与通长盖板'),
    ]
    records=[]
    with tempfile.TemporaryDirectory() as directory:
        work=Path(directory)
        library=work/'liulin-raster.so'
        subprocess.run(['cc','-O2','-shared','-fPIC',str(RASTER/'photo_glb_raster.c'),
                        '-o',str(library),'-lm'],check=True)
        lib=ctypes.CDLL(str(library))
        lib.paint.restype=lib.shadow_depth.restype=None
        for i,(asset,crop,(x,y),width,description) in enumerate(views):
            clipped=work/('full.glb' if asset==full else 'low.glb')
            if not clipped.exists():
                clip_near_plane(asset,clipped,camera)
            picture,stats=raster(clipped,lib,width*2,camera,crop,sun,[217,39])
            height=round(width*(crop[3]-crop[1])/(crop[2]-crop[0]))
            canvas.paste(picture.resize((width,height),Image.Resampling.LANCZOS),(x,y))
            text(x,y+height+8,description,15 if i>=2 else 17)
            records.append(dict(view=description,mesh_sha256=sha(asset),**stats))
    text(32,749,'栏杆由两段各 3 根以及中间 21 根方形花瓶栏杆柱组成。',21,True)
    text(32,796,'图中立面、铁艺、门窗与纹理均取自模型。整体尺度采用六处砖皮的名义高度 65 ± 5 毫米。',17)
    output.parent.mkdir(parents=True,exist_ok=True)
    canvas.save(output,quality=91,optimize=True)
    output.with_suffix('.json').write_text(json.dumps(dict(license='MIT',source_photo_pixels=0,
        station='gao06',views=records),ensure_ascii=False,indent=1)+'\n')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['full','lod','output']:
        parser.add_argument(name,type=Path)
    args=parser.parse_args()
    render(args.full,args.lod,args.output)
