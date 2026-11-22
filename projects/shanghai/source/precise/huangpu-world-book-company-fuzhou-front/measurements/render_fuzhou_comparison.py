"""Pair Fayhoo's 2015 Fuzhou Road photograph with a render of the released mesh."""
import argparse
import ctypes
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

HERE=Path(__file__).resolve().parent
BACKEND=HERE.parents[1]/"huangpu-yuanmingyuan-apartments-street-front/measurements"
sys.path.insert(0,str(BACKEND))
sys.path.insert(0,str(HERE.parent/"source"))
from photo_glb_raster import raster
from fuzhou_photo_plane import CAMERAS
from fuzhou_skylight import SurfaceCapture, horizon_shading

CROP=(250,42,1265,1424)
DETAIL=[("东侧窗裙、红色窗台与浅灰砖缝",(1022,860,1245,1065)),
        ("中部壁柱与连续压顶",(713,158,1032,392))]

def checksum(f):
    return hashlib.sha256(f.read_bytes()).hexdigest()

def april_light():
    hour=17+56/60+18/3600
    lat,lon=math.radians(31.234),121.481
    g=2*math.pi/365*(94-1+(hour-12)/24)
    eq=229.18*(.000075+.001868*math.cos(g)-.032077*math.sin(g)-.014615*math.cos(2*g)-.040849*math.sin(2*g))
    dec=.006918-.399912*math.cos(g)+.070257*math.sin(g)-.006758*math.cos(2*g)+.000907*math.sin(2*g)-.002697*math.cos(3*g)+.00148*math.sin(3*g)
    ha=math.radians((60*hour+eq+4*lon-480)/4-180)
    en=np.array([-math.cos(dec)*math.sin(ha),math.sin(dec)*math.cos(lat)-math.cos(dec)*math.cos(ha)*math.sin(lat)])
    up=math.sin(lat)*math.sin(dec)+math.cos(lat)*math.cos(dec)*math.cos(ha)
    t=math.radians(70.952)
    light=np.array([en@np.array([math.sin(t),math.cos(t)]),en@np.array([-math.cos(t),math.sin(t)]),up],np.float32)
    light/=np.linalg.norm(light)
    return light,[round(math.degrees(math.atan2(en[0],en[1]))%360,2), round(math.degrees(math.asin(up)),2)]

def font(size,bold=False):
    name='NotoSansCJK-Bold.ttc' if bold else 'NotoSansCJK-Regular.ttc'
    return ImageFont.truetype('/usr/share/fonts/opentype/noto/'+name,size,index=2)

def render(source,photo,output,width):
    assert checksum(photo)=='d4458ee4422ade274ea0a74d5dda71666da1e9a24b8f3cf6f8ba74ca9239e568'
    original=Image.open(photo).convert('RGB')
    assert original.size==(2144,1424)
    sun,angles=april_light()
    with tempfile.TemporaryDirectory() as temp:
        libfile=Path(temp)/'raster.so'
        subprocess.run(['cc','-O2','-fPIC','-shared','-o',str(libfile),str(BACKEND/'photo_glb_raster.c'),'-lm'],check=True)
        lib=ctypes.CDLL(str(libfile))
        lib.shadow_depth.restype=lib.paint.restype=None
        surfaces=SurfaceCapture(lib,source)
        rendered,meta=raster(source,surfaces,width,CAMERAS['2015_street'],CROP,sun,angles)
        rendered,blocked=horizon_shading(rendered,surfaces.depth,CAMERAS['2015_street'],CROP)
        meta['local_sky_occlusion']={'direction_sectors':8,'radius_m':1.25,'mean_visible_horizon_factor':blocked}
    bg=(248,246,241);ink=(44,36,31);muted=(94,83,72)
    out=Image.new('RGB',(1500,1670),bg)
    d=ImageDraw.Draw(out);f=width/(CROP[2]-CROP[0]);cols=(34,765)
    d.text((34,18),'世界书局大楼 · 福州路立面',font=font(42,True),fill=ink)
    d.text((36,81),'上海市黄浦区福州路 390 号　｜　2015 年 4 月 4 日',font=font(21),fill=muted)
    pw,top=698,156;h=round(pw*(CROP[3]-CROP[1])/(CROP[2]-CROP[0]))
    for x,title,img in zip(cols,('福州路街景','同机位三维模型'),(original.crop(CROP),rendered)):
        d.text((x,116),title,font=font(22,True),fill=ink)
        out.paste(img.resize((pw,h),Image.Resampling.LANCZOS),(x,top))
    y=top+h+22
    for x,(caption,box) in zip(cols,DETAIL):
        local=tuple(round((v-CROP[i%2])*f)for i,v in enumerate(box))
        d.text((x,y),caption,font=font(21,True),fill=ink)
        for k,img in enumerate((original.crop(box),rendered.crop(local))):
            out.paste(ImageOps.fit(img,(342,265),method=Image.Resampling.LANCZOS),(x+k*356,y+42))
    line=y+325
    d.line((34,line,1463,line),fill=(200,192,181))
    d.text((34,line+11),'摄影　Fayhoo · Wikimedia Commons · CC BY-SA 3.0（局部裁切）',font=font(18),fill=muted)
    d.text((34,line+40),'模型与对照图　CC BY-SA 3.0。窗框、贴面和压顶的进深按 2015 年街景与 2016 年登记照片估算。',font=font(17),fill=muted)
    out.crop((0,0,1500,line+79)).save(output,quality=94,optimize=True,subsampling=0)
    meta.update({'subject':'世界书局大楼福州路立面','photo_credit':'Fayhoo, 2015-04-04 17:56:18 local, CC BY-SA 3.0','primary_photo_page':'https://commons.wikimedia.org/wiki/File:Waiwen_Shudian.JPG','panel_license':'https://creativecommons.org/licenses/by-sa/3.0/','source_photo_sha256':checksum(photo),'input_glb_sha256':checksum(source),'camera_record_sha256':checksum(HERE/'fuzhou-street-cameras.json'),'primary_detail_crops':DETAIL,'plate_sha256':checksum(output)})
    output.with_suffix('.json').write_text(json.dumps(meta,ensure_ascii=False,indent=1)+'\n')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for arg in ('model','photo','output'):parser.add_argument(arg,type=Path)
    parser.add_argument('--width',type=int,default=1870)
    a=parser.parse_args();render(a.model,a.photo,a.output,a.width)
