"""Pair licensed 2017 window details with the assembled street model in the registered camera."""
import argparse
import hashlib
import json
import struct
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from check_street_windows import mesh, projector

M = Path(__file__).resolve().parent
# Coordinates on Antigng's uncropped 5312 × 2988 photograph.
ROWS = [
    ('南屋临街二层双窗','两扇浅色窗框上方，各有一樘横向通亮。砖墙在两组窗之间。',(562,1485,1452,1885)),
    ('北屋弄侧二层窗','深色窗框外可见横向护栏和开启的窗扇。模型取固定框与扇格的平面位置。',(2974,1666,3482,2110)),
]


def colors(path):
    data=path.read_bytes()
    header=struct.unpack_from('<4sIII4s',data)
    assert header[0:2]==(b'glTF',2) and header[4]==b'JSON'
    doc=json.loads(data[20:20+header[3]]);buf=memoryview(data)[28+header[3]:]
    rgb=np.array([m['pbrMetallicRoughness']['baseColorFactor'][:3] for m in doc['materials']])
    # sRGB texture samples modulate a linear base colour. The table stores sRGB render multipliers.
    shade_rgb=np.clip(255*np.where(rgb<.0031308,12.92*rgb,1.055*rgb**(1/2.4)-.055),0,255)
    texdata=[]
    for im in doc.get('images',[]):
        view=doc['bufferViews'][im['bufferView']];begin=view.get('byteOffset',0)
        texdata.append(np.array(Image.open(BytesIO(bytes(buf[begin:begin+view['byteLength']]))).convert('RGB')))
    textures={}
    for i,m in enumerate(doc['materials']):
        ref=m['pbrMetallicRoughness'].get('baseColorTexture')
        if ref:textures[i]=texdata[doc['textures'][ref['index']]['source']]
    def attr(idx):
        ac=doc['accessors'][idx];view=doc['bufferViews'][ac['bufferView']]
        width={'SCALAR':1,'VEC2':2}[ac['type']];dt=np.dtype({5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[ac['componentType']])
        return np.ndarray((ac['count'],width),dt,buf,view.get('byteOffset',0)+ac.get('byteOffset',0),
                          strides=(view.get('byteStride',width*dt.itemsize),dt.itemsize))
    us=[]
    for node in doc['nodes']:
        if 'mesh' not in node:continue
        for pr in doc['meshes'][node['mesh']]['primitives']:
            ix=attr(pr['indices']).reshape(-1,3)
            if pr['material'] in textures:us.append(attr(pr['attributes']['TEXCOORD_0'])[ix])
            else:us.append(np.zeros((*ix.shape,2),dtype=np.float32))
    return shade_rgb,textures,np.concatenate(us)


def render(triangles, ids, materials, matrix, crop, fit):
    palette,textures,uvtri=materials
    a,b,c,d = crop
    ratio = min(fit[0]/(c-a),fit[1]/(d-b))
    width,height=round((c-a)*ratio),round((d-b)*ratio)
    projected=projector(matrix,triangles)
    xy=(projected[:,:,:2]-[a,b])*ratio
    view_depth=projected[:,:,2]
    bounds0=xy.min(1);bounds1=xy.max(1)
    selected=np.flatnonzero((view_depth>.01).all(1)&(bounds0[:,0]<width)&(bounds1[:,0]>0)&
                            (bounds0[:,1]<height)&(bounds1[:,1]>0))
    out=np.full((height,width,3),[222,229,232],dtype=np.uint8)
    depth=np.full((height,width),np.inf)
    normals=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0])
    illumination=np.array([-.35,-.67,.65])
    shade=.78+.22*np.abs(normals@illumination)/np.maximum(1e-12,np.linalg.norm(normals,axis=1))
    for i in selected:
        p, q, r=xy[i]
        u,v=q-p,r-p
        det=u[0]*v[1]-u[1]*v[0]
        if abs(det)<1e-8:continue
        low=np.maximum(np.floor(bounds0[i]).astype(int),0)
        high=np.minimum(np.ceil(bounds1[i]).astype(int)+1,[width,height])
        l,t=low;rr,bb=high
        if rr<=l or bb<=t:continue
        yy,xx=np.ogrid[t:bb,l:rr];x=xx+.5-p[0];y=yy+.5-p[1]
        s=(x*v[1]-y*v[0])/det; h=(u[0]*y-u[1]*x)/det; w=1-s-h
        inside=(s>=0)&(h>=0)&(w>=0)
        if not inside.any():continue
        z0,z1,z2=view_depth[i]
        with np.errstate(divide='ignore',invalid='ignore'):z=1/(w/z0+s/z1+h/z2)
        depth_region=depth[t:bb,l:rr];changed=inside&(z<depth_region)
        depth_region[changed]=z[changed]
        base=palette[ids[i]]*shade[i]
        if ids[i] not in textures or not changed.any():
            out[t:bb,l:rr][changed]=base
            continue
        tex=textures[ids[i]]
        weights=np.stack([w[changed]/z0,s[changed]/z1,h[changed]/z2],axis=-1)*z[changed,None]
        uv=weights@uvtri[i]
        tx=np.floor((uv[:,0]%1)*tex.shape[1]).astype(int)%tex.shape[1]
        ty=np.floor((uv[:,1]%1)*tex.shape[0]).astype(int)%tex.shape[0]
        out[t:bb,l:rr][changed]=np.clip(tex[ty,tx]*base/255,0,255)
    return Image.fromarray(out)


