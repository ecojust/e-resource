"""Render the complete balcony views from two delivered GLBs and rectify a licensed detail."""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image,ImageDraw,ImageFont

HERE=Path(__file__).resolve().parent
LIB=HERE.parents[1]/'jingan-jiaozhou-450-garden-residence/measurements'
sys.path.insert(0,str(LIB))
from photo_glb_raster import raster


def camera(eye,target,focal):
    eye=np.asarray(eye,float);forward=np.asarray(target,float)-eye;forward/=np.linalg.norm(forward)
    right=np.cross(forward,[0.,0.,1.]);right/=np.linalg.norm(right)
    down=np.cross(forward,right)
    r=np.vstack([right,down,forward])
    return np.array([[focal,0,0],[0,focal,0],[0,0,1.]])@np.column_stack([r,-r@eye])


def plot(near,far,commons,out):
    data=json.loads((HERE/'balcony-photo-traces.json').read_bytes())
    layout=json.loads((HERE.parent/'source/front-layout.json').read_bytes())
    photo=data['source_images'][0]
    if hashlib.sha256(commons.read_bytes()).hexdigest()!=photo['sha256']:
        raise ValueError('Expected the original 5312 × 2988 Antigng photograph')
    sheet=Image.new('RGB',(1040,833),'#f7f5ef')
    draw=ImageDraw.Draw(sheet)
    def text(x,y,txt,size,bold=False):
        font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-'+('Bold' if bold else 'Regular')+'.ttc',size,index=2)
        draw.text((x,y),txt,fill='#28373a',font=font)
    text(23,10,'公益坊3号楼的两层出挑阳台',30,True)
    text(24,57,'沿四川北路每层九跨。近照可辨六辐圆花、四组方折纹、成对弧托和墩帽。',17)
    rawH=np.array(data['registration']['commons_panel']['drawing_to_native_image'])
    crop=Image.open(commons).transform((670,176),Image.Transform.PERSPECTIVE,
        (rawH/rawH[2,2]).flatten()[:8],Image.Resampling.BICUBIC)
    sheet.paste(crop.resize((480,128),Image.Resampling.LANCZOS),(24,476))
    text(24,609,'2018年2月原照局部，经透视校正',16,True)
    edges=layout['bay_edges'];z0,z1=layout['balcony_z'];span=float(np.median(np.diff(edges)))
    body=span*.097;h=span*.235;depth=layout['balcony_depth']
    middle=.5*(edges[1]+edges[2]);dz=depth-.43*body+.021
    rail_low=z1+.033*h;rail_high=z1+.858*h
    centre=[middle,-dz,(rail_low+rail_high)*.5]
    front=camera([middle,-dz-11,centre[2]],centre,1000)
    pw=1000*(edges[2]-edges[1]-body)/11;ph=1000*(rail_high-rail_low)/11
    look=[edges[2],-depth,z1-.02]
    views=[
      ('从南看九跨长廊与两层板缘',near,camera([-16.,-49.,13.],[18.,-.1,6.8],1050),
       (-420,-130,520,135),(24,100),(993,295),True),
      ('模型中相同一跨的花铁',near,front,(-pw/2,-ph/2,pw/2,ph/2),(532,476),(480,128),False),
      ('两个支托之间留有通缝',near,camera([look[0]-14.5,-depth-19.,z1-5.92],look,2850),
       (-139,-92,139,92),(24,655),(199,132),True),
      ('远景模型保留六辐圆花',far,camera([middle-.24,-dz-3.1,centre[2]+.1],centre,560),
       (-135,-84,135,84),(527,655),(205,132),True)]
    rec=[]
    with tempfile.TemporaryDirectory() as tmp:
        library=Path(tmp)/'paint.so'
        subprocess.run(['cc','-O2','-fPIC','-shared',LIB/'photo_glb_raster.c','-o',library,'-lm'],check=True)
        lib=ctypes.CDLL(str(library));lib.paint.restype=lib.shadow_depth.restype=None
        sun=np.array([-.60,-.78,.76],dtype=np.float32);sun/=np.linalg.norm(sun)
        for title,path,P,bbox,(x,y),(ww,hh),fit in views:
            cx=(bbox[0]+bbox[2])/2;cy=(bbox[1]+bbox[3])/2
            if fit:
                width=max(bbox[2]-bbox[0],(bbox[3]-bbox[1])*ww/hh);height=width*hh/ww
                bbox=(cx-width/2,cy-height/2,cx+width/2,cy+height/2)
            print(title,flush=True)
            img,stats=raster(path,lib,round(ww*1.34),P,bbox,sun,[])
            if stats['zbuffer_foreground_pixels']<400:raise ValueError((title,stats))
            sheet.paste(img.resize((ww,hh),Image.Resampling.LANCZOS),(x,y))
            if y<650:text(x,y+hh+5,title,16,True)
            else:text(x+ww+10,y+43,title,16,True)
            rec.append(dict(title=title,asset=hashlib.sha256(path.read_bytes()).hexdigest(),
                            camera=P.tolist(),crop=bbox,**stats))
    text(24,437,'原照与模型对照',19,True)
    text(24,803,'摄影  Antigng，CC BY-SA 4.0。原片经裁切和透视校正。其余画面由公开三维模型生成。',15)
    out.parent.mkdir(parents=True,exist_ok=True)
    sheet.save(out,quality=91,optimize=True)
    out.with_suffix('.json').write_text(json.dumps(dict(licence_of_comparison_sheet='CC BY-SA 4.0',
        photo=photo,photo_drawing_to_native=rawH.tolist(),views=rec),ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('near','far','commons_original','output'):p.add_argument(k,type=Path)
    a=p.parse_args();plot(a.near,a.far,a.commons_original,a.output)
