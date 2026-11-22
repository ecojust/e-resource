"""Make an attributed, same-camera comparison from the real glTF and original Commons photo."""
import argparse,ctypes,hashlib,json,subprocess,sys,tempfile
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).resolve().parent
RUNTIME=HERE.parents[1]/'huangpu-yuanmingyuan-apartments-street-front/measurements'
sys.path[:0]=[str(HERE.parent/'source'),str(RUNTIME)]
from xiangshan_photo_plane import CALIBRATION
from photo_glb_raster import raster
def sha(f):
    with f.open('rb')as fp:return hashlib.file_digest(fp,'sha256').hexdigest()
def font(n,bold=False):
    return ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-'+('Bold'if bold else 'Regular')+'.ttc',n,index=2)
def render(mesh,photo,out):
    assert sha(photo)=='813f29fcf2512494f18b067c93f8f0f09ddb80e19cbd5450c8159d6518e0096c'
    original=Image.open(photo).convert('RGB');assert original.size==(5312,2988)
    source=json.loads((HERE/'residence-sources.json').read_text())['sources'][0]
    board=Image.new('RGB',(1400,810),'#f7f4ed');draw=ImageDraw.Draw(board)
    draw.text((28,18),'香山路9号住宅　白色山墙老虎窗',font=font(34,True),fill='#31302c')
    draw.text((28,74),'东面窄山墙开一樘窗，西面阔山墙开两樘窗。两者之间还有一段较低的连窗。',font=font(21),fill='#53473e')
    draw.text((28,128),'2018年7月30日　Antigng 摄影',font=font(22,True),fill='#51483e')
    draw.text((714,128),'同一视角的模型',font=font(22,True),fill='#51483e')
    crop=(700,0,4100,1730);p=np.array(CALIBRATION['camera_matrices']['2018_commons'])
    sun=np.array([-.50,-.73,.57],np.float32);sun/=np.linalg.norm(sun)
    with tempfile.TemporaryDirectory()as td:
        binary=Path(td)/'paint.so';subprocess.run(['cc','-O2','-shared','-fPIC','-o',binary,RUNTIME/'photo_glb_raster.c','-lm'],check=True)
        lib=ctypes.CDLL(str(binary));lib.shadow_depth.restype=lib.paint.restype=None
        img,info=raster(mesh,lib,1000,p,crop,sun,[205,30])
        for x,im in [(28,original.crop(crop)),(714,img)]:
            board.paste(im.resize((654,333),Image.Resampling.LANCZOS),(x,176))
        d_crop=(2310,430,3235,1010);im2,detail=raster(mesh,lib,720,p,d_crop,sun,[205,30])
        for x,im in [(28,original.crop(d_crop)),(363,im2)]:
            board.paste(im.resize((306,192),Image.Resampling.LANCZOS),(x,535))
    draw.text((714,550),'西山墙的两樘窗',font=font(24,True),fill='#443e35')
    draw.multiline_text((714,600),'2015年冬景中可以分辨外开窗扇和两架晾杆。\n2018年夏照受树叶与架空线遮挡。\n屋面后部的收口和窗扇厚度为估计。',font=font(19),spacing=7,fill='#564b42')
    draw.text((28,755),'照片由 Antigng 摄于2018年，来自 Wikimedia Commons《香山路9号住宅.jpg》。照片已裁切，图版依 CC BY-SA 4.0 共享。',font=font(17),fill='#625448')
    board.save(out,quality=90)
    out.with_suffix('.json').write_text(json.dumps(dict(photo=source,model_sha256=sha(mesh),camera_sha256=sha(HERE/'xiangshan-exterior-cameras.json'),overview=dict(crop=crop,render=info),detail=dict(crop=d_crop,render=detail),board_sha256=sha(out)),ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser()
    for x in ('model','photo','output'):p.add_argument(x,type=Path)
    a=p.parse_args();render(a.model,a.photo,a.output)
