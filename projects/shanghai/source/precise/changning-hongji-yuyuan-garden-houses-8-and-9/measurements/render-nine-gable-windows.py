"""Two independently registered sight lines onto the present-day model of house 9."""
import argparse
import json
from pathlib import Path
import struct
import sys

import numpy as np
from PIL import Image,ImageDraw,ImageFont

here=Path(__file__).resolve().parent
reader=here.parents[3]/"source/precise/xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact"
sys.path.insert(0,str(reader))
from glb_triangles import load_triangles


def render(path, survey, name, transform):
    photo=survey["images"][name]
    box_size=(545,508)
    tri,material,names,_=load_triangles(path)
    with path.open("rb") as f:
        f.seek(12)
        size,_=struct.unpack("<II",f.read(8))
        doc=json.loads(f.read(size))
    rgb=np.array([m.get("pbrMetallicRoughness",{}).get("baseColorFactor",[.4,.4,.4,1])[:3] for m in doc['materials']])
    rgb=np.where(rgb<=.0031308,rgb*12.92,1.055*np.power(rgb,1/2.4)-.055)
    P=np.array(photo["P"]) @ np.linalg.inv(transform)
    points=tri@P[:,:3].T+P[:,3]
    z=points[:,:,2]
    xy=points[:,:,:2]/z[:,:,None]
    witness=np.array([[.30,-.2,5.18],[6.76,-.2,5.18],[.30,-.2,.03],[6.76,-.2,.03]])
    q=witness@np.array(photo["P"])[:,:3].T+np.array(photo["P"])[:,3]
    q=q[:,:2]/q[:,2,None]
    mid=(q.min(0)+q.max(0))*.5
    scale=min((box_size[0]-32)/(q[:,0].max()-q[:,0].min()),(box_size[1]-24)/(q[:,1].max()-q[:,1].min()))
    xy=(xy-mid)*scale+np.array(box_size)/2
    normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);size=np.linalg.norm(normal,axis=1)
    shade=.78+.22*np.maximum(0,(normal@np.array([-.28,-.75,.60]))/np.maximum(size,1e-9))
    colors=(np.clip(rgb[material]*shade[:,None],0,1)*255).astype(np.uint8)
    w,h=box_size;depth=np.zeros((h,w),np.float32)
    pix=np.full((h,w,3),[237,234,224],dtype=np.uint8)
    active=(z.min(1)>.05)&(xy[:,:,0].max(1)>=0)&(xy[:,:,0].min(1)<w)&(xy[:,:,1].max(1)>=0)&(xy[:,:,1].min(1)<h)
    for index in np.flatnonzero(active):
        qq=xy[index];x0,y0=np.maximum(np.floor(qq.min(0)),0).astype(int)
        x1,y1=np.minimum(np.ceil(qq.max(0)),[w-1,h-1]).astype(int)
        (ax,ay),(bx,by),(cx,cy)=qq
        den=(by-cy)*(ax-cx)+(cx-bx)*(ay-cy)
        if abs(den)<1e-7:continue
        xs=np.arange(x0,x1+1)[None,:]+.5;ys=np.arange(y0,y1+1)[:,None]+.5
        a=((by-cy)*(xs-cx)+(cx-bx)*(ys-cy))/den;b=((cy-ay)*(xs-cx)+(ax-cx)*(ys-cy))/den;c=1-a-b
        distance=a/z[index,0]+b/z[index,1]+c/z[index,2]
        patch=depth[y0:y1+1,x0:x1+1];mask=(a>=0)&(b>=0)&(c>=0)&(distance>patch)
        patch[mask]=distance[mask];pix[y0:y1+1,x0:x1+1][mask]=colors[index]
    return Image.fromarray(pix)

def font(size):
    return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",size)

def main():
    a=argparse.ArgumentParser();a.add_argument("glb",type=Path);a.add_argument("output",type=Path)
    a.add_argument("--transform",type=Path);args=a.parse_args()
    t=np.array(json.loads(args.transform.read_bytes()) if args.transform else np.eye(4))
    sv=json.loads((here/"nine-gable-window-survey.json").read_bytes())
    page=Image.new("RGB",(1125,612),(252,250,245));d=ImageDraw.Draw(page)
    d.text((15,11),"House 9, Hongji garden houses | Six east-facing sash windows",font=font(22),fill="#302e29")
    for i,(key,title) in enumerate([("commons-00","1 August 2015 camera"),("winter2023-18","September 2023 camera")]):
        x=15+i*555;d.text((x,48),title,font=font(16),fill="#393b37")
        page.paste(render(args.glb,sv,key,t),(x,74))
    d.text((15,585),"Both views show the 2023 repair. The full dark strips visible in the 2015 photograph are recorded in the survey.",font=font(14),fill="#444840")
    page.save(args.output,"JPEG",quality=89,optimize=True)

if __name__=="__main__":main()
