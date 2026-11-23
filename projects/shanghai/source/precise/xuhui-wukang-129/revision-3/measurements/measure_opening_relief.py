"""Measure the two open balcony casements and repeated stonework from the two CC photos."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, map_coordinates
from scipy.optimize import minimize_scalar
from scipy.signal import find_peaks

from register_openings import Camera

HERE=Path(__file__).absolute().parent

def correlation_lines(pixels, detrend_sigma, count):
    a=pixels-gaussian_filter(pixels,(detrend_sigma,0))
    a/=np.std(a,axis=0,keepdims=True)+1.e-5
    corr=np.array([1.]+[np.mean(a[s:]*a[:-s])/np.sqrt(np.mean(a[s:]**2)*np.mean(a[:-s]**2)) for s in range(1,count)])
    return a,corr

def sample(im, u, v, scale):
    return map_coordinates(im,[scale*(v+.5)-.5,scale*(u+.5)-.5],order=1)

def read_grooves(yr,im,cam):
    scale=4 if yr==2017 else 1
    if yr==2017:
        patches=[(735.7,738.5,468.,572.),(842.3,847.7,468.,572.)]
        xc,yc,xr,yrad,shear=795.5,449.5,54.,53.,.09
    else:
        patches=[(977.5,978.8,785.,903.),(1098.,1100.3,785.,903.)]
        xc,yc,xr,yrad,shear=1040.5,764.5,62.,62.,.041
    legs=[]
    for side,(x0,x1,y0,y1) in zip(['left','right'],patches):
        y=np.linspace(y0,y1,round((y1-y0)*scale)+1)
        x=np.linspace(-4,4,15)
        xx=np.interp(y,[y0,y1],[x0,x1])[:,None]+x
        yy=np.broadcast_to(y[:,None],xx.shape)
        pix=sample(im,xx,yy,scale)
        a,corr=correlation_lines(pix,7*scale,round(32*scale))
        peaks=find_peaks(corr)[0]
        # The first ridge and its harmonics agree, a slope through all peaks
        # reduces whole-pixel quantisation in the lower-resolution 2026 JPEG.
        initial=max((s for s in peaks if 3.3*scale<=s<=5.5*scale),key=lambda s:corr[s])
        peaks=[int(s) for s in peaks if corr[s]>.18 and abs(s/initial-round(s/initial))<.39]
        initial=np.average([s/max(round(s/initial),1) for s in peaks],weights=[corr[s]*s for s in peaks])
        Y0=cam.wall((scale*(x0+.5)-.5,scale*(y0+.5)-.5),-.075)
        Y1=cam.wall((scale*(x1+.5)-.5,scale*(y1+.5)-.5),-.075)
        g_y,g_x=np.gradient(gaussian_filter(a,(.5*scale,.6)),1/scale,8/14)
        slopes=-np.sum(g_x*g_y,axis=0)/np.maximum(np.sum(g_y**2,axis=0),1.e-12)
        legs.append({'side':side,'native_pixel_path_centres':[[scale*(x0+.5)-.5,scale*(y0+.5)-.5],[scale*(x1+.5)-.5,scale*(y1+.5)-.5]],'sample_length_m':float(np.linalg.norm(Y0-Y1)),'pitch_native_px':float(initial),'pitch_m':float(initial*np.linalg.norm(Y0-Y1)/((y1-y0)*scale)),'ridge_down_right_dv_du':float(np.median(slopes[3:-3])),'correlation_peaks_lag_px_and_r':[ [s,float(corr[s])] for s in peaks]})
    tt=np.linspace(-1.40,1.40,1024)[:,None]
    rr=np.linspace(-3.5,3.5,11)
    u=xc+(xr+rr)*np.sin(tt)-shear*(yrad+rr)*np.cos(tt)
    v=yc-(yrad+rr)*np.cos(tt)
    _,corr=correlation_lines(sample(im,u,v,scale),23,96)
    peaks=[int(s) for s in find_peaks(corr)[0] if 20<=s and corr[s]>.08]
    lag=peaks[0]
    arch={'quarter_or_native_sample_ellipse':[xc,yc,xr,yrad,shear],'sampling_scale_to_native':scale,'angle_limits_rad':[-1.4,1.4],'samples':1024,'arc_correlation_peaks_and_r':[[s,float(corr[s])] for s in peaks],'estimated_repeats_per_semicircle':float(np.pi/(lag*2.8/1023)),'interpretation':'Frequency estimate from the visible arc; count can vary by one or two near the spring joins.'}
    return {'legs':legs,'crown':arch}

def opening_geometry(yr,cam,obs):
    features=obs['openings']
    def pos(key):
        return cam.wall(features[key][str(yr)],.04)
    left=pos('E-left-moving-hinge-upper');right=pos('E-right-moving-hinge-upper')
    length=(right[0]-left[0])/2-.012
    leaves=[]
    for side,hinge,sign in [('left',left,1),('right',right,-1)]:
        target=np.array(features[f'E-{side}-moving-free-upper'][str(yr)])
        def free(a):
            ang=np.radians(a)
            return hinge+np.array([sign*length*np.cos(ang),-length*np.sin(ang),0])
        def solve(target):
            def error(a):
                return np.linalg.norm(cam.builder_pixel(free(a))-target)
            return minimize_scalar(error,bounds=(0,150),method='bounded')
        fit=solve(target)
        tol=7. if yr==2017 else 2.5
        angles=[float(solve(target+[du,dv]).x) for du in (-tol,tol) for dv in (-tol,tol)]
        leaves.append({'side':side,'width_m':float(length),'hinge_builder_u_depth_z_m':hinge.tolist(),'observed_free_upper_native_px':target.tolist(),'outward_open_angle_deg':float(fit.x),'angle_range_corner_readout_only_deg':[min(angles),max(angles)],'free_corner_builder_u_depth_z_m':free(fit.x).tolist(),'projected_free_upper_native_px':cam.builder_pixel(free(fit.x)).tolist(),'pixel_error':float(fit.fun)})
    gate={}
    for name,o in features.items():
        if name.startswith('D-'):
            y=.045 if 'inner' in name else -.075
            gate[name]=cam.wall(o[str(yr)],y).tolist()
    ring={name:pos(name).tolist() for name in features if name.startswith(('E-fixed','E-inner'))}
    return {'leaf_angle_convention':'0 when closed on existing tangent plane, increasing toward the street. Right and left refer to the photograph. Leaves estimated independently in each exposure. Assumed tangent at inward +.04m, each clear effective width half the hinge spacing less 12 mm.','leaf_results':leaves,'future_glass_subdivisions':'Three intermediate horizontal members visible in right leaf, forming four stacked lights. Left is narrower in projection; same subdivisions require inspection where obscured. Fixed fanlight shows an inner half-ring, centre radial and two obliques.','gate_points_builder_u_depth_z_m':gate,'fixed_fanlight_builder_u_depth_z_m':ring}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--references',type=Path,default=HERE.parents[1]/'references')
    parser.add_argument('--observations',type=Path,default=HERE/'opening-observations.json')
    parser.add_argument('--registration',type=Path,default=HERE/'two-photo-cameras.json')
    parser.add_argument('--output',type=Path,default=HERE/'opening-relief-measures.json')
    args=parser.parse_args()
    obs=json.loads(args.observations.read_text())
    report={'schema':'wukang129-original-photograph-opening-and-relief-measurements-1','source_coordinates':'Existing local 3733 ENU frame unchanged. Numeric construction positions here are u toward photograph right, inward depth positive, Z up.','control_sha256':hashlib.sha256(args.observations.read_bytes()).hexdigest(),'camera_sha256':hashlib.sha256(args.registration.read_bytes()).hexdigest(),'images':{}}
    for yr in [2017,2026]:
        f=next(args.references.glob(f'{yr}*.jpg'))
        assert hashlib.sha256(f.read_bytes()).hexdigest()==obs['rights'][str(yr)]['original_jpeg_sha256']
        cam=Camera(yr,args.registration)
        data=opening_geometry(yr,cam,obs)
        data['source']=obs['rights'][str(yr)]
        data['gate_grooves']=read_grooves(yr,np.array(Image.open(f).convert('L'),dtype=np.float32),cam)
        report['images'][str(yr)]=data
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':
    main()
