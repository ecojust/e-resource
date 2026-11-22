"""Project the physical window triangles through each registered camera for the comparison plate."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageOps
M=Path(__file__).resolve().parent
sys.path.insert(0,str(M.parent/"source"))
from check_upper_windows import load_triangles
from fuzhou_photo_plane import CAMERAS
from upper_bookshop_windows import openings

def font(size,bold=False):
    family="NotoSansCJK-Bold.ttc" if bold else "NotoSansCJK-Regular.ttc"
    return ImageFont.truetype("/usr/share/fonts/opentype/noto/"+family,size,index=2)

def paint(mesh,camera,image):
    tris,mats,doc,_=mesh
    p=tris@camera[:,:3].T+camera[:,3]
    uv=p[:,:,:2]/p[:,:,2,None]
    eye=-np.linalg.solve(camera[:,:3],camera[:,3])
    order=np.argsort(np.linalg.norm(tris.mean(1)-eye,axis=1))[::-1]
    n=np.cross(tris[:,1]-tris[:,0],tris[:,2]-tris[:,0])
    n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-12)
    illumination=.74+.48*np.maximum(0,n@np.array([-.26,-.65,.71]))
    factors=np.array([k["pbrMetallicRoughness"]["baseColorFactor"][:3] for k in doc["materials"]])[mats]*illumination[:,None]
    rgb=(np.where(factors<=.0031308,12.92*factors,1.055*factors**(1/2.4)-.055)*255).clip(0,255).astype('u1')
    d=ImageDraw.Draw(image)
    for i in order:
        if min(p[i,:,2])<=0:continue
        d.polygon([tuple(x) for x in uv[i]],fill=tuple(rgb[i]))
    return image

def plate(model,photo,output):
    mesh=load_triangles(model); w,h=1360,1060
    page=Image.new("RGB",(w,h),"#f4f1e9");d=ImageDraw.Draw(page)
    d.text((33,18),"世界书局 · 福州路390号",fill="#172b2c",font=font(40,True))
    d.text((35,81),"上层临街窗扇　五个开间 · 90个窗洞 · 150扇下部玻璃",fill="#344647",font=font(22))
    pic=Image.open(photo).convert("RGB");cam=CAMERAS['2015_street']
    grey=Image.blend(Image.new("RGB",pic.size,"#eeeae2"),ImageOps.grayscale(pic).convert("RGB"),.24)
    comp=paint(mesh,cam,grey)
    crop=(316,141,1209,1067)
    for i,(media,title) in enumerate([(pic,"福州路街面 | 2015年4月4日"),(comp,"同一机位 | 实际近景网格叠合")]):
        item=media.crop(crop).resize((633,651),Image.Resampling.LANCZOS)
        x=35+i*659;page.paste(item,(x,158));d.text((x,117),title,fill="#263235",font=font(24))
    poses=json.loads((M/"bookshop-sash-fit.json").read_bytes())["cameras"]
    for i,(key,box,caption) in enumerate([("4",(223,318,360,520),"东端双扇开启"),("6",(309,0,448,57),"西端上排右扇")]):
        mat=np.array(poses[key]["camera_matrix"])
        x,y=35+i*390,837
        # Enlarge the projection itself to preserve the small ring around the pane.
        scale=min(155/(box[2]-box[0]),128/(box[3]-box[1]))
        T=np.array([[scale,0,-box[0]*scale+6],[0,scale,-box[1]*scale+6],[0,0,1.]])
        inset=paint(mesh,T@mat,Image.new("RGB",(166,140),"#d1ccc2"))
        page.paste(inset,(x,y));d.text((x+174,y+30),caption,fill="#243738",font=font(19))
        d.text((x+174,y+65),"2016年近照机位",fill="#4e5857",font=font(15))
    d.text((834,858),"每孔上亮子横贯全宽。",fill="#273938",font=font(23))
    d.text((834,900),"外开角依2016年近照估算。",fill="#273938",font=font(20))
    d.line((36,992,1324,992),fill="#a8ad9f",width=1)
    d.text((36,1003),"摄影 Fayhoo，2015，Waiwen Shudian.JPG（裁切）及本对照图采用 CC BY-SA 3.0。",fill="#364442",font=font(18))
    page.save(output,quality=90,optimize=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('model',type=Path);p.add_argument('source_photo',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();plate(a.model,a.source_photo,a.output)
