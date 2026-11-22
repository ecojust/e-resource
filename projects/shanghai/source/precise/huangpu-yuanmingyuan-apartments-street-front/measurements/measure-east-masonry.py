"""Measure two brick arches and four gable slopes in the photographic reference images."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates,gaussian_filter1d
from scipy.optimize import least_squares
from scipy.signal import find_peaks,peak_widths

HERE=Path(__file__).resolve().parent


def luminosity(im,x,y):
    return sum(factor*map_coordinates(im[:,:,i],[y,x],order=1) for i,factor in enumerate([.30,.57,.13]))


def compute(street,detail):
    licensed=json.loads((HERE/'heritage-register-and-street-photographs.json').read_bytes())
    detail_meta=next(r for r in licensed['architectural_inventory']['photo_references'] if r['id']=='archive-14')
    for file,meta in [(street,licensed['primary_street_photo']),(detail,detail_meta)]:
        if hashlib.sha256(file.read_bytes()).hexdigest()!=meta['sha256']:raise ValueError(f'Unexpected source photograph: {file}')
    # The 850-wide guide defines the fitted concentric ellipses. Store the
    # observed seam centre in the native 1200-wide photo as well as its angle.
    a=np.asarray(Image.open(detail).convert('RGB')).astype(np.float32);k=a.shape[1]/850.
    th=np.linspace(.008,np.pi-.008,1400);r=np.linspace(-.18,1.2,125);t,r2=np.meshgrid(th,r)
    x=443.6+(150.+r2*71.8)*np.cos(t);y=251.-(120.+r2*61.)*np.sin(t)
    line=np.mean(luminosity(a,k*x,k*y)[(r>.20)&(r<.67)],axis=0)
    signal=gaussian_filter1d(line,.9)-gaussian_filter1d(line,9.)
    joints,p=find_peaks(-signal,distance=7,prominence=6.5)
    upper=[{'angle_rad':round(float(th[j]),6),'detail_px':[round(k*(443.6+(150.+.44*71.8)*np.cos(th[j])),2),round(k*(251.-(120.+.44*61.)*np.sin(th[j])),2)],'contrast':round(float(v),2)}for j,v in zip(joints,p['prominences'])]
    widths=peak_widths(-signal,joints,rel_height=.50)
    for item,left,right in zip(upper,widths[2],widths[3]):
        item['dark_joint_edges_rad']=np.interp([left,right],np.arange(len(th)),th).round(6).tolist()
    t=np.linspace(-1,1,850)[None,:];r=np.linspace(0,1,100)[:,None]
    x=448.+(195.-24.*r)*t;y=(446.+33*t*t)*(1-r)+(511.+13*t*t)*r
    band=np.median(luminosity(a,k*x,k*y)[18:70],axis=0)
    signal=gaussian_filter1d(band,1.2)-gaussian_filter1d(band,13.)
    joints,p=find_peaks(-signal,distance=14,prominence=9.)
    lower=[{'parameter':round(float(t[0,j]),6),'detail_px':[round(k*x[43,j],2),round(k*y[43,j],2)],'contrast':round(float(v),2)}for j,v in zip(joints,p['prominences'])]
    del a
    im=np.asarray(Image.open(street).convert('RGB'));scale=im.shape[1]/760.
    traces=[('south-left',(254,29,339,10)),('south-right',(339,10,408,80)),('north-left',(485,115,529,92)),('north-right',(530,90,574,139))]
    roofs={}
    for name,(x0,v0,x1,v1) in traces:
        xs=np.arange(round((x0+1)*scale),round((x1-1)*scale),3);near=(v0+(xs/scale-x0)/(x1-x0)*(v1-v0))*scale
        off=np.arange(-40,41);u=np.broadcast_to(xs[:,None],(len(xs),len(off)));v=near[:,None]+off[None,:]
        channels=[map_coordinates(im[:,:,i].astype(np.float32),[v,u],order=1)for i in range(3)];warm=channels[0]-channels[2];bright=np.mean(channels,axis=0)
        field=gaussian_filter1d(warm-.9*bright,.9,axis=1);gradient=field[:,4:]-field[:,:-4]
        k0=np.argmax(gradient-.04*off[None,2:-2]**2,axis=1);vs=near+off[k0+2];good=gradient[np.arange(len(xs)),k0]>18
        offset=(xs-xs.mean())/scale;fit=least_squares(lambda b:(b[0]+b[1]*offset-vs)[good],[vs.mean(),(v1-v0)/(x1-x0)*scale],loss='soft_l1',f_scale=2.).x
        good &= abs(fit[0]+fit[1]*offset-vs)<5.
        roofs[name]={'native_edge_points':np.column_stack((xs[good],vs[good])).round(2).tolist(),'line_native_slope_intercept':np.polyfit(xs[good],vs[good],1).tolist()}
    return {'source':'Livelikerw 2014 oblique, archive-14 2016 arched-bay detail and archive-05 frontal elevation. The control coordinates designate observed brick and coping edges; relief in metres is estimated.',
            'upper_radial_joints':upper,'lower_wedge_joints':lower,'gable_edges':roofs,
            'front_detail_guide':'Pixels in the central elevation study convert to original archive-05 pixels as u=480+x/1.75, v=y/1.75. The guide is the centre of the source image at higher scale.',
            'central_window_guides':{'arched':{'left':103,'right':333,'sill':231,'spring':166,'head':63,'outer_left':47,'outer_right':384,'outer_head':3},'segmental':{'left':99,'right':332,'sill':606,'spring':411,'head':390,'outer_left':77,'outer_right':356,'outer_spring':362,'outer_head':324}},
            'front_face_depth_m':.885,'arch_window_depth_m':1.37,'outer_wing_width_m':23.458}

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('street',type=Path);ap.add_argument('detail',type=Path);ap.add_argument('--output',type=Path,default=HERE/'east-brickwork-features.json');arg=ap.parse_args()
    result=compute(arg.street,arg.detail);arg.output.write_text(json.dumps(result,ensure_ascii=False,indent=1)+'\n')
