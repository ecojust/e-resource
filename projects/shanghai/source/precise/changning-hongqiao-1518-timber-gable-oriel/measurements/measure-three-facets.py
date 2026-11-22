"""Orient the three oriel facets, cap and apron joints against the original garden photograph."""
import os
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image
w=Path(__file__).resolve().parents[1];cam=json.loads((w/'measurements/garden-camera.json').read_bytes());Q=np.array(cam['pinhole_3x4']);im=Image.open(Path(os.environ.get('HONGQIAO_GARDEN_PHOTO',w/'garden-original.jpg')));scale=im.width/800
# A bright sill stripe separates dark glazing from the roughcast base. Each pane is identified separately.
region=np.round(np.array([518,226,608,302])*scale).astype(int);rgb=np.array(im.crop(tuple(region))).astype(float);lum=np.mean(rgb,axis=2)
windows=[]
for j,(x0,x1) in enumerate([(523.,536.4),(547.,575.7),(589.0,599.8)]):
    centers=[];rows=[]
    for row in range(lum.shape[0]):
        y=(region[1]+row+.5)/scale
        if not 243.5<y<286.0:continue
        xx=(np.arange(lum.shape[1])+region[0]+.5)/scale;sel=(xx>=x0)&(xx<=x1)&(lum[row]<102)
        pts=xx[sel]
        if len(pts)>5:rows.append((y,pts.min(),pts.max()))
    rows=np.asarray(rows)
    lo,hi=np.percentile(rows[:,1],20),np.percentile(rows[:,2],80)
    x=(np.arange(lum.shape[1])+region[0]+.5)/scale;low=[];high=[]
    for k in np.flatnonzero((x>lo+1.)&(x<hi-1.)):
        # Only the near-contiguous aperture above the white sill is eligible.
        arr=lum[:,k];indices=np.flatnonzero(arr<107)
        runs=np.split(indices,np.flatnonzero(np.diff(indices)>5)+1);runs=[r for r in runs if len(r) and r[-1]-r[0]>22*scale]
        if not runs:continue
        run=max(runs,key=lambda r:r[-1]-r[0]);low.append((run[0]+region[1]+.5)/scale);high.append((run[-1]+region[1]+.5)/scale)
    if not low:
        # The acute left pane is only a few pixels wide in the working image and leans across its height.
        yy=(np.arange(lum.shape[0])+region[1]+.5)/scale
        slope,offset=np.polyfit(rows[:,0],(rows[:,1]+rows[:,2])/2,1)
        loc=np.clip(np.rint((slope*yy+offset)*scale-region[0]-.5).astype(int),1,lum.shape[1]-2)
        observed=np.min(lum[np.arange(len(yy))[:,None],loc[:,None]+np.array([-1,0,1])],axis=1)
        interior=np.flatnonzero(observed<119);runs=np.split(interior,np.flatnonzero(np.diff(interior)>9)+1)
        key=max((r for r in runs if len(r)),key=len);assert len(key)>46
        low.append(yy[key[0]]);high.append(yy[key[-1]])
    assert low and high
    windows.append(dict(semantic=['left oblique light','central wide light','right oblique light'][j],approx_image_xyxy=[float(lo),float(np.median(low)),float(hi),float(np.median(high))],visible_row_count=len(rows)))
# x,z measurements use known parallel world planes; y is estimated because only one garden photograph survives.
# Two central arrises define the leading flat face. Short returns on both sides meet the garden wall.
outline_pixels=[[516,293.0],[521.0,293.5],[543.5,294.8],[579.7,295.0],[606.2,295.1],[610.2,294.8]]
setbacks=[0,-.20,-.70,-.70,-.20,0]
def onplane(pixel,y):
 H=Q[:,[0,2,3]].copy();H[:,2]+=Q[:,1]*y;v=np.linalg.solve(H,[*pixel,1]);return [v[0]/v[2],y,v[1]/v[2]]
points=[onplane(px,y)for px,y in zip(outline_pixels,setbacks)];sill=float(np.median([p[2]for p in points]));world=[[p[0],p[1]]for p in points]
d={'source_sha256':cam['garden_photo_sha256'],'source_size':list(im.size),'glass_samples':windows,'sill_working_xy':outline_pixels,'faceted_bay_xy':world,'adopted_outer_depth_m':.70,'sill_elevation_m':sill,'sill_spread_m':float(np.ptp(np.asarray(points)[:,2])),'description':'凸窗向花园突出，中央为较宽的正面窗，两侧各有一扇窄面。以窗间折线和毛面抹灰边界分面。投影深度仅有单个花园视角，以0.70米估定。'}
(w/'measurements/oriel-facets.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');print(windows,world,sill)
