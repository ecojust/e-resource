"""Compare the gate piers and painted ironwork with the two measured 2017 viewpoints."""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from render_lintel import RASTER, clip_near_plane, raster

HERE = Path(__file__).resolve().parent


def draw(photo, near, far, output):
    survey = json.loads((HERE/'south-gate-leaves-and-piers.json').read_bytes())
    source = survey['primary_source']
    digest = lambda f: hashlib.sha256(f.read_bytes()).hexdigest()
    assert digest(photo) == source['sha256']
    width, height = 1120, 760
    canvas = Image.new('RGB', (width,height), '#f4f0e8')
    pen = ImageDraw.Draw(canvas)
    def label(x,y,s,size,bold=False):
        weight = 'Bold' if bold else 'Regular'
        font = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-'+weight+'.ttc', size,index=2)
        pen.text((x,y), s,font=font,fill='#302c25')
    label(30,16,'常熟路荣康别墅南口',37,True)
    label(31,73,'两侧浅色石柱与深绿铁件　｜　2017年街面',20)
    src_box = [2390,2300,3305,2985]
    panel_size = (520,round(520*(src_box[3]-src_box[1])/(src_box[2]-src_box[0])))
    label(31,121,'2017年8月19日　原照局部',21,True)
    canvas.paste(Image.open(photo).crop(src_box).resize(panel_size, Image.Resampling.LANCZOS),(31,161))
    label(570,121,'同一机位　近景模型',21,True)
    sun = np.array([-.57,-.65,.58],np.float32)
    sun /= np.linalg.norm(sun)
    angles = [float(np.degrees(np.arctan2(sun[0],sun[1]))%360),float(np.degrees(np.arcsin(sun[2])))]
    shots = [(near,'original_full_matrix',src_box,(570,161),520),
             (far,'september_800x890_matrix',[530,326,682,600],(574,598),78)]
    records = []
    with tempfile.TemporaryDirectory(dir=output.parent) as tmp:
        tmp = Path(tmp)
        so = tmp/'raster.so'
        subprocess.run(['cc','-O2','-shared','-fPIC',str(RASTER/'photo_glb_raster.c'),'-o',str(so),'-lm'],check=True)
        lib = ctypes.CDLL(str(so))
        lib.paint.restype = lib.shadow_depth.restype = None
        for i,(model,key,region,origin,w) in enumerate(shots):
            P = np.asarray(survey['source_camera'][key])
            clipped = tmp/(str(i)+'.glb')
            clip = clip_near_plane(model,clipped,P)
            panel,info = raster(clipped,lib,round(w*1.5),P,region,sun,angles)
            canvas.paste(panel.resize((w,round(panel.height*w/panel.width)),Image.Resampling.LANCZOS), origin)
            records.append({'source_camera':key,'crop':region,'sha256':digest(model),'clip':clip,'render':info})
    label(31,571,'照片中可辨的构件',21,True)
    label(31,612,'南柱上部有一道窄颈，北侧铁件折向弄内。',19)
    label(31,645,'白色柱帽和门额间的空隙在照片中可见。',19)
    label(31,706,'原照 Antigng／Wikimedia Commons，图板 CC BY-SA 4.0。',15)
    label(570,561,'2017年9月3日机位　低面数模型',20,True)
    label(680,634,'两幅街照都能分辨铁件的转折。',18)
    label(680,672,'进深估计误差约 0.4 至 0.5 米。',16)
    canvas.save(output,quality=90,optimize=True)
    output.with_suffix('.json').write_text(json.dumps({'license':source['license'],'license_url':source['license_url'],
        'source_url':source['page'],'photographer':source['author'],'source_sha256':digest(photo),
        'source_crop':src_box,'board_sha256':digest(output),'renders':records},ensure_ascii=False,indent=1)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for key in ('photo','near','far','output'):
        parser.add_argument(key,type=Path)
    args=parser.parse_args()
    draw(args.photo,args.near,args.far,args.output)
