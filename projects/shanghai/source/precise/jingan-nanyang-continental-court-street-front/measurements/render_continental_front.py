"""Draw four original, photo-registered views from the released near and far street frontages."""
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

HERE=Path(__file__).resolve().parent
RASTER=HERE.parents[1]/'jingan-jiaozhou-450-garden-residence/measurements'
sys.path[:0]=[str(RASTER),str(HERE.parent/'source')]
from photo_glb_raster import raster
from continental_street_wall import Bay

def checksum(f):
    with f.open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def draw(full,lod,output):
    photo=json.loads((HERE/'street-photo-registration.json').read_text())['photos']
    P={tag:np.array(row['P_native'])for tag,row in photo.items()}
    def framing(tag,baynum,ulo,uhi,zlo,zhi,pad):
        bay=Bay(baynum)
        world=np.array([[*bay.point(u,.44,z),1.]for u in np.linspace(ulo,uhi,8)for z in (zlo,zhi)])
        q=world@P[tag].T;uv=q[:,:2]/q[:,2,None]
        return np.round(np.r_[uv.min(axis=0)-pad,uv.max(axis=0)+pad]).astype(int).tolist()
    size=(1290,926);canvas=Image.new('RGB',size,'#f4f0e6');g=ImageDraw.Draw(canvas)
    def line(x,y,words,px,bold=False):
        f=Path('/usr/share/fonts/opentype/noto')/('NotoSansCJK-Bold.ttc'if bold else'NotoSansCJK-Regular.ttc')
        g.text((x,y),words,font=ImageFont.truetype(str(f),px,index=2),fill='#283d35')
    line(31,10,'南洋大楼的十一跨转角',33,True)
    line(32,62,'陕西北路与南京西路　　1927 年竣工的 Continental Court Apartments',18)
    jobs=[('a',full,[545,325,4750,2500],(32,112),765,410,'南京西路望向街角，四层临街立面自北翼转入陕西北路。'),
          ('e',lod,[0,0,2000,1317],(834,112),422,410,'陕西北路一侧的水刷石尖墩与成对长窗 · 远景模型'),
          ('c',full,framing('c',7,.07,5.2,7.52,12.05,40),(32,557),429,231,'菱形砖间饰、四瓣浮雕与灰色窗框'),
          ('a',full,framing('a',4,.08,5.29,15.42,17.55,44),(484,557),415,231,'四处方形凹口和口顶细条'),
          ('d',full,framing('d',5,.06,5.36,4.43,12.92,30),(922,557),334,231,'三联凸窗与逐层挑出的灰石线脚')]
    light=np.array([-.53,.63,.57],dtype=np.float32);light/=np.linalg.norm(light);data=[]
    with tempfile.TemporaryDirectory()as tmp:
        libfile=Path(tmp)/'render.so'
        subprocess.run(['cc','-O2','-shared','-fPIC',str(RASTER/'photo_glb_raster.c'),'-o',str(libfile),'-lm'],check=True)
        lib=ctypes.CDLL(str(libfile));lib.paint.restype=lib.shadow_depth.restype=None
        for tag,mesh,crop,(x,y),width,height,label in jobs:
            scale=min(width/(crop[2]-crop[0]),height/(crop[3]-crop[1]))
            dw=max(1,round(scale*(crop[2]-crop[0])));dh=max(1,round(scale*(crop[3]-crop[1])))
            im,meta=raster(mesh,lib,round(dw*1.6),P[tag],crop,light,[320,35])
            canvas.paste(im.resize((dw,dh),Image.Resampling.LANCZOS),(x+(width-dw)//2,y+(height-dh)//2))
            line(x,y+height+7,label,14 if width<500 else 17)
            data.append(dict(source_camera=tag,label=label,asset_sha256=checksum(mesh),**meta))
    line(32,837,'十二根尖墩之间是十一跨。九组三联窗与二十四组双窗共开七十五个净窗洞。',20,True)
    line(33,882,'画面取自模型。街角平面与高程由照片和公开建筑轮廓拟合；窗后深度和部分遮挡位置为估值。',16)
    output.parent.mkdir(parents=True,exist_ok=True);canvas.save(output,quality=92,optimize=True)
    output.with_suffix('.json').write_text(json.dumps(dict(license='MIT',imported_photo_pixels=0,views=data),ensure_ascii=False,indent=1)+'\n')

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    for arg in ['full','lod','output']:ap.add_argument(arg,type=Path)
    a=ap.parse_args();draw(a.full,a.lod,a.output)
