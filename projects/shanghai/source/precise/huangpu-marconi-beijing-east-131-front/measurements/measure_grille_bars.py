"""Measure the painted uprights and their short fret returns in the 2017 street photograph."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import cv2
import numpy as np
from PIL import Image,ImageOps
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks,peak_widths

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'source'))
from marconi_photo_plane import CALIBRATION

def measure(photo):
    ref=json.loads((HERE/'portal-photo-traces.json').read_text())['primary']
    assert hashlib.sha256(photo.read_bytes()).hexdigest()==ref['sha256']
    im=np.asarray(ImageOps.exif_transpose(Image.open(photo)).convert('RGB'))
    width=612;scale=245.
    cols,rows=np.meshgrid(np.arange(width),np.arange(1164))
    x=cols/scale-1.26;z=4.79-rows/scale
    q=np.stack((x,np.full_like(x,.79),z,np.ones_like(x)),axis=-1)@np.array(CALIBRATION['camera_matrices']['2017_front']).T
    image=cv2.remap(im,(q[:,:,0]/q[:,:,2]).astype('float32'),(q[:,:,1]/q[:,:,2]).astype('float32'),cv2.INTER_LINEAR)
    y=lambda z:round((4.79-z)*scale)
    lum=image@np.array([.2,.64,.16])
    profile=gaussian_filter1d(np.median(lum[y(1.38):y(.88)],axis=0),1.)
    peaks,props=find_peaks(profile,prominence=8,distance=5)
    good=(peaks>=70)&(peaks<=542)
    peaks=peaks[good]
    widths,_,edges_l,edges_r=peak_widths(profile,peaks,rel_height=.51)
    bars=[dict(x_m=float(i/scale-1.26),width_m=float(np.clip(w/scale,.014,.065)),samples=float(w))
          for i,w in zip(peaks,widths)]
    # The west edge is a broad plate. A soft highlight on its right side
    # biases peak_widths; bracket its contiguous painted interval instead.
    edge=peaks[-1]
    floor=float(np.min(profile[edge-30:edge-5]))
    threshold=floor+.45*(profile[edge]-floor)
    left,right=int(edge),int(edge)
    while left>0 and profile[left-1]>=threshold:left-=1
    while right+1<len(profile) and profile[right+1]>=threshold:right+=1
    bars[-1].update(x_m=(left+right)/(2*scale)-1.26,width_m=(right-left+1)/scale,
                    contiguous_half_light_edges_px=[left,right])
    returns=[]
    for i,(l,r) in enumerate(zip(peaks,peaks[1:])):
        if r-l>39:continue
        # Use the centre of the clear interval, away from either vertical.
        arr=lum[:,round((l+r)/2)-1:round((l+r)/2)+2].mean(1)
        for name,zmin,zmax in [('bottom',.43,.61),('top',1.405,1.49)]:
            low,high=y(zmax),y(zmin)
            a=arr[low:high]
            # A local painted bridge between thin uprights has a light ridge,
            # with open dark spaces above and below it.
            if len(a)<3:continue
            ids,_=find_peaks(gaussian_filter1d(a,.9),prominence=12)
            if len(ids)==0:continue
            j=int(ids[np.argmax(a[ids])])
            if a[j]<28:continue
            returns.append(dict(left=i,right=i+1,kind=name,z_m=4.79-(low+j)/scale,
                                ridge_luminance=round(float(a[j]),1)))
    return dict(photograph=ref,board=dict(scale_px_per_m=scale,x0_m=-1.26,z_top_m=4.79,reference_plane_y_m=.79),
                sampling='Median luminance across the lower grille between z=.88 and 1.38 m, followed by half-prominence widths; returns measured between neighbouring uprights.',
                bars=bars,returns=returns)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('photo',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    d=measure(a.photo);a.output.write_text(json.dumps(d,ensure_ascii=False,indent=1)+'\n')
    print(len(d['bars']),len(d['returns']))