def font(size):
    return ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',size,index=2)


def make(photo,model,destination):
    native=Image.open(photo).convert('RGB')
    credit=json.loads((M/'southern-lane-evidence.json').read_bytes())['commons']
    photo_sig=hashlib.sha256(photo.read_bytes()).hexdigest()
    assert native.size==(5312,2988) and photo_sig==credit['sha256']
    registered=M/'commons-2017-street-registered.json'
    pose=json.loads(registered.read_bytes());matrix=np.array(pose['matrix'])
    triangles,ids,_,_,modelsha=mesh(model);palette=colors(model)
    out=Image.new('RGB',(1100,840),(249,248,244));draw=ImageDraw.Draw(out)
    def label(x,y,text,size,colour='#252a29'):
        draw.text((x,y),text,font=font(size),fill=colour)
    label(34,16,'荣康别墅南弄口两侧的窗扇',31)
    label(35,68,'实景  ·  2017年8月19日',19)
    label(563,68,'三维模型  ·  同机位投影',19)
    top=108;panels=[]
    for i,(title,note,rect) in enumerate(ROWS):
        fit=(506,227 if i==0 else 274)
        renderimg=render(triangles,ids,palette,matrix,rect,fit)
        source=native.crop(rect).resize(renderimg.size,Image.Resampling.LANCZOS)
        for x,im in [(34,source),(562,renderimg)]:
            draw.rectangle((x,top,x+505,top+fit[1]-1),fill='#deded9')
            out.paste(im,(x+(fit[0]-im.width)//2,top+(fit[1]-im.height)//2))
        label(34,top+fit[1]+5,title,19)
        label(34,top+fit[1]+35,note,16,'#414946')
        panels.append({'name':title,'original_pixel_crop':list(rect),'actual_pixels':list(renderimg.size)})
        top+=fit[1]+76
    label(34,top+3,'实景摄影 Antigng  ·  Wikimedia Commons《荣康别墅.jpg》  ·  CC BY-SA 4.0',15)
    label(34,top+27,'两行均裁自同一张原片。原图的树枝、线缆和外置护栏会遮住部分窗框。',15)
    final=destination/'registered-2017-window-pair.jpg';destination.mkdir(exist_ok=True,parents=True)
    out.crop((0,0,out.width,top+63)).save(final,quality=91,subsampling=0,optimize=True)
    info=dict(title='荣康别墅南弄口两侧的窗扇',photo_title=credit['title'],photo_author=credit['author'],
              shot=credit['photographed'],source=credit['page'],license='CC BY-SA 4.0',license_url=credit['license_url'],
              adaptations='The photograph was cropped, reduced and paired with a newly generated model projection. The comparison board is shared under CC BY-SA 4.0.',
              original_sha256=photo_sig,model_sha256=modelsha,camera_sha256=hashlib.sha256(registered.read_bytes()).hexdigest(),
              method='Both sides use the same crop in the registered 5312 by 2988 image. Per-pixel perspective depth resolves model surfaces. Colour identifies material; photographed exposure is retained.',
              panels=panels,board_sha256=hashlib.sha256(final.read_bytes()).hexdigest())
    (destination/'registered-2017-window-pair.json').write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n')
    print(info['board_sha256'])

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('photograph',type=Path);p.add_argument('model',type=Path)
    p.add_argument('destination',type=Path);a=p.parse_args();make(a.photograph,a.model,a.destination)
