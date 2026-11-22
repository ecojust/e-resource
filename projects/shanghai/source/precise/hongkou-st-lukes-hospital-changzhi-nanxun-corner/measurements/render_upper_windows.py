"""Render the Changzhi and Nanxun upper-window comparison from the delivered GLBs."""
import argparse
import ctypes
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'source'
LIB = HERE.parents[1] / 'jingan-jiaozhou-450-garden-residence/measurements'
sys.path.insert(0,str(LIB))
from photo_glb_raster import raster


def camera(eye,target,f):
    forward=target-eye
    forward=forward/np.linalg.norm(forward)
    right=np.cross(forward,[0.,0.,1.]);right/=np.linalg.norm(right)
    down=np.cross(forward,right)
    R=np.vstack((right,down,forward))
    return np.array([[f,0.,320.],[0.,f,180.],[0.,0.,1.]])@np.column_stack((R,-R@eye))


def plot(near,far,out):
    rows=json.loads((SOURCE/'upper-window-layout.json').read_bytes())['rows']
    layout=json.loads((HERE/'upper-window-host-layout.json').read_bytes())
    faces={f['id']:f for f in layout['faces']}
    def faceview(face,axis,level,distance,advance=0.,height=0.):
        row=next(r for r in rows if r['face']==face and r['axis']==axis and r['level']==level)
        f=faces[face];a=np.array(f['a']);t=(np.array(f['b'])-a)/f['length']
        z=(row['sill']+row['crown'])*.5
        target=np.r_[a+t*(row['center_fraction']*f['length']),z]
        eye=target+np.r_[np.array(f['out'])*distance+t*advance,height]*6.
        return camera(eye,target,3300.)
    cam=json.loads((HERE/'upper-window-cameras.json').read_bytes())['hk202342']
    R=np.array(cam['R']);P=np.array(cam['K'])@np.column_stack((R,-R@cam['eye']))
    v=[
        ('长治路上层圆券及山花两排三联窗',near,P,(26,318,318,695),(25,113),(465,428),(-.95,-.4,.82)),
        ('南浔路六轴与转角处的窄窗',far,faceview('nanxun',3,3,17.5,3.5,-1.5),(5,-20,635,380),(518,113),(468,328),(-.36,-.90,.83)),
        ('近景   |   长治路上层的放射状窗梃',near,faceview('changzhi',4,4,3.8,.75,.15),(90,-5,550,365),(25,600),(285,224),(-.88,-.46,.85)),
        ('近景   |   挑出墙面的成对窗扇',near,faceview('changzhi',5,3,4.2,1.4,-.4),(110,-15,530,375),(357,600),(279,224),(-.84,-.54,.79)),
        ('2021年南浔路远端下排的覆盖面',far,faceview('nanxun',6,2,4.8,-1.2,.3),(115,-20,525,380),(684,600),(299,224),(-.39,-.92,.82))]
    sheet=Image.new('RGB',(1012,901),'#f7f5ef');d=ImageDraw.Draw(sheet)
    def label(x,y,content,size,bold=False):
        path='/usr/share/fonts/opentype/noto/NotoSansCJK-'+('Bold' if bold else 'Regular')+'.ttc'
        d.text((x,y),content,font=ImageFont.truetype(path,size,index=2),fill='#273a3c')
    label(24,12,'同仁医院旧址   |   长治路与南浔路的上层窗',33,True)
    label(25,66,'五段墙面的50个窗洞。左上采用2023年区刊的街角机位，其余图展示窗框与洞膛的关系。',18)
    records=[]
    with tempfile.TemporaryDirectory() as tmp:
        library=Path(tmp)/'paint.so'
        subprocess.run(['cc','-O2','-fPIC','-shared',LIB/'photo_glb_raster.c','-o',library,'-lm'],check=True)
        lib=ctypes.CDLL(str(library));lib.paint.restype=lib.shadow_depth.restype=None
        for title,path,matrix,bounds,(x,y),(ww,hh),sun in v:
            cx=(bounds[0]+bounds[2])/2;cy=(bounds[1]+bounds[3])/2
            width=max(bounds[2]-bounds[0],(bounds[3]-bounds[1])*ww/hh);height=width*hh/ww
            bbox=(cx-width/2,cy-height/2,cx+width/2,cy+height/2)
            vector=np.asarray(sun,dtype=np.float32);vector/=np.linalg.norm(vector)
            print(title,flush=True)
            img,stats=raster(path,lib,round(ww*1.22),matrix,bbox,vector,[])
            if stats['zbuffer_foreground_pixels']<500:raise ValueError((title,stats))
            sheet.paste(img.resize((ww,hh),Image.Resampling.LANCZOS),(x,y))
            label(x,y+hh+6,title,17,True)
            records.append(dict(title=title,asset=hashlib.sha256(path.read_bytes()).hexdigest(),P=matrix.tolist(),crop=bbox,**stats))
    label(24,870,'窗轴从每面起点依次编号。远端封板沿用2021年实见形态。本文图像由项目三维模型生成。',16)
    out.parent.mkdir(parents=True,exist_ok=True);sheet.save(out,quality=91,optimize=True)
    out.with_suffix('.json').write_text(json.dumps(dict(views=records),ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('near','far','output'):p.add_argument(k,type=Path)
    a=p.parse_args();plot(a.near,a.far,a.output)
