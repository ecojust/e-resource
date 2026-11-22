"""Compare the 195 South Shaanxi Road frontage to WQL's 2018 photograph in the same projection."""
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
SIBLINGS=HERE.parents[1]
RASTER=SIBLINGS/"huangpu-yuanmingyuan-apartments-street-front/measurements"
sys.path[:0]=[str(HERE.parent/"source"),str(RASTER),str(SIBLINGS/"huangpu-world-book-company-fuzhou-front/measurements")]
from photo_glb_raster import raster
from fuzhou_skylight import SurfaceCapture,horizon_shading
from west_photo_plane import matrix,CALIBRATION

CROP=(524,650,3250,2445)
DETAILS=[("南侧门廊的圆券与吊灯",(2650,1536,2980,1763)),("二层格窗与短长相间的红砖边",(1948,964,2383,1252))]

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def daylight():
    hour=14+24/60+55/3600;d=161;lat,lon=math.radians(31.215),121.456
    g=2*math.pi/365*(d-1+(hour-12)/24)
    eq=229.18*(.000075+.001868*math.cos(g)-.032077*math.sin(g)-.014615*math.cos(2*g)-.040849*math.sin(2*g))
    dec=.006918-.399912*math.cos(g)+.070257*math.sin(g)-.006758*math.cos(2*g)+.000907*math.sin(2*g)-.002697*math.cos(3*g)+.00148*math.sin(3*g)
    ha=math.radians((60*hour+eq+4*lon-480)/4-180)
    en=np.array([-math.cos(dec)*math.sin(ha),math.sin(dec)*math.cos(lat)-math.cos(dec)*math.cos(ha)*math.sin(lat)])
    up=math.sin(lat)*math.sin(dec)+math.cos(lat)*math.cos(dec)*math.cos(ha)
    azi=math.radians(CALIBRATION["metric_measured"]["approx_x_bearing_deg"])
    light=np.array([en@np.array([math.sin(azi),math.cos(azi)]),en@np.array([-math.cos(azi),math.sin(azi)]),up],dtype='float32')
    light/=np.linalg.norm(light)
    return light,[round(math.degrees(math.atan2(en[0],en[1]))%360,2),round(math.degrees(math.asin(up)),2)]

def font(size,bold=False):
    return ImageFont.truetype('/usr/share/fonts/opentype/noto/'+('NotoSansCJK-Bold.ttc' if bold else 'NotoSansCJK-Regular.ttc'),size,index=2)

def build(model,photo,output,width):
    assert sha(photo)=='96a5a7a4ab2042a0dd613e5290c215b121941e5b0af42fa2e5d43582860df9c5'
    ref=Image.open(photo).convert('RGB');assert ref.size==(4160,3120)
    cam=matrix('2018_commons');sun,angles=daylight()
    with tempfile.TemporaryDirectory() as tmp:
        shared=Path(tmp)/'raster.so';subprocess.run(['cc','-O2','-shared','-fPIC','-o',str(shared),str(RASTER/'photo_glb_raster.c'),'-lm'],check=True)
        lib=ctypes.CDLL(str(shared));lib.shadow_depth.restype=lib.paint.restype=None;capture=SurfaceCapture(lib,model)
        result,meta=raster(model,capture,width,cam,CROP,sun,angles)
        result,blocked=horizon_shading(result,capture.depth,cam,CROP)
    r=Image.Resampling.LANCZOS;cols=[34,899];pw=830;top=151;h=round(pw*(CROP[3]-CROP[1])/(CROP[2]-CROP[0]))
    paper=Image.new('RGB',(1768,1260),(246,245,239));draw=ImageDraw.Draw(paper);ink=(45,40,35);muted=(91,84,75)
    draw.text((34,14),'陕西南路 195 号住宅 · 临街西立面',font=font(40,True),fill=ink)
    draw.text((36,74),'上海市黄浦区　｜　2018 年 6 月 10 日',font=font(21),fill=muted)
    for x,title,im in zip(cols,['街道实景','同机位三维模型'],[ref.crop(CROP),result]):
        draw.text((x,111),title,font=font(23,True),fill=ink);paper.paste(im.resize((pw,h),r),(x,top))
    pos=top+h+23;scale=width/(CROP[2]-CROP[0])
    for x,(title,rect) in zip(cols,DETAILS):
        draw.text((x,pos),title,font=font(22,True),fill=ink)
        crop=tuple(round((v-CROP[k%2])*scale)for k,v in enumerate(rect))
        for k,im in enumerate([ref.crop(rect),result.crop(crop)]):
            paper.paste(ImageOps.fit(im,(408,281),method=r),(x+k*422,pos+43))
    line=pos+344;draw.line((34,line,1727,line),fill=(195,189,179))
    draw.text((34,line+11),'摄影　WQL · Wikimedia Commons · CC BY-SA 4.0（局部裁切）',font=font(18),fill=muted)
    draw.text((34,line+41),'登记地址为陕西南路 191—197 号。本图仅重建可由 195 号实照交叉定位的临街外部，比例、门廊进深和色泽按影像估算。',font=font(17),fill=muted)
    paper.crop((0,0,1768,line+81)).save(output,quality=94,optimize=True,subsampling=0)
    meta.update({'source_photo_sha256':sha(photo),'model_input_sha256':sha(model),'camera_sha256':sha(HERE/'west-upper-window-calibration.json'),'geometry_scope':'2018 publicly visible facade of no. 195','photographer':'WQL','photo_url':'https://commons.wikimedia.org/wiki/File:%E9%99%95%E8%A5%BF%E5%8D%97%E8%B7%AF195%E5%8F%B7.jpg','license':'https://creativecommons.org/licenses/by-sa/4.0/','exposure_local':'2018-06-10 14:24:55','detail_original_rectangles':DETAILS,'near_field_sky_occlusion':blocked,'plate_sha256':sha(output)})
    output.with_suffix('.json').write_text(json.dumps(meta,indent=1,ensure_ascii=False)+'\n')

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ['mesh','photo','output']:ap.add_argument(name,type=Path)
    ap.add_argument('--width',type=int,default=2600)
    a=ap.parse_args();build(a.mesh,a.photo,a.output,a.width)
