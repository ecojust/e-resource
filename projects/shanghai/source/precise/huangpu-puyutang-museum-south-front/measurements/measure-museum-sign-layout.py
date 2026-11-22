"""Measure each inscription's placement without reproducing the source calligraphic outlines."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter, label

BOARD = np.array([[273.,685.],[513.,695.],[514.,753.],[272.,747.]])
REGIONS = [(38,44,65,75),(67,36,98,80),(98,35,126,82),(127,41,160,82),
           (160,40,189,84),(188,45,216,83),(215,43,245,85)]

def homography():
    a,b=[],[]
    for (u,v),(x,y) in zip([(0.,0.),(1.,0.),(1.,1.),(0.,1.)],BOARD):
        a.extend(([u,v,1.,0.,0.,0.,-u*x,-v*x],[0.,0.,0.,u,v,1.,-u*y,-v*y]));b.extend((x,y))
    return np.r_[np.linalg.solve(a,b),1.].reshape(3,3)

def map_points(xy,h):
    q=np.column_stack((xy,np.ones(len(xy))))@h.T
    return q[:,:2]/q[:,2,None]

def measure(source, review=None):
    origin=np.array([248.,660.])
    with Image.open(source) as im:tile=im.crop((248,660,558,772)).convert('RGB')
    rgb=np.asarray(tile,float);h=homography();inv=np.linalg.inv(h)
    red,green,blue=rgb.transpose(2,0,1)
    # The patinated letters are less red than the brown plaque. Keep separate
    # components of a character (dots and stroke ends), including narrow strokes.
    chroma=gaussian_filter(.75*(red-blue)+.25*(red-green),.48)
    luma=rgb@np.array([.299,.587,.114]);rows=[];outline=tile.resize((620,224))
    pen=ImageDraw.Draw(outline)
    for char,(x0,y0,x1,y1) in zip('上海民政博物馆',REGIONS):
        roi=chroma[y0:y1,x0:x1];lum=luma[y0:y1,x0:x1]
        mask=(roi<4.2)&(lum>52.)
        labs,n=label(mask,np.ones((3,3)));valid=[i for i in range(1,n+1) if (labs==i).sum()>=3]
        local_y,local_x=np.where(np.isin(labs,valid));x=local_x+x0;y=local_y+y0
        if len(x)<10:raise ValueError('Insufficient visible metal on '+char)
        uv=map_points(np.column_stack((x,y))+origin,inv)
        # Include the antialiased transition from the visible patina to the
        # thin dark side of the raised letter (roughly one source pixel).
        u0,v0=uv.min(axis=0)-[1./240.,.85/60.]
        u1,v1=uv.max(axis=0)+[1./240.,.85/60.]
        box_uv=np.array([[u0,v0],[u1,v0],[u1,v1],[u0,v1]])
        corners=map_points(box_uv,h)
        metal=np.median(rgb[y,x],axis=0)
        record=dict(character=char,board_uv_bounds=np.round([u0,v0,u1,v1],5).tolist(),
                    source_quad_px=np.round(corners,2).tolist(),
                    lower_alignment_px=np.round(corners[[3,2]],2).tolist(),
                    measured_metal_pixels=len(x),median_lit_srgb=np.rint(metal).astype(int).tolist())
        rows.append(record);ss=[tuple(2*(p-origin)) for p in corners]
        pen.line([*ss,ss[0]],fill='#a7f4c9',width=1)
    small=np.array([[494.3,706.9],[504.6,707.7],[504.4,743.2],[494.1,743.0]])
    ss=[tuple(2*(p-origin)) for p in small];pen.line([*ss,ss[0]],fill='#f4cd6a',width=1)
    if review:outline.save(review,quality=96)
    mat=rgb[32:37,38:222].reshape(-1,3)
    return {'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'photo_record':'立面20140816，上海普育堂旧址南门近照。',
            'source_photo_size_px':[800,1200],'board_corners_px':BOARD.tolist(),'main_inscription':'上海民政博物馆',
            'glyph_style':'The seven editable substitute letterforms are scaled and placed within measured source extents. The lower alignment follows the photographed board plane; it does not infer a uniform typographic baseline.',
            'characters':rows,'plaque_lit_median_srgb':np.rint(np.median(mat,axis=0)).astype(int).tolist(),
            'small_vertical_inscription':{'source_quad_px':small.tolist(),'board_uv_quad':np.round(map_points(small,inv),5).tolist(),'reading':'竖题可见，原照分辨率不足以可靠辨读。','shape':'Narrow vertical marks at the right margin.'}}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--photo',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--review',type=Path)
    a=p.parse_args();r=measure(a.photo,a.review);a.output.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print([(s['character'],s['source_quad_px'][0],s['source_quad_px'][2])for s in r['characters']])
