"""Rasterize the actual GLB with its two recorded garden cameras and translucent glazing."""
import argparse
from io import BytesIO
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


def texture_data(doc,data,json_length):
    binary=data[28+json_length:]
    types={5121:'u1',5123:'<u2',5125:'<u4',5120:'i1',5122:'<i2',5126:'<f4'}
    def accessor(idx):
        ref=doc['accessors'][idx];view=doc['bufferViews'][ref['bufferView']]
        dt=np.dtype(types[ref['componentType']]);n={'SCALAR':1,'VEC2':2,'VEC3':3}[ref['type']]
        off=view.get('byteOffset',0)+ref.get('byteOffset',0)
        a=np.ndarray((ref['count'],n),dtype=dt,buffer=binary,offset=off,strides=(view.get('byteStride',dt.itemsize*n),dt.itemsize))
        return a.astype(float)/np.iinfo(dt).max if ref.get('normalized') else a
    images=[]
    for asset in doc.get('images',[]):
        view=doc['bufferViews'][asset['bufferView']];a=view.get('byteOffset',0)
        images.append(np.asarray(Image.open(BytesIO(binary[a:a+view['byteLength']])).convert('RGB'))/255.)
    uv=[]
    def visit(idx):
        node=doc['nodes'][idx]
        if 'mesh' in node:
            for prim in doc['meshes'][node['mesh']]['primitives']:
                faces=accessor(prim['indices']).reshape(-1,3).astype(int)
                tex=prim['attributes'].get('TEXCOORD_0')
                uv.append(accessor(tex)[faces] if tex is not None else np.zeros((len(faces),3,2)))
        for child in node.get('children',[]):visit(child)
    for idx in doc['scenes'][doc.get('scene',0)]['nodes']:visit(idx)
    maps={}
    for mid,mat in enumerate(doc['materials']):
        pbr=mat['pbrMetallicRoughness']
        if 'baseColorTexture' in pbr:
            alb=images[doc['textures'][pbr['baseColorTexture']['index']]['source']]
            lin=np.where(alb<=.04045,alb/12.92,((alb+.055)/1.055)**2.4)
            norm=None
            if mat.get('normalTexture'):
                norm=images[doc['textures'][mat['normalTexture']['index']]['source']]*2-1
            maps[mid]=lin,norm
    return np.concatenate(uv),maps


def raster(path,cam,crop,width):
    data=path.read_bytes()
    length=struct.unpack_from('<I',data,12)[0]
    doc=json.loads(data[20:20+length])
    tri,mi,names,_=runpy.run_path(str(HELPER))['load_triangles'](path)
    k,r,eye=[np.array(cam[key])for key in ('K','R','C')]
    scale=width/(crop[2]-crop[0]);height=round((crop[3]-crop[1])*scale)
    zbuffer=np.full((height,width),np.inf);scene=np.zeros((height,width,3))+[.78,.78,.745]
    rgba=np.array([m['pbrMetallicRoughness']['baseColorFactor']for m in doc['materials']])
    tex_uv,textures=texture_data(doc,data,length)
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
        if not np.any(hit):continue
        if mi[j] in textures:
            # Perspective-correct UVs and each material's embedded tangent-space normal map.
            coords=((1-u[hit]-v[hit])[:,None]/d[0]*tex_uv[j,0]+u[hit,None]/d[1]*tex_uv[j,1]+v[hit,None]/d[2]*tex_uv[j,2])*depth[hit,None]
            alb,nm=textures[mi[j]]
            ix=np.floor((coords[:,0]%1)*alb.shape[1]).astype(int)%alb.shape[1]
            iy=np.floor((coords[:,1]%1)*alb.shape[0]).astype(int)%alb.shape[0]
            light=weight[j]
            tuv=tex_uv[j,1:]-tex_uv[j,0];edges=tri[j,1:]-tri[j,0]
            if nm is not None and abs(np.linalg.det(tuv))>1e-9:
                tangent,bitangent=np.linalg.solve(tuv,edges)
                tangent/=np.linalg.norm(tangent);bitangent/=np.linalg.norm(bitangent)
                normals=nm[iy,ix]@np.vstack([tangent,bitangent,normal[j]])
                normals/=np.linalg.norm(normals,axis=1)[:,None]
                light=(.56+.31*np.maximum(0,normals@daylight)+.12*(normals@viewdir[j]))[:,None]
            color=alb[iy,ix]*rgba[mi[j],:3]*light
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
