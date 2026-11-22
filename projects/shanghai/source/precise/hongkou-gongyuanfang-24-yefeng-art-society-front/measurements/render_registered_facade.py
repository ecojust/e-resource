"""Render the exported mesh from three published camera positions at Gongyuanfang No. 24."""
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
    pose=HERE/'two-cameras-and-curved-sill.json'
    cameras=json.loads(pose.read_bytes())
    press_file=HERE/'press-entrance-camera.json'
    press=json.loads(press_file.read_bytes());cameras['press']=press['press']
    source={k:v for k,v in zip(('front','oblique_wall'),cameras['reference_images'])}
    source['press']={'url':press['image']['image'],'sha256':press['image']['sha256']}
    sun=np.array([-.38,-.72,.58],np.float32);sun/=np.linalg.norm(sun)
    canvas=Image.new('RGB',(1120,1005),(244,242,235))
    draw=ImageDraw.Draw(canvas)
    def label(x,y,txt,size,colour='#292d2b'):
        draw.text((x,y),txt,font=ImageFont.truetype(str(args.font),size=size),fill=colour)
    label(26,13,'公园坊24号　野风画会旧址',34)
    label(27,66,'从两期公开照片的三个实拍位置观察模型',20)
    rows=[
        ('numbered-front','front',[0,40,578,853],438,(24,106),'2019年图6　卵石墙、双层弧窗与退台敞廊'),
        ('entry-to-lane','press',[0,86,520,802],413,(486,106),'2022年刊图　红砖券内的门与四级台阶'),
        ('gable-window','oblique_wall',[405,170,590,325],186,(916,106),'山墙最上层的木窗'),
        ('guard','oblique_wall',[414,335,640,557],186,(916,385),'下窗的铁网和窗台'),
        ('curved-heads','front',[263,388,500,493],360,(24,755),'上层窗洞与弧形敞廊的下缘'),
        ('threshold','press',[108,527,424,677],410,(486,722),'门槛、灰色水泥裙墙与台阶中部的窄坡'),
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
            report[name]={**stats,'source_photo_sha256':source[key]['sha256']}
    label(27,965,'原创网格渲染。屋面只做到近檐和后梁之间，拍摄日期未载的旧址照片按2022年刊出时间标注。',16,'#555950')
    fig=args.output/'no24-three-published-views.jpg'
    canvas.save(fig,quality=92,subsampling=0,optimize=True)
    out=dict(mesh_sha256=sha(args.mesh),camera_sha256=sha(pose),comparison_jpg_sha256=sha(fig),
             photographs_embedded=False,sources=[r['url']for r in source.values()],press_camera_sha256=sha(press_file),
             views=report)
    (args.output/'registered-no24.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
