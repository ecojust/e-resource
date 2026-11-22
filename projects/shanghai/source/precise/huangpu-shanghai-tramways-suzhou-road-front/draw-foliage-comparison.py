"""Project the reviewed GLB onto the four camera crops of the 2015 entrance façade."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import struct
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps


def image_camera(mesh,project,source):
    sys.path.insert(0,str(source))
    from photo_plane import H,D
    lib=runpy.run_path(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py')
    faces,indices,names,info=lib['load_triangles'](mesh)
    with mesh.open('rb')as f:
        f.seek(12);n,_=struct.unpack('<II',f.read(8));doc=json.loads(f.read(n))
    palette=[]
    for material in doc['materials']:
        spec=material['pbrMetallicRoughness'];c=np.array(spec['baseColorFactor'][:3])
        if 'baseColorTexture'in spec:
            with Image.open(source/'tramways-cream-render.png')as texture:c=(np.asarray(texture.convert('RGB'),float)/255.)**2.2
            c=np.mean(c,axis=(0,1))
        palette.append(c)
    # Use the original camera and a diffuse upper-left light. Exact contours and
    # occlusion derive from the geometry. No source-photo colour enters the mesh.
    centre=np.linalg.solve(np.column_stack((H[:,0],D,H[:,1])),-H[:,2])
    norm=np.cross(faces[:,1]-faces[:,0],faces[:,2]-faces[:,0])
    norm/=np.maximum(np.linalg.norm(norm,axis=1,keepdims=True),1e-12)
    front=np.einsum('ij,ij->i',norm,centre-faces[:,0])>0
    flags=np.array([mat.get('doubleSided',False)for mat in doc['materials']])[indices]
    visible=front|flags
    light=np.array([-.42,-.67,.82]);light/=np.linalg.norm(light)
    lit=.49+.69*np.maximum(0.,norm@light)
    cols=np.clip((np.asarray(palette)[indices]*lit[:,None])**(1/2.2)*255.,0,255).astype('uint8')
    xyz=faces.reshape(-1,3);h=np.column_stack((xyz[:,0],xyz[:,2],np.ones(len(xyz))))@H.T+xyz[:,1,None]*D
    xy=(h[:,:2]/h[:,2,None]).reshape(-1,3,2)
    invz=1./abs(h[:,2].reshape(-1,3))
    return xy[visible],invz[visible],cols[visible],info


def draw_panel(scene,box,size):
    polygons,depth,colors,_=scene
    w,h=size
    lo=np.array(box[:2]);span=np.subtract(box[2:],lo)
    p=(polygons-lo)*([w,h]/span)
    lower=np.floor(np.min(p,axis=1)).astype(int);upper=np.ceil(np.max(p,axis=1)).astype(int)
    keep=np.flatnonzero((upper[:,0]>=0)&(upper[:,1]>=0)&(lower[:,0]<w)&(lower[:,1]<h))
    canvas=np.full((h,w,3),[218,218,209],dtype='uint8');zbuf=np.full((h,w),-np.inf)
    for k in keep:
        x0,y0=np.maximum(lower[k],[0,0]);x1,y1=np.minimum(upper[k],[w-1,h-1])
        if x0>x1 or y0>y1:continue
        (ax,ay),(bx,by),(cx,cy)=p[k]
        denom=(by-cy)*(ax-cx)+(cx-bx)*(ay-cy)
        if abs(denom)<1e-9:continue
        y,x=np.ogrid[y0+.5:y1+1.5,x0+.5:x1+1.5]
        a=((by-cy)*(x-cx)+(cx-bx)*(y-cy))/denom
        b=((cy-ay)*(x-cx)+(ax-cx)*(y-cy))/denom;c=1-a-b
        iz=a*depth[k,0]+b*depth[k,1]+c*depth[k,2]
        previous=zbuf[y0:y1+1,x0:x1+1];hit=(np.minimum(np.minimum(a,b),c)>=-1.e-9)&(iz>previous)
        previous[hit]=iz[hit];canvas[y0:y1+1,x0:x1+1][hit]=colors[k]
    return Image.fromarray(canvas)


def make(photo,scene,records,out):
    size=(1120,885);paper=Image.new('RGB',size,'#f5f0e5');pen=ImageDraw.Draw(paper)
    def title(x,y,s,pt,bold=False):
        font='/usr/share/fonts/opentype/noto/NotoSansCJK-'+('Bold' if bold else 'Regular')+'.ttc'
        pen.text((x,y),s,font=ImageFont.truetype(font,pt,index=2),fill='#312e29')
    title(35,18,'南苏州路 185 号的四枚浮雕花环',31,True)
    title(36,70,'英商上海电车公司大楼　｜　沿街立面从左至右',19)
    pen.line((36,110,1082,110),fill='#aba394')
    boxes=[v['source_box']for v in records]
    # Use the same aspect and scale for both rows within a single column.
    with Image.open(photo)as original:
        upright=ImageOps.exif_transpose(original)
        for k,box in enumerate(boxes):
            x=41+k*268;bx=np.array(box);centre=(bx[:2]+bx[2:])*.5
            span=np.array(bx[2:])-bx[:2];height=span[1]*1.035
            width=height*231/245
            bb=np.rint(np.r_[centre-[width,height]*np.array([.5,.5]),centre+[width,height]*np.array([.5,.5])]).astype(int)
            panel=(231,245);title(x,130,['第一枚','第二枚','第三枚','第四枚'][k],17,True)
            crop=upright.crop(tuple(bb)).resize(panel,Image.Resampling.LANCZOS)
            paper.paste(crop,(x,189))
            model=draw_panel(scene,bb,panel)
            paper.paste(model,(x,502))
    title(38,156,'2015 年街面照片',15)
    title(38,463,'由下载模型按同一机位绘制',16)
    pen.line((36,776,1082,776),fill='#aba394')
    title(37,797,'四枚花环分别保留红褐色叶瓣和露出后方墙面的环心。凸起深度按照片估算。',17)
    title(37,841,'摄影 Antigng，2015 年 7 月 20 日。原照裁自 Wikimedia Commons。图板采用 CC BY-SA 4.0。',14)
    paper.save(out,quality=91,subsampling=0,optimize=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('photo','mesh','source','project','wreaths','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();m=json.loads(a.wreaths.read_bytes())
    with a.photo.open('rb')as f:
        if hashlib.file_digest(f,'sha256').hexdigest()!=m['photo_sha256']:raise ValueError('Unexpected source photograph')
    scene=image_camera(a.mesh,a.project,a.source)
    make(a.photo,scene,m['wreaths'],a.output)
    print(scene[-1]['sha256'],hashlib.sha256(a.output.read_bytes()).hexdigest())
