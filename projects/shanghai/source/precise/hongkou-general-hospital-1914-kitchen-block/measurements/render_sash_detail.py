"""Show the three registered window faces and the two sculpted stone heads in model-only views."""
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

HERE=Path(__file__).resolve().parent
LIB=HERE.parents[1]/'jingan-jiaozhou-450-garden-residence/measurements'
sys.path[:0]=[str(LIB),str(HERE/'camera-fit')]
from photo_glb_raster import raster
import registered, court_registered


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def camera(K,R,eye):
    return K@np.column_stack((R,-R@eye))


def detail_view(o):
    c,w,z=o['center'],o['width'],o['head']
    target=np.array([c,-.08,z-.12*w]);eye=target+np.array([-.95,-4.9,.20])*w
    forward=target-eye;forward/=np.linalg.norm(forward)
    right=np.cross(forward,np.array([0.,0.,1.]));right/=np.linalg.norm(right)
    down=np.cross(forward,right)
    R=np.vstack((right,down,forward))
    return camera(np.array([[710.,0.,260.],[0.,710.,156.],[0.,0.,1.]]),R,eye)


def create(near,far,out):
    window_data=json.loads((HERE.parent/'source/sash-layout.json').read_bytes())['faces']
    east=np.array(json.loads((HERE/'east-recess-independent-camera.json').read_bytes())['camera_P'])
    north=camera(registered.K,registered.R,registered.eye)
    court=camera(court_registered.K,court_registered.R,court_registered.eye)
    upper=lambda i: next(o for o in window_data['north']if o['axis']==i and o['level']==3)
    views=[
      ('天潼路北面十窗轴',near,north,(285,70,731,541),(28,111),(405,375),(-.32,-.92,.83)),
      ('三角窗额与中央楔石',near,detail_view(upper(5)),(58,-69,462,322),(458,111),(277,265),(-.63,-.64,.92)),
      ('弧形窗额与断开檐线',near,detail_view(upper(4)),(58,-69,462,322),(765,111),(277,265),(-.63,-.64,.92)),
      ('院面交替的三角额与平额',far,court,(244,150,625,351),(482,433),(524,260),(.42,.89,.80)),
      ('乍浦路双窄窗及后退墙',far,east,(242,158,459,407),(48,550),(363,218),(-.82,-.35,.88))]
    sheet=Image.new('RGB',(1070,853),'#f8f6ef')
    draw=ImageDraw.Draw(sheet)
    def write(x,y,text,size=20,bold=False):
        font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-'+('Bold'if bold else'Regular')+'.ttc',size,index=2)
        draw.text((x,y),text,fill='#2b383a',font=font)
    write(27,16,'公济医院一九一四年后勤楼   |   石窗额与钢窗',33,True)
    write(28,65,'街面与院面依2019—2020年实照定位。三角额和弧额细图用模型近正视观察。',20)
    records=[]
    with tempfile.TemporaryDirectory()as tmp:
        so=Path(tmp)/'render.so';subprocess.run(['cc','-O2','-fPIC','-shared',LIB/'photo_glb_raster.c','-o',so,'-lm'],check=True)
        lib=ctypes.CDLL(str(so));lib.shadow_depth.restype=lib.paint.restype=None
        for label,asset,P,bounds,(x,y),(width,height),vector in views:
            ratio=width/height;cx=(bounds[0]+bounds[2])/2;cy=(bounds[1]+bounds[3])/2
            ww=max(bounds[2]-bounds[0],(bounds[3]-bounds[1])*ratio);hh=ww/ratio
            box=(cx-ww/2,cy-hh/2,cx+ww/2,cy+hh/2)
            sun=np.array(vector,dtype=np.float32);sun/=np.linalg.norm(sun)
            im,stats=raster(asset,lib,round(width*1.2),P,box,sun,[])
            if stats['zbuffer_foreground_pixels']<1000:raise ValueError(label)
            sheet.paste(im.resize((width,height),Image.Resampling.LANCZOS),(x,y));write(x,y+height+7,label,19,True)
            records.append(dict(caption=label,asset_sha256=sha(asset),P=P.tolist(),crop=list(box),**stats))
    write(28,815,'各图以原创模型绘制。灰色窗框后退，石窗额、楔石与钢窗梃均为独立实体。',17)
    out.parent.mkdir(parents=True,exist_ok=True);sheet.save(out,quality=91,optimize=True)
    out.with_suffix('.json').write_text(json.dumps(dict(views=records,rights='Original renders of the project geometry. Source exposures contributed camera and measurement information.'),ensure_ascii=False,indent=1)+'\n')


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('near',type=Path);ap.add_argument('far',type=Path);ap.add_argument('output',type=Path)
    a=ap.parse_args();create(a.near,a.far,a.output)
