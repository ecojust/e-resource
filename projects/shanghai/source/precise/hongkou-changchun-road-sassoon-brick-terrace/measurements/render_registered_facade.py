"""Render the exported mesh from the 2015 and 2023 viewpoints of the same eight bays."""
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
    pose=HERE/'north-frontage-cameras.json'
    cameras=json.loads(pose.read_bytes())
    source={('gao' if 'gao-' in r['file'] else 'front'):r for r in cameras['source_images']}
    sun=np.array([-.61,-.64,.47],dtype=np.float32)
    sun/=np.linalg.norm(sun)
    canvas=Image.new('RGB',(1050,843),(244,242,235))
    draw=ImageDraw.Draw(canvas)
    def label(x,y,txt,size,colour='#292d2b'):
        draw.text((x,y),txt,font=ImageFont.truetype(str(args.font),size=size),fill=colour)
    label(26,12,'长春路沙逊楼群　临街八开间',32)
    label(27,60,'同一段北立面在两处相机位置下的模型投影',19)
    rows=[
        ('street','front',[0,0,865,576],490,(25,105),'临街正面　两端是双山花，中央为四个开间'),
        ('earlier','gao',[0,0,4000,2760],484,(542,105),'2015年的斜视机位　楼身319号位于左侧第二轴'),
        ('arches','front',[72,158,501,391],490,(25,495),'上层中央的扁弧窗与二层的红砖券'),
        ('plate','front',[99,292,384,460],484,(542,478),'楼身号码牌在院墙后方，两者处在不同平面'),
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
    label(26,802,'图像由解压后的近景 GLB 生成。相机依据上海虹口所刊正照及高参88于2015年4月25日拍摄的原片。',16,'#555950')
    fig=args.output/'eight-bays-and-two-cameras.jpg'
    canvas.save(fig,quality=92,subsampling=0,optimize=True)
    out=dict(mesh_sha256=sha(args.mesh),camera_sha256=sha(pose),comparison_jpg_sha256=sha(fig),
             photographs_embedded=False,sources=[source['front']['ref'],source['gao']['ref']],
             views=report)
    (args.output/'registered-terrace.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
