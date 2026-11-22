"""Extract the visible five metal Chinese characters on the entrance lintel from Livelikerw's photograph."""
import argparse,hashlib,json
from pathlib import Path
from shapely.geometry import box
from shapely.ops import unary_union
import numpy as np
from scipy.ndimage import binary_closing
from PIL import Image,ImageDraw

PHOTO_SHA='efc50b1013bf893fce9273984440ad952763564eb387088dc40c5835848f65f3'
# Loose original-pixel bounds surround each casting. Every cast stroke is
# dark against the limestone. Local exterior samples set the background.
CHARS=[('圓',(2876,2538,2924,2595)),('明',(2937,2538,2987,2598)),('園',(3000,2541,3048,2598)),
       ('公',(3058,2546,3110,2600)),('寓',(3121,2546,3172,2603))]
def read_letter(image,char,bounds):
    x,y,right,bottom=bounds
    patch=Image.fromarray(image[y:bottom,x:right]).convert('L')
    grey=np.asarray(patch)
    background=float(np.median(np.r_[grey[:3].ravel(),grey[:,-4:].ravel(),grey[:,0:3].ravel()]))
    scale=4
    enlarged=np.asarray(patch.resize((patch.width*scale,patch.height*scale),Image.Resampling.BICUBIC))
    thresholds={'圓':54,'明':59,'園':51,'公':62,'寓':47}
    radius={'圓':3,'明':4,'園':3,'公':3,'寓':3}[char]
    yy,xx=np.mgrid[-radius:radius+1,-radius:radius+1]
    pigment=binary_closing(enlarged < thresholds[char],structure=xx*xx+yy*yy<=radius**2)
    runs=[]
    for v,row in enumerate(pigment):
        breaks=np.flatnonzero(np.diff(np.r_[False,row,False].astype('int8')))
        for start,end in breaks.reshape(-1,2):
            runs.append(box(x+start/scale,y+v/scale,x+end/scale,y+(v+1)/scale))
    outline=unary_union(runs).simplify(.32,preserve_topology=True)
    components=[]
    for geom in getattr(outline,'geoms',[outline]):
        if geom.area<3.:continue
        components.append(dict(shell=list(geom.exterior.coords)[:-1],holes=[list(r.coords)[:-1]for r in geom.interiors if abs(r.length)>4]))
    return dict(character=char,bounds_source_px=list(bounds),local_stone_level=background,greyscale_threshold=thresholds[char],closing_radius_px=radius/scale,strokes=components)

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('photo',type=Path);ap.add_argument('output',type=Path);ap.add_argument('--overlay',type=Path)
    a=ap.parse_args()
    assert hashlib.sha256(a.photo.read_bytes()).hexdigest()==PHOTO_SHA
    image=np.asarray(Image.open(a.photo).convert('RGB'))
    assert image.shape[:2]==(3264,4912)
    letters=[read_letter(image,ch,rect)for ch,rect in CHARS]
    record=dict(photo='https://commons.wikimedia.org/wiki/File:Yuanmingyuan_Apartments_Rockbund_Shanghai.JPG',photographer='Livelikerw',date='2014-01-27',photo_sha256=PHOTO_SHA,license='CC BY-SA 3.0',source_size=[4912,3264],reading='圓明園公寓',letters=letters)
    a.output.write_text(json.dumps(record,ensure_ascii=False,indent=1)+'\n')
    if a.overlay:
        canvas=Image.fromarray(image)
        draw=ImageDraw.Draw(canvas)
        for letter in letters:
            for geom in letter['strokes']:
                for ring in [geom['shell'],*geom['holes']]:
                    pts=[tuple(p)for p in ring]
                    draw.line([*pts,pts[0]],fill=(255,230,20),width=1)
        canvas.crop((2868,2528,3180,2610)).resize((936,246)).save(a.overlay)
