"""Rasterize the actual GLB with its two recorded garden cameras and translucent glazing."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import struct

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE=Path(__file__).resolve().parent
HELPER=HERE.parents[3]/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
VIEWS={'whb2019':((32,124,490,277),'2019年《文汇报》庭院视角'), 'garden2017':((24,130,405,244),'2017年《解放日报》水池视角')}


def raster(path,cam,crop,width):
    data=path.read_bytes()
    length=struct.unpack_from('<I',data,12)[0]
    doc=json.loads(data[20:20+length])
    tri,mi,names,_=runpy.run_path(str(HELPER))['load_triangles'](path)
    k,r,eye=[np.array(cam[key])for key in ('K','R','C')]
    scale=width/(crop[2]-crop[0]);height=round((crop[3]-crop[1])*scale)
    zbuffer=np.full((height,width),np.inf);scene=np.zeros((height,width,3))+[.78,.78,.745]
    rgba=np.array([m['pbrMetallicRoughness']['baseColorFactor']for m in doc['materials']])
    cam_xyz=(tri-eye)@r.T;uvw=cam_xyz@k.T
    projected=(uvw[:,:,:2]/uvw[:,:,2,None]-crop[:2])*scale
    normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);normal/=np.linalg.norm(normal,axis=1)[:,None]
    visible=np.flatnonzero((np.sum(normal*(eye-tri[:,0]),axis=1)>0)&(cam_xyz[:,:,2].min(axis=1)>.01))
    viewdir=eye-tri.mean(axis=1);viewdir/=np.linalg.norm(viewdir,axis=1)[:,None]
    daylight=np.array([.19,-.61,.77]);daylight/=np.linalg.norm(daylight)
    weight=.56+.31*np.maximum(0,normal@daylight)+.12*np.sum(viewdir*normal,axis=1)
    opaque=visible[rgba[mi[visible],3]>=.99];trans=visible[rgba[mi[visible],3]<.99]
    order=np.concatenate([opaque,trans[np.argsort(-cam_xyz[trans,:,2].mean(axis=1))]])
    for j in order:
        xy=projected[j]
        lo=np.maximum(0,np.floor(xy.min(axis=0)).astype(int));hi=np.minimum((width,height),np.ceil(xy.max(axis=0)).astype(int)+1)
        if min(hi-lo)<=0:continue
        a,b,c=xy;den=(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
        if abs(den)<1e-8:continue
        lx,ly=lo;hx,hy=hi
        ys,xs=np.mgrid[ly:hy,lx:hx];xx=xs+.5-a[0];yy=ys+.5-a[1]
        u=(xx*(c[1]-a[1])-yy*(c[0]-a[0]))/den
        v=((b[0]-a[0])*yy-(b[1]-a[1])*xx)/den
        hit=(u>=0)&(v>=0)&(u+v<=1)
        d=cam_xyz[j,:,2]
        depth=1/((1-u-v)/d[0]+u/d[1]+v/d[2])
        zb=zbuffer[ly:hy,lx:hx];hit&=depth<zb
        color=rgba[mi[j],:3]*weight[j];alpha=rgba[mi[j],3]
        local=scene[ly:hy,lx:hx];local[hit]=color*alpha+local[hit]*(1-alpha)
        if alpha>=.99:zb[hit]=depth[hit]
    mapped=np.where(scene<=.0031308,12.92*scene,1.055*scene**(1/2.4)-.055)
    return Image.fromarray(np.clip(mapped*255,0,255).astype('uint8'))


def render(mesh,out,width):
    out.mkdir(exist_ok=True,parents=True)
    book=json.loads((HERE/'garden-cameras.json').read_bytes())
    cards=[];report={'mesh_sha256':hashlib.sha256(mesh.read_bytes()).hexdigest(),'inputs':'Actual GLB plus fitted cameras. No source imagery is loaded.','views':{}}
    for name,(crop,caption) in VIEWS.items():
        pic=raster(mesh,book['stations'][name],crop,width*2)
        pic=pic.resize((width,round(pic.height/2)),Image.Resampling.LANCZOS)
        target=out/(name+'-model.jpg');pic.save(target,quality=94,subsampling=0)
        cards.append((caption,pic));report['views'][name]={'file':target.name,'original_image_crop':crop,'width':width,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}
    ws=width+20;hs=max(im.height for _,im in cards)+42
    comp=Image.new('RGB',(ws*2,hs),(237,234,226));draw=ImageDraw.Draw(comp)
    font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',15,index=2)
    for i,(caption,im) in enumerate(cards):
        comp.paste(im,(i*ws+10,(hs-32-im.height)//2));draw.text((i*ws+10,hs-27),caption,font=font,fill=(48,44,40))
    comp.save(out/'registered-garden.jpg',quality=93,subsampling=0)
    (out/'registered-renders.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mesh',type=Path);parser.add_argument('out',type=Path)
    parser.add_argument('--width',type=int,default=496);args=parser.parse_args();render(args.mesh,args.out,args.width)
