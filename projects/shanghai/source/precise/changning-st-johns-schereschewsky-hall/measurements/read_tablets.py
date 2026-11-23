"""Digitize three observed character outlines on each tower tablet, in normalized tablet coordinates."""
from pathlib import Path
import argparse
import json
import numpy as np
from PIL import Image
from shapely.geometry import box
from shapely.ops import unary_union
SAMPLES={'lower':{'source_rect':[485,433,643,465],'letters':[[510,442,527,458],[551,442,566,458],[592,442,610,458]]},
         'upper':{'source_rect':[506,139,604,158],'letters':[[525,143,537,155],[550,143,562,155],[576,143,589,155]]}}
def polygons(a,rect,tablet):
 x0,y0,x1,y1=rect;x,y,r,b=tablet;clip=a[y0:y1,x0:x1]
 dark=clip<np.clip(np.quantile(clip,.78)-44,104,169)
 rows=[]
 silhouette=unary_union([box(int(i),int(j),int(i)+1,int(j)+1)for j,i in zip(*np.nonzero(dark))]).buffer(.10,join_style=2).buffer(-.075,join_style=2)
 for q in getattr(silhouette,'geoms',[silhouette]):
    if q.area<1.5:continue
    rings=[q.exterior,*q.interiors]
    rows.append([[[round((xx+x0-x)/(r-x)-.5,6),round(.5-(yy+y0-y)/(b-y),6)]for xx,yy in ring.coords]for ring in rings])
 return rows
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('image',type=Path);p.add_argument('out',type=Path);a=p.parse_args()
 arr=np.asarray(Image.open(a.image).convert('L'));assert arr.shape==(810,1080)
 out={}
 for label,ob in SAMPLES.items():
    q={**ob,'polygons':[poly for rec in ob['letters']for poly in polygons(arr,rec,ob['source_rect'])]}
    out[label]=q
 a.out.write_text(json.dumps(out,ensure_ascii=False,separators=(',',':'))+'\n')
