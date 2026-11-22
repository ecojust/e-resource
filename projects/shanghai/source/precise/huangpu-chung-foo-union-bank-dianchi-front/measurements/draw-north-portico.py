"""Render three matching crops from Fayhoo's photograph and the exported bank GLB.

The fitted 3×4 camera projects the actual vertices into the source photograph.
A per-pixel reciprocal-depth test resolves the visible surface. The model uses
directional illumination and its own material colours.
"""
import argparse
import ctypes
import hashlib
import io
import json
from pathlib import Path
import runpy
import struct
import subprocess
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont

PHOTO_SHA = 'c488b0074286f2a53096c7a2ef64da30773bf27f5094539a6474d54ed4ace530'
SOURCE_PAGE = 'https://commons.wikimedia.org/wiki/File:Zhongfudalou.jpg'
LICENSE = 'https://creativecommons.org/licenses/by-sa/3.0/'
CROPS = [
    ('柱列与梁底', (112, 835, 1992, 1345), 175),
    ('右侧双柱中靠左一根的卷涡柱头', (1620, 1011, 1816, 1159), 305),
    ('门廊中央三枚浅罩与横向梁底线脚', (700, 1060, 1615, 1227), 138),
]
# The argument depth is reciprocal camera depth. It is linear in image space.
RASTER = r"""
#include <math.h>
#include <stdint.h>
void fill(int n,int w,int h,const double *p,const double *iz,
          const uint8_t *colors,double *buf,uint8_t *rgb) {
    for(int k=0;k<n;k++){
        const double *v=p+6*k;
        const double dx1=v[2]-v[0],dy1=v[3]-v[1],dx2=v[4]-v[0],dy2=v[5]-v[1];
        const double det=dx1*dy2-dy1*dx2;
        if(fabs(det)<1e-12)continue;
        const int x0=fmax(0,floor(fmin(v[0],fmin(v[2],v[4]))));
        const int y0=fmax(0,floor(fmin(v[1],fmin(v[3],v[5]))));
        const int x1=fmin(w-1,ceil(fmax(v[0],fmax(v[2],v[4]))));
        const int y1=fmin(h-1,ceil(fmax(v[1],fmax(v[3],v[5]))));
        for(int y=y0;y<=y1;y++){
            for(int x=x0;x<=x1;x++){
                const double dx=x+.5-v[0],dy=y+.5-v[1];
                const double u=(dx*dy2-dy*dx2)/det,t=(dx1*dy-dy1*dx)/det;
                if(u<0||t<0||u+t>1)continue;
                const int j=y*w+x;
                const double depth=(1-u-t)*iz[3*k]+u*iz[3*k+1]+t*iz[3*k+2];
                if(depth<=buf[j])continue;
                buf[j]=depth;
                for(int s=0;s<3;s++)rgb[3*j+s]=colors[3*k+s];
            }
        }
    }
}
"""
def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()

def project_geometry(mesh, project, camera):
    helper = project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
    faces, materials, _, info = runpy.run_path(str(helper))['load_triangles'](mesh)
    with mesh.open('rb') as stream:
        stream.seek(12)
        length, _ = struct.unpack('<II', stream.read(8))
        doc = json.loads(stream.read(length))
        stream.read(8)
        binary = stream.tell()
        swatches = []
        for material in doc['materials']:
            pbr = material['pbrMetallicRoughness']
            color = np.array(pbr.get('baseColorFactor',[1,1,1,1])[:3], dtype=float)
            if 'baseColorTexture' in pbr:
                image_id = doc['textures'][pbr['baseColorTexture']['index']]['source']
                view = doc['bufferViews'][doc['images'][image_id]['bufferView']]
                stream.seek(binary+view.get('byteOffset',0))
                tex = Image.open(io.BytesIO(stream.read(view['byteLength']))).convert('RGB')
                tex.thumbnail((96,96))
                s = np.asarray(tex,dtype=float)/255
                color *= np.where(s<=.04045,s/12.92,((s+.055)/1.055)**2.4).mean(axis=(0,1))
            swatches.append(color)
    eye = -np.linalg.solve(camera[:,:3], camera[:,3])
    normal = np.cross(faces[:,1]-faces[:,0],faces[:,2]-faces[:,0])
    normal /= np.maximum(np.linalg.norm(normal,axis=1,keepdims=True),1e-12)
    front = np.einsum('ij,ij->i', normal, eye-faces[:,0])>0
    double_sided = np.array([m.get('doubleSided',False) for m in doc['materials']])[materials]
    visible = front|double_sided
    q = faces[visible]@camera[:,:3].T + camera[:,3]
    # All of this exterior lies in front of the fitted north camera.
    if q[:,:,2].min()<=0:raise ValueError('Invalid fitted bank camera or input mesh')
    light=np.array([-.73,-.58,.45]);light/=np.linalg.norm(light)
    lighting=.39+.78*np.maximum(0,(normal[visible]@light)*np.where(front[visible],1,-1))
    colors=np.array(swatches)[materials[visible]]*lighting[:,None]
    colors=np.where(colors<=.0031308,12.92*colors,1.055*np.maximum(colors,0)**(1/2.4)-.055)
    return q[:,:,:2]/q[:,:,2,None],1/q[:,:,2],np.rint(colors.clip(0,1)*255).astype('uint8'),info

