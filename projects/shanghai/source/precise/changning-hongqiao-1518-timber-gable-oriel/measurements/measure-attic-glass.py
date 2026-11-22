"""Trace the four blue-grey glazed lights, separating them from brown wood and the small foreground roof."""
import os
from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image
from scipy.ndimage import label
root=Path(__file__).resolve().parents[1];source=Path(os.environ.get('HONGQIAO_GARDEN_PHOTO',root/'garden-original.jpg'));im=Image.open(source);scale=im.width/800
region=np.rint(np.array([533,118,600,178])*scale).astype(int);arr=np.asarray(im.crop(tuple(region))).astype(float);R,G,B=arr.transpose(2,0,1)
blue=(B-R>10)&(G-R>4)&(R>26)&(R<124)&(B<172)
# The camera view shows four separate unbroken panes and a pitched oriel roof partly overlapping the lowest edge.
components,n=label(blue);rows=[];edges=[]
for k in range(1,n+1):
 yy,xx=np.where(components==k)
 if len(xx)<3500:continue
 xy=np.column_stack([(xx+region[0]+.5)/scale,(yy+region[1]+.5)/scale]);x,y=xy.T
 if np.ptp(x)<5 or np.ptp(y)<30:continue
 rows.append((np.median(x),xy))
rows.sort(key=lambda d:d[0]);assert len(rows)==4

def line(x,y):
    fit=np.polyfit(x,y,1)
    for _ in range(3):
        residual=y-np.polyval(fit,x);med=np.median(residual);mad=np.median(np.abs(residual-med));keep=abs(residual-med)<max(.24,mad*3.3)
        fit=np.polyfit(x[keep],y[keep],1)
    return fit
for i,(mid,xy)in enumerate(rows):
 x,y=xy.T;ye=np.unique(y);ye=ye[(ye>136)&(ye<167)];xmin=np.array([min(x[y==v])for v in ye]);xmax=np.array([max(x[y==v])for v in ye]);xl=line(ye,xmin);xr=line(ye,xmax)
 # Upper and lower glass edges are measured on interior columns, away from the wood stiles.
 xe=np.unique(x);xe=xe[(xe>np.quantile(x,.20))&(xe<np.quantile(x,.80))];ymin=np.array([min(y[x==v])for v in xe]);ymax=np.array([max(y[x==v])for v in xe]);yt=line(xe,ymin);yb=line(xe,ymax)
 def cross(xline,yline):
    a,b=xline;c,d=yline;cx=(a*d+b)/(1-a*c);return [cx,c*cx+d]
 corners=[cross(xl,yt),cross(xr,yt),cross(xr,yb),cross(xl,yb)];edges.append(dict(pane=i+1,blue_pixels=len(xy),working_corners=corners,left_x_as_y=xl.tolist(),right_x_as_y=xr.tolist(),top_y_as_x=yt.tolist(),bottom_y_as_x=yb.tolist(),sampled_center=float(mid)))
result=dict(sha256=hashlib.sha256(source.read_bytes()).hexdigest(),source_size=list(im.size),working_size=[800,600],region_native=region.tolist(),segmentation='largest contiguous blue-grey components, fitted only at interior columns and middle rows',source_reference='Fayhoo，虹桥路白崇禧旧居，2018-07-14，CC BY-SA 3.0',panes=edges)
f=root/'measurements/attic-glass.json';f.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print([(r['pane'],r['blue_pixels'],np.asarray(r['working_corners']).round(2).tolist())for r in edges])
