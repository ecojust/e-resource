"""Select bronze, shadowed counters, steel, glass and stone from the photograph independently of mesh contours."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt,gaussian_filter

W=Path(__file__).resolve().parents[1]
source_hash='e3c32ee79cb3203236105cf72483c2e9df6d0013f52eba0b35a4ecedb52d9faf'
crop=np.asarray(Image.open(W/'sign/source-crop.png').convert('RGB'),dtype=float)
scale=np.array(crop.shape[:2][::-1])/[850.,214.]
origin=np.floor(np.array([206,208])*7296/690)
trace_boxes=[(91,28,216,199),(260,40,390,175),(451,39,591,181),(613,32,751,182)]
holes=[[(56,86),(98,70)],[(65,99),(99,93)],[(75,72),(64,92),(84,94),(66,115),(82,126)],[(116,44),(113,71),(91,119),(105,133),(116,141)]]
points=[]
def add(category,kind,uv,number=None):
    row=dict(category=category,kind=kind,pixel=np.asarray(uv).round(3).tolist())
    if number is not None:row['group']=number
    points.append(row)
for n,(box,spots)in enumerate(zip(trace_boxes,holes),1):
    x0,y0,x1,y1=np.rint(np.array(box)*np.tile(scale,2)).astype(int)
    image=crop[y0:y1,x0:x1];red,green,blue=image.transpose(2,0,1)
    # Broad, bright bronze cores are readily distinguishable from grey stone.
    # The nine points per character cover separate patches across its strokes.
    mask=(red-blue>np.percentile(red-blue,83))&(red>np.percentile(red,28))
    distance=distance_transform_edt(mask);yy,xx=np.indices(red.shape)
    for _ in range(9):
        y,x=np.unravel_index(np.argmax(distance),distance.shape)
        add('sign','bronze',origin+[x0+x,y0+y],n)
        distance[(yy-y)**2+(xx-x)**2<14**2]=0
    for cx,cy in spots:
        px,py=np.rint([cx/160*(x1-x0),cy/190*(y1-y0)]).astype(int);extent=7
        window=gaussian_filter(red,.9)[py-extent:py+extent+1,px-extent:px+extent+1]
        dy,dx=np.unravel_index(np.argmin(window),window.shape)
        source_point=origin+[x0+px+dx-extent,y0+py+dy-extent]
        if n==4 and cx==116 and cy==44:
            # The original automatic seed sits on the blurred light-to-shadow
            # transition at the tip. The dark recess itself is below and left.
            source_point=np.array([3411.,2326.])
        add('sign','counter',source_point,n)

fan_origin=np.floor(np.array([192,113])*7296/690)
fan_end=np.floor(np.array([366,199])*7296/690)
fan_scale=(fan_end-fan_origin)/[809,400]
def fan(xy):return (np.array(xy)+.5)*fan_scale-.5+fan_origin
for n,xy in enumerate([(124,260),(284,95),(519,92),(685,245),(221,302),(323,226),(469,212),(578,298)],1):add('fan','glass',fan(xy),n)
thumb=np.asarray(Image.open(W/'research/fan-check.jpg').convert('L'),float)
for n,(x,y)in enumerate([(225,74),(409,29),(755,319),(325,150),(536,174),(153,347),(229,196),(293,264),(402,191),(407,104),(501,267),(599,172),(555,362)],1):
    a=thumb[y-7:y+8,x-7:x+8];yy,xx=np.unravel_index(np.argmin(gaussian_filter(a,1.3)),a.shape)
    add('fan','metal',fan([x+xx-7,y+yy-7]),n)
f=np.load(W/'sign/rectified-fluting-survey.npz');q,norm,v=[f[k]for k in ('q','norm','v')]
for n,s in enumerate(range(56,len(q)-55,97),1):
    luminance=gaussian_filter(v[:,100],1.)
    d=s-8+np.argmin(luminance[s-8:s+9]);a=d-7+np.argmax(luminance[d-7:d+8])
    add('archivolt','trough',q[d]+100*norm[d],n)
    add('archivolt','ridge',q[a]+100*norm[a],n)
(W/'measurements/independent-source-points.json').write_text(json.dumps({'photograph_sha256':source_hash,'points':points},ensure_ascii=False,indent=2)+'\n')
print(len(points))