def model_crop(projected, box, size, raster):
    xy, inverse_z, colors, _=projected
    width,height=size
    scale=np.array(size)/(np.array(box[2:])-box[:2])
    points=(xy-box[:2])*scale
    intersects=np.all(points.max(axis=1)>=0,axis=1)&np.all(points.min(axis=1)<size,axis=1)
    # Two samples per axis soften diagonal stone mouldings at publication scale.
    factor=2
    rgb=np.full((height*factor,width*factor,3),(221,224,223),dtype='uint8')
    depth=np.full(rgb.shape[:2],-np.inf)
    args=[np.ascontiguousarray(points[intersects]*factor), np.ascontiguousarray(inverse_z[intersects]),
          np.ascontiguousarray(colors[intersects]),depth,rgb]
    raster(int(intersects.sum()),width*factor,height*factor,*[a.ctypes.data for a in args])
    return Image.fromarray(rgb).resize(size,Image.Resampling.LANCZOS)

def board(photo, model, camera_file, project, output):
    if digest(photo)!=PHOTO_SHA:raise ValueError('Unexpected source photograph')
    camera=np.array(json.loads(camera_file.read_bytes())['close']['camera_3x4'])
    projected=project_geometry(model,project,camera)
    result=Image.new('RGB',(1270,1160),'#f6f4ee')
    draw=ImageDraw.Draw(result)
    def label(x,y,string,size,bold=False,ink='#2c342f'):
        style='Bold' if bold else 'Regular'
        face=ImageFont.truetype(f'/usr/share/fonts/opentype/noto/NotoSansCJK-{style}.ttc',size,index=2)
        draw.text((x,y),string,font=face,fill=ink)
    label(36,14,'中孚银行北门廊',34,True)
    label(37,65,'上海 · 滇池路 103 号',19)
    draw.line((36,107,1234,107),fill='#a2aaa0')
    label(36,114,'实物照片',22,True);label(648,114,'同机位模型',22,True)
    original=Image.open(photo).convert('RGB')
    if original.size!=(2041,1363):raise ValueError('Unexpected photograph dimensions')
    with tempfile.TemporaryDirectory() as temporary:
        lib=Path(temporary)/'zbuf.so'
        subprocess.run(['cc','-O2','-shared','-fPIC','-x','c','-','-lm','-o',lib],input=RASTER.encode(),check=True)
        raster=ctypes.CDLL(str(lib)).fill
        raster.argtypes=[ctypes.c_int]*3+[ctypes.c_void_p]*5
        y=161
        frame_rows=[]
        for caption,box,max_height in CROPS:
            available=586
            scale=min(available/(box[2]-box[0]),max_height/(box[3]-box[1]))
            size=(round((box[2]-box[0])*scale),round((box[3]-box[1])*scale))
            label(36,y,caption,19,True)
            y+=37
            nat=original.crop(box).resize(size,Image.Resampling.LANCZOS)
            counterpart=model_crop(projected,box,size,raster)
            for x,im in [(36,nat),(648,counterpart)]:
                cell=x+(available-size[0])//2
                result.paste(im,(cell,y))
            frame_rows.append({'label':caption,'photo_pixel_bounds':list(box),'panel_pixels':list(size)})
            y+=size[1]+20
    draw.line((36,y+3,1234,y+3),fill='#a2aaa0')
    label(36,y+12,'摄影 Fayhoo，原图 Zhongfudalou.jpg，2015 年上传至 Wikimedia Commons。',15)
    label(36,y+36,'照片经裁切和缩放。模型按同一照片的标定相机投影，以侧光显示石饰和梁底起伏。图板许可 CC BY-SA 3.0。',15)
    result=result.crop((0,0,result.width,y+75))
    result.save(output,quality=94,subsampling=0,optimize=True)
    return {'photo_sha256':PHOTO_SHA,'photo':SOURCE_PAGE,'photo_original_name':'Zhongfudalou.jpg',
            'photographer':'Fayhoo','uploaded':'2015-01-19','photographed':None,'license':'CC BY-SA 3.0',
            'license_url':LICENSE,'changes':'Cropped and resized photograph; independently projected GLB using the same camera and crop.',
            'model_sha256':digest(model),'camera_sha256':digest(camera_file),'camera_role':'close','regions':frame_rows,
            'renderer':'Reciprocal-depth z buffer; directional light and linear material base colours, sampled mean for the procedural stone texture.',
            'comparison_jpeg_sha256':digest(output),'image_pixels':list(result.size)}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('photo','mesh','camera','project','output','record'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args()
    receipt=board(a.photo,a.mesh,a.camera,a.project,a.output)
    receipt['program_sha256']=digest(Path(__file__))
    a.record.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
