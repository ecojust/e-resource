"""Rectify the courtyard's large four-leaf window in the contractor's first 580 × 380 photograph."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates, gaussian_filter1d

HERE = Path(__file__).parent
SHA256 = '7ad4ed0d72a12e59155b97b88f7a71fe21dce7599e34c5cfa8ef49d899c9997c'
# Native image coordinates, clockwise from the upper left. The projected
# white sill is excluded from these four masonry/frame boundary observations.
CORNERS = [(412.9,107.0),(512.6,105.7),(523.5,177.4),(420.7,178.0)]

def homography(src, dst):
    design=[];observed=[]
    for (x,y),(u,v) in zip(src,dst):
        design.extend(([x,y,1,0,0,0,-u*x,-u*y],[0,0,0,x,y,1,-v*x,-v*y]))
        observed.extend((u,v))
    return np.r_[np.linalg.solve(design,observed),1].reshape(3,3)

def measure(photo):
    assert hashlib.sha256(photo.read_bytes()).hexdigest()==SHA256
    im=np.asarray(Image.open(photo).convert('RGB'),dtype=float)
    assert im.shape[:2]==(380,580)
    n=240;u,v=np.meshgrid(np.linspace(0,1,n),np.linspace(0,1,n))
    h=homography([(0,0),(1,0),(1,1),(0,1)],CORNERS)
    xy=h@np.vstack((u.ravel(),v.ravel(),np.ones(n*n)));xy=xy[:2]/xy[2]
    rect=np.stack([map_coordinates(im[...,i],xy[::-1],order=1,mode='nearest').reshape(n,n)for i in range(3)],axis=-1)
    light=rect@np.array([.2126,.7152,.0722])
    # Median curves average over the panes but omit the outer 9% where the
    # inlaid reveal and the projecting ledge have their own shadows.
    horiz=np.median(light[round(n*.12):round(n*.92),:],axis=0)
    vertical=np.median(light[:,round(n*.08):round(n*.93)],axis=1)
    def minima(curve,priors,half_width):
        filtered=gaussian_filter1d(curve,1.7);out=[]
        for prior in priors:
            lo,hi=round((prior-half_width)*(n-1)),round((prior+half_width)*(n-1))
            out.append(float(lo+np.argmin(filtered[lo:hi+1]))/(n-1))
        return out
    posts=minima(horiz,[.245,.495,.747],.045)
    rails=minima(vertical,[.253,.42,.590,.751],.061)
    inner_x=[.037,*posts,.963];inner_y=[.08,*rails,.965]
    readings=[]
    for i,(l,r) in enumerate(zip(inner_x,inner_x[1:])):
        for j,(t,b) in enumerate(zip(inner_y,inner_y[1:])):
            mask=(u>l+.25*(r-l))&(u<r-.25*(r-l))&(v>t+.28*(b-t))&(v<b-.28*(b-t))
            readings.append({'column':i+1,'row_from_top':j+1,'median_rgb_8bit':np.median(rect[mask],axis=0).round(1).tolist()})
    return {'photo':'Shanghai Weifang Architectural Decoration, 313 South Xiangyang Road, restoration gallery, first view',
            'url':'http://www.shwfjz.com/newwsm/editor/attached/image/20180109/20180109132994789478.JPG',
            'image_sha256':SHA256,'original_pixels':[580,380],'corner_pixels':CORNERS,
            'unit_to_photo_H':h.tolist(),'left_to_right_frame_centres':posts,'top_down_transverse_centres':rails,
            'sampling':'Rectified fractional coordinates, measured only on the recorded first photograph. Seven intermediate curves follow actual luminance minima. The glass samples summarize reflections and illumination at the time of photography. Timber or steel composition could not be established from the photograph.',
            'glass_readings':readings,
            'sill_end_pixels':[[412,179],[536,179],[535,184],[413,186]],
            'side_ties':'Two short dark fasteners are visible to each side near the head; position and their exact use remain approximate.',
            'sill_description':'Narrow light-painted projecting sill below all four leaves. The first photograph crops the top casement and part of the street-level opening.'}

if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('photo',type=Path);cli.add_argument('--output',type=Path,default=HERE/'large-window-readings.json')
    a=cli.parse_args();a.output.write_text(json.dumps(measure(a.photo),ensure_ascii=False,indent=2)+'\n')
