"""Sample the shaded plaster, pier and door colour fields at two registered camera poses."""
import argparse,json
from pathlib import Path
import numpy as np
from scipy.ndimage import map_coordinates, gaussian_filter
from PIL import Image
from register_gate import Camera

RECTANGLES={
 'cream plaster':[(0.,-.67,-.28,2.38,2.67),(0.,.24,.74,2.38,2.67)],
 'blue grey pier':[(-.077,-1.39,-1.13,1.69,2.59),(-.077,1.15,1.48,1.69,2.58)],
 'dark door':[(.12,-.62,-.29,1.35,1.92),(.12,.29,.68,1.36,1.94)]}

def sample(image,cam,rect):
    y,left,right,bottom,top=rect
    step=.005
    x,z=np.meshgrid(np.arange(left,right,step),np.arange(bottom,top,step))
    ps=np.stack([x,z*0+y,z,np.ones_like(x)]).reshape((4,-1));q=cam.p@ps
    u,v=(q[:2]/q[2]).reshape((2,*x.shape));ij=[v,u]
    good=(u>=.5)&(u<image.shape[1]-1.5)&(v>=.5)&(v<image.shape[0]-1.5)
    col=np.stack([map_coordinates(t,ij,order=1,mode='nearest') for t in image.transpose(2,0,1)],axis=2)
    if good.sum()<100:return None
    values=col[good];lo,hi=np.percentile(values, [10,90],axis=0)
    mid=np.median(values,axis=0);lum=col.mean(axis=2);mask=good.copy()
    # Omit extremes from ringing, crossing wires and clipped paint highlights.
    mask&=np.all((col>=lo)&(col<=hi),axis=2);mask=gaussian_filter(mask.astype(float),1.)>.96
    def adjacent(axis,n):
        r=np.roll(lum,n,axis);m=mask&np.roll(mask,n,axis)
        if axis==0:m[:n,:]=False
        else:m[:,:n]=False
        return float(np.median(np.abs(lum[m]-r[m]))) if m.any() else None
    return {'count':int(good.sum()),'median_rgb':mid.tolist(),'rgb_p10':lo.tolist(),'rgb_p90':hi.tolist(),
            'median_in_plane_luminance_change':{str(n*step):[adjacent(1,n),adjacent(0,n)]for n in (1,3,8,16)},'rectangle':rect}

def measure(photos):
    out={}
    for mat,rects in RECTANGLES.items():
        out[mat]={}
        for view,f in photos.items():
            im=np.asarray(Image.open(f).convert('RGB'),float);c=Camera(view)
            out[mat][view]=[r for rc in rects if (r:=sample(im,c,rc)) is not None]
    return out
if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('portrait',type=Path);cli.add_argument('landscape',type=Path);cli.add_argument('output',type=Path)
    a=cli.parse_args();result=measure({'06':a.portrait,'07':a.landscape});a.output.write_text(json.dumps(result,indent=2)+'\n')
