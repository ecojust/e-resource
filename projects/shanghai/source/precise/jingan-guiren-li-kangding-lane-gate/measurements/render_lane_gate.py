"""Render the assembled gate from the two archived survey camera matrices."""

import argparse
import ctypes
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from render_gable_relief import RASTER, clip_near_plane, raster

HERE=Path(__file__).resolve().parent


def draw(near, far, out):
    record=HERE/'gate-camera-registration.json'
    cameras=json.loads(record.read_text())['views']
    board=Image.new('RGB',(1040,745),'#f3f1e9')
    pen=ImageDraw.Draw(board)
    def caption(point,text,size,bold=False):
        weight='Bold' if bold else 'Regular'
        font=ImageFont.truetype(f'/usr/share/fonts/opentype/noto/NotoSansCJK-{weight}.ttc',size,index=2)
        pen.text(point,text,font=font,fill='#322e26')
    caption((30,15),'归仁里过街楼的铁栅门',36,True)
    caption((31,71),'固定顶栏、双扇与左侧人行小门　｜　街面测量机位的模型视图',18)
    views=[(near,'struct-2020-middle',(-1.64,1.58,-.12,3.64),(30,124),474,'过街楼门洞与顶栏'),
           (far,'struct-2015-east',(-1.52,.54,-.07,2.89),(545,124),448,'左扇内另设人行小门，中梃并列')]
    light=np.array([-.56,-.58,.59],np.float32);light/=np.linalg.norm(light)
    angles=[float(np.degrees(np.arctan2(light[0],light[1]))%360),float(np.degrees(np.arcsin(light[2])))]
    rows=[]
    with tempfile.TemporaryDirectory() as td:
        directory=Path(td);library=directory/'render.so'
        subprocess.run(['cc','-O2','-shared','-fPIC',str(RASTER/'photo_glb_raster.c'),'-o',str(library),'-lm'],check=True)
        lib=ctypes.CDLL(str(library));lib.paint.restype=lib.shadow_depth.restype=None
        for i,(mesh,key,(x0,x1,z0,z1),(left,top),width,title) in enumerate(views):
            cam=np.asarray(cameras[key]['xyz_to_image'])
            data=np.array([[x,.20,z,1.] for x in [x0,x1] for z in [z0,z1]])@cam.T
            uv=data[:,:2]/data[:,2:]
            crop=np.r_[uv.min(0),uv.max(0)]
            # Both panels have an identical physical page height. The image
            # aspect is preserved inside the cell, including the oblique view.
            factor=min(width/(crop[2]-crop[0]),478/(crop[3]-crop[1]))
            actual_width=round((crop[2]-crop[0])*factor)
            clipped=directory/f'{i}.glb'
            clip=clip_near_plane(mesh,clipped,cam)
            image,log=raster(clipped,lib,round(1.45*actual_width),cam,crop.tolist(),light,angles)
            height=round(image.height*actual_width/image.width)
            board.paste(image.resize((actual_width,height),Image.Resampling.LANCZOS),(left,top))
            caption((left,top+height+11),title,19,True)
            rows.append(dict(view=key,crop=crop.round(3).tolist(),mesh=mesh.name,mesh_sha256=hashlib.sha256(mesh.read_bytes()).hexdigest(),clip=clip,raster=log))
    caption((31,678),'门扇上的短横杆、矩形格眼据高参88于2016年7月2日所摄原片绘制。',17)
    caption((31,706),'照片中右下角有自行车遮挡，门片前后距离取近似值。',16)
    out.parent.mkdir(parents=True,exist_ok=True);board.save(out,quality=90,optimize=True)
    out.with_suffix('.json').write_text(json.dumps(dict(photo_pixels_embedded=False,views=rows,calibration_sha256=hashlib.sha256(record.read_bytes()).hexdigest(),image_sha256=hashlib.sha256(out.read_bytes()).hexdigest()),ensure_ascii=False,indent=1)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('near',type=Path);p.add_argument('far',type=Path);p.add_argument('out',type=Path)
    a=p.parse_args();draw(a.near,a.far,a.out)
