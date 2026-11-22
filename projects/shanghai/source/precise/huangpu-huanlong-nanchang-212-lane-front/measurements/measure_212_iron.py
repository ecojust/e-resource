"""Recompute Lane 212 arch and lantern measurements using three source images.

Use Antigng's Commons original, then the full native street frames named
gate212-2-201512.jpg and gate212-3-201512.jpg in the same order. The camera
record gives their checksums and station, bearing, field of view and crop.
"""
import argparse
import hashlib
import json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image,ImageOps
from scipy import ndimage
from scipy.optimize import least_squares

CAMERAS=['commons_2015','gate212-3-201512','gate212-2-201512']
def bases(record):
    balls=np.array(record['gate_controls']['globes_metres']);origin=balls.mean(axis=0);origin[2]=0.
    u=np.r_[balls[1,:2]-balls[0,:2],0.];u/=np.linalg.norm(u)
    return origin,u,np.array([-u[1],u[0],0.]),np.array([0.,0.,1.])
def orthophoto(record,key,image):
    origin,u,v,up=bases(record);x,z=np.meshgrid(np.arange(1100)/207.-2.65,5.58-np.arange(1160)/207.)
    points=origin+x[:,:,None]*u-.30*v+z[:,:,None]*up
    P=np.array(record['camera_matrices'][key]);q=points@P[:,:3].T+P[:,3];uv=q[:,:,:2]/q[:,:,2:]
    return cv2.remap(image,uv[:,:,0].astype('float32'),uv[:,:,1].astype('float32'),cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
def arches(record,images):
    plates={cam:orthophoto(record,cam,images[cam]).mean(axis=2)for cam in CAMERAS};result={}
    for name,height,half,rise in [('outer',4.565,2.263,.91),('inner',4.02,1.650,.61)]:
        out=[]
        for cam in CAMERAS:
            lum=plates[cam];pts=[]
            for u in np.linspace(-half+.03,half-.03,31):
                x=int(round((u+2.65)*207));guess=height-rise*(u/half)**2
                hint=guess+{'commons_2015':0.,'gate212-3-201512':.040,'gate212-2-201512':.050}[cam]
                zs=5.58-np.arange(lum.shape[0])/207.;candidates=np.where(np.abs(zs-hint)<(.090 if cam=='commons_2015' else .10))[0]
                profile=np.median(lum[:,x-2:x+3],axis=1)
                # Locate a dark strap between two lighter sides. A weak ridge
                # is retained as an unused observation in the published table.
                contrast=np.minimum(profile[candidates-6],profile[candidates+6])-profile[candidates]-.19*np.abs((zs[candidates]-hint)*207)
                k=np.argmax(contrast);z=zs[candidates[k]];quality=float(contrast[k])
                pts.append(dict(u_m=round(float(u),4),z_m=round(float(z),4),local_contrast=round(quality,2),use=quality>7))
            out.append({'camera':cam,'samples':pts})
        primary=np.array([(p['u_m']/half,p['z_m'])for p in out[0]['samples']if p['use']])
        def residual(v):
            t=primary[:,0];return np.r_[v[0]+v[1]*t+v[2]*t*t+v[3]*t**4-primary[:,1],v[3]*.10]
        coef=least_squares(residual,[height,0,-rise,0],loss='soft_l1',f_scale=.018).x
        result[name]={'halfspan_m':half,'height_polynomial':coef.tolist(),'derivation':'Primary metric samples from Commons. Polynomial z = a + b*t + c*t² + d*t⁴; t = u/halfspan. The two December views independently document the member in winter.','samples':out}
    return result
def lamps_and_leaf(record,images):
    origin,u,v,up=bases(record)
    bounds={'commons_2015':[(3464,1896,80,52),(3894,1831,90,70)],'gate212-2-201512':[(465,375,22,16),(563,385,14,14)],'gate212-3-201512':[(300,365,24,17),(450,366,22,17)]}
    views={}
    for cam,regions in bounds.items():
        picks=[]
        for cx,cy,dx,dy in regions:
            r,g,b=images[cam][cy-dy:cy+dy+1,cx-dx:cx+dx+1].astype(float).transpose(2,0,1)
            mask=(r>1.24*g)&(r>1.22*b)&(r>(54 if cam=='commons_2015' else 34))
            labels,n=ndimage.label(ndimage.binary_closing(mask,iterations=2))
            if not n:raise ValueError('No red lantern patch in the prescribed source region.')
            ys,xs=np.nonzero(labels==np.argmax(np.bincount(labels.ravel())[1:])+1)
            picks.append([round(cx-dx+float(np.median(xs)),3),round(cy-dy+float(np.median(ys)),3)])
        views[cam]=picks
    lamps=[]
    for idx in (0,1):
        def residual(par):
            xyz=origin+par[0]*u+par[1]*v+par[2]*up;errors=[]
            for cam in bounds:
                p=np.asarray(record['camera_matrices'][cam])@np.r_[xyz,1.]
                errors.extend((p[:2]/p[2]-views[cam][idx])/(3.6 if cam=='commons_2015' else 1.))
            return errors
        fit=least_squares(residual,[-.64 if idx==0 else .81,0.,3.60],loss='soft_l1',f_scale=3.5)
        lamps.append(dict(local_uvz=fit.x.tolist(),fit_residuals_rescaled=residual(fit.x)))
    return dict(principal_photo=record['source_url'],three_camera_lantern_observations_native_pixels=views,lanterns=lamps,west_leaf={'visible_hinge_xz_cc_px':[3297,2275],'free_upper_px':[3598,2115],'free_bottom_px':[3634,2906],'estimated_hinge_uv_m':[-1.62,.42651],'length_m':1.61,'angle_inward_deg':83.20406,'elevations_m':[2.54092,3.17757,.58997],'note':'Three identifiable points in the dated photograph, using half the clear width. Door state is September 2015. East mobile leaf largely concealed.'},source_rights='Antigng, CC BY-SA 4.0. Winter street photographs used for geometry only.')
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('commons','west','center','output'):parser.add_argument(key,type=Path)
    parser.add_argument('--cameras',type=Path,default=Path(__file__).with_name('212-window-cameras.json'));args=parser.parse_args()
    record=json.loads(args.cameras.read_bytes());files=dict(zip(CAMERAS,[args.commons,args.center,args.west]));images={}
    for key,path in files.items():
        target=record['original_sha256']if key=='commons_2015'else record['street_sources'][key]['sha256']
        if hashlib.sha256(path.read_bytes()).hexdigest()!=target:raise ValueError(f'Unexpected original checksum for {key}.')
        images[key]=np.array(ImageOps.exif_transpose(Image.open(path)).convert('RGB'))
    args.output.mkdir(parents=True,exist_ok=True)
    for f,data in [('arch-curves.json',arches(record,images)),('lane212-iron-street-fabric.json',lamps_and_leaf(record,images))]:
        (args.output/f).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
