"""Render the actual released gateway meshes at their street survey camera poses."""
import argparse,ctypes,hashlib,json,subprocess,sys,tempfile
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).resolve().parent
RASTER=HERE.parents[1]/'jingan-jiaozhou-450-garden-residence/measurements'
sys.path.insert(0,str(RASTER))
from photo_glb_raster import raster

def draw(model,far,output):
    views=json.loads((HERE/'gate-camera-registration.json').read_text())['views']
    canvas=Image.new('RGB',(1220,880),'#ede9e0');pen=ImageDraw.Draw(canvas)
    def text(x,y,t,s,b=False):
        ff=Path('/usr/share/fonts/opentype/noto')/('NotoSansCJK-Bold.ttc'if b else'NotoSansCJK-Regular.ttc')
        pen.text((x,y),t,font=ImageFont.truetype(str(ff),s,index=2),fill='#2b3937')
    text(30,13,'归仁里过街楼',34,True);text(32,64,'康定东路3弄　｜　上海市第五批优秀历史建筑 5B053',18)
    light=np.array([-.44,-.66,.61]);light/=np.linalg.norm(light);data=[]
    def crop(M,bounds):
        q=np.c_[bounds,np.ones(len(bounds))]@M.T;px=q[:,:2]/q[:,2,None];a,b=px.min(axis=0),px.max(axis=0)
        return np.rint([a[0]-12,a[1]-13,b[0]+12,b[1]+15]).astype(int).tolist()
    cases=[(model,'struct-2020-middle',[[-6.12,-.92,0],[6.67,-.92,0],[-6.12,0,7.96],[6.67,-.89,7.55],[-.86,-.11,9.29],[1.34,-.11,9.29]],(28,112,745,380),'门洞贯通地层，左侧清水砖墙和右侧封闭窗廊围合弄口'),
           (far,'struct-2015-east',[[-6.1,-.10,0],[6.65,-.89,0],[-6.1,0,7.96],[6.65,-.89,7.55],[-.86,-.1,9.29],[1.34,-.1,9.29]],(796,112,393,380),'从街道东侧斜望 · 远景网格'),
           (model,'crown-winter20',[[-2.05,-.18,7.24],[2.10,-.18,7.24],[-1.03,-.18,9.32],[1.35,-.18,9.32]],(28,548,385,219),'阶梯形山花、镜心与两侧悬饰'),
           (model,'struct-2015-east',[[-5.52,-.02,1.0],[-2.74,-.02,1.0],[-5.52,0,3.87],[-2.74,0,3.87]],(427,548,348,219),'灰砖墙中的红砖腰线与下窗横栅'),
           (model,'struct-2015-middle',[[1.98,-.91,3.60],[6.61,-.91,3.60],[1.98,-.91,7.42],[6.61,-.91,7.42]],(796,548,393,219),'六扇廊窗与横贯两侧实板的十格亮窗')]
    with tempfile.TemporaryDirectory()as temp:
        dll=Path(temp)/'raster.so';subprocess.run(['cc','-O2','-shared','-fPIC',str(RASTER/'photo_glb_raster.c'),'-o',str(dll),'-lm'],check=True)
        lib=ctypes.CDLL(str(dll));lib.paint.restype=lib.shadow_depth.restype=None
        for f,k,bounds,(x,y,wd,ht),caption in cases:
            M=np.array(views[k]['xyz_to_image']);uv=crop(M,bounds)
            s=min(wd/(uv[2]-uv[0]),ht/(uv[3]-uv[1]));ww=max(1,round((uv[2]-uv[0])*s));hh=max(1,round((uv[3]-uv[1])*s))
            im,meta=raster(f,lib,round(ww*1.60),M,uv,light,[222,41])
            canvas.paste(im.resize((ww,hh),Image.Resampling.LANCZOS),(x+(wd-ww)//2,y+(ht-hh)//2))
            text(x,y+ht+7,caption,14);data.append(dict(camera=k,caption=caption,mesh_sha256=hashlib.sha256(f.read_bytes()).hexdigest(),**meta))
    text(30,815,'街面尺度按分期照片估算，图中只呈现过街楼和相邻两跨。',18,True)
    output.parent.mkdir(exist_ok=True,parents=True);canvas.save(output,quality=91,optimize=True)
    output.with_suffix('.json').write_text(json.dumps(dict(license='MIT',photo_pixels_embedded=0,views=data),ensure_ascii=False,indent=1)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('full','far','output'):p.add_argument(k,type=Path)
    args=p.parse_args();draw(args.full,args.far,args.output)
