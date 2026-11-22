"""Render the exported mesh from the two recorded 2015 camera stations."""
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
SHARED = HERE.parents[1] / 'jingan-jiaozhou-450-garden-residence/measurements'
sys.path.insert(0, str(SHARED))
from photo_glb_raster import raster

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mesh',type=Path)
    parser.add_argument('output',type=Path)
    parser.add_argument('--font',type=Path,default=Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'))
    args=parser.parse_args()
    args.output.mkdir(exist_ok=True,parents=True)
    pose=HERE/'paired-entrance-cameras.json'
    cameras=json.loads(pose.read_bytes())
    source=json.loads((HERE/'paired-front-sightlines.json').read_bytes())['views']
    sun=np.array([-.61,-.64,.47],dtype=np.float32)
    sun/=np.linalg.norm(sun)
    canvas=Image.new('RGB',(1000,792),(244,242,235))
    draw=ImageDraw.Draw(canvas)
    def label(x,y,txt,size,colour='#292d2b'):
        draw.text((x,y),txt,font=ImageFont.truetype(str(args.font),size=size),fill=colour)
    label(26,14,'武进路225弄　双券宅门',32)
    label(27,61,'2015年7月19日两处相机位置所见的模型',19)
    rows=[
        ('04','camera_P',[0,0,3264,4912],413,(25,105),'院内全景，左为9号、右为11号'),
        ('08','camera_close_P',[0,52,4912,3160],502,(470,105),'近处仰视，两券的横档、气窗与二层窗'),
        ('cabinet','camera_P',[944,3250,1760,4205],196,(470,497),'两户之间的软管卷盘箱'),
        ('fan','camera_P',[1772,2040,3120,3375],268,(701,473),'11号券额、门牌与门洞'),
    ]
    report={}
    with tempfile.TemporaryDirectory() as tmp:
        libpath=Path(tmp)/'raster.so'
        subprocess.run(['cc','-O2','-fPIC','-shared',str(SHARED/'photo_glb_raster.c'),'-lm','-o',str(libpath)],check=True)
        lib=ctypes.CDLL(str(libpath));lib.paint.restype=lib.shadow_depth.restype=None
        for name,key,crop,width,loc,desc in rows:
            im,stats=raster(args.mesh,lib,width,np.asarray(cameras[key]),crop,sun,[224,28])
            canvas.paste(im,loc);x,y=loc
            label(x,y+im.height+5,desc,16)
            report[name]={**stats,'source_photo_sha256':source['08' if name=='08' else '04']['sha256']}
    label(26,758,'图像由解压后的近景 GLB 生成。照片来源为高参88《武进路225弄9号、11号一对经典的双门》。',15,'#555950')
    fig=args.output/'two-registered-views.jpg'
    canvas.save(fig,quality=92,subsampling=0,optimize=True)
    out=dict(mesh_sha256=sha(args.mesh),camera_sha256=sha(pose),comparison_jpg_sha256=sha(fig),
             photographs_embedded=False,source_url='https://blog.sina.com.cn/s/blog_5d1bdf480102vysd.html',
             views=report)
    (args.output/'registered-courtyard.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
