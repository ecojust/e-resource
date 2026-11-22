"""Render the public entrance passage and east-wall lettering of Guangfu Road 195 from its released mesh."""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from render_public_entrance import HERE, RASTER, clip_near_plane, east_camera, hall_camera, raster


def text(pen, xy, label, size=19, bold=False):
    family = 'Bold' if bold else 'Regular'
    font = ImageFont.truetype(f'/usr/share/fonts/opentype/noto/NotoSansCJK-{family}.ttc', size, index=2)
    pen.text(xy, label, font=font, fill='#292d2b')


def east_detail_camera():
    layout = json.loads((HERE / 'riverfront-layout.json').read_bytes())
    start, end = np.asarray(layout['east_return'])
    along = (end - start) / np.linalg.norm(end - start)
    outward = np.array([along[1], -along[0]])
    eye = np.r_[start + along*3.4 + outward*21, 16.73]
    rotation = np.array([[along[0], along[1], 0], [0, 0, -1], [-outward[0], -outward[1], 0]])
    k = np.array([[2300, 0, 390], [0, 2300, 190], [0, 0, 1]])
    return k @ np.column_stack([rotation, -rotation @ eye])


def draw_plan(pen, passage):
    x0, y0, width, height = 801, 135, 201, 358
    xm = x0 + width/2
    scale = height / 15
    def planar(x,y):
        return (round(xm+x*scale),round(y0+height-y*scale))
    west, east = [], []
    for left, right in passage['pier_centres_x_y_m']:
        west.append(tuple(left))
        east.append(tuple(right))
    for side in (west, east):
        for x,y in side:
            px,py=planar(x,y)
            pen.rectangle((px-4,py-5,px+4,py+5),fill='#303b3a')
        pen.line([planar(x,y) for x,y in side], fill='#727874', width=2)
    for x in (-2.46,2.46):
        pen.line([planar(x,.4),planar(x,14.91)],fill='#b89c5e',width=3)
    pen.line([planar(-2.4825,0),planar(2.4825,0)],fill='#9c5143',width=4)
    pen.line([planar(-4,14.91),planar(4,14.91)],fill='#6e7778',width=2)
    text(pen,(x0-16,y0-31),'首个可辨侧向转折',14)
    text(pen,(x0+44,y0+height+4),'临河门槛',15)
    text(pen,(xm-30,y0+height*.45),'14.9 m',16,True)


def produce(model, audit):
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    with tempfile.TemporaryDirectory() as tmp:
        w=Path(tmp)
        backend=w/'paint.so'
        subprocess.run(['cc','-O2','-shared','-fPIC',str(RASTER/'photo_glb_raster.c'),'-lm','-o',str(backend)],check=True)
        lib=ctypes.CDLL(str(backend));lib.paint.restype=lib.shadow_depth.restype=None
        def shot(camera,crop,width,sun):
            sun=np.array(sun,np.float32);sun/=np.linalg.norm(sun)
            angles=[float(np.degrees(np.arctan2(sun[0],sun[1]))%360),float(np.degrees(np.arcsin(sun[2])))]
            cut=w/'subject.glb';clip=clip_near_plane(model,cut,camera)
            image,stats=raster(cut,lib,round(width*1.25),camera,crop,sun,angles)
            out=image.resize((width,round(width*image.height/image.width)),Image.Resampling.LANCZOS)
            return out,dict(camera_P=camera.tolist(),crop=crop,clip=clip,render=stats)
        def save(board,folder,name,records,measurement):
            filename=audit/folder/(name+'.jpg')
            board.save(filename,quality=90,optimize=True)
            report=dict(model_sha256=digest(model),jpg_sha256=digest(filename),records=records,
                        measurements=measurement,measurements_sha256=digest(HERE/measurement),
                        source='https://www.sohu.com/a/971431850_121124642',
                        image_credit='Original render of the released model. Diagrams and images use independent model geometry.')
            filename.with_suffix('.json').write_text(json.dumps(report,ensure_ascii=False,indent=1)+'\n')
            print(folder,digest(filename))
        board=Image.new('RGB',(1080,652),'#f6f4ee');pen=ImageDraw.Draw(board)
        text(pen,(26,12),'首层中央通道',33,True)
        text(pen,(27,65),'光复路195号　图中朝向为自苏州河侧门槛向北。',18)
        image,view=shot(hall_camera(),[30,15,1015,632],717,[-.49,-.66,.57])
        board.paste(image,(27,119))
        draw_plan(pen,json.loads((HERE/'public-entrance-passage.json').read_bytes()))
        text(pen,(27,579),'三对柱轴距门槛约2.11、7.32、12.46米。两列纵向灯带由折面罩与深色金属边条构成。',18)
        text(pen,(27,614),'平面参考修缮设计院首层图，立面参照竣工照片。视野末端为模型所取入口段的边界。',16)
        save(board,'south-passage','public-passage', [view],'public-entrance-passage.json')

        board=Image.new('RGB',(1080,625),'#f6f4ee');pen=ImageDraw.Draw(board)
        text(pen,(26,12),'临河东墙的两行金字',33,True)
        text(pen,(27,65),'修缮后的「BAIspace 百空间」和「光二仓库 EST 1933」',19)
        oblique,v1=shot(east_camera(),[349,92,483,185],480,[.76,-.35,.55])
        detail,v2=shot(east_detail_camera(),[88,37,693,328],510,[.72,-.39,.57])
        text(pen,(27,111),'按竣工地面照配准的斜视',16,True)
        text(pen,(546,111),'近正视的模型细部',16,True)
        board.paste(oblique,(27,146));board.paste(detail,(546,146))
        text(pen,(546,410),'上下行字面和侧壁均为独立几何。',17)
        text(pen,(27,519),'以南转角为起点，字标沿东墙占约1.0至5.8米，距南门槛面高约15.9至17.6米。',18)
        text(pen,(27,565),'地面照与另一张斜航拍交会估计的位置误差约为沿墙0.7米、高程0.25米。',16)
        save(board,'east-return-sign','east-return-lettering',[v1,v2],'east-return-sign-registration.json')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('model',type=Path)
    parser.add_argument('audit',type=Path)
    args=parser.parse_args()
    produce(args.model,args.audit)
