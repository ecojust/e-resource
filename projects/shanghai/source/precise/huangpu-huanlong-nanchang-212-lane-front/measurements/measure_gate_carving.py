"""Measure the west pier's east face from the attributed, upright 2015 photograph."""
from pathlib import Path
import argparse
import hashlib
import json
import cv2
import numpy as np
from PIL import Image, ImageOps
from shapely.geometry import Polygon, MultiPolygon
from shapely import make_valid

def contours(binary, mask_points, min_area, tolerance, scale):
    mask=np.zeros(binary.shape,np.uint8)
    cv2.fillPoly(mask,[np.rint(np.array(mask_points)*scale/500.).astype('int32')],255)
    image=((binary.astype(np.uint8)*255)&mask)
    outlines,hierarchy=cv2.findContours(image,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_SIMPLE)
    result=[]
    if hierarchy is None:return result
    def coords(idx):
        c=cv2.approxPolyDP(outlines[idx],tolerance,True)[:,0]
        return [[round(-.4+px/scale,5),round(3.11-py/scale,5)]for px,py in c]
    for i,entry in enumerate(hierarchy[0]):
        if entry[3]>=0 or cv2.contourArea(outlines[i])<min_area:continue
        loop=coords(i)
        if len(loop)<3:continue
        holes=[];h=entry[2]
        while h>=0:
            p=coords(h)
            if len(p)>=3 and cv2.contourArea(outlines[h])>min_area*.30:holes.append(p)
            h=hierarchy[0,h,0]
        polygon=make_valid(Polygon(loop,holes))
        shapes=polygon.geoms if hasattr(polygon,'geoms') else [polygon]
        for poly in shapes:
            if poly.geom_type!='Polygon' or poly.area<min_area/scale**2:continue
            result.append(dict(outline=list(poly.exterior.coords)[:-1],holes=[list(l.coords)[:-1]for l in poly.interiors]))
    return result

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('photo',type=Path);ap.add_argument('calibration',type=Path);ap.add_argument('output',type=Path);args=ap.parse_args()
    cal=json.loads(args.calibration.read_bytes());src=np.array(ImageOps.exif_transpose(Image.open(args.photo)).convert('RGB'))
    digest=hashlib.sha256(args.photo.read_bytes()).hexdigest()
    if digest!=cal['original_sha256']:raise ValueError('Original photograph checksum differs.')
    balls=np.array(cal['gate_controls']['globes_metres']);origin=balls.mean(axis=0);origin[2]=0.
    u=np.r_[balls[1,:2]-balls[0,:2],0.];u/=np.linalg.norm(u);v=np.array([-u[1],u[0],0.]);scale=820.
    x,z=np.meshgrid(np.arange(713)/scale-.40,3.11-np.arange(1033)/scale)
    xyz=origin-1.62*u+x[:,:,None]*v+z[:,:,None]*[0.,0.,1.];P=np.array(cal['camera_matrices']['commons_2015']);q=xyz@P[:,:3].T+P[:,3];uv=q[:,:,:2]/q[:,:,2:]
    im=cv2.remap(src,uv[:,:,0].astype('float32'),uv[:,:,1].astype('float32'),cv2.INTER_LINEAR).astype(float);r,g,b=np.moveaxis(im,2,0)
    def field(points):
        return [[round(-.4+x/500,5),round(3.11-y/500,5)]for x,y in points]
    shield=contours((r<173)&(g<164),[(120,125),(187,124),(207,117),(236,118),(273,114),(321,119),(332,129),(341,203),(285,245),(246,251),(180,251),(157,229),(129,183)],180,.95,scale)
    crest_mask=[(120,125),(187,124),(207,117),(236,118),(273,114),(321,119),(332,129),(341,203),(285,245),(246,251),(180,251),(157,229),(129,183)]
    ridges=contours((r<174)&(g<163)&(r>113)&(g>109),crest_mask,28,.82,scale)
    crown=contours((r<171)&(g<159)&(r>144)&(g>135),crest_mask,25,.82,scale)
    green=[(79,295),(383,276),(390,370),(82,384)]
    letter=contours((r>107)&(g>122)&(b>95),[(101,298),(360,283),(372,366),(102,377)],11,.8,scale)
    civil=[(142,386),(329,375),(335,468),(143,482)]
    red=contours((r<163)&(g<124)&(b<128)&((r-g)>7),[(163,400),(308,390),(319,455),(166,462)],8,.8,scale)
    data=dict(source=cal['source_url'],source_sha256=digest,license='CC BY-SA 4.0',photographer='Antigng',basis='u between sphere centres, v into lane, z upwards; metres. East face of western shaft u=-1.620 m.',
              rectification={'scale_px_per_m':scale,'size':[713,1033],'v_min':-.40,'z_max':3.11,'approximate_front_and_rear_of_shaft_v_m':[-.295,.395]},
              plaque={'text':['212弄1-10号','南昌路'],'face_vz':field(green),'glyph_shapes':letter},
              civic_plaque={'text':'文明弄','face_vz':field(civil),'paint':red},
              capital={'observation':'Repeated foliate-and-scroll cast relief in the frieze below both globes; the strongly lit east face of the western pier supplies the measured silhouette. Depth and reverse faces are approximations.','silhouette_vz':shield,'raised_vz':ridges,'highest_vz':crown})
    args.output.write_text(json.dumps(data,ensure_ascii=False,indent=1)+'\n')
    print('capital / address / civil fragments',len(shield),len(letter),len(red))
if __name__=='__main__':main()
