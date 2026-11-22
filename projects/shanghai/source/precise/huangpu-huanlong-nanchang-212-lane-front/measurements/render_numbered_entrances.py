"""Render the two actual Lane 212/244 components, each at its photographed address."""
import argparse
import ctypes
import hashlib
import json
import math
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageOps

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
RASTER=ROOT/'huangpu-yuanmingyuan-apartments-street-front/measurements'
sys.path[:0]=[str(HERE.parent/'source'),str(HERE/'lane-244'),str(RASTER),str(ROOT/'huangpu-world-book-company-fuzhou-front/measurements')]
from huanlong_photo_plane import CALIBRATION
from check_component import transform
from separate_entries import location
from photo_glb_raster import read_glb,raster
from fuzhou_skylight import SurfaceCapture,horizon_shading

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def font(n,bold=False):return ImageFont.truetype('/usr/share/fonts/opentype/noto/'+('NotoSansCJK-Bold.ttc' if bold else 'NotoSansCJK-Regular.ttc'),n,index=2)
def solar():
    hour=14+16/60+32/3600;lat=math.radians(31.2199);lon=121.461
    g=2*math.pi/365*(252-1+(hour-12)/24)
    e=229.18*(.000075+.001868*math.cos(g)-.032077*math.sin(g)-.014615*math.cos(2*g)-.040849*math.sin(2*g))
    dec=.006918-.399912*math.cos(g)+.070257*math.sin(g)-.006758*math.cos(2*g)+.000907*math.sin(2*g)-.002697*math.cos(3*g)+.00148*math.sin(3*g)
    ha=math.radians((hour*60+e+4*lon-480)/4-180)
    en=np.array([-math.cos(dec)*math.sin(ha),math.sin(dec)*math.cos(lat)-math.cos(dec)*math.cos(ha)*math.sin(lat)])
    z=math.sin(lat)*math.sin(dec)+math.cos(lat)*math.cos(dec)*math.cos(ha);a=math.radians(CALIBRATION['bearing_degrees'])
    return np.array([en@[math.sin(a),math.cos(a)],en@[-math.cos(a),math.sin(a)],z]),[round(math.degrees(math.atan2(*en))%360,2),round(math.degrees(math.asin(z)),2)]
def isolate_sites(original,work):
    # Sites are over 85 m apart. Use each set of original GLB primitives for its
    # local camera and shadow map, preserving all original buffers and indices.
    blob=original.read_bytes();size,kind=struct.unpack_from('<II',blob,12);doc=json.loads(blob[20:20+size]);chunks=blob[20+size:]
    parts=iter(read_glb(original)[0]);scene=doc['scenes'][doc.get('scene',0)];sub={212:[],244:[]};counts={212:0,244:0}
    for inode in scene['nodes']:
        n=doc['nodes'][inode];mesh=doc['meshes'][n['mesh']];by={212:[],244:[]}
        for prim in mesh['primitives']:
            pts,_,_,idx,_,_=next(parts);x=pts[:,0]
            if x.min()>-30:site=212
            elif x.max()<-50:site=244
            else:raise ValueError('A primitive bridges the two independently observed addresses.')
            by[site].append(prim);counts[site]+=len(idx)//3
        for site,prims in by.items():
            if prims:sub[site].append(({k:v for k,v in n.items()if k!='mesh'},{**mesh,'primitives':prims}))
    result={}
    for site,rows in sub.items():
        if not rows:raise ValueError(f'Missing geometry for Lane {site}.')
        outdoc={**doc,'nodes':[{**n,'mesh':i} for i,(n,_) in enumerate(rows)],'meshes':[m for _,m in rows], 'scenes':[{**scene,'nodes':list(range(len(rows)))}],'scene':0}
        data=json.dumps(outdoc,ensure_ascii=False,separators=(',',':')).encode();data+=b' '*(-len(data)%4);out=work/f'{site}.glb'
        out.write_bytes(struct.pack('<4sIIII',b'glTF',2,20+len(data)+len(chunks),len(data),kind)+data+chunks);result[site]=out
    return result,counts
