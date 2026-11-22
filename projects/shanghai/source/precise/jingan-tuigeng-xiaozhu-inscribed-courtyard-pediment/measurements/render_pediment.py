"""Publish only images of the delivered GLBs. An oblique camera shows the estimated coping profile."""
import sys,ctypes,tempfile,subprocess,json,hashlib,argparse
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).resolve().parent
project=next((p for p in HERE.parents if (p/'source/precise/hongkou-general-post-office').is_dir()),None)
if project is None:
    import os
    project=Path(os.environ['E_RESOURCE_SHANGHAI'])
rasterdir=project/'source/precise/jingan-jiaozhou-450-garden-residence/measurements';sys.path.insert(0,str(rasterdir))
from photo_glb_raster import raster
from pediment_dimensions import P
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def view(eye,target,focus=960):
    eye=np.array(eye);z=np.asarray(target)-eye;z=z/np.linalg.norm(z)
    x=np.cross(z,[0,0,1]);x/=np.linalg.norm(x);y=np.cross(z,x)
    r=np.array([x,y,z]);return np.array([[focus,0,450],[0,focus,260],[0,0,1]])@np.column_stack([r,-r@eye])
def draw(near,far,output):
    canvas=Image.new('RGB',(1280,1020),'#f3eee4');d=ImageDraw.Draw(canvas)
    font='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
    def text(x,y,s,size,color='#39372f'):d.text((x,y),s,font=ImageFont.truetype(font,size,index=2),fill=color)
    text(36,20,'退耕小筑二进院墙题额',37);text(36,86,'长乐路662弄 · 吴镜渊旧居',21)
    with tempfile.TemporaryDirectory()as td:
        so=Path(td)/'r.so';subprocess.run(['cc','-O2','-fPIC','-shared',rasterdir/'photo_glb_raster.c','-lm','-o',so],check=True)
        lib=ctypes.CDLL(str(so));lib.paint.restype=lib.shadow_depth.restype=None
        sun=np.array([-.39,-.73,.55]);sun/=np.linalg.norm(sun)
        pictures=[
        ('原照机位 · 院墙弧肩和下檐',near,P,[135,118,885,452],760,32,143),
        ('侧视 · 上檐出挑与下部滴水',near,view([3.20,-3.85,2.32],[.45,0,.63],950),[96,64,835,482],432,818,144),
        ('阳文题面 · 由右至左',near,P,[191,304,565,403],917,32,566),
        ('远档 · 回纹与笔画',far,P,[193,275,578,401],284,967,569)]
        details=[]
        for label,mesh,cam,crop,size,x,y in pictures:
            im,r=raster(mesh,lib,size,cam,crop,sun,[218,34]);canvas.paste(im,(x,y));text(x,y+im.height+4,label,17);details.append(dict(label=label,mesh_sha256=sha(mesh),geometry=r))
    text(36,897,'额面四字依石刻笔锋和起伏分别建模，边框保留折回的方形纹路。',21)
    text(36,938,'题面宽1.80米用作模型比例；院墙厚度、弧檐出挑和阳文高度均为估计。',18)
    text(36,973,'模型图未使用原照像素。原照见2018年乐游静安、2022年市文化旅游局图文，题额形制另据施泳峰记述。',15)
    canvas.save(output,quality=91,optimize=True);output.with_suffix('.json').write_text(json.dumps(dict(model_only=True,sha256=sha(output),views=details),ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ['near','far','output']:parser.add_argument(name,type=Path)
    args=parser.parse_args();draw(args.near,args.far,args.output)
