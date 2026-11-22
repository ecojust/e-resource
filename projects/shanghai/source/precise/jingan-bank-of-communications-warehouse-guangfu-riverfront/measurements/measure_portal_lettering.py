"""Regenerate traced front-face polygons using the two original exposures and the published image registration.

Requires numpy, Pillow, OpenCV and Shapely. Both inputs are the photographic sources of plates 16 and 17
in portal-source-review.json. No image is copied to the public output.
"""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
import cv2
from PIL import Image
from shapely.geometry import Polygon
from shapely import make_valid

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('front',type=Path)
parser.add_argument('oblique',type=Path)
parser.add_argument('output',type=Path)
args=parser.parse_args()
here=Path(__file__).resolve().parent
j=json.loads((here/'portal-photo-registration.json').read_bytes())
for source,key in [(args.front,'reference_SHA'),(args.oblique,'oblique_SHA')]:
    if hashlib.sha256(source.read_bytes()).hexdigest()!=j[key]:
        raise ValueError(f'Incorrect source exposure: {source.name}')
a=np.asarray(Image.open(args.front).convert('RGB'))
b=np.asarray(Image.open(args.oblique).convert('RGB'))
p=np.array(j['matched_reference_and_oblique']);p=np.unique(np.round(p,1),axis=0)
rectified = {}
reference = {}
for label,box,take in [('four',(473,587,611,617),(p[:,1]>581)&(p[:,1]<635)),('brand',(494,181,588,255),(p[:,0]>504)&(p[:,0]<579)&(p[:,1]>176)&(p[:,1]<257))]:
 # RANSAC on the same architectural face, excluding vegetation and the decorative lower plaque.
 if take.sum()<4:raise ValueError(label)
 ha,good=cv2.findHomography(p[take,:2],p[take,2:],cv2.RANSAC,3)
 s=4;u0,v0,u1,v1=box;xx,yy=np.meshgrid(u0+(np.arange((u1-u0)*s)+.5)/s,v0+(np.arange((v1-v0)*s)+.5)/s)
 pts=np.stack([xx,yy,np.ones_like(xx)],axis=-1)@ha.T
 coords=(pts[:,:,:2]/pts[:,:,2:]).astype('f')
 rect=cv2.remap(b,coords,None,cv2.INTER_CUBIC)
 ref=cv2.remap(a,np.stack((xx,yy),axis=-1).astype('f'),None,cv2.INTER_CUBIC)

 rectified[label]={'front':ref,'oblique':rect}
 reference[label]={'box':box,'scale':s,'H16to17':ha.tolist()}

def outlines(mask,box,scale):
    cs,tree=cv2.findContours((mask*255).astype('uint8'),cv2.RETR_CCOMP,cv2.CHAIN_APPROX_SIMPLE)
    if tree is None:return []
    def contour(c):
        pts=cv2.approxPolyDP(c,.68,True).reshape(-1,2)
        return pts/scale+np.array(box[:2])
    out=[]
    for i,c in enumerate(cs):
        if tree[0,i,3]>=0 or cv2.contourArea(c)<3.0:continue
        a=contour(c);hole=tree[0,i,2];holes=[]
        while hole>=0:
            b=contour(cs[hole])
            if len(b)>=3 and cv2.contourArea(cs[hole])>=2:holes.append(b)
            hole=tree[0,hole,0]
        if len(a)<3:continue
        obj=make_valid(Polygon(a,holes))
        for q in ([obj] if obj.geom_type=='Polygon' else getattr(obj,'geoms',[])):
            if q.geom_type!='Polygon' or q.area<.15:continue
            q=q.simplify(.095,preserve_topology=True)
            if q.is_valid:out.append({'outer':np.round(np.asarray(q.exterior.coords)[:-1],3).tolist(),'holes':[np.round(np.asarray(h.coords)[:-1],3).tolist() for h in q.interiors]})
    return out
rows=[('four','光',(479.0,593.0,500.0,611.2)),('four','二',(513.0,594.3,535.0,608.8)),('four','倉',(548.6,593.5,571.0,611.3)),('four','庫',(583.4,593.1,605.6,611.2)),
      ('brand','百',(503.0,190.0,526.7,211.5)),('brand','空',(529.2,190.1,552.8,211.6)),('brand','间',(556.2,190.6,579.8,212.0)),
      ('brand','BAIspace',(503.0,213.2,580.6,231.7))]
result=[];s=4
for label,letter,box in rows:
    pos=reference[label]['box'];field='oblique' if label=='four' else 'front';im=np.asarray(rectified[label][field],dtype=float)
    a,b,c,d=[int(round((v-pos[j%2])*s))for j,v in enumerate(box)]; crop=im[b:d,a:c];lum=crop@np.array([.299,.587,.114]);R,G,B=crop.transpose(2,0,1)
    if label=='brand':
        fg=(R>(140 if letter=='BAIspace' else 157))&(R-B>(10 if letter=='BAIspace' else 18))&(G-B>(5 if letter=='BAIspace' else 9))
    else:
        # Registered illumination: use lower chroma grey bronze strokes against the pale buff field.
        # Both photographs independently support the limits; fine grey openings come from the oblique capture.
        cutoff={'光':168,'二':168,'倉':144,'庫':141}[letter];fg=lum<cutoff
    fg=cv2.morphologyEx(fg.astype('uint8'),cv2.MORPH_CLOSE,np.ones((2,2),'uint8')).astype(bool)
    normalized_box=(pos[0]+a/s,pos[1]+b/s,pos[0]+c/s,pos[1]+d/s)
    out=outlines(fg,normalized_box,s);result.append(dict(text=letter,source_view=field,box=normalized_box,polygons=out))
args.output.write_text(json.dumps(dict(image_space='studio 16 full frame, 1080 x 810',inscriptions=result),ensure_ascii=False,separators=(',',':'))+'\n')
