"""Recompute the entrance section from the original measurements in this folder."""
from pathlib import Path
import json
import numpy as np
from scipy.optimize import least_squares
HERE=Path(__file__).resolve().parent

def read(name):return json.loads((HERE/name).read_text())

def backproject(p,uv,y):
    h=np.column_stack([uv,np.ones(len(uv))])@np.linalg.inv(np.column_stack((p[:,[0,2]],p[:,3]+p[:,1]*y))).T
    return h[:,:2]/h[:,2:]

def main():
    ref=read('complete-entrance-arch.json');samples=np.asarray(ref['native_pixels_and_local_sections'])
    use=np.asarray(ref['sections_included']);p=np.asarray(read('porch-frontal-camera.json')['P'])
    x,z=backproject(p,samples[use,3:5],ref['back_of_soffit_y_m']).T
    def residual(v,x,z):
        cx,r,h,b=v
        return (((x-cx)/r)**2+((z-b)/h)**2-1)/2
    f=least_squares(lambda v:np.r_[residual(v,x,z),(v[3]-.018)*10],[1.49,1.60,.98,.018],
                    loss='soft_l1',f_scale=.010,bounds=([1.38,1.32,.78,-.05],[1.56,1.72,1.24,.06]))
    target=[ref[k] for k in ['ellipse_center_x','horizontal_radius_m','rise_m','spring_z_m']]
    assert np.max(abs(f.x-target))<.0001
    close=read('porch-arch-section.json');q=np.asarray(read('porch-camera.json')['P'])
    xz=backproject(q,np.array(close['inner_arris_pixels']),.207)
    print('Clear span %.3f m, rise %.3f m, %d frontal sections.'%(f.x[1]*2,f.x[2],len(use)))
    print('Independent close-photo observations',len(xz),'median dimensionless ellipse residual',
          round(float(np.median(abs(residual(f.x,*xz.T)))),5))
    vps=read('porch-source-lines.json')['axes']
    for axis,r in vps.items():
        px=np.asarray(r['segments']);vp=np.asarray(r['vp']);idx=np.asarray(r['hold']);a=px[:,:2];b=px[:,2:]
        h=vp-(a+b)/2;d=b-a
        errors=abs((h[:,0]*d[:,1]-h[:,1]*d[:,0])/np.linalg.norm(h,axis=1))
        print(axis,'held-out lines',len(idx),'median native residual',round(float(np.median(errors[idx])),3),'px')
    print('Pavement focal registrations',read('tiled-pavement.json')['repeat_spacing_m'])
if __name__=='__main__':main()
