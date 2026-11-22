"""Render the stone door surround from two measured street cameras."""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from PIL import Image,ImageDraw,ImageFont
import numpy as np
from render_south_frieze import RASTER,clip_near_plane,raster

HERE=Path(__file__).resolve().parent


def draw(near,far,out):
    source=HERE/'main-porch-observations.json'
    photos=json.loads(source.read_bytes())['photos']
    canvas=Image.new('RGB',(1160,662),'#f1eee8')
    pen=ImageDraw.Draw(canvas)
    def label(x,y,copy,size,bold=False):
        weight='Bold' if bold else 'Regular'
        f=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-'+weight+'.ttc',size,index=2)
        pen.text((x,y),copy,font=f,fill='#322f2a')
    label(29,16,'胶州路原邮政供应处的石门套',34,True)
    label(30,66,'中央门洞　｜　冬季街照标定下的真实模型视图',18)
    sun=np.array([-.41,-.70,.59],np.float32);sun/=np.linalg.norm(sun)
    angles=[float(np.degrees(np.arctan2(sun[0],sun[1]))%360),float(np.degrees(np.arcsin(sun[2])))]
    shots=[(near,'north-2015',[70,46,509,470],29,139,426,'2015年冬　门柱与通透门洞'),
           (near,'mid-2020',[65,89,565,199],489,144,641,'2020年冬　浅色压顶与外挑雨篷'),
           (far,'south-2015',[73,138,323,323],538,337,320,'2015年冬　斜面的柱头与门楣')]
    records=[]
    with tempfile.TemporaryDirectory() as td:
        work=Path(td);so=work/'render.so'
        subprocess.run(['cc','-O2','-shared','-fPIC',str(RASTER/'photo_glb_raster.c'),'-lm','-o',str(so)],check=True)
        lib=ctypes.CDLL(str(so));lib.paint.restype=lib.shadow_depth.restype=None
        for idx,(mesh,name,crop,x,y,w,caption) in enumerate(shots):
            P=np.array(photos[name]['matrix']);clipped=work/f'{idx}.glb'
            clipping=clip_near_plane(mesh,clipped,P)
            frame,measure=raster(clipped,lib,round(w*1.32),P,crop,sun,angles)
            canvas.paste(frame.resize((w,round(w*frame.height/frame.width)),Image.Resampling.LANCZOS),(x,y))
            label(x,y-30,caption,16,True)
            records.append({'camera':name,'date':photos[name]['date'],'sha256':hashlib.sha256(mesh.read_bytes()).hexdigest(),
                            'render':measure,'clip':clipping})
    label(30,591,'门洞实测净宽约1.78米，装饰门楣下缘高约3.73米。树篱遮住的柱脚以可见直边延至街面。',17)
    label(30,626,'各图均为模型渲染。摄影观测与当期地址资料列在本工程来源中。',15)
    out.parent.mkdir(parents=True,exist_ok=True);canvas.save(out,quality=89,optimize=True)
    out.with_suffix('.json').write_text(json.dumps({'photograph_pixels_used':False,'measurements_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'views':records},ensure_ascii=False,indent=1)+'\n')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('near',type=Path);ap.add_argument('far',type=Path);ap.add_argument('output',type=Path)
    args=ap.parse_args();draw(args.near,args.far,args.output)
