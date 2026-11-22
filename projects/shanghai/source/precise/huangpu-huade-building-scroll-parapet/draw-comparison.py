"""Show where the released parapet mesh falls on the original street photograph."""
import argparse
import json
from pathlib import Path
import runpy
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
from shapely.geometry import Polygon
from shapely.ops import unary_union

parser=argparse.ArgumentParser(description=__doc__)
for arg in ['project','source','photo','mesh','measurements','review','output']:
    parser.add_argument('--'+arg,type=Path,required=True)
args=parser.parse_args()
sys.path.insert(0,str(args.source))
from photo_plane import H,D
helper=runpy.run_path(args.project/'data/audit/postal-office-v1/independent-glb-review-helpers.py')
tri,idx,names,identity=helper['load_triangles'](args.mesh)
review=json.loads(args.review.read_bytes())
if identity['sha256']!=review['asset']:raise ValueError('Wrong geometry for this photographic review')
raw=Image.open(args.photo)
obs=json.loads(args.measurements.read_bytes())
a,b,c,d=obs['crop_upright_xyxy']
crop=raw.crop((b,raw.height-c,d,raw.height-a)).transpose(Image.Transpose.ROTATE_270).convert('RGB')
mat=np.asarray(names)[idx]
flat=mat=='Soffit roundel face'
z=tri[flat,:,2].min()
bottom=tri[flat & (np.max(abs(tri[:,:,2]-z),axis=1)<.0004)]
p=bottom.reshape(-1,3)
xyw=np.column_stack((p[:,0],p[:,2],np.ones(len(p))))@H.T+p[:,1,None]*D
points=(xyw[:,:2]/xyw[:,2,None]).reshape(-1,3,2)
discs=unary_union([Polygon(t) for t in points]).buffer(.02,join_style='mitre')
outlines=[list(d.exterior.coords) for d in discs.geoms if d.area>8]
if len(outlines)!=18:raise ValueError('Expected eighteen roundel faces')
sheet=Image.new('RGB',(1240,870),'#f7f5ed')
draw=ImageDraw.Draw(sheet)
def font(size,bold=False):
    name='Bold' if bold else 'Regular'
    return ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-'+name+'.ttc',size,index=2)
def text(pos,msg,size=17,bold=False):
    draw.text(pos,msg,font=font(size,bold),fill='#283638')
def inset(region,box,curves=(),marks=()):
    x,y,size_x,size_y=box
    thumb=ImageOps.contain(crop.crop(region),(size_x,size_y),Image.Resampling.LANCZOS)
    left=x+(size_x-thumb.width)//2;top=y+(size_y-thumb.height)//2
    sheet.paste(thumb,(left,top))
    sx=thumb.width/(region[2]-region[0]);sy=thumb.height/(region[3]-region[1])
    def xy(pt):return (left+(pt[0]-region[0]) * sx,top+(pt[1]-region[1])*sy)
    for coords in curves:
        transformed=[xy(p) for p in coords]
        draw.line(transformed,fill='#5be9de',width=2)
    for point in marks:
        px,py=xy(point);draw.ellipse((px-2.5,py-2.5,px+2.5,py+2.5),fill='#ffd359',outline='#342e21')
text((32,13),'华德大楼的露台石栏',38,True)
text((34,75),'上海 · 四川中路 620 号　｜　2015 年沿街实拍与模型轮廓',20)
draw.line((32,115,1208,115),fill='#a1ada7',width=1)
text((34,127),'两块卷草栏板及托板在同一张照片中的位置',18,True)
inset((0,0,1018,596),(32,164,642,370))
text((705,127),'四个半圆形开孔',18,True)
for i,(box,rect) in enumerate([((700,161,238,330),(463,251,531,340)),((958,161,238,330),(702,376,756,452))]):
    curves=[];marks=[]
    for g in [i,i+2]:
        rec=review['apertures'][g]
        curves.extend([[(r['x'],r['model_pair'][k])for r in rec if r['model_pair']]for k in [0,1]])
        marks.extend([(r['x'],r['photo_upper'])for r in rec[::3]])
    inset(rect,box,curves,marks)
text((707,489),'近侧栏板',16);text((965,489),'远侧栏板',16)
text((34,546),'近侧托板的九枚圆饰',18,True);text((642,546),'远侧托板的九枚圆饰',18,True)
for i,(box,region) in enumerate([((33,579,563,198),(192,293,418,397)),((642,579,563,198),(451,412,670,517))]):
    curves=[path for path in outlines if region[0]<np.mean(np.asarray(path)[:,0])<region[2]]
    inset(region,box,curves,[q['shadow_crown'] for q in obs['soffit_boss_crowns'][i]])
draw.line((34,795,1206,795),fill='#a1ada7',width=1)
text((35,801),'青线为三维模型投影，黄点取自原照。圆饰黄点标记侧缘暗带，青线标记圆盘底面外沿。',16)
text((35,834),'照片由 Antigng 摄于 2015 年 7 月 20 日，取自 Wikimedia Commons《华德大楼》，已裁切。图板采用 CC BY-SA 4.0。',15)
sheet.save(args.output,quality=90,optimize=True,subsampling=0)
