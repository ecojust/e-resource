"""Join the dated Commons street photographs to the matching views of a released GLB."""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageOps

HERE=Path(__file__).resolve().parent
BASE=HERE.parents[1]
BACKEND=BASE/'huangpu-yuanmingyuan-apartments-street-front/measurements'
sys.path[:0]=[str(BACKEND),str(BASE/'huangpu-world-book-company-fuzhou-front/measurements'),str(HERE.parent/'source')]
from fuzhou_skylight import SurfaceCapture,horizon_shading
from photo_glb_raster import raster
from marconi_photo_plane import CALIBRATION

CROPS=[
    ('2017_front','main',(1780,2618,2764,4368),1200),
    ('2015_oblique','arch',(1540,3910,2150,4456),540),
    ('2017_front','capital',(1859,3281,2048,3459),430),
    ('2017_front','number',(2024,3348,2167,3470),430)
]
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def font(n,bold=False):
    name='NotoSansCJK-'+('Bold' if bold else 'Regular')+'.ttc'
    return ImageFont.truetype('/usr/share/fonts/opentype/noto/'+name,n,index=2)

def plate(model,front,side,out):
    photos={}
    for name,file in [('2017_front',front),('2015_oblique',side)]:
        if sha(file)!=CALIBRATION['cameras'][name]['sha256']:
            raise ValueError('Expected the original Commons file for '+name)
        photos[name]=ImageOps.exif_transpose(Image.open(file)).convert('RGB')
    canvas=Image.new('RGB',(1480,1780),'#f6f3ee');d=ImageDraw.Draw(canvas)
    ink,muted='#322e29','#62594f'
    d.text((38,20),'北京东路 131 号 · 砖拱入口',font=font(42,True),fill=ink)
    d.text((40,83),'1947 年电话簿所载马可尼公司地址　｜　2015 年、2017 年街景',font=font(22),fill=muted)
    views={}
    with tempfile.TemporaryDirectory() as work:
        so=Path(work)/'raster.so'
        subprocess.run(['cc','-O2','-fPIC','-shared','-o',str(so),str(BACKEND/'photo_glb_raster.c'),'-lm'],check=True)
        lib=ctypes.CDLL(str(so));lib.shadow_depth.restype=lib.paint.restype=None
        light=np.array([-.38,-.75,.72],dtype='float32');light/=np.linalg.norm(light)
        for idx,(cam,key,crop,width) in enumerate(CROPS):
            matrix=np.array(CALIBRATION['camera_matrices'][cam]);surfaces=SurfaceCapture(lib,model)
            rendered,meta=raster(model,surfaces,width,matrix,crop,light,None)
            rendered,ao=horizon_shading(rendered,surfaces.depth,matrix,crop)
            meta['mean_local_sky_occlusion']=ao
            meta['camera']=cam
            views[key]=meta
            paired=(photos[cam].crop(crop),rendered)
            if idx==0:
                for x,label,img in zip((38,751),('2017 年 8 月街景','同机位模型'),paired):
                    d.text((x,131),label,font=font(23,True),fill=ink)
                    h=round(690*(crop[3]-crop[1])/(crop[2]-crop[0]))
                    canvas.paste(img.resize((690,h),Image.Resampling.LANCZOS),(x,174))
            else:
                x=(38,518,998)[idx-1]; y=1435
                label=('2015 年侧看券肩与券腹','附柱的卷纹与叶饰','绿色 131 门牌')[idx-1]
                d.text((x,y),label,font=font(20,True),fill=ink)
                for j,img in enumerate(paired):
                    h=round(220*(crop[3]-crop[1])/(crop[2]-crop[0]))
                    canvas.paste(img.resize((220,h),Image.Resampling.LANCZOS),(x+230*j,y+42))
    d.line((38,1696,1440,1696),fill='#c9c3ba')
    d.text((38,1705),'摄影　Antigng · Wikimedia Commons · CC BY-SA 4.0，两张原照均作局部裁切。每组左图为照片，右图为模型。',font=font(17),fill=muted)
    d.text((38,1734),'模型按街景估算尺度。门上临时海报保留框体与外形。',font=font(16),fill=muted)
    out.parent.mkdir(parents=True,exist_ok=True)
    canvas.save(out,quality=93,optimize=True,subsampling=0)
    trace=json.loads((HERE/'portal-photo-traces.json').read_text())
    meta=dict(model_sha256=sha(model),plate_sha256=sha(out),views=views,
              photographs=[trace['primary'],trace['second']],plate_license='https://creativecommons.org/licenses/by-sa/4.0/',
              illustrative_light_xyz=light.tolist(),camera_record_sha256=sha(HERE/'marconi-front-cameras.json'))
    out.with_suffix('.json').write_text(json.dumps(meta,ensure_ascii=False,indent=1)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('model','photo_2017','photo_2015','output'):p.add_argument(k,type=Path)
    a=p.parse_args()
    plate(a.model,a.photo_2017,a.photo_2015,a.output)