def board(model,photo,out,level):
    if digest(photo)!=CALIBRATION['original_sha256']:raise ValueError('Supply the identified unmodified Commons original.')
    ref=ImageOps.exif_transpose(Image.open(photo)).convert('RGB');paper=Image.new('RGB',(1614,1490),'#f6f5ef');draw=ImageDraw.Draw(paper);title='#30332c';muted='#565d53'
    draw.text((40,18),'南昌路212弄门楼与244弄入口',font=font(43,True),fill=title)
    draw.text((42,82),'上海黄浦　　2015 年摄影比对　　'+('近景模型'if level=='full'else'远景模型'),font=font(22),fill=muted)
    notes=[];sun,angles=solar()
    with tempfile.TemporaryDirectory()as td:
        tmp=Path(td);site,counts=isolate_sites(model,tmp);so=tmp/'entrances.so';subprocess.run(['cc','-O2','-shared','-fPIC','-o',str(so),str(RASTER/'photo_glb_raster.c'),'-lm'],check=True)
        lib=ctypes.CDLL(str(so));lib.shadow_depth.restype=lib.paint.restype=None
        def view(number,P,crop,width,light,angle):
            capture=SurfaceCapture(lib,site[number]);im,stats=raster(site[number],capture,width,P,crop,light,angle)
            im,ao=horizon_shading(im,capture.depth,P,crop);notes.append(dict(site=number,source_crop=crop,pixels=stats['rendered_px'],visible=stats['zbuffer_foreground_pixels'],triangles=stats['triangles'],sky_occlusion=ao));return im
        main=np.array(CALIBRATION['camera_matrices']['commons_2015']);crop=(2790,690,4930,2960);rect=(749,795)
        for x,label,im in [(40,'212弄 · 2015年9月实拍',ref.crop(crop)),(826,'212弄 · 同机位模型',view(212,main,crop,1700,sun,angles))]:
            draw.text((x,139),label,font=font(23,True),fill=title);paper.paste(im.resize(rect,Image.Resampling.LANCZOS),(x,184))
        y=1042;original=(3140,2140,3345,2450)
        for x,label,im in [(40,'实拍门牌',ref.crop(original)),(229,'模型门牌',view(212,main,original,335,sun,angles))]:
            draw.text((x,y-45),label,font=font(20,True),fill=title);paper.paste(im.resize((160,242),Image.Resampling.LANCZOS),(x,y))
        winter=np.array([-.52,-.55,.70]);winter/=np.linalg.norm(winter)
        winter_camera=np.array(CALIBRATION['camera_matrices']['gate212-3-201512'])
        im=view(212,winter_camera,(42,140,659,749),765,winter,None);draw.text((433,y-45),'沿街看212弄门楼',font=font(20,True),fill=title);paper.paste(im.resize((344,340),Image.Resampling.LANCZOS),(433,y))
        eye,M,r=transform('root244-alley-wide');local=np.column_stack([M,-M@eye]);cam=local@np.linalg.inv(location())
        im=view(244,cam,(103,25,577,474),800,winter,None);draw.text((826,y-45),'244弄西侧绿牌、窄窗与内收铁门',font=font(20,True),fill=title);paper.paste(im.resize((363,344),Image.Resampling.LANCZOS),(826,y))
        draw.multiline_text((1230,y+8),'两处实物相距约85.6米。\n\n212弄的旧称为环龙别业。\n244弄由西侧弄牌及东邻\n242号门牌交叉定位。',font=font(21),fill=muted,spacing=10)
    draw.line((40,1400,1574,1400),fill='#c7c5b8',width=2)
    draw.text((42,1417),'摄影　Antigng · Wikimedia Commons · CC BY-SA 4.0（裁切）。其余视图由实际交付的三维模型绘制。',font=font(19),fill=muted)
    draw.text((42,1452),'门扇开启状态取自2015年照片，两处位置及门楼尺度为摄影估算。',font=font(17),fill=muted)
    paper.save(out,quality=92,optimize=True,subsampling=0)
    out.with_suffix('.json').write_text(json.dumps(dict(level=level,model_sha256=digest(model),board_sha256=digest(out),original_photo_sha256=digest(photo),photographer='Antigng',original=CALIBRATION['source_url'],license='CC BY-SA 4.0',license_url='https://creativecommons.org/licenses/by-sa/4.0/',changes='EXIF orientation, two crops, resizing, original layout and model renders. No street-view imagery reproduced.',date_local='2015-09-09 14:16:32',solar_azimuth_altitude=angles,winter_light='illustrative, capture times unknown',triangles_in_each_address=counts,views=notes),indent=2,ensure_ascii=False)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mesh',type=Path);p.add_argument('photo',type=Path);p.add_argument('output',type=Path);p.add_argument('--level',choices=['full','lod'],required=True)
    a=p.parse_args();board(a.mesh,a.photo,a.output,a.level)
