"""Produce a licensed source/model comparison and two survey-camera model views."""
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
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
RASTER = HERE.parents[1]/'jingan-jiaozhou-450-garden-residence/measurements'
CLIP = HERE.parents[1]/'huangpu-zhengjia-lane-39-street-gate/measurements'
sys.path[:0] = [str(RASTER),str(CLIP)]
from photo_glb_raster import raster
from clip_courtyard_camera import clip_near_plane
from fit_southern_lintel import EVIDENCE, OBS, METRES


def camera(index, layout):
    observation = OBS[index]
    delta = layout['sources'][observation['name']]['yaw_pitch_roll_correction_degrees']
    az,pitch,roll = np.radians([observation['az']+delta[0],observation['pitch']+delta[1],delta[2]])
    forward = np.array([np.sin(az),np.cos(az),0.])
    across = np.array([np.cos(az),-np.sin(az),0.])
    up = np.array([0.,0.,1.])
    view = forward*np.cos(pitch)+up*np.sin(pitch)
    vertical = -forward*np.sin(pitch)+up*np.cos(pitch)
    side = across*np.cos(roll)+vertical*np.sin(roll)
    top = vertical*np.cos(roll)-across*np.sin(roll)
    f = observation['width']/(2*np.tan(np.deg2rad(observation['hfov'])/2))
    proj = np.stack([view*observation['width']/2+f*side,
                     view*observation['height']/2-f*top,view])
    origin = np.array(layout['origin_wgs84'])
    angle = math.radians(layout['x_bearing_degrees'])
    axes = np.array([[math.sin(angle),-math.cos(angle),0.],
                     [math.cos(angle),math.sin(angle),0.],[0.,0.,1.]])
    eye = np.r_[(np.array(observation['position_wgs84'])-origin)*METRES,observation['height_m']]
    return np.column_stack([proj@axes, -proj@eye])


def draw(original, near, far, out):
    data = json.loads((HERE/'southern-lane-registration.json').read_bytes())
    source = EVIDENCE['commons']
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    if digest(original) != source['sha256']:
        raise ValueError('Unexpected Commons original')
    canvas = Image.new('RGB',(1280,720),'#f1eee8')
    pen = ImageDraw.Draw(canvas)
    def label(x,y,phrase,size,bold=False):
        weight = 'Bold' if bold else 'Regular'
        font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-'+weight+'.ttc',size,index=2)
        pen.text((x,y),phrase,font=font,fill='#302c25')
    label(30,14,'荣康别墅南口的双峰门额',35,True)
    label(31,68,'常熟路　｜　两翼各三道横带，中央浅色卷饰和贯通下沿',19)
    crop = [2445,2030,3201,2292]
    original_panel = Image.open(original).crop(crop)
    canvas.paste(original_panel.resize((640,222),Image.Resampling.LANCZOS),(30,137))
    label(32,102,'2017年8月19日　原照局部',19,True)
    label(32,363,'Antigng 摄《荣康别墅》／Wikimedia Commons，CC BY-SA 4.0。',14)
    sun = np.array([-.55,-.64,.535],np.float32)
    sun /= np.linalg.norm(sun)
    angles=[float(np.degrees(np.arctan2(sun[0],sun[1]))%360),float(np.degrees(np.arcsin(sun[2])))]
    shots = [(near,0,[170,146,439,252],30,437,645,'2021年北站　近景模型'),
             (far,2,[386,143,608,244],712,139,531,'2017年9月斜视　低面数模型'),
             (near,0,[282,180,332,221],729,429,281,'中央纹样　近景模型')]
    records = []
    with tempfile.TemporaryDirectory() as td:
        temp = Path(td);so=temp/'raster.so'
        subprocess.run(['cc','-O2','-shared','-fPIC',str(RASTER/'photo_glb_raster.c'),'-lm','-o',str(so)],check=True)
        lib=ctypes.CDLL(str(so));lib.paint.restype=lib.shadow_depth.restype=None
        for idx,(mesh,k,region,x,y,w,caption) in enumerate(shots):
            P = camera(k,data)
            clipped = temp/(str(idx)+'.glb')
            stats=clip_near_plane(mesh,clipped,P)
            panel,record=raster(clipped,lib,round(w*1.35),P,region,sun,angles)
            size=(w,round(panel.height*w/panel.width))
            canvas.paste(panel.resize(size,Image.Resampling.LANCZOS),(x,y))
            label(x,y-33,caption,18,True)
            records.append({'station':OBS[k]['station'],'camera_date':OBS[k]['date'],'model':digest(mesh),
                            'clip':stats,'render':record})
    label(1032,460,'双峰间有一',17);label(1032,491,'道浅弧凹口。',17)
    label(1032,545,'门额宽约',17);label(1032,571,'3.50 米。',22,True)
    label(31,681,'历史立面按实照量测。图案没有可确认的文字释读。图板含署名原照裁图，按 CC BY-SA 4.0 提供。',15)
    out.parent.mkdir(exist_ok=True,parents=True)
    canvas.save(out,quality=90,optimize=True)
    out.with_suffix('.json').write_text(json.dumps({'board_sha256':digest(out),'license':'CC BY-SA 4.0',
        'license_url':source['license_url'],'commons_original':source['page'],'photographer':source['author'],
        'cropped_original_pixels':crop,'other_photographs_reproduced':False,'renders':records},ensure_ascii=False,indent=1)+'\n')


if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('commons',type=Path);p.add_argument('near',type=Path);p.add_argument('far',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();draw(a.commons,a.near,a.far,a.output)
