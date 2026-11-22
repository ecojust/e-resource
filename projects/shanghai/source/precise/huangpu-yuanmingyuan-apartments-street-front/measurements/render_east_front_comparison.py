"""Recreate the paired 2014 street photograph and the actual published Yuanmingyuan mesh."""
import argparse,ctypes,hashlib,json,math,subprocess,sys,tempfile
from pathlib import Path

import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageOps

from photo_glb_raster import raster
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'source'))
from east_photo_plane import CAMERAS

CROP=(488,16,4310,3264)
DETAILS=[('中央砖券与窗间石饰',(2625,1170,3235,1805)),('南山墙的 A.D. 铭牌',(1700,49,2620,870))]


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def winter_sun():
    # NOAA fractional-year sun position for the camera's local EXIF timestamp.
    hour=15+19/60+49/3600;lat=math.radians(31.2434);longitude=121.4836
    g=2*math.pi/365*(27-1+(hour-12)/24)
    eq=229.18*(.000075+.001868*math.cos(g)-.032077*math.sin(g)-.014615*math.cos(2*g)-.040849*math.sin(2*g))
    dec=.006918-.399912*math.cos(g)+.070257*math.sin(g)-.006758*math.cos(2*g)+.000907*math.sin(2*g)-.002697*math.cos(3*g)+.001480*math.sin(3*g)
    ha=math.radians((60*hour+eq+4*longitude-480)/4-180)
    en=np.array([-math.cos(dec)*math.sin(ha),math.sin(dec)*math.cos(lat)-math.cos(dec)*math.cos(ha)*math.sin(lat)])
    up=math.sin(lat)*math.sin(dec)+math.cos(lat)*math.cos(dec)*math.cos(ha)
    phi=math.radians(82.83855-90);axis=np.array([math.sin(phi),math.cos(phi)]);inside=[-axis[1],axis[0]]
    light=np.array([en@axis,en@inside,up],dtype=np.float32);light/=np.linalg.norm(light)
    return light,[round(math.degrees(math.atan2(en[0],en[1]))%360,2),round(math.degrees(math.asin(up)),2)]


def font(size,bold=False):
    name='NotoSansCJK-Bold.ttc' if bold else 'NotoSansCJK-Regular.ttc'
    return ImageFont.truetype(str(Path('/usr/share/fonts/opentype/noto')/name),size,index=2)


def make(model,photo,output,width):
    ref=json.loads((HERE/'heritage-register-and-street-photographs.json').read_bytes())['primary_street_photo']
    assert digest(photo)==ref['sha256'];natural=ImageOps.exif_transpose(Image.open(photo));assert natural.size==(4912,3264)
    light,angles=winter_sun()
    with tempfile.TemporaryDirectory()as d:
        libfile=Path(d)/'raster.so';subprocess.run(['cc','-O2','-fPIC','-shared','-o',str(libfile),str(HERE/'photo_glb_raster.c'),'-lm'],check=True)
        lib=ctypes.CDLL(str(libfile));lib.shadow_depth.restype=lib.paint.restype=None
        raw,meta=raster(model,lib,width,CAMERAS['2014_oblique'],CROP,light,angles)
    x0,y0,x1,y1=CROP;f=raw.width/(x1-x0);res=Image.Resampling.LANCZOS
    panel=Image.new('RGB',(1852,1580),(247,246,241));d=ImageDraw.Draw(panel);ink=(40,36,31);muted=(91,83,73)
    d.text((42,23),'圆明园公寓 · 东立面',font=font(44,True),fill=ink)
    d.text((44,89),'上海市黄浦区圆明园路 115 号　｜　2014 年 1 月 27 日',font=font(22),fill=muted)
    cols=[42,941];pw=868;top=176;mh=round(pw*(y1-y0)/(x1-x0));pos=top+mh+22
    for x,title,im in zip(cols,['街道实景','同机位三维模型'],[natural.crop(CROP),raw]):
        d.text((x,131),title,font=font(23,True),fill=ink);panel.paste(im.resize((pw,mh),res),(x,top))
    cell=424;h=310
    for col,(label,coords) in zip(cols,DETAILS):
        small=tuple(round((v-(x0 if i%2==0 else y0))*f)for i,v in enumerate(coords))
        d.text((col,pos),label,font=font(22,True),fill=ink)
        for j,im in enumerate([natural.crop(coords),raw.crop(small)]):
            img=ImageOps.fit(im,(cell,h),method=res,centering=(.5,.5));panel.paste(img,(col+j*(cell+16),pos+47))
    y=pos+47+h+22;d.line((42,y,1810,y),fill=(202,196,186),width=1)
    d.text((42,y+13),'摄影　Livelikerw · Wikimedia Commons · CC BY-SA 3.0（局部裁切）',font=font(19),fill=muted)
    d.text((42,y+46),'模型与对照图　CC BY-SA 3.0。窗洞进深与砖石色泽结合 2014 年街景和 2016 年登记照片估算。',font=font(18),fill=muted)
    panel.crop((0,0,1852,y+91)).save(output,quality=94,optimize=True,subsampling=0)
    meta.update({'subject':'圆明园公寓东立面与切角柱廊','model_sha256':digest(model),'photo_sha256':ref['sha256'],'photo_page':ref['page'],'photo_author':ref['Artist'],'photo_license':ref['LicenseUrl'],'plate_license':'https://creativecommons.org/licenses/by-sa/3.0/','camera_sha256':digest(HERE/'east-front-cameras.json'),'detail_original_rectangles':[xy for _,xy in DETAILS],'exposure_local':'2014-01-27 15:19:49 Asia/Shanghai','light_model':'Estimated solar direction, shadow map and hemispherical skylight. The procedural materials do not reproduce tree shadows or reflections.','plate_sha256':digest(output)})
    output.with_suffix('.json').write_text(json.dumps(meta,ensure_ascii=False,indent=1)+'\n')

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ['model','photo','output']:ap.add_argument(name,type=Path)
    ap.add_argument('--render-width',type=int,default=2380);a=ap.parse_args();make(a.model,a.photo,a.output,a.render_width)
