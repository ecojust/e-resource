"""Original photograph and the delivered court model, plus two surveyed street views of the entrance."""
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

HERE=Path(__file__).resolve().parent;SIBLINGS=HERE.parents[1]
RASTER=SIBLINGS/'huangpu-yuanmingyuan-apartments-street-front/measurements'
sys.path[:0]=[str(HERE.parent/'source'),str(RASTER),str(SIBLINGS/'huangpu-world-book-company-fuzhou-front/measurements')]
from courtyard_photo_plane import MATRIX
from courtyard_placement import TRANSFORM
from zheng_gate_camera import REC,matrix
from photo_glb_raster import raster,read_glb
from fuzhou_skylight import SurfaceCapture,horizon_shading

def sha(f):
    return hashlib.sha256(f.read_bytes()).hexdigest()

def font(size,heavy=False):
    return ImageFont.truetype('/usr/share/fonts/opentype/noto/'+('NotoSansCJK-Bold.ttc'if heavy else'NotoSansCJK-Regular.ttc'),size,index=2)

def sun_position():
    # Solar time at the EXIF exposure. The north-facing wall is in shade.
    hour=14+46/60+26/3600;day=252;lat=math.radians(31.212);lon=121.458
    g=2*math.pi/365*(day-1+(hour-12)/24)
    eq=229.18*(.000075+.001868*math.cos(g)-.032077*math.sin(g)-.014615*math.cos(2*g)-.040849*math.sin(2*g))
    dec=(.006918-.399912*math.cos(g)+.070257*math.sin(g)-.006758*math.cos(2*g)+.000907*math.sin(2*g)-.002697*math.cos(3*g)+.00148*math.sin(3*g))
    ha=math.radians((hour*60+eq+4*lon-480)/4-180)
    en=np.array([-math.cos(dec)*math.sin(ha),math.sin(dec)*math.cos(lat)-math.cos(dec)*math.cos(ha)*math.sin(lat)])
    up=math.sin(lat)*math.sin(dec)+math.cos(lat)*math.cos(dec)*math.cos(ha)
    a=math.radians(REC['x_axis_bearing_deg'])
    light=np.array([en@[math.sin(a),math.cos(a)],en@[-math.cos(a),math.sin(a)],up]);light/=np.linalg.norm(light)
    return light,[round(math.degrees(math.atan2(en[0],en[1]))%360.,2),round(math.degrees(math.asin(up)),2)]

def court_scene(original,out,camera):
    """Retain the original GLB primitives on the photographed side of the camera.

    The street and courtyard components are physically separate. No triangle
    intersects this camera; the projected wall retains its original vertex,
    index, normal, UV, material and texture byte ranges.
    """
    data=original.read_bytes();jlen,jtype=struct.unpack_from('<II',data,12)
    doc=json.loads(data[20:20+jlen]);original_chunks=data[20+jlen:]
    parts,_,_=read_glb(original);parts=iter(parts);meshes=[];nodes=[];retained=0;excluded=0
    scene=doc['scenes'][doc.get('scene',0)]
    for inode in scene['nodes']:
        node=doc['nodes'][inode];mesh=doc['meshes'][node['mesh']];visible=[]
        for prim in mesh['primitives']:
            vertices,_,_,idx,_,_=next(parts)
            depth=vertices@camera[2,:3]+camera[2,3];n=len(idx)//3
            if depth.min()>.10:visible.append(prim);retained+=n
            elif depth.max()<=.10:excluded+=n
            else:raise ValueError('The street and court no longer form separate primitives at this viewpoint')
        if visible:
            nodes.append({**node,'mesh':len(meshes)});meshes.append({**mesh,'primitives':visible})
    if not retained:raise ValueError('The original photograph sees no geometry')
    doc['nodes']=nodes;doc['meshes']=meshes;scene['nodes']=list(range(len(nodes)))
    desc=json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode();desc+=b' '*(-len(desc)%4)
    total=20+len(desc)+len(original_chunks)
    out.write_bytes(struct.pack('<4sIIII',b'glTF',2,total,len(desc),jtype)+desc+original_chunks)
    return {'visible_triangles':retained,'triangles_behind_camera':excluded,'near_plane_m':.10}

