"""Render the released mesh at the street and film cameras and draw its measured window schedule."""
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
sys.path[:0]=[str(HERE.parent/'source'),str(RASTER)]
from daren_photo_plane import camera_matrix
from photo_glb_raster import raster
import street_brick_arcade as architecture


def make_board(mesh,output):
    paper=Image.new('RGB',(1400,1110),'#faf8f1');draw=ImageDraw.Draw(paper);fonts=Path('/usr/share/fonts/opentype/noto')
    def label(x,y,txt,size,bold=False,color='#2e302d'):
        face='Bold' if bold else 'Regular';font=ImageFont.truetype(str(fonts/f'NotoSansCJK-{face}.ttc'),size,index=2)
        draw.text((x,y),txt,font=font,fill=color)
    label(41,18,'康定东路 20 号的十四孔砖券',41,True)
    label(43,88,'原大任小学沿街立面。两种宽度的砖券交替排列，到露台处出现两个相邻的窄孔。',23)
    sun=np.asarray([-.43,-.61,.67],np.float32);sun/=np.linalg.norm(sun)
    views=[('视频原机位的全排砖券','video-4.28',(83,241,921,461),42,140,1316),
           ('东侧街道所见的窄券与宽券','east15-wall',(199,338,424,435),42,551,636),
           ('中间两道窄券与木门','video-4.28',(474,310,655,388),718,551,636)]
    details=[]
    with tempfile.TemporaryDirectory() as raw:
        so=Path(raw)/'arcade-view.so';subprocess.run(['cc','-O2','-fPIC','-shared',str(RASTER/'photo_glb_raster.c'),'-o',str(so),'-lm'],check=True)
        lib=ctypes.CDLL(str(so));lib.shadow_depth.restype=lib.paint.restype=None
        for name,camera,crop,x,y,width in views:
            im,rec=raster(mesh,lib,width*2,camera_matrix(camera),crop,sun,[215,43]);assert rec['zbuffer_foreground_pixels']>20000
            h=round(width*(crop[3]-crop[1])/(crop[2]-crop[0]));paper.paste(im.resize((width,h),Image.Resampling.LANCZOS),(x,y));details.append(dict(title=name,camera=camera,crop_native=crop,**rec))
    label(43,500,'2015 年东侧街道机位',22,True);label(719,500,'2026 年园前机位',22,True)
    label(43,836,'墙面开口的实测轮廓',23,True)
    rows=json.loads(architecture.SECTIONS.read_text())['openings'];origin=58.;scale=48.2;zero=1013.
    def paper_point(x,z):return (origin+x*scale,zero-(z-4.82)*38.)
    for o in rows:
        l=o['center']-o['half_width'];r=o['center']+o['half_width'];z=o['sill'];num=o['number'];color='#ad7349' if num==8 else '#9a6150'
        profile=[(l,z),(r,z),*[architecture._point(o,t)for t in np.linspace(0,np.pi,35)]]
        pts=[paper_point(*q)for q in profile];draw.polygon(pts,fill='#e9e4d8' if num!=8 else '#e7cb9e');draw.line(pts+[pts[0]],fill=color,width=2)
        px,_=paper_point(o['center'],z);label(px-7,978,str(num),15,num==8)
    label(43,1024,'窄孔净宽约 0.9 米，宽孔约 2 米。第 8 孔通向露台，栏杆遮住了门槛。',18)
    label(43,1061,'机位取自 2015、2020 年街景及街景写生达人 2026 年实拍。图中三幅均为模型渲染。',17,color='#56554f')
    output.parent.mkdir(parents=True,exist_ok=True);paper.save(output,quality=92,optimize=True)
    output.with_suffix('.json').write_text(json.dumps(dict(mesh_sha256=hashlib.sha256(mesh.read_bytes()).hexdigest(),
        graphic_license='MIT',source_pixels_included=False,original_actor='街景写生达人',
        frame_reference='https://www.bilibili.com/video/BV1MeFVzqEiJ/?t=4.28',station_reference='street-front-cameras.json',
        diagram='Measured wall-plane sections of fourteen openings. The height of the door threshold and the sills hidden by the balcony are estimated.',
        views=details),ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('decoded_mesh',type=Path);p.add_argument('output',type=Path);q=p.parse_args();make_board(q.decoded_mesh,q.output)
