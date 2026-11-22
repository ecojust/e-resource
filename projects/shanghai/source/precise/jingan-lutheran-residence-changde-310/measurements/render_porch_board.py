"""Render the full entrance and detail views at the two recorded photographic cameras."""
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
CLIP=HERE.parents[1]/'huangpu-zhengjia-lane-39-street-gate/measurements'
sys.path[:0]=[str(RASTER),str(CLIP)]
from photo_glb_raster import raster
from clip_courtyard_camera import clip_near_plane

def draw_board(model,output,standalone=False):
    canvas=Image.new('RGB',(1470,1190),'#f7f5ee');ink=ImageDraw.Draw(canvas)
    fonts=Path('/usr/share/fonts/opentype/noto')
    def label(pos,txt,size,bold=False,col='#34352f'):
        style='Bold' if bold else 'Regular'
        ink.text(pos,txt,fill=col,font=ImageFont.truetype(str(fonts/('NotoSansCJK-'+style+'.ttc')),size,index=2))
    label((43,19),'常德路 310 号的砖券门廊',40,True)
    label((45,84),'信义会住宅　｜　浅拱两端各有一根雕花石柱。臂墙从旁边的小柱弯向院内石墩。',22)
    anchor=np.eye(4)
    if not standalone:anchor[:3,3]=[1.54,.04,-1.86]
    sun=np.array([-.28,-.49,.825],np.float32);sun/=np.linalg.norm(sun)
    views=[('院内正面','porch-frontal-camera.json',[60,275,2880,1750],42,145,849),
           ('左柱柱头与回卷纹','porch-camera.json',[293,150,565,307],919,145,503),
           ('中央双菱花键石','porch-frontal-camera.json',[1330,316,1667,565],919,485,503),
           ('花砖地坪与门槛','porch-frontal-camera.json',[1020,1390,1948,1556],42,646,849)]
    recs=[]
    with tempfile.TemporaryDirectory() as tmp:
        library=Path(tmp)/'porch.so'
        subprocess.run(['cc','-O2','-fPIC','-shared',str(RASTER/'photo_glb_raster.c'),'-o',str(library),'-lm'],check=True)
        lib=ctypes.CDLL(str(library));lib.shadow_depth.restype=lib.paint.restype=None
        for i,(name,c,crop,x,y,width) in enumerate(views):
            camera=np.asarray(json.loads((HERE/c).read_text())['P'])@anchor
            clipped=Path(tmp)/('view-'+str(i)+'.glb')
            clip_record=clip_near_plane(model,clipped,camera)
            image,record=raster(clipped,lib,width*2,camera,crop,sun,[210,47])
            height=round(width*(crop[3]-crop[1])/(crop[2]-crop[0]))
            canvas.paste(image.resize((width,height),Image.Resampling.LANCZOS),(x,y))
            recs.append(dict(detail=name,original_camera=c,near_clip=clip_record,**record))
            clipped.unlink()
    label((43,595),'院内正面　　2021 年 2 月 17 日 13:59 的摄影位置',20)
    label((919,437),'左柱柱头　　方形层檐下的双涡卷和叶饰',18)
    label((919,858),'中央键石　　两枚菱形花饰上下相接',18)
    label((43,803),'地坪　　绿色和赭色的双边在两边柱脚转成直角',19)
    label((43,900),'剖面实测',25,True)
    s=json.loads((HERE/'complete-entrance-arch.json').read_text())
    rx=s['horizontal_radius_m'];rz=s['rise_m'];base=s['spring_z_m']
    xmid,y0,k=395,1097,131
    for off,color,wd in [(0,'#7f4535',3),(.16,'#a56b53',2),(.31,'#a56b53',2),(.496,'#7f4535',3)]:
        ang=np.linspace(0,np.pi,121);c=np.cos(ang);v=np.sin(ang)
        n=np.hypot(rz*c,rx*v);xx=rx*c+off*rz*c/n;zz=base+rz*v+off*rx*v/n
        ink.line(list(zip(xmid+k*xx,y0-k*zz)),fill=color,width=wd)
    ink.line((xmid-k*rx,y0+4,xmid+k*rx,y0+4),fill='#69574e',width=1)
    for x in [xmid-k*rx,xmid+k*rx]:ink.line((x,y0-5,x,y0+12),fill='#69574e',width=2)
    label((270,1109),'砖券净跨约 3.21 米',18)
    label((735,937),'拱口净高从起拱处量，约 0.98 米。',22,True)
    label((735,989),'两根主柱中心相距约 3.64 米。以灰砖每皮 65 毫米估算尺度，',18)
    label((735,1024),'正面与侧面实景共同约束拱形、券内进深和石柱轮廓。',18)
    label((735,1071),'参考 Nina 2021 年实拍与高参 88 图文。图中各视图均为模型渲染。',17,col='#5e5a50')
    output.parent.mkdir(parents=True,exist_ok=True);canvas.save(output,quality=92,optimize=True)
    output.with_suffix('.json').write_text(json.dumps(dict(mesh_sha256=hashlib.sha256(model.read_bytes()).hexdigest(),
        source_photographs_embedded=False,figure_license='MIT',cameras=['https://www.meipian.cn/3f5icwhf',
        'https://blog.sina.cn/dpool/blog/s/blog_5d1bdf480102zeb6.html'],views=recs),ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('decoded_mesh',type=Path)
    p.add_argument('output',type=Path);p.add_argument('--standalone',action='store_true')
    a=p.parse_args();draw_board(a.decoded_mesh,a.output,a.standalone)