def build(mesh,photo,out,role):
    record=json.loads((HERE/'courtyard-house-photo-identification.json').read_bytes())
    if sha(photo)!=record['photo']['sha256']:raise ValueError('Original Antigng photograph required')
    ref=ImageOps.exif_transpose(Image.open(photo)).convert('RGB')
    paper=Image.new('RGB',(1766,1570),(246,245,239));draw=ImageDraw.Draw(paper);dark=(47,48,40);gray=(85,88,77)
    draw.text((42,18),'永嘉路 39 弄 · 郑家衖',font=font(46,True),fill=dark)
    draw.text((44,95),'上海黄浦　｜　院内横屋与沿街弄口　｜　'+('近景模型'if role=='full'else'轻量模型'),font=font(23),fill=gray)
    crop=(0,1450,2988,4040);pw=818;ph=round(pw*(crop[3]-crop[1])/(crop[2]-crop[0]));top=190
    main_camera=MATRIX@np.linalg.inv(TRANSFORM);sun,angles=sun_position();reports=[]
    def paint_view(lib,cam,region,width,sun,illumin,scene=None):
        scene=mesh if scene is None else scene
        capture=SurfaceCapture(lib,scene);im,report=raster(scene,capture,width,cam,region,sun,illumin);im,ao=horizon_shading(im,capture.depth,cam,region)
        reports.append({'crop':region,'width':width,'model_visible_pixels':report['zbuffer_foreground_pixels'],'triangles':report['triangles'],'sky_occlusion':ao})
        return im
    with tempfile.TemporaryDirectory() as tmp:
        so=Path(tmp)/'courtyard.so';subprocess.run(['cc','-O2','-shared','-fPIC','-o',str(so),str(RASTER/'photo_glb_raster.c'),'-lm'],check=True)
        lib=ctypes.CDLL(str(so));lib.paint.restype=lib.shadow_depth.restype=None
        visible=Path(tmp)/'front.glb';split=court_scene(mesh,visible,main_camera)
        model=paint_view(lib,main_camera,crop,2100,sun,angles,visible)
        for x,title,im in [(42,'院内实拍 · 2015 年 9 月',ref.crop(crop)),(903,'同机位三维模型',model)]:
            draw.text((x,top-46),title,font=font(23,True),fill=dark);paper.paste(im.resize((pw,ph),Image.Resampling.LANCZOS),(x,top))
        y=top+ph+75
        winter=np.array([-.5,-.46,.70]);winter/=np.linalg.norm(winter)
        items=[(42,'沿永嘉路看两片铁门与院内横屋','root-gate-15',(104,85,810,567),824),
               (909,'从西侧斜看收拢的门扇','root-gate-west15',(200,138,730,520),515),
               (1461,'门柱与彩色竖牌','root-leftpost-15',(274,-25,520,634),230)]
        ymax=y
        for x,title,n,rect,width in items:
            im=paint_view(lib,matrix(n),rect,round(1.45*width),winter,None);height=round(width*(rect[3]-rect[1])/(rect[2]-rect[0]))
            # Fit the narrow sign into the shared bottom row, keeping its aspect ratio.
            scale=min(1,435/height);th=round(height*scale);tw=round(width*scale)
            draw.text((x,y-44),title,font=font(21,True),fill=dark)
            paper.paste(im.resize((tw,th),Image.Resampling.LANCZOS),(x,y));ymax=max(ymax,y+th)
    bottom=ymax+24;draw.line((42,bottom,1724,bottom),fill=(196,192,180),width=2)
    draw.text((43,bottom+12),'院内摄影　Antigng · Wikimedia Commons · CC BY-SA 4.0（裁切）　　模型图依据公开机位绘制。',font=font(19),fill=gray)
    draw.text((43,bottom+47),'入弄后的距离依据照片估算。窗的位置、“家政”匾与外机可在 2015 年弄口街景中交叉辨认，院内门牌待核。',font=font(18),fill=gray)
    paper.crop((0,0,paper.width,bottom+88)).save(out,quality=93,optimize=True,subsampling=0)
    out.with_suffix('.json').write_text(json.dumps(dict(geometry=role,mesh_sha256=sha(mesh),plate_sha256=sha(out),source_photo_sha256=sha(photo),photographer='Antigng',file_page=record['photo']['file_page'],license='CC BY-SA 4.0',license_url=record['photo']['license_url'],exposure_local_time=record['photo']['exif_local_time'],solar_azimuth_elevation_deg=angles,gate_illumination='Illustrative; actual December exposure time unknown.',court_camera_visibility=split,views=reports),ensure_ascii=False,indent=1)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mesh',type=Path);p.add_argument('photo',type=Path);p.add_argument('output',type=Path);p.add_argument('--mode',required=True,choices=['full','lod'])
    a=p.parse_args();build(a.mesh,a.photo,a.output,a.mode)
